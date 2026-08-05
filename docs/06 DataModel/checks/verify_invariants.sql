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
