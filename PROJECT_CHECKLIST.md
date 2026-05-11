# PROJECT_CHECKLIST.md

## Task 1 — Docker / Infrastructure

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Dev compose: `web` + `postgres` services | ⬜ Not started | `docker-compose.yml` | Currently has web + db; needs schema.sql mount |
| Prod compose: `web` + `postgres` + `nginx` | ⬜ Not started | `docker-compose.prod.yml` | Structure exists; needs schema.sql mount |
| `docker compose up` starts the webpage | ⬜ Not started | `docker-compose.yml` | App returns hello-world only; real routes not yet built |
| Persistent volumes (data survives container stop) | ⬜ Not started | `docker-compose.yml`, `docker-compose.prod.yml` | Named volumes exist but schema not yet persistent |
| Non-sensitive files stored in Git | ⬜ Not started | repo root | `.env.prod` / `.env.prod.db` must stay out of Git |
| CI: build containers, start, pass only on no errors | ⬜ Not started | `.github/workflows/ci.yml` | Currently only tests `GET /` |

## Task 2 — Database Schema

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Schema file at `services/postgres/schema.sql` | ⬜ Not started | `services/postgres/schema.sql` | File does not exist yet |
| `schema.sql` loads automatically on DB startup | ⬜ Not started | `docker-compose.yml` | Mount into `/docker-entrypoint-initdb.d/` |
| At least 3 tables | ⬜ Not started | `schema.sql` | Planned: `users`, `messages`, `sessions` (or similar) |
| Every table has a primary key | ⬜ Not started | `schema.sql` | |
| Every table has ≥ 2 columns with types/constraints | ⬜ Not started | `schema.sql` | |
| Appropriate indexes for all fast routes | ⬜ Not started | `schema.sql` | Includes full-text search index |
| RUM index for full-text search (preferred over GIN) | ⬜ Not started | `schema.sql` | Requires `rum` extension; fallback to GIN if unavailable |
| Test data loading script | ⬜ Not started | `services/postgres/load_test_data.sql` (or `.py`) | |
| After script: ≥ 2 tables have ≥ 1,000,000 rows | ⬜ Not started | test data script | `messages` + `users` are the likely targets |

## Routes

### `/` — Homepage feed

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link always visible in menu | ⬜ Not started | `templates/base.html` | |
| Displays all messages, newest first | ⬜ Not started | `project/__init__.py` or blueprint | No-JOIN query acceptable here |
| Each message shows username, creation time, body | ⬜ Not started | `templates/index.html` | Requires JOIN on users |
| 20 messages per page | ⬜ Not started | route handler | Use `LIMIT`/`OFFSET` |
| Previous / next pagination | ⬜ Not started | `templates/index.html` | Pass page param in URL |

### `/login`

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link visible only when logged out | ⬜ Not started | `templates/base.html` | |
| Form with username + password (password hidden) | ⬜ Not started | `templates/login.html` | `<input type="password">` |
| Error shown for wrong username/password | ⬜ Not started | route handler | Do not reveal which field is wrong |
| Redirect to `/` on success | ⬜ Not started | route handler | Set session cookie |

### `/logout`

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link visible only when logged in | ⬜ Not started | `templates/base.html` | |
| Clears session/cookies | ⬜ Not started | route handler | `session.clear()` |

### `/create_account`

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link visible only when logged out | ⬜ Not started | `templates/base.html` | |
| Error on duplicate username | ⬜ Not started | route handler | Catch unique constraint violation |
| Password entered twice; mismatch gives error | ⬜ Not started | `templates/create_account.html` | Validate in Python, not only JS |

### `/create_message`

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link visible only when logged in | ⬜ Not started | `templates/base.html` | |
| Form to write message body | ⬜ Not started | `templates/create_message.html` | |
| Stores user id + creation timestamp | ⬜ Not started | route handler | `user_id` FK, `created_at TIMESTAMPTZ DEFAULT NOW()` |
| New message appears on homepage immediately | ⬜ Not started | route handler | Redirect to `/` after insert |

### `/search`

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Link always visible in menu | ⬜ Not started | `templates/base.html` | |
| Input field for search query | ⬜ Not started | `templates/search.html` | |
| Full-text search over messages | ⬜ Not started | route handler | Use `tsvector`/`tsquery`; parameterized query |
| Results similar to homepage (username, time, body) | ⬜ Not started | `templates/search.html` | |
| Pagination for many matches | ⬜ Not started | route handler + template | |
| Order by relevance (ts_rank) | ⬜ Not started | route handler | For full credit |
| Highlight matching terms (ts_headline) | ⬜ Not started | `templates/search.html` | For full credit |
| RUM index used | ⬜ Not started | `schema.sql` | For full credit |
| Spelling suggestions via pg_trgm | ⬜ Not started | `schema.sql` + route | Extra credit only; implement last |

## SQL Safety

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Parameterized queries everywhere | ⬜ Not started | all route handlers | psycopg2 `%s` or SQLAlchemy bound params |
| No SQL f-strings or string concatenation from user input | ⬜ Not started | all route handlers | |

## Query Coverage

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| At least one query with no JOIN | ⬜ Not started | TBD | e.g., fetch session user by id |
| At least one query with a JOIN | ⬜ Not started | TBD | e.g., messages JOIN users |
| At least one full-text search query | ⬜ Not started | `/search` route | |

## App Housekeeping

| Requirement | Status | File/Route | Notes |
|---|---|---|---|
| Remove `db.drop_all()` from `manage.py` | ⬜ Not started | `services/web/manage.py` | Critical — prevents data loss on restart |
| Set `APP_FOLDER` env var in `.env.dev` | ⬜ Not started | `.env.dev` | Config.py static/media folders depend on it |
| Flask secret key set for sessions | ⬜ Not started | `.env.dev`, `config.py` | Required for `session` cookie |

---

**Legend:** ⬜ Not started | 🔄 In progress | ✅ Done | ❌ Blocked
