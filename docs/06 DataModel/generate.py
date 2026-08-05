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

    # INDEXES BEFORE FOREIGN KEYS. The composite FK of SW-ADR-072 references
    # `categories (id, user_id)`, and PostgreSQL requires a unique constraint or
    # index on exactly those columns to already exist — otherwise:
    #   there is no unique constraint matching given keys for referenced table
    # The first version of this generator emitted every FK before every index
    # and produced DDL that could not be applied to an empty database at all.
    ix = []
    for i in spec["indexes"]:
        d = i["definition"].strip()
        uniq = d.upper().startswith("UNIQUE")
        body = d[len("UNIQUE"):].strip() if uniq else d
        ix.append("-- %s\nCREATE %sINDEX %s ON %s %s;"
                  % (i["source"], "UNIQUE " if uniq else "",
                     index_name(i["table"], d), i["table"], body))
    out.append("\n".join(ix))

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
                "-- SECURITY DEFINER runs this as the TABLE OWNER — which is not, on its own,\n"
                "-- enough. FORCE ROW LEVEL SECURITY subjects the owner to its own policies, so\n"
                "-- the owner sees exactly what `app.user_id` says and nothing else. The first\n"
                "-- version of this function was LANGUAGE sql with no GUC handling, and it\n"
                "-- returned (0, NULL) for every account except the caller's own — silently,\n"
                "-- and looking exactly like a correct privacy-respecting answer.\n"
                "--\n"
                "-- So the identity is swapped to the TARGET for the length of the query and\n"
                "-- restored before returning. It is transaction-local (set_config(..., true)),\n"
                "-- and it refuses to run when app.user_id is unset rather than restoring to\n"
                "-- something that was never there — an unset GUC reads as NULL, an empty one\n"
                "-- raises on ::bigint, and the two are not the same state.\n"
                "--\n"
                "-- THE RETURN TYPE IS STILL THE GUARD. An amount cannot come back through this\n"
                "-- function because there is no column for one, so SRC-001 §4.5 is structurally\n"
                "-- true at the DATABASE and not merely in a response model.\n"
                "-- SET search_path is MANDATORY: without it a definer function is a\n"
                "-- privilege-escalation vector (an attacker-controlled schema shadows a name).\n"
                "-- VOLATILE, not STABLE: it mutates a GUC, and labelling that STABLE would be\n"
                "-- a lie the planner is entitled to act on.\n"
                "CREATE OR REPLACE FUNCTION {name}({args})\n"
                "    RETURNS TABLE ({returns})\n"
                "    LANGUAGE plpgsql\n"
                "    VOLATILE\n"
                "    SECURITY DEFINER\n"
                "    SET search_path = pg_catalog, public\n"
                "AS $fn$\n"
                "DECLARE\n"
                "    caller TEXT := current_setting('app.user_id', true);\n"
                "BEGIN\n"
                "    IF caller IS NULL OR caller = '' THEN\n"
                "        RAISE EXCEPTION '{name} requires app.user_id to be set (SW-ADR-136)';\n"
                "    END IF;\n"
                "    PERFORM set_config('app.user_id', target_user_id::text, true);\n"
                "    RETURN QUERY\n"
                "    {body}\n"
                "    PERFORM set_config('app.user_id', caller, true);\n"
                "END;\n"
                "$fn$;\n"
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
            if t.get("created_by"):
                # A table this schema does not create. `alembic_version` is
                # Alembic's own, so a plain GRANT here fails when security.sql
                # is applied standalone to a database that has never been
                # migrated — which is exactly how a fresh clone starts. Inside
                # the baseline migration the table always exists by this point,
                # because Alembic creates it before running upgrade().
                out.append(
                    "-- {why}\n-- {created_by}\n"
                    "DO $do$ BEGIN\n"
                    "    IF to_regclass('public.{table}') IS NOT NULL THEN\n"
                    "        GRANT {privileges} ON {table} TO {to};\n"
                    "    END IF;\n"
                    "END $do$;".format(table=t["on"][0], **t))
            else:
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


def render_baseline_migration(spec):
    """The Alembic baseline, with the DDL EMBEDDED rather than read at runtime.

    Three ways to get the generated DDL into a migration, and only one is right:

    * hand-transcribe it — creates a third artifact that drifts from the spec,
      which is the failure this package has filed six records about;
    * read `schema.sql` at runtime — requires shipping `docs/` inside the
      container image, and a migration that depends on documentation being
      present is a deploy that fails when someone trims the image;
    * **generate the migration too**, so it is self-contained AND cannot drift,
      because `generate.py --check` compares it against `datamodel.json`.

    `downgrade()` drops in reverse dependency order. It exists because `E0-S3`
    asserts *migrate down then up again exits 0* — a one-way migration is a
    migration nobody has tested.
    """
    schema = render_schema(spec)
    security = render_security(spec)
    tables = list(spec["tables"])

    def statements(sql):
        """Split SQL into individual statements, respecting `$$` bodies.

        **asyncpg wraps every execute in a prepared statement, and a prepared
        statement cannot carry multiple commands** — one `op.execute()` of the
        whole script fails with `cannot insert multiple commands into a
        prepared statement`, after dumping the entire script into the traceback.

        The split happens HERE, at generation time, where the content is known
        and the `$$ … $$` function bodies can be tracked exactly. Splitting at
        runtime would mean shipping a SQL parser to solve a problem that does
        not exist until then.
        """
        # Dollar quoting is TAGGED: `$$`, `$do$`, `$body$` are all legal and a
        # tag only closes against itself. Counting `$$` alone split the first
        # `DO $do$ ... END $do$;` block into three statements at its inner
        # semicolons, and the third of those was a bare `END $do$;` — a syntax
        # error at migration time, from a generator whose whole job is to make
        # that impossible. Tracked as a STACK of open tags.
        import re as _re
        TAG = _re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$")

        out, buf, open_tags = [], [], []
        for line in sql.split("\n"):
            s = line.strip()
            if not buf and (not s or s.startswith("--")):
                continue                       # comment or blank BETWEEN statements
            buf.append(line)
            for tag in TAG.findall(s):
                if open_tags and open_tags[-1] == tag:
                    open_tags.pop()
                else:
                    open_tags.append(tag)
            in_dollar = bool(open_tags)
            # A statement can end `;   -- why this line matters`, and the trailing
            # comment made a plain endswith(";") miss it — which silently merged
            # the next statement onto this one and reproduced the very
            # multiple-commands error this split exists to prevent.
            if not in_dollar and ";" in s:
                after = s[s.rindex(";") + 1:].strip()
                if not after or after.startswith("--"):
                    out.append("\n".join(buf).strip())
                    buf = []
        tail = "\n".join(buf).strip()
        if tail:
            out.append(tail)
        return out

    def as_list(sql):
        return "\n".join('    r"""%s""",' % s for s in statements(sql))

    return '''"""baseline: the whole schema, its policies and its grants

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
%s
]

SECURITY = [
%s
]

# Reverse dependency order. Policies and the trigger go with their tables, so
# dropping the table is enough — but the FUNCTIONS are schema-level and outlive
# it, and a downgrade that leaves them behind makes the next upgrade fail on a
# duplicate object rather than on anything meaningful.
DROP = [
    r"""DROP TRIGGER IF EXISTS trg_audit_log_immutable ON admin_audit_log;""",
    r"""DROP FUNCTION IF EXISTS audit_log_is_append_only();""",
    r"""DROP FUNCTION IF EXISTS admin_expense_stats(BIGINT);""",
%s
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
''' % (as_list(schema), as_list(security),
       "\n".join('    r"""DROP TABLE IF EXISTS %s CASCADE;""",' % t
                 for t in reversed(tables)))


ARTIFACTS = [("schema.sql", render_schema),
             ("security.sql", render_security),
             ("TRACEABILITY.tsv", render_traceability),
             (os.path.join("..", "30 Deployment", "rds_bootstrap.sql"), render_bootstrap),
             (os.path.join("..", "..", "alembic", "versions",
                           "0001_baseline.py"), render_baseline_migration)]


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
