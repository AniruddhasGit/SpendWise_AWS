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

SCHEMA = r"""
    -- schema.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.
    -- Regenerate:  py "docs/06 DataModel/generate.py"
    -- Verify:      py "docs/06 DataModel/generate.py" --check
    -- SW-ADR-066: a hand patch to a generated file is erased by the next build, silently.
    -- Naming convention (SW-ADR-040) is set on the SQLAlchemy MetaData, not here;
    -- generate.py reproduces it so the DDL and the ORM agree on every identifier.


    -- users  [SRC-001 §6.2]  Outside RLS by SW-ADR-097 — a policy keyed on the request identity cannot serve a pre-authentication lookup.
    CREATE TABLE users (
        id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        currency TEXT NOT NULL DEFAULT 'INR',
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT pk_users PRIMARY KEY (id),
        CONSTRAINT ck_users_email CHECK (char_length(email) <= 254),
        CONSTRAINT ck_users_display_name CHECK (char_length(display_name) BETWEEN 1 AND 100),
        CONSTRAINT ck_users_role CHECK (role IN ('user','admin')),
        CONSTRAINT ck_users_currency CHECK (currency = 'INR')
    );

    -- sessions  [SRC-001 §6.3]  Protected. The identity column is user_id.
    CREATE TABLE sessions (
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
    );

    -- password_resets  [SRC-001 §6.4]  Outside RLS by SW-ADR-071 — redeeming a code is unauthenticated by definition.
    CREATE TABLE password_resets (
        id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
        user_id BIGINT NOT NULL,
        token_hash TEXT NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at TIMESTAMPTZ NULL,
        created_by_admin_id BIGINT NOT NULL,
        CONSTRAINT pk_password_resets PRIMARY KEY (id),
        CONSTRAINT ck_password_resets_token_hash CHECK (char_length(token_hash) = 64)
    );

    -- categories  [SRC-001 §6.5]  Protected.
    CREATE TABLE categories (
        id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
        user_id BIGINT NOT NULL,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT pk_categories PRIMARY KEY (id),
        CONSTRAINT ck_categories_name CHECK (char_length(name) BETWEEN 1 AND 50),
        CONSTRAINT ck_categories_color CHECK (color ~ '^#[0-9a-f]{6}$')
    );

    -- expenses  [SRC-001 §6.6]  Protected. The money table.
    CREATE TABLE expenses (
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
    );

    -- admin_audit_log  [SRC-001 §6.7]  No RLS: admin-only, and immutable at the database (SW-ADR-083). Carries NO foreign keys (SW-ADR-083) so it outlives its subjects.
    CREATE TABLE admin_audit_log (
        id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
        admin_id BIGINT NOT NULL,
        action TEXT NOT NULL,
        target_user_id BIGINT NULL,
        details JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT pk_admin_audit_log PRIMARY KEY (id),
        CONSTRAINT ck_admin_audit_log_action CHECK (action IN ('password_reset_issued','sessions_revoked','user_deactivated','user_reactivated','role_changed','bootstrap_admin_claimed','users_list_viewed','sessions_list_viewed','audit_log_viewed'))
    );

    -- app_meta  [SW-ADR-125]  One row. Holds the signing-secret fingerprint so rotation revokes sessions automatically.
    CREATE TABLE app_meta (
        id SMALLINT NOT NULL DEFAULT 1,
        jwt_secret_fingerprint TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT pk_app_meta PRIMARY KEY (id),
        CONSTRAINT ck_app_meta_id CHECK (id = 1),
        CONSTRAINT ck_app_meta_jwt_secret_fingerprint CHECK (char_length(jwt_secret_fingerprint) = 64)
    );

    -- SRC-001 §6.9
    ALTER TABLE sessions ADD CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    -- SRC-001 §6.9
    ALTER TABLE password_resets ADD CONSTRAINT fk_password_resets_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    -- SRC-001 §6.9
    ALTER TABLE categories ADD CONSTRAINT fk_categories_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    -- SRC-001 §6.9
    ALTER TABLE expenses ADD CONSTRAINT fk_expenses_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;
    -- SW-ADR-072 — composite. NO ACTION because SET NULL would null user_id too, which is NOT NULL. The service nulls category_id explicitly inside the delete transaction.
    ALTER TABLE expenses ADD CONSTRAINT fk_expenses_category_id_user_id FOREIGN KEY (category_id, user_id) REFERENCES categories (id, user_id) ON DELETE NO ACTION;

    -- SW-ADR-027 — case-insensitive identity
    CREATE UNIQUE INDEX uq_users_lower_email ON users (lower(email));
    -- SRC-001 §6.8
    CREATE INDEX ix_sessions_user_id ON sessions (user_id);
    -- SRC-001 §6.8
    CREATE INDEX ix_sessions_last_seen_at ON sessions (last_seen_at);
    -- SW-ADR-039 — partial; satisfiable only because SW-ADR-076 made the column nullable
    CREATE INDEX ix_sessions_revoked_at__where_revoked_at_is_null ON sessions (revoked_at) WHERE revoked_at IS NULL;
    -- SW-ADR-032
    CREATE UNIQUE INDEX uq_password_resets_token_hash ON password_resets (token_hash);
    -- SW-ADR-039
    CREATE INDEX ix_password_resets_user_id__expires_at ON password_resets (user_id, expires_at);
    -- SW-ADR-072 — the target of the composite FK
    CREATE UNIQUE INDEX uq_categories_id__user_id ON categories (id, user_id);
    -- SW-ADR-033
    CREATE UNIQUE INDEX uq_categories_user_id__lower_name ON categories (user_id, lower(name));
    -- SW-ADR-039
    CREATE INDEX ix_categories_user_id ON categories (user_id);
    -- SRC-001 §6.8
    CREATE INDEX ix_expenses_user_id__spent_on_desc ON expenses (user_id, spent_on DESC);
    -- SRC-001 §6.8
    CREATE INDEX ix_expenses_user_id__category_id ON expenses (user_id, category_id);
    -- SW-ADR-039
    CREATE INDEX ix_admin_audit_log_admin_id__created_at_desc ON admin_audit_log (admin_id, created_at DESC);
    -- SW-ADR-039
    CREATE INDEX ix_admin_audit_log_target_user_id ON admin_audit_log (target_user_id);
"""

SECURITY = r"""
    -- security.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.
    -- Regenerate:  py "docs/06 DataModel/generate.py"
    -- Verify:      py "docs/06 DataModel/generate.py" --check
    --
    -- Two roles (SW-ADR-081): spendwise_owner migrates and owns; spendwise_app serves traffic.
    -- The runtime role MUST NOT own a table, MUST NOT be superuser, MUST NOT hold BYPASSRLS.
    -- Verified at boot against the catalog, never assumed (CONSTITUTION Art IV.3).

    -- The request-scoped identity is set with set_config and a BOUND parameter:
    --     SELECT set_config('app.user_id', :uid, true)
    -- SET LOCAL cannot take a bind parameter, and interpolating would be the
    -- f-string-near-SQL that SRC-001 §10.3 forbids (SW-ADR-082).

    -- users: NO row-level security. Outside RLS by SW-ADR-097 — a policy keyed on the request identity cannot serve a pre-authentication lookup.

    -- sessions: protected — Protected. The identity column is user_id
    ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE sessions FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
    CREATE POLICY sessions_owner ON sessions
        FOR ALL
        USING      (user_id = current_setting('app.user_id', true)::bigint)
        WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
    -- USING alone would be used as WITH CHECK too, but stating both makes the
    -- intent explicit and stops a later edit weakening one without the other.

    -- password_resets: NO row-level security. Outside RLS by SW-ADR-071 — redeeming a code is unauthenticated by definition.

    -- categories: protected — Protected
    ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
    ALTER TABLE categories FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
    CREATE POLICY categories_owner ON categories
        FOR ALL
        USING      (user_id = current_setting('app.user_id', true)::bigint)
        WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
    -- USING alone would be used as WITH CHECK too, but stating both makes the
    -- intent explicit and stops a later edit weakening one without the other.

    -- expenses: protected — Protected. The money table
    ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
    ALTER TABLE expenses FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
    CREATE POLICY expenses_owner ON expenses
        FOR ALL
        USING      (user_id = current_setting('app.user_id', true)::bigint)
        WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
    -- USING alone would be used as WITH CHECK too, but stating both makes the
    -- intent explicit and stops a later edit weakening one without the other.

    -- admin_audit_log: NO row-level security. No RLS: admin-only, and immutable at the database (SW-ADR-083). Carries NO foreign keys (SW-ADR-083) so it outlives its subjects.

    -- app_meta: NO row-level security. One row. Holds the signing-secret fingerprint so rotation revokes sessions automatically.

    -- ── admin access ─────────────────────────────────────────────────────
    -- NO admin policy exists on expenses or categories (SW-ADR-129, restoring
    -- SW-ADR-043). `app.is_admin` is consulted by NO policy in this file and is
    -- never set on a request-scoped connection.
    --
    -- A permissive policy `USING (current_setting('app.is_admin') = 'true')` was
    -- what the superseded SW-ADR-077 produced. It is row-level, so it returned
    -- EVERY COLUMN of EVERY ROW — amount and description included — to any
    -- connection with that GUC set. Permissive policies are OR'd, so it could only
    -- ever widen access. No API test could have caught it: the response model still
    -- returned the right fields, from a query allowed to read everything.


    -- expenses: an admin reads COUNT and LAST ACTIVITY DATE only (SW-ADR-129). This is the whole of admin access to the money table.
    -- SECURITY DEFINER bypasses row security by design — which is exactly why
    -- the RETURN TYPE is the guard. An amount cannot come back through this
    -- function because there is no column for one. SRC-001 §4.5 is structurally
    -- true at the DATABASE, not merely in a response model.
    -- SET search_path is MANDATORY: without it a definer function is a
    -- privilege-escalation vector (an attacker-controlled schema shadows a name).
    CREATE OR REPLACE FUNCTION admin_expense_stats(target_user_id BIGINT)
        RETURNS TABLE (expense_count BIGINT, last_activity DATE)
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, public
    AS $$
        SELECT count(*)::bigint, max(spent_on)
          FROM expenses WHERE user_id = target_user_id;
    $$;
    ALTER FUNCTION admin_expense_stats(BIGINT) OWNER TO spendwise_owner;
    REVOKE ALL ON FUNCTION admin_expense_stats(BIGINT) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION admin_expense_stats(BIGINT) TO spendwise_app;

    -- ── privileges (SW-ADR-137) ──────────────────────────────────────────
    -- RLS only NARROWS what a grant already allows. Both are required, and the
    -- boot assertion checks this direction too, not only the dangerous one.
    GRANT USAGE ON SCHEMA public TO spendwise_app;
    -- full CRUD, narrowed by RLS
    GRANT SELECT, INSERT, UPDATE, DELETE ON expenses, categories, sessions TO spendwise_app;
    -- no DELETE: there is no user-deletion path in v1 (SW-ADR-107), and password_resets is pruned by the owner (SW-ADR-122)
    GRANT SELECT, INSERT, UPDATE ON users, password_resets TO spendwise_app;
    -- append-only; UPDATE and DELETE are revoked and a trigger raises (SW-ADR-083)
    GRANT SELECT, INSERT ON admin_audit_log TO spendwise_app;
    -- one row; the signing-secret fingerprint is rewritten on rotation (SW-ADR-125)
    GRANT SELECT, UPDATE ON app_meta TO spendwise_app;

    -- admin_audit_log: immutable (SW-ADR-083). Revoke AND a trigger, so the refusal
    -- is visible rather than a silent permission error.
    REVOKE UPDATE, DELETE ON admin_audit_log FROM spendwise_app;
    CREATE OR REPLACE FUNCTION audit_log_is_append_only() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'admin_audit_log is append-only (SW-ADR-083)';
    END;
    $$ LANGUAGE plpgsql;
    DROP TRIGGER IF EXISTS trg_audit_log_immutable ON admin_audit_log;
    CREATE TRIGGER trg_audit_log_immutable
        BEFORE UPDATE OR DELETE ON admin_audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only();

    -- Migrations run as the OWNER, which FORCE ROW LEVEL SECURITY also subjects to
    -- the policies — so a data migration would silently affect ZERO rows (SW-ADR-081).
    -- env.py therefore issues, on the migration connection only:
    --     SET LOCAL row_security = off;
    -- The runtime role cannot do this: it lacks BYPASSRLS, so the guarantee is unaffected.
"""

# Reverse dependency order. Policies and the trigger go with their tables, so
# dropping the table is enough — but the FUNCTIONS are schema-level and outlive
# it, and a downgrade that leaves them behind makes the next upgrade fail on a
# duplicate object rather than on anything meaningful.
DROP = r"""
DROP TRIGGER IF EXISTS trg_audit_log_immutable ON admin_audit_log;
DROP FUNCTION IF EXISTS audit_log_is_append_only();
DROP FUNCTION IF EXISTS admin_expense_stats(BIGINT);
DROP TABLE IF EXISTS app_meta CASCADE;
DROP TABLE IF EXISTS admin_audit_log CASCADE;
DROP TABLE IF EXISTS expenses CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS password_resets CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""


def upgrade() -> None:
    """Idempotent by construction: this runs once, against an empty database.

    E0-S3 asserts a SECOND `alembic upgrade head` exits 0 and changes nothing —
    that is Alembic's version table doing its job, not this function being
    re-runnable. Running this body twice would correctly fail on a duplicate.
    """
    op.execute(SCHEMA)
    op.execute(SECURITY)


def downgrade() -> None:
    op.execute(DROP)
