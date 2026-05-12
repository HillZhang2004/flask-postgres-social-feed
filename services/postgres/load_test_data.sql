-- services/postgres/load_test_data.sql
--
-- Loads 1,000,000 seed users and 1,000,000 seed messages for testing.
-- Seed rows are identified by username matching '^seed_user_[0-9]+$'.
-- Manually created users and messages are NOT touched.
--
-- Run with (from the project root, while dev stack is running):
--
--   docker compose exec -T db psql -U hello_flask -d hello_flask_dev \
--     < services/postgres/load_test_data.sql
--
-- Safe to rerun: existing seed data is deleted and recreated each time.
-- Expected duration: 5-15 minutes (RUM index maintenance dominates).
-- Optional speedup: uncomment the DROP/CREATE INDEX lines below.

\set ON_ERROR_STOP on
\timing on
\echo '=== Starting test data load ==='

-- ---------------------------------------------------------------------------
-- Optional: drop RUM index before load to speed up inserts, recreate after.
-- Uncomment these two blocks and the final CREATE INDEX if load is too slow.
-- ---------------------------------------------------------------------------
-- \echo 'Dropping RUM index for faster load...'
-- DROP INDEX IF EXISTS idx_messages_rum;

-- ---------------------------------------------------------------------------
-- Cleanup: remove all previous seed data.
-- Regex '^seed_user_[0-9]+$' matches only generated usernames, not manual ones.
-- Cascades automatically to seed users' messages via ON DELETE CASCADE.
-- ---------------------------------------------------------------------------
\echo 'Removing previous seed data (if any)...'
DELETE FROM users WHERE username ~ '^seed_user_[0-9]+$';

-- ---------------------------------------------------------------------------
-- Insert 1,000,000 seed users.
-- Usernames: seed_user_1 through seed_user_1000000.
-- created_at spread 1 second apart so feed ordering is deterministic.
-- ---------------------------------------------------------------------------
\echo 'Inserting 1,000,000 seed users...'
INSERT INTO users (username, created_at)
SELECT
    'seed_user_' || i,
    NOW() - (i * interval '1 second')
FROM generate_series(1, 1000000) AS g(i);

ANALYZE users;

-- ---------------------------------------------------------------------------
-- Insert 1 seed message per seed user (1,000,000 messages total).
-- ROW_NUMBER() is computed once in the CTE to avoid re-evaluation.
-- Bodies contain '[SEED]' marker plus 10 rotating topic phrases so that
-- full-text search returns varied, realistic results.
-- created_at matches the user offset for deterministic ordering.
-- ---------------------------------------------------------------------------
\echo 'Inserting 1,000,000 seed messages...'
WITH seed_users AS (
    SELECT
        user_id,
        ROW_NUMBER() OVER (ORDER BY user_id) AS rn
    FROM users
    WHERE username ~ '^seed_user_[0-9]+$'
)
INSERT INTO messages (user_id, body, created_at)
SELECT
    su.user_id,
    '[SEED] ' || (ARRAY[
        'the quick brown fox jumps over the lazy dog',
        'flask postgres docker nginx python web development',
        'full text search relevance ranking tsvector tsquery',
        'database indexing performance optimization query plan',
        'social feed message board authentication session cookie',
        'generate series artificial data software engineering class',
        'computer science project web application routing template',
        'open source technology programming language library package',
        'docker compose container image volume network port mapping',
        'github actions continuous integration workflow build test'
    ])[(((su.rn - 1) % 10) + 1)::int],
    NOW() - (su.rn * interval '1 second')
FROM seed_users su;

ANALYZE messages;

-- ---------------------------------------------------------------------------
-- Optional: recreate RUM index after load if it was dropped above.
-- ---------------------------------------------------------------------------
-- \echo 'Recreating RUM index...'
-- CREATE INDEX idx_messages_rum ON messages USING rum (tsv rum_tsvector_ops);

-- ---------------------------------------------------------------------------
-- Verification: row counts for all four tables.
-- users and messages must each show >= 1,000,000.
-- ---------------------------------------------------------------------------
\echo '=== Verification counts ==='
SELECT 'users'       AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'credentials',               COUNT(*)               FROM credentials
UNION ALL
SELECT 'messages',                  COUNT(*)               FROM messages
UNION ALL
SELECT 'follows',                   COUNT(*)               FROM follows;

\echo '=== Done ==='
