import os
import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

PER_PAGE = 20


def get_db_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


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
        logged_in=False,
    )


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)
