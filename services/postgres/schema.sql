-- services/postgres/schema.sql
-- Source of truth for all tables, indexes, and extensions.
-- Loaded automatically on first container start via /docker-entrypoint-initdb.d/.

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------

-- pg_trgm is available in the stock postgres:13 image.
-- Keep pg_trgm; it may be used later for spelling suggestions.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- rum is installed via services/postgres/Dockerfile (postgresql-13-rum package).
CREATE EXTENSION IF NOT EXISTS rum;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    user_id    SERIAL      PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (BTRIM(username) <> '')
);

CREATE TABLE IF NOT EXISTS credentials (
    user_id       INTEGER     PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    password_hash TEXT        NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    message_id BIGSERIAL   PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    body       TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tsv        TSVECTOR    GENERATED ALWAYS AS (to_tsvector('english', body)) STORED,
    CHECK (BTRIM(body) <> '')
);

CREATE TABLE IF NOT EXISTS follows (
    follower_id INTEGER     NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    followed_id INTEGER     NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, followed_id),
    CHECK (follower_id <> followed_id)
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

-- users(username): the UNIQUE constraint already creates a btree index on
-- username, so no separate CREATE INDEX is needed here.

-- Stable newest-first ordering for the paginated homepage feed.
CREATE INDEX IF NOT EXISTS idx_messages_created_at_id
    ON messages (created_at DESC, message_id DESC);

-- Fast per-user message lookups and messages JOIN users queries.
CREATE INDEX IF NOT EXISTS idx_messages_user_id
    ON messages (user_id);

-- RUM index on the generated tsvector column for ranked full-text search.
-- Requires the postgresql-13-rum package installed in services/postgres/Dockerfile.
CREATE INDEX IF NOT EXISTS idx_messages_rum
    ON messages USING rum (tsv rum_tsvector_ops);

-- Fast reverse-follow lookups.
CREATE INDEX IF NOT EXISTS idx_follows_followed_id
    ON follows (followed_id);
