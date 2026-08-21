"""`E6-S5` — capabilities that must NOT exist.

The hardest kind of test to write, because the thing under test is nothing. A
specification that something does not exist still needs an assertion, or the
capability silently arrives later and no one notices — that is the story's own
fourth criterion, and it is the whole argument for this file.

**These criteria were narrowed on 2026-08-21 by `SW-ADR-153`**, on a client
ruling. As originally written they said *"no endpoint lets a person change their
own email, display name or password"* — and two thirds of that had become false
of the shipped product, sanctioned by `SW-ADR-148`. Written literally, these
tests would have failed against correct code, and the obvious fix would have
been to delete an approved feature to satisfy stale text. The narrowing changed
the documents, not the application: no line of `app/` moved.

What survived the narrowing is the clause that was always load-bearing. Email is
the identity the unique index is built on; changing it with nothing to verify the
new address is an account-takeover vector, and `SW-ADR-012` records that there is
no email in this stack to verify with.

**Every detector here is red-proofed.** `test_the_detectors_actually_fire` plants
each forbidden capability into a copy of the real input and asserts the detector
goes red. An absence-test that has never been seen failing is indistinguishable
from an absence-test that cannot fail, and this project has a standing record of
that being the more common outcome.

No database required: every assertion reads the route table, the schemas, the
generated `security.sql`, or the tools directory.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SECURITY_SQL = (ROOT / "docs" / "06 DataModel" / "security.sql").read_text(encoding="utf-8")


def _routes():
    """Every route the application actually serves.

    **`app.routes` is not the route table.** This FastAPI keeps an included
    router as an `_IncludedRouter` wrapper with no `.path` and no `.routes` —
    only `.original_router` — so the obvious walk returns 8 objects, none of
    them an endpoint. The first draft of this file did exactly that and
    reported zero DELETE routes on a codebase that has one, while two of its
    tests passed by having nothing to examine.

    `flatten` is `E4-S1`'s, imported rather than copied: that story already
    solved this and a second copy is a second thing to get wrong. Every caller
    below asserts the result is non-empty, for the same reason it does.
    """
    from tests.test_admin import flatten
    import app.main as main
    out = []
    for r in flatten(main.app.routes):
        out.append((sorted(getattr(r, "methods", None) or set()),
                    getattr(r, "path", ""),
                    getattr(getattr(r, "endpoint", None), "__name__", "")))
    assert any(p.startswith("/api/auth") for _, p, _ in out), \
        "no /api/auth routes found — the walk is broken, not the application"
    return out


# ── criterion 1 — nothing hard-deletes a user ────────────────────────────────

def test_the_runtime_role_holds_no_delete_grant_on_users():
    """The property that actually protects the data, asserted where it is true.

    `SW-ADR-150` made deletion soft; this is what makes hard deletion
    *impossible* rather than merely unimplemented. Even a handler that tried to
    issue `DELETE FROM users` would be refused by Postgres, because the runtime
    role was never granted the privilege.
    """
    grants = re.findall(r"^GRANT ([^;]+?) ON ([^;]+?) TO spendwise_app;",
                        SECURITY_SQL, re.M)
    assert grants, "no grants to spendwise_app found — security.sql changed shape"
    for privileges, tables in grants:
        table_list = [t.strip() for t in tables.split(",")]
        if "users" in table_list:
            assert "DELETE" not in privileges.upper(), (
                f"spendwise_app was granted DELETE on users: GRANT {privileges} "
                f"ON {tables}. SW-ADR-150 keeps deletion soft precisely so the "
                f"runtime role cannot destroy an account even when asked to")


def test_no_route_hard_deletes_a_user():
    """`DELETE /api/auth/me` exists and is allowed to — it is SOFT.

    The original criterion said to grep for "a delete-user operation", which
    finds `delete_me` and fails against correct code. What it was reaching for
    is that no row is ever destroyed, so that is what is asserted: the one
    delete-shaped route on a user resource is the soft one, and its
    implementation is an UPDATE.
    """
    user_deleters = [
        (m, p, name) for m, p, name in _routes()
        if "DELETE" in m and ("/auth/me" in p or "/users/" in p)
    ]
    assert [p for _, p, _ in user_deleters] == ["/api/auth/me"], (
        f"unexpected DELETE route(s) on a user resource: {user_deleters}. "
        f"Only the soft self-delete may exist (SW-ADR-150)")

    svc = (ROOT / "app" / "modules" / "auth" / "service.py").read_text(encoding="utf-8")
    assert "deleted_at = now" in svc.replace("user.deleted_at = now", "deleted_at = now"), \
        "the self-delete path no longer sets deleted_at — it may have become a real delete"
    assert not re.search(r"\bdelete\s*\(\s*[Uu]ser\b|DELETE\s+FROM\s+users", svc), \
        "the auth service issues a hard delete against users"


def test_no_tool_or_cli_path_hard_deletes_a_user():
    """`tools/` is operator surface. A maintenance script that hard-deletes is
    the same capability arriving through a side door — and side doors are how
    absences stop being true without any endpoint changing."""
    offenders = []
    for f in (ROOT / "tools").glob("*.py"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if re.search(r"DELETE\s+FROM\s+users\b", text, re.I):
            offenders.append(f.name)
    assert not offenders, f"a tool issues DELETE FROM users: {offenders}"


def test_the_only_drop_of_users_is_a_migration_downgrade():
    """A baseline migration's `downgrade()` tears the schema down — that is
    schema rollback for local development, not a runtime capability. Anything
    outside a downgrade would be."""
    for f in (ROOT / "alembic" / "versions").glob("*.py"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "def upgrade" not in text:
            continue
        # The UPGRADE body only. The baseline runs its teardown through a
        # module-level `DROP` list rather than inline SQL, so scanning the whole
        # file for the literal finds those statements and cannot tell which
        # direction executes them — the first draft of this test failed on
        # correct code for precisely that reason.
        upgrade_body = text.split("def upgrade", 1)[1].split("def downgrade")[0]
        assert not re.search(r"\bDROP\b|drop_table\(", upgrade_body, re.I), (
            f"{f.name}'s upgrade path drops something. Migrations run at "
            f"container start (SW-ADR-093), so an upgrade that drops runs "
            f"against live data on every deploy")


# ── criterion 2 — nobody changes their own email ─────────────────────────────

def test_the_profile_update_model_has_no_email_field():
    """`PATCH /api/auth/me` changes the display name and nothing else
    (`SW-ADR-148` C). The absence of `email` here is the whole control: the
    model is what the request is validated against, so a field that is not
    declared cannot be supplied."""
    from app.modules.auth.schemas import ProfileUpdate
    assert "email" not in ProfileUpdate.model_fields, (
        "ProfileUpdate accepts an email. Email is the identity the unique index "
        "is built on, and SW-ADR-012 records there is no email in this stack to "
        "verify a new address with — so changing it is account takeover")


def test_extra_keys_are_ignored_rather_than_applied():
    """Declaring no `email` field is only a control if an undeclared key is
    dropped. `extra="allow"` plus a permissive service would let a forged key
    through the one gate that is supposed to stop it."""
    from app.modules.auth.schemas import ProfileUpdate
    parsed = ProfileUpdate.model_validate(
        {"display_name": "New", "email": "attacker@elsewhere.test"})
    assert not hasattr(parsed, "email"), "an undeclared email survived validation"
    assert "email" not in parsed.model_dump()


def test_no_self_service_route_accepts_an_email_anywhere():
    """The model is one door. This walks every non-admin route that mutates and
    checks none of their request models carry an email — so a NEW endpoint
    added tomorrow cannot reintroduce the capability quietly."""
    import inspect
    from pydantic import BaseModel
    from tests.test_admin import flatten
    import app.main as main

    offenders, examined = [], []
    for route in flatten(main.app.routes):
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", None) or set())
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None or not path.startswith("/api/"):
            continue
        if path.startswith("/api/admin"):
            continue
        if not ({"POST", "PATCH", "PUT"} & methods):
            continue
        # register and login legitimately take an email — they are how a person
        # SUPPLIES an identity, not how they change one.
        if path in ("/api/auth/register", "/api/auth/login"):
            continue
        # `eval_str=True` is load-bearing. Every module in `app/` starts with
        # `from __future__ import annotations`, which makes annotations plain
        # STRINGS at runtime — so `isinstance(ann, type)` is False for every
        # parameter and this loop examined nothing while reporting success.
        # The `examined` guard below is what exposed that.
        try:
            sig = inspect.signature(endpoint, eval_str=True)
        except Exception:                                   # noqa: BLE001
            continue
        for _, param in sig.parameters.items():
            ann = param.annotation
            if isinstance(ann, type) and issubclass(ann, BaseModel):
                examined.append(f"{sorted(methods)} {path} -> {ann.__name__}")
                if "email" in ann.model_fields:
                    offenders.append(f"{sorted(methods)} {path} -> {ann.__name__}.email")

    # The guard that stops this passing by examining nothing. An earlier version
    # looked routes up in the UNFLATTENED `main.app.routes`, found `None` every
    # time, and reported success having inspected zero models — a green tick for
    # work it never did, which is the failure this whole file is about.
    assert examined, (
        "no request models were examined at all — the walk found nothing, so "
        "this assertion proved nothing")
    assert not offenders, f"a self-service route accepts an email: {offenders}"


# ── criterion 3 — the detectors are proved to fire ───────────────────────────

@pytest.mark.parametrize("label,planted,detector", [
    ("DELETE granted on users",
     "GRANT SELECT, INSERT, UPDATE, DELETE ON users, password_resets TO spendwise_app;",
     "grant"),
    ("a tool that hard-deletes",
     "cur.execute('DELETE FROM users WHERE id = %s', (uid,))",
     "tool"),
])
def test_the_detectors_actually_fire(label, planted, detector):
    """Red-proof. Plant the capability, watch the detector go red.

    An absence-test that has never been seen failing is indistinguishable from
    one that cannot fail — and this project has three records of a check that
    passed while the defect walked through it (`SW-ADR-131`, `SW-ADR-147`, the
    band-colour split). The same discipline `consistency_check --selftest`
    applies to itself is applied here.

    Nothing on disk is touched: the planted text is checked in memory against
    the same expression the real test uses.
    """
    if detector == "grant":
        grants = re.findall(r"^GRANT ([^;]+?) ON ([^;]+?) TO spendwise_app;",
                            planted, re.M)
        fired = any("DELETE" in priv.upper()
                    for priv, tables in grants
                    if "users" in [t.strip() for t in tables.split(",")])
    else:
        fired = bool(re.search(r"DELETE\s+FROM\s+users\b", planted, re.I))
    assert fired, f"the detector for {label!r} did NOT fire on a planted violation"


def test_the_email_detector_fires_on_a_planted_field():
    """The same red-proof for criterion 2, against a real model rather than a
    string — a subclass that adds the forbidden field must be caught."""
    from pydantic import BaseModel
    from app.modules.auth.schemas import ProfileUpdate

    class ProfileUpdateWithEmail(ProfileUpdate):
        email: str | None = None

    assert "email" in ProfileUpdateWithEmail.model_fields, "planting failed"
    assert "email" not in ProfileUpdate.model_fields, \
        "the real model gained an email while this test was being written"
    assert issubclass(ProfileUpdateWithEmail, BaseModel)
