-- security.sql — GENERATED from datamodel.json. DO NOT HAND-EDIT.
-- Two roles (SW-ADR-044): spendwise_owner migrates and owns; spendwise_app serves traffic.
-- The runtime role MUST NOT own a table, MUST NOT be superuser, MUST NOT hold BYPASSRLS.
-- Verified at boot against the catalog, never assumed (CONSTITUTION Art IV.3).

-- The request-scoped identity is set with set_config and a BOUND parameter:
--     SELECT set_config('app.user_id', :uid, true)
-- SET LOCAL cannot take a bind parameter, and interpolating would be the
-- f-string-near-SQL that SRC-001 §10.3 forbids (SW-ADR-082).

-- users: NO row-level security. Outside RLS by SW-ADR-097 — a policy keyed on the request identity cannot serve a pre-authentication lookup.
-- sessions: protected
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
CREATE POLICY sessions_owner ON sessions
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
-- USING alone would be used as WITH CHECK too, but stating both makes the
-- intent explicit and stops a later edit weakening one without the other.

-- password_resets: NO row-level security. Outside RLS by SW-ADR-071 — redeeming a code is unauthenticated by definition.
-- categories: protected
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
CREATE POLICY categories_owner ON categories
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
-- USING alone would be used as WITH CHECK too, but stating both makes the
-- intent explicit and stops a later edit weakening one without the other.

-- expenses: protected
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
CREATE POLICY expenses_owner ON expenses
    FOR ALL
    USING      (user_id = current_setting('app.user_id', true)::bigint)
    WITH CHECK (user_id = current_setting('app.user_id', true)::bigint);
-- USING alone would be used as WITH CHECK too, but stating both makes the
-- intent explicit and stops a later edit weakening one without the other.

-- admin_audit_log: NO row-level security. No RLS: admin-only, and immutable at the database (SW-ADR-031). Carries NO foreign keys (SW-ADR-083) so it outlives its subjects.
-- app_meta: NO row-level security. One row. Holds the signing-secret fingerprint so rotation revokes sessions automatically.
-- expenses: an admin may read AGGREGATES ONLY (SW-ADR-077).
-- The response model additionally has no field capable of holding an amount,
-- so SRC-001 §4.5 is structurally true rather than a rule someone must remember.
CREATE POLICY expenses_admin_count ON expenses
    FOR SELECT
    USING (current_setting('app.is_admin', true) = 'true');

-- admin_audit_log: immutable (SW-ADR-031). Revoke AND a trigger, so the refusal
-- is visible rather than a silent permission error.
REVOKE UPDATE, DELETE ON admin_audit_log FROM spendwise_app;
CREATE OR REPLACE FUNCTION audit_log_is_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'admin_audit_log is append-only (SW-ADR-031)';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON admin_audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_is_append_only();

-- Migrations run as the OWNER, which FORCE ROW LEVEL SECURITY also subjects to
-- the policies — so a data migration would silently affect ZERO rows (SW-ADR-081).
-- env.py therefore issues, on the migration connection only:
--     SET LOCAL row_security = off;
-- The runtime role cannot do this: it lacks BYPASSRLS, so the guarantee is unaffected.
