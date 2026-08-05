-- schema.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.
-- Regenerate:  py "docs/06 DataModel/generate.py"
-- Verify:      py "docs/06 DataModel/generate.py" --check
-- SW-ADR-066: a hand patch to a generated file is erased by the next build, silently.
-- Naming convention (SW-ADR-040) is set on the SQLAlchemy MetaData, not here;
-- generate.py reproduces it so the DDL and the ORM agree on every identifier.


-- users  [SRC-001 §6.2]  Outside RLS by SW-ADR-097 — a policy keyed on the request identity cannot serve a pre-authentication lookup. CR-001 added deleted_at: closing an account is SOFT. The unique index on lower(email) stays TOTAL, so a closed account keeps its address - a partial index would let someone return under the same address and leave two rows sharing one, which every lookup would then have to disambiguate correctly forever (SW-ADR-150).
CREATE TABLE users (
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
-- SW-ADR-150 - partial, like ix_sessions_revoked_at: live accounts are the ones every request looks up, closed ones accumulate forever, and indexing them would grow the index without ever being read
CREATE INDEX ix_users_deleted_at__where_deleted_at_is_null ON users (deleted_at) WHERE deleted_at IS NULL;

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
