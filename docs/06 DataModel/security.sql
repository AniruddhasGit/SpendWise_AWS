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
