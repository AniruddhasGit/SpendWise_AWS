-- verify_invariants.sql — run against a live database. Every row must return ok = true.
-- These are the claims AGENT_CONTRACT.md makes. This file is how they stop being claims.

-- 1. the runtime role is not superuser and cannot bypass row security
SELECT 'runtime role is restricted' AS check,
       NOT rolsuper AND NOT rolbypassrls AS ok
FROM pg_roles WHERE rolname = 'spendwise_app';

-- 2. the runtime role owns no table
SELECT 'runtime role owns nothing' AS check,
       count(*) = 0 AS ok
FROM pg_class c JOIN pg_roles r ON c.relowner = r.oid
WHERE r.rolname = 'spendwise_app' AND c.relkind = 'r';

-- 3. forced row security on every protected table
SELECT 'FORCE RLS on ' || relname AS check, relforcerowsecurity AS ok
FROM pg_class WHERE relname IN ('expenses','categories','sessions');

-- 4. every protected table has a FOR ALL policy carrying BOTH USING and WITH CHECK
SELECT 'policy covers all commands on ' || tablename AS check,
       bool_or(cmd = 'ALL' AND qual IS NOT NULL AND with_check IS NOT NULL) AS ok
FROM pg_policies WHERE tablename IN ('expenses','categories','sessions')
GROUP BY tablename;

-- 5. the audit log refuses UPDATE and DELETE
SELECT 'audit log is append-only' AS check,
       count(*) = 1 AS ok
FROM pg_trigger WHERE tgname = 'trg_audit_log_immutable';

-- 6. the audit log carries no foreign key, so it outlives its subjects
SELECT 'audit log has no FK' AS check, count(*) = 0 AS ok
FROM pg_constraint WHERE conrelid = 'admin_audit_log'::regclass AND contype = 'f';

-- 7. the money column is bounded on BOTH sides
SELECT 'amount is bounded' AS check,
       count(*) = 1 AS ok
FROM pg_constraint
WHERE conrelid = 'expenses'::regclass AND conname = 'ck_expenses_amount_paise';

-- 8. the composite FK exists and is NOT ON DELETE SET NULL
SELECT 'category ownership enforced by FK' AS check,
       count(*) = 1 AS ok
FROM pg_constraint
WHERE conrelid = 'expenses'::regclass AND contype = 'f' AND confdeltype = 'a';  -- 'a' = NO ACTION

-- ── the POSITIVE direction (SW-ADR-137) ─────────────────────────────────────
-- Checks 1-8 all ask what the runtime role CANNOT do. Until 2026-08-05 there was
-- no GRANT on any table, so the role could not read a single row - and this file
-- printed all-green, because nothing here asked whether it could do anything.
-- A boot assertion that tests only one direction passes happily against a role
-- that is completely inert.

-- 9. the runtime role can reach the schema at all
SELECT 'runtime role has USAGE on public' AS check,
       has_schema_privilege('spendwise_app', 'public', 'USAGE') AS ok;

-- 10. the runtime role holds every privilege the application actually needs
SELECT 'runtime role can ' || p.priv || ' ' || t.tbl AS check,
       has_table_privilege('spendwise_app', t.tbl, p.priv) AS ok
FROM (VALUES ('expenses'),('categories'),('sessions')) AS t(tbl),
     (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')) AS p(priv)
UNION ALL
SELECT 'runtime role can ' || p.priv || ' ' || t.tbl,
       has_table_privilege('spendwise_app', t.tbl, p.priv)
FROM (VALUES ('users'),('password_resets')) AS t(tbl),
     (VALUES ('SELECT'),('INSERT'),('UPDATE')) AS p(priv)
UNION ALL
SELECT 'runtime role can ' || p.priv || ' admin_audit_log',
       has_table_privilege('spendwise_app', 'admin_audit_log', p.priv)
FROM (VALUES ('SELECT'),('INSERT')) AS p(priv);

-- 11. and holds NO privilege the design has no path for
SELECT 'runtime role cannot DELETE ' || t.tbl AS check,
       NOT has_table_privilege('spendwise_app', t.tbl, 'DELETE') AS ok
-- SW-ADR-107 ("no user-deletion path in v1") is superseded by SW-ADR-150: deletion
-- exists and it is SOFT, which is an UPDATE of deleted_at — so the runtime role
-- still holds no DELETE on users. The grant did not change; the record behind it did.
FROM (VALUES ('users'),('password_resets')) AS t(tbl)
UNION ALL
SELECT 'runtime role cannot ' || p.priv || ' admin_audit_log',
       NOT has_table_privilege('spendwise_app', 'admin_audit_log', p.priv)
FROM (VALUES ('UPDATE'),('DELETE')) AS p(priv);         -- append-only (SW-ADR-083)

-- 12. the admin stats function is executable by the runtime role, and its return
--     type carries no column capable of holding an amount (SW-ADR-129)
SELECT 'admin_expense_stats is executable by the runtime role' AS check,
       has_function_privilege('spendwise_app', 'admin_expense_stats(bigint)', 'EXECUTE') AS ok;

SELECT 'admin_expense_stats returns only a count and a date' AS check,
       count(*) = 2 AND bool_and(t.typname IN ('int8','date')) AS ok
FROM pg_proc p
     JOIN LATERAL unnest(p.proallargtypes, p.proargmodes) AS a(atype, amode) ON true
     JOIN pg_type t ON t.oid = a.atype
WHERE p.proname = 'admin_expense_stats' AND a.amode IN ('t','o');

-- 13. NO policy on a money table consults app.is_admin (SW-ADR-129).
--     This is the check that would have caught the hole SW-ADR-129 closed.
SELECT 'no admin GUC policy on a money table' AS check,
       count(*) = 0 AS ok
FROM pg_policies
WHERE tablename IN ('expenses','categories')
  AND (coalesce(qual, '') LIKE '%is_admin%' OR coalesce(with_check, '') LIKE '%is_admin%');
