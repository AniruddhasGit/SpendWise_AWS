-- rds_bootstrap.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.
-- Regenerate:  py "docs/06 DataModel/generate.py"
--
-- RUN THIS ONCE, AS THE RDS MASTER USER, CONNECTED TO THE `postgres` DATABASE.
--
-- Source: SW-ADR-008 (one RDS from day one) · SW-ADR-068 (two databases inside it) · SW-ADR-081
--
-- Roles and databases CANNOT be created by Alembic: CREATE DATABASE will not
-- run inside a transaction, and the owner role has no privilege to create
-- roles. They are created once, by the client, as the RDS master user -
-- which is why this generates a separate bootstrap script rather than a
-- migration.
--
-- * The RDS master user is NOT a superuser - it holds `rds_superuser`.
--   Everything below works under that; nothing here needs true superuser.
-- * RDS FORCES SSL. Both connection strings need it. For asyncpg via
--   SQLAlchemy the parameter is `?ssl=require` - NOT libpq's
--   `sslmode=require`, which asyncpg does not accept and which fails at
--   connect time with an unhelpful error.
-- * PostgreSQL 15 and later no longer grant CREATE on schema `public` to
--   PUBLIC. Creating each database WITH OWNER spendwise_owner is what gives
--   the owner rights over its public schema.
-- * Run this ONCE, as the master user, connected to the default `postgres`
--   database. It is idempotent: every statement is guarded, so re-running it
--   is safe.
--
-- ── HOW TO RUN ──────────────────────────────────────────────────────
-- Run it with psql, passing the passwords as variables so they never enter this file:
--
--     psql "host=YOUR-ENDPOINT.rds.amazonaws.com port=5432 dbname=postgres user=MASTER sslmode=require" \
--          -v spendwise_owner_password="OWNER_PASSWORD_HERE" \
--          -v spendwise_app_password="APP_PASSWORD_HERE" \
--          -f "docs/30 Deployment/rds_bootstrap.sql"
--
-- psql already ships with the PostgreSQL install on this machine. Its full path is
-- printed by:
--
--     where.exe psql        (or look under C:/Program Files/PostgreSQL/*/bin/)
--
-- pgAdmin will NOT run this file. The :'name' variables and the \gexec meta-command
-- are psql features, not SQL - pgAdmin silently does the wrong thing with both. Use
-- psql, or run the statements by hand with each :'..._password' replaced by a quoted
-- literal and each CREATE DATABASE executed directly instead of through \gexec.
--
-- Generate the two passwords with:
--
--     py -c "import secrets; print(secrets.token_urlsafe(24))"
--
-- They go into .env, which is gitignored, and into SSM Parameter Store as SecureString
-- for the deploy - prep-queue items 7 and 14. They never enter git.

\set ON_ERROR_STOP on

-- ── roles ───────────────────────────────────────────────────────────
-- Passwords are NOT in this file and never will be. Set them below, or
-- create the roles here and ALTER ... PASSWORD separately. Whatever you
-- choose, the password never enters git (CONSTITUTION Art IV.4).

-- spendwise_owner — Owns every table. Runs Alembic. NEVER serves a request.
-- It owns the tables, so FORCE ROW LEVEL SECURITY is what stops it bypassing
-- its own policies during a data migration (SW-ADR-081).
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'spendwise_owner') THEN
        CREATE ROLE spendwise_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS INHERIT
            PASSWORD :'spendwise_owner_password';
    END IF;
END $$;
-- re-assert the attributes even if the role already existed:
ALTER ROLE spendwise_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS INHERIT;

-- spendwise_app — What the application connects as. Serves every request.
-- Owns NO table, is NOT superuser, holds NO BYPASSRLS - asserted against the
-- catalog at boot (P-OPS-02). If it owned the tables it could ALTER TABLE
-- ... NO FORCE ROW LEVEL SECURITY, which is the guarantee removing itself.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'spendwise_app') THEN
        CREATE ROLE spendwise_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS INHERIT
            PASSWORD :'spendwise_app_password';
    END IF;
END $$;
-- re-assert the attributes even if the role already existed:
ALTER ROLE spendwise_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS INHERIT;

-- ── databases ───────────────────────────────────────────────────────
-- CREATE DATABASE cannot run inside a transaction or a DO block, so these
-- are guarded with \gexec rather than an IF NOT EXISTS.

-- spendwise — DEV. What the application connects to.
SELECT 'CREATE DATABASE spendwise WITH OWNER spendwise_owner ENCODING ''UTF8'''
 WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'spendwise')\gexec

-- spendwise_test — The test database. The seeder REFUSES to run against any database not named spendwise_test (SW-ADR-086), and CV-24's per-case TRUNCATE ... RESTART IDENTITY CASCADE only ever touches this one.
SELECT 'CREATE DATABASE spendwise_test WITH OWNER spendwise_owner ENCODING ''UTF8'''
 WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'spendwise_test')\gexec

-- ── connect privileges ──────────────────────────────────────────────
-- The runtime role may CONNECT. Everything it may then DO is granted by
-- security.sql, inside the migration, and narrowed again by RLS.
GRANT CONNECT ON DATABASE spendwise TO spendwise_app;
GRANT CONNECT ON DATABASE spendwise_test TO spendwise_app;

-- Nobody else. PUBLIC can connect to any database by default, which is a
-- default worth removing on a publicly-reachable instance.
REVOKE CONNECT ON DATABASE spendwise FROM PUBLIC;

-- ── verify — every row must come back as expected ───────────────────
-- E0-S2 asserts these three at BOOT as well. Checking here means a
-- mistake surfaces now, not as a failing gate an hour later.
SELECT rolname, rolsuper, rolbypassrls, rolcreaterole
  FROM pg_roles WHERE rolname LIKE 'spendwise%';
--  expected: rolsuper = f, rolbypassrls = f, rolcreaterole = f  for BOTH

SELECT datname, pg_get_userbyid(datdba) AS owner
  FROM pg_database WHERE datname LIKE 'spendwise%';
--  expected: owner = spendwise_owner  for both databases
