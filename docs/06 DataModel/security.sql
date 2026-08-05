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

-- users: NO row-level security. Outside RLS by SW-ADR-097 — a policy keyed on the request identity cannot serve a pre-authentication lookup. CR-001 added deleted_at: closing an account is SOFT. The unique index on lower(email) stays TOTAL, so a closed account keeps its address - a partial index would let someone return under the same address and leave two rows sharing one, which every lookup would then have to disambiguate correctly forever (SW-ADR-150).

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
-- SECURITY DEFINER runs this as the TABLE OWNER — which is not, on its own,
-- enough. FORCE ROW LEVEL SECURITY subjects the owner to its own policies, so
-- the owner sees exactly what `app.user_id` says and nothing else. The first
-- version of this function was LANGUAGE sql with no GUC handling, and it
-- returned (0, NULL) for every account except the caller's own — silently,
-- and looking exactly like a correct privacy-respecting answer.
--
-- So the identity is swapped to the TARGET for the length of the query and
-- restored before returning. It is transaction-local (set_config(..., true)),
-- and it refuses to run when app.user_id is unset rather than restoring to
-- something that was never there — an unset GUC reads as NULL, an empty one
-- raises on ::bigint, and the two are not the same state.
--
-- THE RETURN TYPE IS STILL THE GUARD. An amount cannot come back through this
-- function because there is no column for one, so SRC-001 §4.5 is structurally
-- true at the DATABASE and not merely in a response model.
-- SET search_path is MANDATORY: without it a definer function is a
-- privilege-escalation vector (an attacker-controlled schema shadows a name).
-- VOLATILE, not STABLE: it mutates a GUC, and labelling that STABLE would be
-- a lie the planner is entitled to act on.
CREATE OR REPLACE FUNCTION admin_expense_stats(target_user_id BIGINT)
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
$fn$;
ALTER FUNCTION admin_expense_stats(BIGINT) OWNER TO spendwise_owner;
REVOKE ALL ON FUNCTION admin_expense_stats(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_expense_stats(BIGINT) TO spendwise_app;


-- sessions: an admin sees WHO IS SIGNED IN (SRC-001 §4.2) and nothing about where from. `sessions` carries exactly one policy, keyed on app.user_id, so an admin querying it directly sees only their own - the capability the matrix grants was unreachable. The RETURN TYPE carries no ip and no user_agent, which makes SW-ADR-106 structurally true at the DATABASE rather than only in a Pydantic model.
-- SECURITY DEFINER runs this as the TABLE OWNER — which is not, on its own,
-- enough. FORCE ROW LEVEL SECURITY subjects the owner to its own policies, so
-- the owner sees exactly what `app.user_id` says and nothing else. The first
-- version of this function was LANGUAGE sql with no GUC handling, and it
-- returned (0, NULL) for every account except the caller's own — silently,
-- and looking exactly like a correct privacy-respecting answer.
--
-- So the identity is swapped to the TARGET for the length of the query and
-- restored before returning. It is transaction-local (set_config(..., true)),
-- and it refuses to run when app.user_id is unset rather than restoring to
-- something that was never there — an unset GUC reads as NULL, an empty one
-- raises on ::bigint, and the two are not the same state.
--
-- THE RETURN TYPE IS STILL THE GUARD. An amount cannot come back through this
-- function because there is no column for one, so SRC-001 §4.5 is structurally
-- true at the DATABASE and not merely in a response model.
-- SET search_path is MANDATORY: without it a definer function is a
-- privilege-escalation vector (an attacker-controlled schema shadows a name).
-- VOLATILE, not STABLE: it mutates a GUC, and labelling that STABLE would be
-- a lie the planner is entitled to act on.
CREATE OR REPLACE FUNCTION admin_user_sessions(target_user_id BIGINT)
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
$fn$;
ALTER FUNCTION admin_user_sessions(BIGINT) OWNER TO spendwise_owner;
REVOKE ALL ON FUNCTION admin_user_sessions(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_user_sessions(BIGINT) TO spendwise_app;


-- sessions: FORCE SIGN SOMEONE OUT (SRC-001 §4.2), and the revocation SW-ADR-100 (2) requires in the same transaction as a deactivation. Without this the UPDATE matched zero rows under RLS and REPORTED SUCCESS - a force-sign-out that signs nobody out, and an audit row claiming it did.
-- SECURITY DEFINER runs this as the TABLE OWNER — which is not, on its own,
-- enough. FORCE ROW LEVEL SECURITY subjects the owner to its own policies, so
-- the owner sees exactly what `app.user_id` says and nothing else. The first
-- version of this function was LANGUAGE sql with no GUC handling, and it
-- returned (0, NULL) for every account except the caller's own — silently,
-- and looking exactly like a correct privacy-respecting answer.
--
-- So the identity is swapped to the TARGET for the length of the query and
-- restored before returning. It is transaction-local (set_config(..., true)),
-- and it refuses to run when app.user_id is unset rather than restoring to
-- something that was never there — an unset GUC reads as NULL, an empty one
-- raises on ::bigint, and the two are not the same state.
--
-- THE RETURN TYPE IS STILL THE GUARD. An amount cannot come back through this
-- function because there is no column for one, so SRC-001 §4.5 is structurally
-- true at the DATABASE and not merely in a response model.
-- SET search_path is MANDATORY: without it a definer function is a
-- privilege-escalation vector (an attacker-controlled schema shadows a name).
-- VOLATILE, not STABLE: it mutates a GUC, and labelling that STABLE would be
-- a lie the planner is entitled to act on.
CREATE OR REPLACE FUNCTION admin_revoke_sessions(target_user_id BIGINT)
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
$fn$;
ALTER FUNCTION admin_revoke_sessions(BIGINT) OWNER TO spendwise_owner;
REVOKE ALL ON FUNCTION admin_revoke_sessions(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_revoke_sessions(BIGINT) TO spendwise_app;


-- expenses: an admin reads one person's SPENDING PER DAY (CR-001, SW-ADR-151). THREE COLUMNS AND NO FOURTH - there is no category_id, no description and no expense id, so 'what did they spend it on' is unanswerable through this function at any granularity. That is the line the client drew when they granted amount visibility: 'the expenses that are happening not the categories spent on'. The RETURN TYPE is what enforces it, exactly as SW-ADR-129 established for the count - a principle pointed at a line that moved, not a principle abandoned.
-- SECURITY DEFINER runs this as the TABLE OWNER — which is not, on its own,
-- enough. FORCE ROW LEVEL SECURITY subjects the owner to its own policies, so
-- the owner sees exactly what `app.user_id` says and nothing else. The first
-- version of this function was LANGUAGE sql with no GUC handling, and it
-- returned (0, NULL) for every account except the caller's own — silently,
-- and looking exactly like a correct privacy-respecting answer.
--
-- So the identity is swapped to the TARGET for the length of the query and
-- restored before returning. It is transaction-local (set_config(..., true)),
-- and it refuses to run when app.user_id is unset rather than restoring to
-- something that was never there — an unset GUC reads as NULL, an empty one
-- raises on ::bigint, and the two are not the same state.
--
-- THE RETURN TYPE IS STILL THE GUARD. An amount cannot come back through this
-- function because there is no column for one, so SRC-001 §4.5 is structurally
-- true at the DATABASE and not merely in a response model.
-- SET search_path is MANDATORY: without it a definer function is a
-- privilege-escalation vector (an attacker-controlled schema shadows a name).
-- VOLATILE, not STABLE: it mutates a GUC, and labelling that STABLE would be
-- a lie the planner is entitled to act on.
CREATE OR REPLACE FUNCTION admin_user_daily(target_user_id BIGINT, from_date DATE, to_date DATE)
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
$fn$;
ALTER FUNCTION admin_user_daily(BIGINT, DATE, DATE) OWNER TO spendwise_owner;
REVOKE ALL ON FUNCTION admin_user_daily(BIGINT, DATE, DATE) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_user_daily(BIGINT, DATE, DATE) TO spendwise_app;

-- ── privileges (SW-ADR-137) ──────────────────────────────────────────
-- RLS only NARROWS what a grant already allows. Both are required, and the
-- boot assertion checks this direction too, not only the dangerous one.
GRANT USAGE ON SCHEMA public TO spendwise_app;
-- full CRUD, narrowed by RLS
GRANT SELECT, INSERT, UPDATE, DELETE ON expenses, categories, sessions TO spendwise_app;
-- no DELETE, and the reason SURVIVED the record that first gave it: SW-ADR-107 ruled out user deletion in v1 and was SUPERSEDED by SW-ADR-150, which added deletion in its SOFT form - an UPDATE setting deleted_at, not a DELETE. So the runtime role still needs no DELETE on users, and now cannot destroy an account even when a person asks it to. password_resets is pruned by the owner (SW-ADR-122).
GRANT SELECT, INSERT, UPDATE ON users, password_resets TO spendwise_app;
-- append-only; UPDATE and DELETE are revoked and a trigger raises (SW-ADR-083)
GRANT SELECT, INSERT ON admin_audit_log TO spendwise_app;
-- one row; the signing-secret fingerprint is rewritten on rotation (SW-ADR-125)
GRANT SELECT, UPDATE ON app_meta TO spendwise_app;
-- /readyz reports the running migration revision (P-OPS-03, E0-S10 AC2) and it runs as the RUNTIME role. SELECT only: the runtime role still holds no DDL and cannot alter migration state, so SW-ADR-081's two-URL separation is untouched. Added 2026-08-05, when /readyz was written and returned 503 permission denied - the acceptance criterion had named the revision since the Bible was written and nothing had ever granted the role that could read it.
-- alembic, not this schema - so the GRANT is emitted at the END of the baseline migration, after Alembic has created its own version table
DO $do$ BEGIN
    IF to_regclass('public.alembic_version') IS NOT NULL THEN
        GRANT SELECT ON alembic_version TO spendwise_app;
    END IF;
END $do$;

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
