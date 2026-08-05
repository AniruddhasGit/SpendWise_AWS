#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive `schema.sql`, `security.sql` and `TRACEABILITY.tsv` from `datamodel.json`.

All three carry a GENERATED banner. Until 2026-08-05 that banner was
**unfalsifiable**: the script that wrote them lived in a scratch directory and
was gone, so nobody could regenerate a file and compare. `SW-ADR-066` says a
hand patch to a generated file is erased by the next build — but there was no
next build, so a hand patch simply became the artifact.

Under that cover `security.sql` had drifted. It carried an admin policy on
`expenses` that appears NOWHERE in `datamodel.json`, and that policy was the
isolation hole `SW-ADR-129` closes. `fingerprints.json` could not have caught
it: it watches for a generated hash moving without the spec moving, which is
blind to content the spec never contained.

This script lives in the repository so the banner can be checked:

    py "docs/06 DataModel/generate.py" --check

exits non-zero if any committed file differs from what the spec produces.
`tools/consistency_check.py` runs it.

Usage:
    generate.py            rewrite all three artifacts
    generate.py --check    verify the committed files match, write nothing
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "datamodel.json")


# ── naming ────────────────────────────────────────────────────────────────
# Alembic's convention is set on the SQLAlchemy MetaData (SW-ADR-040); these
# reproduce it so the generated DDL and the ORM agree on every identifier.

def _slug(s):
    return s.strip().lower().replace("(", "_").replace(")", "").replace(" ", "_")


def index_name(table, definition):
    d = definition.strip()
    uniq = d.upper().startswith("UNIQUE")
    if uniq:
        d = d[len("UNIQUE"):].strip()
    m = re.match(r"\((.*?)\)\s*(WHERE .*)?$", d, re.S)
    if not m:
        raise ValueError("cannot parse index definition: %r" % definition)
    parts = [_slug(p) for p in m.group(1).split(",")]
    if m.group(2):
        parts.append(_slug(m.group(2)))
    return ("uq_" if uniq else "ix_") + table + "_" + "__".join(parts)


def fk_name(table, column):
    # a composite column list arrives as "(category_id, user_id)" — every
    # non-identifier character collapses to a single underscore
    return "fk_%s_%s" % (table, re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_"))


# ── renderers ─────────────────────────────────────────────────────────────

SCHEMA_HEADER = """\
-- schema.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.
-- Regenerate:  py "docs/06 DataModel/generate.py"
-- Verify:      py "docs/06 DataModel/generate.py" --check
-- SW-ADR-066: a hand patch to a generated file is erased by the next build, silently.
-- Naming convention (SW-ADR-040) is set on the SQLAlchemy MetaData, not here;
-- generate.py reproduces it so the DDL and the ORM agree on every identifier.
"""


def render_schema(spec):
    out = [SCHEMA_HEADER]
    for table, t in spec["tables"].items():
        lines = ["-- %s  [%s]  %s" % (table, t["source"], t.get("note", "")),
                 "CREATE TABLE %s (" % table]
        body, checks = [], []
        pk = []
        for c in t["columns"]:
            seg = "    %s %s" % (c["name"], c["type"])
            if c.get("nullability"):
                seg += " " + c["nullability"]
            if c.get("default") is not None:
                seg += " DEFAULT " + c["default"]
            body.append(seg)
            if c.get("check"):
                checks.append("    CONSTRAINT ck_%s_%s CHECK (%s)" % (table, c["name"], c["check"]))
            if c.get("primary_key") or c["name"] == "id":
                pk.append(c["name"])
        body.append("    CONSTRAINT pk_%s PRIMARY KEY (%s)" % (table, ", ".join(pk)))
        body.extend(checks)
        lines.append(",\n".join(body))
        lines.append(");")
        out.append("\n".join(lines))

    fks = []
    for fk in spec["foreign_keys"]:
        col = fk["column"] if fk["column"].startswith("(") else "(%s)" % fk["column"]
        m = re.match(r"(\w+)\((.*)\)$", fk["references"].strip(), re.S)
        ref_t, inner = m.group(1), m.group(2).strip()
        if inner.startswith("(") and inner.endswith(")"):
            inner = inner[1:-1].strip()
        fks.append("-- %s\nALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY %s REFERENCES %s (%s) ON DELETE %s;"
                   % (fk["source"], fk["table"], fk_name(fk["table"], fk["column"]),
                      col, ref_t, inner, fk["on_delete"]))
    out.append("\n".join(fks))

    ix = []
    for i in spec["indexes"]:
        d = i["definition"].strip()
        uniq = d.upper().startswith("UNIQUE")
        body = d[len("UNIQUE"):].strip() if uniq else d
        ix.append("-- %s\nCREATE %sINDEX %s ON %s %s;"
                  % (i["source"], "UNIQUE " if uniq else "",
                     index_name(i["table"], d), i["table"], body))
    out.append("\n".join(ix))
    return "\n\n".join(out) + "\n"


SECURITY_HEADER = """\
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
"""

OWNER_POLICY = """\
-- {table}: protected — {note}
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;   -- owners bypass RLS otherwise, silently
CREATE POLICY {table}_owner ON {table}
    FOR ALL
    USING      ({col} = current_setting('app.user_id', true)::bigint)
    WITH CHECK ({col} = current_setting('app.user_id', true)::bigint);
-- USING alone would be used as WITH CHECK too, but stating both makes the
-- intent explicit and stops a later edit weakening one without the other.
"""


def render_security(spec):
    out = [SECURITY_HEADER]
    for table, t in spec["tables"].items():
        if t.get("rls"):
            out.append(OWNER_POLICY.format(
                table=table, col=t.get("identity_column", "user_id"),
                note=t.get("note", "").rstrip(".")))
        else:
            out.append("-- %s: NO row-level security. %s\n" % (table, t.get("note", "")))

    aa = spec.get("admin_access", {})
    if aa.get("policies_on_money_tables") is False:
        out.append(
            "-- ── admin access ─────────────────────────────────────────────────────\n"
            "-- NO admin policy exists on expenses or categories (SW-ADR-129, restoring\n"
            "-- SW-ADR-043). `app.is_admin` is consulted by NO policy in this file and is\n"
            "-- never set on a request-scoped connection.\n"
            "--\n"
            "-- A permissive policy `USING (current_setting('app.is_admin') = 'true')` was\n"
            "-- what the superseded SW-ADR-077 produced. It is row-level, so it returned\n"
            "-- EVERY COLUMN of EVERY ROW — amount and description included — to any\n"
            "-- connection with that GUC set. Permissive policies are OR'd, so it could only\n"
            "-- ever widen access. No API test could have caught it: the response model still\n"
            "-- returned the right fields, from a query allowed to read everything.\n")
        for fn in aa.get("functions", []):
            out.append(
                "\n-- {purpose}\n"
                "-- SECURITY DEFINER bypasses row security by design — which is exactly why\n"
                "-- the RETURN TYPE is the guard. An amount cannot come back through this\n"
                "-- function because there is no column for one. SRC-001 §4.5 is structurally\n"
                "-- true at the DATABASE, not merely in a response model.\n"
                "-- SET search_path is MANDATORY: without it a definer function is a\n"
                "-- privilege-escalation vector (an attacker-controlled schema shadows a name).\n"
                "CREATE OR REPLACE FUNCTION {name}({args})\n"
                "    RETURNS TABLE ({returns})\n"
                "    LANGUAGE sql\n"
                "    STABLE\n"
                "    SECURITY DEFINER\n"
                "    SET search_path = pg_catalog, public\n"
                "AS $$\n"
                "    {body}\n"
                "$$;\n"
                "ALTER FUNCTION {name}({argtypes}) OWNER TO spendwise_owner;\n"
                "REVOKE ALL ON FUNCTION {name}({argtypes}) FROM PUBLIC;\n"
                "GRANT EXECUTE ON FUNCTION {name}({argtypes}) TO spendwise_app;\n".format(**fn))

    # ── privileges ────────────────────────────────────────────────────────
    # There were NO table grants here until 2026-08-05 (SW-ADR-137). Every query
    # by the runtime role would have failed with permission denied, and
    # verify_invariants.sql would still have printed all-green, because it only
    # ever checked what the role CANNOT do. RLS narrows a grant; with no grant it
    # was protecting a door already welded shut.
    g = spec.get("grants")
    if g:
        out.append("-- ── privileges (SW-ADR-137) ──────────────────────────────────────────\n"
                   "-- RLS only NARROWS what a grant already allows. Both are required, and the\n"
                   "-- boot assertion checks this direction too, not only the dangerous one.")
        for role in g.get("schema_usage", []):
            out.append("GRANT USAGE ON SCHEMA public TO %s;" % role)
        for t in g["tables"]:
            out.append("-- %s\nGRANT %s ON %s TO %s;"
                       % (t["why"], t["privileges"], ", ".join(t["on"]), t["to"]))

    out.append("""
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
""")
    return "\n".join(out)


def render_traceability(spec):
    rows = [("object", "source_id", "status")]
    for table, t in spec["tables"].items():
        rows.append(("tables/%s" % table, t["source"], "RULED"))
        for c in t["columns"]:
            rows.append(("tables/%s.%s" % (table, c["name"]), c["source"], "RULED"))
    for fk in spec["foreign_keys"]:
        rows.append(("foreign_keys/%s" % fk_name(fk["table"], fk["column"]),
                     fk["source"], "RULED"))
    for i in spec["indexes"]:
        rows.append(("indexes/%s" % index_name(i["table"], i["definition"]),
                     i["source"], "RULED"))
    aa = spec.get("admin_access", {})
    for fn in aa.get("functions", []):
        rows.append(("functions/%s" % fn["name"], aa["source"], "RULED"))
    return "".join("\t".join(r) + "\n" for r in rows)


def render_bootstrap(spec):
    """The one script the CLIENT runs by hand, as the RDS master user.

    Everything else in this package is an Alembic migration. This is not, for
    two reasons that are properties of PostgreSQL rather than choices:
    `CREATE DATABASE` cannot run inside a transaction, and the owner role has no
    privilege to create roles. So it is generated here and handed over.
    """
    c = spec.get("cluster")
    if not c:
        return ""
    L = ["-- rds_bootstrap.sql — GENERATED from datamodel.json by generate.py. DO NOT HAND-EDIT.",
         "-- Regenerate:  py \"docs/06 DataModel/generate.py\"",
         "--",
         "-- RUN THIS ONCE, AS THE RDS MASTER USER, CONNECTED TO THE `postgres` DATABASE.",
         "--",
         "-- Source: " + c["source"],
         "--",
         "-- " + "\n-- ".join(_wrap(c["note"])),
         "--"]
    for n in c["rds_notes"]:
        L.append("-- * " + "\n--   ".join(_wrap(n)))
    if c.get("how_to_run"):
        L += ["--", "-- ── HOW TO RUN ──────────────────────────────────────────────────────"]
        # Emitted VERBATIM. These lines are hand-wrapped in the spec, and
        # re-wrapping them broke a command across two lines and mangled a
        # Windows path (`\18\bin` -> a backspace escape). Layout the author
        # chose is layout the author meant.
        for h in c["how_to_run"]:
            L.append(("-- " + h).rstrip())
    L += ["", "\\set ON_ERROR_STOP on", ""]

    L.append("-- ── roles ───────────────────────────────────────────────────────────")
    L.append("-- Passwords are NOT in this file and never will be. Set them below, or")
    L.append("-- create the roles here and ALTER ... PASSWORD separately. Whatever you")
    L.append("-- choose, the password never enters git (CONSTITUTION Art IV.4).")
    for r in c["roles"]:
        L += ["",
              "-- %s — %s" % (r["name"], r["purpose"]),
              "-- " + "\n-- ".join(_wrap(r["why"])),
              "DO $$ BEGIN",
              "    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '%s') THEN" % r["name"],
              "        CREATE ROLE %s %s" % (r["name"], r["attributes"]),
              "            PASSWORD :'%s_password';" % r["name"],
              "    END IF;",
              "END $$;",
              "-- re-assert the attributes even if the role already existed:",
              "ALTER ROLE %s %s;" % (r["name"], r["attributes"])]

    L += ["", "-- ── databases ───────────────────────────────────────────────────────",
          "-- CREATE DATABASE cannot run inside a transaction or a DO block, so these",
          "-- are guarded with \\gexec rather than an IF NOT EXISTS."]
    for d in c["databases"]:
        L += ["",
              "-- %s — %s" % (d["name"], d["purpose"]),
              "SELECT 'CREATE DATABASE %s WITH OWNER %s ENCODING ''UTF8'''"
              % (d["name"], d["owner"]),
              " WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '%s')\\gexec"
              % d["name"]]

    L += ["", "-- ── connect privileges ──────────────────────────────────────────────",
          "-- The runtime role may CONNECT. Everything it may then DO is granted by",
          "-- security.sql, inside the migration, and narrowed again by RLS."]
    app = next((r["name"] for r in c["roles"] if "app" in r["name"]), "spendwise_app")
    for d in c["databases"]:
        L.append("GRANT CONNECT ON DATABASE %s TO %s;" % (d["name"], app))
    L += ["",
          "-- Nobody else. PUBLIC can connect to any database by default, which is a",
          "-- default worth removing on a publicly-reachable instance.",
          "REVOKE CONNECT ON DATABASE %s FROM PUBLIC;" % c["databases"][0]["name"],
          "",
          "-- ── verify — every row must come back as expected ───────────────────",
          "-- E0-S2 asserts these three at BOOT as well. Checking here means a",
          "-- mistake surfaces now, not as a failing gate an hour later.",
          "SELECT rolname, rolsuper, rolbypassrls, rolcreaterole",
          "  FROM pg_roles WHERE rolname LIKE 'spendwise%';",
          "--  expected: rolsuper = f, rolbypassrls = f, rolcreaterole = f  for BOTH",
          "",
          "SELECT datname, pg_get_userbyid(datdba) AS owner",
          "  FROM pg_database WHERE datname LIKE 'spendwise%';",
          "--  expected: owner = %s  for both databases" % c["databases"][0]["owner"],
          ""]
    return "\n".join(L)


def _wrap(s, w=74):
    out, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out


ARTIFACTS = [("schema.sql", render_schema),
             ("security.sql", render_security),
             ("TRACEABILITY.tsv", render_traceability),
             (os.path.join("..", "30 Deployment", "rds_bootstrap.sql"), render_bootstrap)]


def main():
    with open(SPEC, encoding="utf-8") as f:
        spec = json.load(f)
    check = "--check" in sys.argv
    bad = 0
    for name, render in ARTIFACTS:
        path = os.path.join(HERE, name)
        generated = render(spec)
        if not check:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(generated)
            print("wrote %-18s %6d bytes" % (name, len(generated)))
            continue
        try:
            with open(path, encoding="utf-8") as f:
                committed = f.read()
        except FileNotFoundError:
            print("FAIL  %s does not exist" % name)
            bad += 1
            continue
        if committed != generated:
            bad += 1
            print("FAIL  %s has drifted from datamodel.json — the failure mode" % name)
            print("      SW-ADR-129 was raised for. Diff (committed -> spec):")
            import difflib
            for line in list(difflib.unified_diff(
                    committed.splitlines(), generated.splitlines(),
                    "committed", "from spec", lineterm="", n=1))[:30]:
                print("      " + line)
        else:
            print("PASS  %-18s matches datamodel.json (%d bytes)" % (name, len(generated)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
