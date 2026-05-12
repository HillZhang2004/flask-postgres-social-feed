![Build and Test Dev Environment](https://github.com/HillZhang2004/flask-postgres-social-feed/actions/workflows/ci.yml/badge.svg?branch=build-final-project)
# Flask + Postgres Social Feed

A Twitter-clone social feed web app built with Flask, Postgres, Gunicorn, and Nginx, fully containerized with Docker Compose and tested via GitHub Actions CI.

## Overview

Users can create accounts, log in, post short messages, browse a paginated feed of all messages, and search posts using full-text search with highlighted matches. The app runs as a multi-container system with separate services for the web application, database, and reverse proxy.

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** Postgres with RUM index for full-text search
- **App Server:** Gunicorn
- **Reverse Proxy:** Nginx
- **Containerization:** Docker, Docker Compose
- **CI:** GitHub Actions

## Features

- User registration and login with session-based authentication
- Paginated feed of all messages, newest first (20 per page)
- Post creation restricted to authenticated users
- Full-text search over messages, results ordered by relevance with highlighted matches
- RUM index on the messages table for performant search
- Persistent named Postgres volume — data survives container restarts
- Separate dev (`docker-compose.yml`) and prod (`docker-compose.prod.yml`) configurations
- Test data loader that inserts ≥ 1,000,000 rows into key tables

## Routes

| Route | Auth required | Description |
|---|---|---|
| `/` | No | Paginated feed of all messages |
| `/login` | No (logged-out only) | Username + password login |
| `/logout` | Yes | Clear session and log out |
| `/create_account` | No (logged-out only) | Register a new account |
| `/create_message` | Yes | Post a new message |
| `/search` | No | Full-text search with relevance ranking |

## Architecture

- **web** — Flask app container: routing, authentication, database queries via psycopg2
- **db** — Postgres container: schema loaded automatically from `services/postgres/schema.sql` on first start
- **nginx** — Reverse proxy (prod only): forwards traffic to Gunicorn, serves static files

## Project Structure

```
services/
  web/          Flask app, Dockerfiles, requirements
  nginx/        Nginx config (prod)
  postgres/     schema.sql, test data loader
docker-compose.yml          dev stack (port 8765)
docker-compose.prod.yml     prod stack with Nginx (port 1340)
.env.dev                    development environment variables
.github/workflows/ci.yml    GitHub Actions CI
```

## Development Setup

Start the development stack (app on port 8765):

```bash
docker compose up -d --build
```

The development app is reachable at http://localhost:8765/.

Load 1,000,000 seed users and 1,000,000 seed messages into the development database:

```bash
docker compose exec -T db psql -U hello_flask -d hello_flask_dev < services/postgres/load_test_data.sql
```

## Production Setup

Create local production env files from the examples:

```bash
cp .env.prod.example .env.prod
cp .env.prod.db.example .env.prod.db
```

Edit both files with local production values. These files are gitignored and should not be committed.

Start the production stack (Nginx on port 1340):

```bash
docker compose -p flask-social-prod -f docker-compose.prod.yml up -d --build
```

The production app is reachable through Nginx at http://localhost:1340/.

## CI

GitHub Actions runs on pushes to `main` and `build-final-project`, and on pull requests to `main`. The workflow builds all containers, starts them, and verifies:

- homepage returns HTTP 200
- the `rum` Postgres extension is installed
- all four schema tables exist
- the `idx_messages_rum` index exists
