"""baseline: the whole schema, its policies and its grants

GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT — regenerate.
Verify:  py "docs/06 DataModel/generate.py" --check

Revision ID: 0001_baseline
Revises:
"""
from __future__ import annotations

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels = None
depends_on = None

# The DDL below is the byte-for-byte content of the generated schema.sql and
# security.sql. It is embedded rather than read from docs/ so the migration
# ships self-contained in the image, and generated rather than transcribed so
# it cannot drift from the spec of record.

# INDIVIDUAL statements, not one blob. asyncpg wraps every execute in a PREPARED
# STATEMENT, and a prepared statement cannot carry multiple commands — a single
# op.execute() of the whole script fails with "cannot insert multiple commands
# into a prepared statement". Split in generate.py, where the $$ … $$ function
# bodies are known exactly.

SCHEMA = [
    r"""CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    currency TEXT NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT ck_users_email CHECK (char_length(email) <= 254),
    CONSTRAINT ck_users_display_name CHECK (char_length(display_name) BETWEEN 1 AND 100),
    CONSTRAINT ck_users_role CHECK (role IN ('user','admin')),
    CONSTRAINT ck_users_currency CHECK (currency = 'INR')
);""",
    r"""CREATE TABLE sessions (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    user_id BIGINT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    user_agent TEXT NULL,
    ip INET NULL,
    CONSTRAINT pk_sessions PRIMARY KEY (id),
    CONSTRAINT ck_sessions_user_agent CHECK (user_agent IS NULL OR char_length(user_agent) <= 500)
);""",
    r"""CREATE TABLE password_resets (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    user_id BIGINT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_by_admin_id BIGINT NOT NULL,
    CONSTRAINT pk_password_resets PRIMARY KEY (id),
    CONSTRAINT ck_password_resets_token_hash CHECK (char_length(token_hash) = 64)
);""",
    r"""CREATE TABLE categories (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    user_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_categories PRIMARY KEY (id),
    CONSTRAINT ck_categories_name CHECK (char_length(name) BETWEEN 1 AND 50),
    CONSTRAINT ck_categories_color CHECK (color ~ '^#[0-9a-f]{6}$')
);""",
    r"""CREATE TABLE expenses (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    user_id BIGINT NOT NULL,
    category_id BIGINT NULL,
    amount_paise BIGINT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    description TEXT NULL,
    spent_on DATE NOT NULL,
    receipt_key TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NULL,
    CONSTRAINT pk_expenses PRIMARY KEY (id),
    CONSTRAINT ck_expenses_amount_paise CHECK (amount_paise > 0 AND amount_paise <= 1000000000000),
    CONSTRAINT ck_expenses_currency CHECK (currency = 'INR'),
    CONSTRAINT ck_expenses_description CHECK (description IS NULL OR char_length(description) <= 500),
    CONSTRAINT ck_expenses_spent_on CHECK (spent_on BETWEEN DATE '2000-01-01' AND DATE '2100-12-31'),
    CONSTRAINT ck_expenses_receipt_key CHECK (receipt_key IS NULL OR char_length(receipt_key) <= 512)
);""",
    r"""CREATE TABLE admin_audit_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    admin_id BIGINT NOT NULL,
    action TEXT NOT NULL,
    target_user_id BIGINT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_admin_audit_log PRIMARY KEY (id),
    CONSTRAINT ck_admin_audit_log_action CHECK (action IN ('password_reset_issued','sessions_revoked','user_deactivated','user_reactivated','role_changed','bootstrap_admin_claimed','users_list_viewed','sessions_list_viewed','audit_log_viewed'))
);""",
    r"""CREATE TABLE app_meta (
    id SMALLINT NOT NULL DEFAULT 1,
    jwt_secret_fingerprint TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_app_meta PRIMARY KEY (id),
    CONSTRAINT ck_app_meta_id CHECK (id = 1),
    CONSTRAINT ck_app_meta_jwt_secret_fingerprint CHECK (char_length(jwt_secret_fingerprint) = 64)
);""",
    r"""CREATE UNIQUE INDEX uq_users_lower_email ON users (lower(email));""",
    r"""CREATE INDEX ix_sessions_user_id ON sessions (user_id);""",
    r"""CREATE INDEX ix_sessions_last_seen_at ON sessions (last_seen_at);""",
    r"""CREATE INDEX ix_sessions_revoked_at__where_revoked_at_is_null ON sessions (revoked_at) WHERE revoked_at IS NULL;""",
    r"""CREATE UNIQUE INDEX uq_password_resets_token_hash ON password_resets (token_hash);""",
    r"""CREATE INDEX ix_password_resets_user_id__expires_at ON password_resets (user_id, expires_at);""",
    r"""CREATE UNIQUE INDEX uq_categories_id__user_id ON categories (id, user_id);""",
    r"""CREATE UNIQUE INDEX uq_categories_user_id__lower_name ON categories (user_id, lower(name));""",
    r"""CREATE INDEX ix_categories_user_id ON categories (user_id);""",
    r"""CREATE INDEX ix_expenses_user_id__spent_on_desc ON expenses (user_id, spent_on DESC);""",
    r"""CREATE INDEX ix_expenses_user_id__category_id ON expenses (user_id, category_id);""",
    r"""CREATE INDEX ix_admin_audit_log_admin_id__created_at_desc ON admin_audit_log (admin_id, created_at DESC);""",
    r"""CREATE INDEX ix_admin_audit_log_target_user_id ON admin_audit_log (target_user_id);""",
    r"""CREATE INDEX ix_users_deleted_at__where_deleted_at_is_null ON users (deleted_at) WHERE deleted_at IS NULL;""",
    r"""ALTER TABLE sessions ADD CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;""",
    r"""ALTER TABLE password_resets ADD CONSTRAINT fk_password_resets_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;""",
    r"""ALTER TABLE categories ADD CONSTRAINT fk_categories_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;""",
    r"""ALTER TABLE expenses ADD CONSTRAINT fk_expenses_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;""",
    r"""ALTER TABLE expenses ADD CONSTRAINT fk_expenses_category_id_user_id FOREIGN KEY (category_id, user_id) REFERENCES categories (id, user_id) ON DELETE NO ACTION;""",
]

SECURITY = [
    r"""ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;""",
    r"""ALTER TABLE sessions FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently""",
    r"""CREATE POLICY sessions_owner ON sessions
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);""",
    r"""ALTER TABLE categories ENABLE ROW LEVEL SECURITY;""",
    r"""ALTER TABLE categories FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently""",
    r"""CREATE POLICY categories_owner ON categories
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);""",
    r"""ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;""",
    r"""ALTER TABLE expenses FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently""",
    r"""CREATE POLICY expenses_owner ON expenses
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);""",
    r"""CREATE OR REPLACE FUNCTION admin_expense_stats(target_user_id BIGINT)
    RETURNS TABLE (expense_count BIGINT, last_activity DATE)
    LANGUAGE plpgsql
    VOLATILE
    SECURITY DEFINER
    SET search_path = pg_catalog, public
AS $fn$
DECLARE
    caller TEXT := current_setting('app.user_id', true);
BEGIN
    IF caller IS NULL OR caller = '' THEN
        RAISE EXCEPTION 'admin_expense_stats requires app.user_id to be set (SW-ADR-136)';
    END IF;
    PERFORM set_config('app.user_id', target_user_id::text, true);
    RETURN QUERY
    SELECT count(*)::bigint, max(spent_on)
      FROM expenses WHERE user_id = target_user_id;
    PERFORM set_config('app.user_id', caller, true);
END;
$fn$;""",
    r"""ALTER FUNCTION admin_expense_stats(BIGINT) OWNER TO spendwise_owner;""",
    r"""REVOKE ALL ON FUNCTION admin_expense_stats(BIGINT) FROM PUBLIC;""",
    r"""GRANT EXECUTE ON FUNCTION admin_expense_stats(BIGINT) TO spendwise_app;""",
    r"""CREATE OR REPLACE FUNCTION admin_user_sessions(target_user_id BIGINT)
    RETURNS TABLE (id BIGINT, user_id BIGINT, issued_at TIMESTAMPTZ, last_seen_at TIMESTAMPTZ, expires_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ)
    LANGUAGE plpgsql
    VOLATILE
    SECURITY DEFINER
    SET search_path = pg_catalog, public
AS $fn$
DECLARE
    caller TEXT := current_setting('app.user_id', true);
BEGIN
    IF caller IS NULL OR caller = '' THEN
        RAISE EXCEPTION 'admin_user_sessions requires app.user_id to be set (SW-ADR-136)';
    END IF;
    PERFORM set_config('app.user_id', target_user_id::text, true);
    RETURN QUERY
    SELECT s.id, s.user_id, s.issued_at, s.last_seen_at, s.expires_at, s.revoked_at
      FROM sessions s
     WHERE s.user_id = target_user_id
       AND s.revoked_at IS NULL
       AND s.expires_at > now()
     ORDER BY s.last_seen_at DESC, s.id DESC;
    PERFORM set_config('app.user_id', caller, true);
END;
$fn$;""",
    r"""ALTER FUNCTION admin_user_sessions(BIGINT) OWNER TO spendwise_owner;""",
    r"""REVOKE ALL ON FUNCTION admin_user_sessions(BIGINT) FROM PUBLIC;""",
    r"""GRANT EXECUTE ON FUNCTION admin_user_sessions(BIGINT) TO spendwise_app;""",
    r"""CREATE OR REPLACE FUNCTION admin_revoke_sessions(target_user_id BIGINT)
    RETURNS TABLE (revoked BIGINT)
    LANGUAGE plpgsql
    VOLATILE
    SECURITY DEFINER
    SET search_path = pg_catalog, public
AS $fn$
DECLARE
    caller TEXT := current_setting('app.user_id', true);
BEGIN
    IF caller IS NULL OR caller = '' THEN
        RAISE EXCEPTION 'admin_revoke_sessions requires app.user_id to be set (SW-ADR-136)';
    END IF;
    PERFORM set_config('app.user_id', target_user_id::text, true);
    RETURN QUERY
    WITH gone AS (
        UPDATE sessions SET revoked_at = now()
         WHERE user_id = target_user_id AND revoked_at IS NULL
        RETURNING 1
    )
    SELECT count(*)::bigint FROM gone;
    PERFORM set_config('app.user_id', caller, true);
END;
$fn$;""",
    r"""ALTER FUNCTION admin_revoke_sessions(BIGINT) OWNER TO spendwise_owner;""",
    r"""REVOKE ALL ON FUNCTION admin_revoke_sessions(BIGINT) FROM PUBLIC;""",
    r"""GRANT EXECUTE ON FUNCTION admin_revoke_sessions(BIGINT) TO spendwise_app;""",
    r"""CREATE OR REPLACE FUNCTION admin_user_daily(target_user_id BIGINT, from_date DATE, to_date DATE)
    RETURNS TABLE (day DATE, total_paise BIGINT, entries BIGINT)
    LANGUAGE plpgsql
    VOLATILE
    SECURITY DEFINER
    SET search_path = pg_catalog, public
AS $fn$
DECLARE
    caller TEXT := current_setting('app.user_id', true);
BEGIN
    IF caller IS NULL OR caller = '' THEN
        RAISE EXCEPTION 'admin_user_daily requires app.user_id to be set (SW-ADR-136)';
    END IF;
    PERFORM set_config('app.user_id', target_user_id::text, true);
    RETURN QUERY
    SELECT e.spent_on, sum(e.amount_paise)::bigint, count(e.id)::bigint
      FROM expenses e
     WHERE e.user_id = target_user_id
       AND e.spent_on BETWEEN from_date AND to_date
     GROUP BY e.spent_on
     ORDER BY e.spent_on;
    PERFORM set_config('app.user_id', caller, true);
END;
$fn$;""",
    r"""ALTER FUNCTION admin_user_daily(BIGINT, DATE, DATE) OWNER TO spendwise_owner;""",
    r"""REVOKE ALL ON FUNCTION admin_user_daily(BIGINT, DATE, DATE) FROM PUBLIC;""",
    r"""GRANT EXECUTE ON FUNCTION admin_user_daily(BIGINT, DATE, DATE) TO spendwise_app;""",
    r"""GRANT USAGE ON SCHEMA public TO spendwise_app;""",
    r"""GRANT SELECT, INSERT, UPDATE, DELETE ON expenses, categories, sessions TO spendwise_app;""",
    r"""GRANT SELECT, INSERT, UPDATE ON users, password_resets TO spendwise_app;""",
    r"""GRANT SELECT, INSERT ON admin_audit_log TO spendwise_app;""",
    r"""GRANT SELECT, UPDATE ON app_meta TO spendwise_app;""",
    r"""DO $do$ BEGIN
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        GRANT SELECT ON alembic_version TO spendwise_app;
    END IF;
END $do$;""",
    r"""REVOKE UPDATE, DELETE ON admin_audit_log FROM spendwise_app;""",
    r"""CREATE OR REPLACE FUNCTION audit_log_is_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'admin_audit_log is append-only (SW-ADR-083)';
END;
$$ LANGUAGE plpgsql;""",
    r"""DROP TRIGGER IF EXISTS trg_audit_log_immutable ON admin_audit_log;""",
    r"""CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON admin_audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only();""",
]

# Reverse dependency order. Policies and the trigger go with their tables, so
# dropping the table is enough — but the FUNCTIONS are schema-level and outlive
# it, and a downgrade that leaves them behind makes the next upgrade fail on a
# duplicate object rather than on anything meaningful.
DROP = [
    r"""DROP TRIGGER IF EXISTS trg_audit_log_immutable ON admin_audit_log;""",
    r"""DROP FUNCTION IF EXISTS audit_log_is_append_only();""",
    r"""DROP FUNCTION IF EXISTS admin_expense_stats(BIGINT);""",
    r"""DROP TABLE IF EXISTS app_meta CASCADE;""",
    r"""DROP TABLE IF EXISTS admin_audit_log CASCADE;""",
    r"""DROP TABLE IF EXISTS expenses CASCADE;""",
    r"""DROP TABLE IF EXISTS categories CASCADE;""",
    r"""DROP TABLE IF EXISTS password_resets CASCADE;""",
    r"""DROP TABLE IF EXISTS sessions CASCADE;""",
    r"""DROP TABLE IF EXISTS users CASCADE;""",
]


def upgrade() -> None:
    """Idempotent by construction: this runs once, against an empty database.

    E0-S3 asserts a SECOND `alembic upgrade head` exits 0 and changes nothing —
    that is Alembic's version table doing its job, not this function being
    re-runnable. Running this body twice would correctly fail on a duplicate.
    """
    for stmt in SCHEMA + SECURITY:
        op.execute(stmt)


def downgrade() -> None:
    for stmt in DROP:
        op.execute(stmt)
