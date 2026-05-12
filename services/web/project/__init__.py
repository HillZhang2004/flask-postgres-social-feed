import html as _html
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from markupsafe import Markup

from flask import (
    Flask, flash, redirect, render_template,
    request, send_from_directory, session, url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

PER_PAGE = 20

_HL_OPTIONS = "StartSel=__HL_START__, StopSel=__HL_END__, HighlightAll=true"


def _apply_highlight(raw):
    escaped = _html.escape(raw)
    return Markup(
        escaped
        .replace("__HL_START__", "<mark>")
        .replace("__HL_END__", "</mark>")
    )


def get_db_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@app.context_processor
def inject_auth():
    return {
        "logged_in": "user_id" in session,
        "current_user": session.get("username"),
    }


@app.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    offset = (page - 1) * PER_PAGE

    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT m.message_id, u.username, m.body, m.created_at
                FROM messages m
                JOIN users u ON u.user_id = m.user_id
                ORDER BY m.created_at DESC, m.message_id DESC
                LIMIT %s OFFSET %s
                """,
                (PER_PAGE, offset),
            )
            messages = cur.fetchall()

            cur.execute("SELECT COUNT(*) AS total FROM messages")
            total = cur.fetchone()["total"]

    has_prev = page > 1
    has_next = (offset + PER_PAGE) < total

    return render_template(
        "index.html",
        messages=messages,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
    )


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if "user_id" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username:
            error = "Username is required."
        elif len(username) > 50:
            error = "Username cannot be longer than 50 characters."
        elif not password:
            error = "Password is required."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            with get_db_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Pre-check for a clearer UX error message.
                    cur.execute(
                        "SELECT user_id FROM users WHERE username = %s",
                        (username,),
                    )
                    if cur.fetchone():
                        error = "Username already taken."
                    else:
                        # ON CONFLICT DO NOTHING guards against race conditions.
                        cur.execute(
                            """
                            INSERT INTO users (username) VALUES (%s)
                            ON CONFLICT (username) DO NOTHING
                            RETURNING user_id
                            """,
                            (username,),
                        )
                        row = cur.fetchone()
                        if row is None:
                            error = "Username already taken."
                        else:
                            cur.execute(
                                "INSERT INTO credentials (user_id, password_hash) VALUES (%s, %s)",
                                (row["user_id"], generate_password_hash(password)),
                            )

            if error is None:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))

    return render_template("create_account.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        else:
            with get_db_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT u.user_id, u.username, c.password_hash
                        FROM users u
                        JOIN credentials c ON c.user_id = u.user_id
                        WHERE u.username = %s
                        """,
                        (username,),
                    )
                    row = cur.fetchone()

            if row is None or not check_password_hash(row["password_hash"], password):
                error = "Invalid username or password."
            else:
                session.clear()
                session["user_id"] = row["user_id"]
                session["username"] = row["username"]
                return redirect(url_for("index"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/create_message", methods=["GET", "POST"])
def create_message():
    if "user_id" not in session:
        return redirect(url_for("login"))

    error = None
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if not body:
            error = "Message cannot be blank."
        else:
            with get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO messages (user_id, body) VALUES (%s, %s)",
                        (session["user_id"], body),
                    )
            return redirect(url_for("index"))

    return render_template("create_message.html", error=error)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    offset = (page - 1) * PER_PAGE

    results = []
    total = 0

    if q:
        with get_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        m.message_id,
                        u.username,
                        m.created_at,
                        ts_rank(m.tsv, websearch_to_tsquery('english', %s)) AS rank,
                        ts_headline(
                            'english', m.body,
                            websearch_to_tsquery('english', %s),
                            %s
                        ) AS headline
                    FROM messages m
                    JOIN users u ON u.user_id = m.user_id
                    WHERE m.tsv @@ websearch_to_tsquery('english', %s)
                    ORDER BY rank DESC, m.message_id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (q, q, _HL_OPTIONS, q, PER_PAGE, offset),
                )
                rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM messages
                    WHERE tsv @@ websearch_to_tsquery('english', %s)
                    """,
                    (q,),
                )
                total = cur.fetchone()["total"]

        results = [
            {**row, "headline": _apply_highlight(row["headline"])}
            for row in rows
        ]

    has_prev = page > 1
    has_next = (offset + PER_PAGE) < total

    return render_template(
        "search.html",
        q=q,
        results=results,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
    )


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)
