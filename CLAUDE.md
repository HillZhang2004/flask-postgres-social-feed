# CLAUDE.md — Project Rules and Constraints

## Environment

- All development, Docker commands, database work, and testing must run on the Lambda server (`~/flask-postgres-social-feed`).
- Do not run commands on a local laptop or local VSCode.
- The professor will connect to a port on the Lambda server during the demo; the server must already be running.

## Project Goal

Build a Twitter-clone social feed web app using Flask + Postgres + Nginx, containerized with Docker Compose, with a GitHub Actions CI workflow.

## Required Routes (exact paths — do not rename)

| Route | Auth state | Purpose |
|---|---|---|
| `/` | always visible | Paginated feed of all messages, newest first, 20/page |
| `/login` | logged-out only | Username + password form; redirect to `/` on success |
| `/logout` | logged-in only | Clear session/cookies, log out |
| `/create_account` | logged-out only | Register new user; validate duplicate username, password confirm |
| `/create_message` | logged-in only | Post a new message; stores user id + timestamp |
| `/search` | always visible | Full-text search over messages; paginated results ordered by relevance; highlight matches |

- Use Jinja2 HTML templates with a visible navigation menu. Not a JSON-only API.
- Menu link visibility must change based on login state (see table above).

## Database Rules

- Schema file: `services/postgres/schema.sql` — this is the source of truth for all tables and indexes.
- `schema.sql` must load automatically on database container startup (via Docker volume mount into `/docker-entrypoint-initdb.d/`).
- At least 3 tables. Every table must have a primary key and at least 2 columns with appropriate types and constraints.
- Add all indexes needed for fast routes in `schema.sql`.
- Use a RUM index (not GIN) for full-text search if feasible; order search results by relevance; highlight matching terms.
- Include a separate script that loads test data: after running it, at least 2 tables must have ≥ 1,000,000 rows.
- Persistent named volumes — database data must not be wiped when containers stop.

## SQL Safety

- Use parameterized queries everywhere (psycopg2 `%s` placeholders or SQLAlchemy bound params).
- Never build SQL strings with f-strings or string concatenation from user input.
- SQL injection in any route results in negative points for that route.

## Query Requirements (must implement all three)

- At least one query with no JOIN.
- At least one query with a JOIN.
- At least one full-text search query.

## Flask App Constraints

- Remove the `db.drop_all()` call from `manage.py::create_db`. Schema is managed by `schema.sql`, not SQLAlchemy's `create_all`/`drop_all`.
- The database must persist across container restarts.
- `APP_FOLDER` env var must be set so `config.py` can resolve `STATIC_FOLDER` and `MEDIA_FOLDER`.

## Docker Compose

- `docker-compose.yml` (dev): `web` + `db` services. App reachable on port 8765.
- `docker-compose.prod.yml` (prod): `web` + `db` + `nginx`. Nginx on port 1340.
- Both must use persistent named volumes for Postgres data.

## GitHub Actions (`ci.yml`)

- Must build containers, start containers, and pass only when there are no startup errors.
- Runs on push/PR to `main`.

## Destructive Commands — Never Run Without Explicit Approval

- `docker compose down -v`
- `docker volume prune`
- `docker system prune -a`
- `rm -rf`
- `git reset --hard`
- `git clean -fdx`

## Work Style

- Work in small stages. Test after each stage before moving on.
- Store all non-sensitive project files in Git (no secrets, no `.env.prod` files).
