"""The container's constraints, asserted against the files rather than trusted.

`SW-ADR-011` had the build session write the Dockerfile late, and the cost it
recorded is that the clean-clone evidence is weaker for it. These tests are part
of paying that cost back: every rule `SRC-001 §11` states about the image is
checked here, statically, so it cannot drift without something going red.

**No Docker daemon is required.** These read the two files. A test that needed
`docker build` would not run on a bare clone, would not run in the day-one gate,
and would quietly become the suite's slowest case — so the things that CAN be
checked by reading are checked by reading. What only a real build can prove
(that the image assembles, runs as uid 999, resolves `client/dist`, and refuses
to bind the port when migrations fail) was verified by building and running it,
and is recorded in the commit rather than pretended at here.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
ENTRYPOINT = (ROOT / "docker-entrypoint.sh").read_text(encoding="utf-8")
DOCKERIGNORE = (ROOT / ".dockerignore").read_text(encoding="utf-8")


# ── SRC-001 §11.1 — the two stages ───────────────────────────────────────────

def test_the_client_is_built_in_a_node_stage_that_does_not_survive():
    """"Only the results carry over, not the Node toolchain."

    A single-stage image that installed node would work and ship ~200MB of
    build tooling to production, where it is attack surface with no purpose.
    """
    assert re.search(r"^FROM (?:--platform=\S+ )?node:20-alpine AS client",
                     DOCKERFILE, re.M), \
        "SRC-001 §11.1 names node:20-alpine as the first stage"
    assert re.search(r"^COPY --from=client ", DOCKERFILE, re.M), \
        "nothing is copied out of the client stage — the build result is discarded"
    # The runtime stage must not install node itself.
    runtime = re.split(r"^FROM .*python:", DOCKERFILE, maxsplit=1, flags=re.M)[1]
    assert "npm" not in runtime and "nodejs" not in runtime, \
        "the runtime stage installs node — that is the toolchain §11.1 excludes"


def test_the_python_base_pins_its_patch_version():
    """RUNTIME_VERSIONS.md: "Pin the patch, not just 3.12."

    A floating `python:3.12` means two builds of the same commit can differ,
    which is exactly the property `requirements.lock` exists to remove one
    layer up. Pinning one and floating the other is half a guarantee.
    """
    m = re.search(r"^FROM (?:--platform=\S+ )?(python:3\.12\.\d+-slim)",
                  DOCKERFILE, re.M)
    assert m, "the runtime base must be python:3.12.<patch>-slim, patch pinned"
    assert "-alpine" not in m.group(1), \
        "SW-ADR-016 locks the stack; alpine's musl forces source builds of " \
        "wheels that ship manylinux binaries"


def test_the_runtime_stage_pins_its_cpu_architecture():
    """The image must declare the CPU it is for, not inherit the builder's.

    `SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13) leaves building and pushing to the client, by hand, from
    whatever laptop is in front of them. An unpinned runtime stage therefore
    produces an arm64 image on Apple Silicon and an amd64 image everywhere
    else, from the identical commit.

    That failure is unusually expensive: the push succeeds, ECS accepts the
    task definition and places the task, and only then does the container die
    with `exec format error`. Nothing in the deploy path reads as wrong until
    the very last step, and until the `/ecs/spendwise` log group exists there
    is no record of it at all.

    The client stage is deliberately NOT pinned — it emits JavaScript, which
    has no architecture, so pinning it would buy nothing and cost emulation.
    """
    runtime_from = re.search(r"^FROM (--platform=\S+ )?python:", DOCKERFILE, re.M)
    assert runtime_from, "no runtime FROM line found"
    assert runtime_from.group(1), \
        "the runtime stage does not pin --platform; the image's architecture " \
        "would be whatever the builder's laptop happens to be"
    assert "linux/amd64" in runtime_from.group(1), \
        "the runtime stage must pin linux/amd64 — the deploy target is a " \
        "t3.micro, which is x86"

    client_from = re.search(r"^FROM (--platform=\S+ )?node:", DOCKERFILE, re.M)
    assert client_from, "no client FROM line found"
    assert "BUILDPLATFORM" in (client_from.group(1) or ""), \
        "the client stage should track $BUILDPLATFORM so it builds natively"


def test_dependencies_come_from_the_lock_never_from_pyproject():
    """RUNTIME_VERSIONS.md: ranges "resolve differently on different days"."""
    assert "requirements.lock" in DOCKERFILE
    assert not re.search(r"pip install[^\n]*pyproject", DOCKERFILE), \
        "installing from pyproject ranges makes the image non-reproducible"


# ── SRC-001 §11.2 — process hygiene ──────────────────────────────────────────

def test_the_container_runs_as_a_non_root_user():
    """`SRC-001 §11.2`: "Run as a non-root user." Not optional."""
    assert re.search(r"^USER (?!root)\S+", DOCKERFILE, re.M), \
        "no USER instruction, or it switches to root"
    user_at = DOCKERFILE.index("USER ")
    assert DOCKERFILE.index("pip install") < user_at, \
        "pip runs as the app user, so the application can rewrite its own " \
        "dependencies at runtime"


def test_tini_is_the_entrypoint_so_sigterm_is_forwarded():
    """`SRC-001 §11.2` asks for tini by name. PID 1 gets no default signal
    handlers, so without an init SIGTERM is dropped, in-flight requests are cut
    instead of drained, and ECS waits out its stop timeout on every deploy."""
    assert re.search(r'ENTRYPOINT \["/usr/bin/tini", "--"', DOCKERFILE), \
        "tini is not PID 1"


def test_uvicorn_replaces_the_shell_rather_than_being_its_child():
    """Without `exec`, tini signals the shell, the shell does not forward, and
    uvicorn never learns the task is stopping."""
    assert re.search(r"^exec uvicorn ", ENTRYPOINT, re.M), \
        "uvicorn is started without exec — SIGTERM stops at the shell"


# ── SW-ADR-093 — migrate, then serve ─────────────────────────────────────────

def test_migrations_run_before_uvicorn_is_started():
    """`SW-ADR-093`: "before uvicorn binds the port".

    Reversed, a task enters service against a schema it has not finished
    migrating, and the health check calls it healthy while it 500s.
    """
    assert ENTRYPOINT.index("alembic upgrade head") < ENTRYPOINT.index("exec uvicorn"), \
        "uvicorn starts before the migration"


def test_a_failed_migration_stops_the_container_and_does_not_retry():
    """`SW-ADR-093`: "no retry, exit non-zero". A retry loop turns a broken
    migration into a task that flaps and an alarm nobody wired."""
    assert re.search(r"^set -e", ENTRYPOINT, re.M), \
        "without `set -e` a failed alembic run falls through to uvicorn"
    # Comments stripped first. The first version of this test scanned the whole
    # file and matched the word "retry" inside a comment QUOTING the ADR that
    # forbids retrying — a test failing on its own rationale. Scan what runs.
    code = "\n".join(l for l in ENTRYPOINT.splitlines()
                     if l.strip() and not l.lstrip().startswith("#"))
    assert not re.search(r"\b(while|until|sleep)\b", code), \
        "the entrypoint loops or sleeps — SW-ADR-093 rules retrying out explicitly"


# ── the trap this file exists for ────────────────────────────────────────────

def test_the_worker_count_matches_the_setting_the_rate_limiter_divides_by():
    """**Two places hold the worker count and they must be one number.**

    `SRC-001 §11.3` says `--workers 2`. `app/core/settings.py` defaults
    `UVICORN_WORKERS` to 2, and `app/core/ratelimit.py` divides `SW-ADR-128`'s
    effective limits by it to get each process's allowance — because the store
    is in-process, so N workers hold N counters.

    Run three workers against a setting of two and every authentication limit
    is silently 1.5x what was ruled. Nothing fails. Nothing logs. The throttle
    is simply looser than the record says it is — the same class of defect as
    `band-colour-agreement`: one value, two homes, no one checking.
    """
    from app.core.settings import Settings

    default_workers = Settings.model_fields["UVICORN_WORKERS"].default
    assert default_workers == 2, \
        "SRC-001 §11.3 fixes this at 2; changing it changes every rate limit"

    # The entrypoint must not hardcode a different number.
    hardcoded = re.findall(r"--workers[= ]\"?(\d+)", ENTRYPOINT)
    for n in hardcoded:
        assert int(n) == default_workers, (
            f"the entrypoint hardcodes --workers {n} while UVICORN_WORKERS "
            f"defaults to {default_workers}; the rate limits would be "
            f"{n}/{default_workers}x what SW-ADR-128 ruled")
    assert "UVICORN_WORKERS" in ENTRYPOINT, \
        "the entrypoint should take its worker count from the same setting the " \
        "limiter divides by, so the two cannot disagree"


# ── SW-ADR-127 — the health check ────────────────────────────────────────────

def test_curl_is_installed_because_the_ecs_health_check_needs_it():
    """`SW-ADR-127` fixes the check as
    `CMD-SHELL curl -f http://localhost:{port}/healthz || exit 1`.

    The slim base ships no curl, so a health check written to that ADR fails
    for want of the binary — and the task is reaped as unhealthy while serving
    correctly, which is the most expensive way to be wrong about nothing.
    """
    assert re.search(r"apt-get install[^\n]*curl", DOCKERFILE), "curl is not installed"


def test_the_health_check_uses_healthz_and_not_readyz():
    """`/healthz` opens no database session; `/readyz` does. A container health
    check pointed at `/readyz` restarts the task every time the database
    hiccups, which converts a brief database problem into an outage."""
    assert "/healthz" in DOCKERFILE
    assert "/readyz" not in DOCKERFILE


def test_the_start_period_covers_boot_time_migrations():
    """A start period shorter than the migration reports a task unhealthy while
    it is correctly migrating, and ECS kills it mid-upgrade."""
    m = re.search(r"--start-period=(\d+)s", DOCKERFILE)
    assert m and int(m.group(1)) >= 120, \
        "SW-ADR-127 sizes startPeriod at 120s to cover migrations"


# ── .dockerignore — the one that would leak ──────────────────────────────────

@pytest.mark.parametrize("pattern", [".env", "*.pem", "*.key"])
def test_secrets_never_enter_the_build_context(pattern):
    """A layer keeps what it copied even if a later layer deletes it. A `.env`
    baked into an image is readable by anyone who can pull it, and this
    `.env` holds the database credentials and the session signing secret."""
    assert pattern in DOCKERIGNORE, f"{pattern} can reach the build context"


def test_a_locally_built_client_cannot_be_copied_in_by_accident():
    """`client/dist` is produced by stage 1. If a local one rode in on the
    build context, the image would ship whatever was last built on somebody's
    laptop, from a commit nobody recorded."""
    assert "client/dist/" in DOCKERIGNORE
    assert "client/node_modules/" in DOCKERIGNORE


def test_every_docs_file_read_at_runtime_is_actually_in_the_image():
    """`.dockerignore` excludes `docs/`. Anything under it that the app READS
    at runtime must be copied back in explicitly, or the image is broken in a
    way no import-time check can see.

    This is not hypothetical. `app/core/errors.py` loads the error-code table
    from `contract.json`, and `app/modules/categories/service.py` loads the
    seeded category list from the same file — both deliberately, so the code
    and the spec of record cannot drift. The first real deploy shipped without
    it: `/healthz` answered 200, and every error path raised FileNotFoundError
    *inside the handler that formats errors*, so the 500 could not even
    describe itself. CI's smoke test polls `/healthz` only, so it stayed green.

    The test is written against the pattern rather than the one known file, so
    the next module that reads a spec at runtime is caught on the commit that
    adds it.

    THE SCAN ROOTS ARE READ OUT OF THE DOCKERFILE, not listed here. The first
    version of this test hard-coded `app/` and therefore missed
    `alembic/versions/0002_cr001_soft_delete_and_admin_daily.py:36`, which
    reads `docs/06 DataModel/security.sql` *during the migration*. That one
    stayed invisible for five weeks because every database it met was already
    at head, so alembic never ran it and never opened the file. CI's database
    is created empty on every run, and CI was red on main for four commits.

    So: whatever the image COPYs in, this test looks at. A test that guards the
    image while holding its own opinion of what the image contains is a test
    that goes green on the day those two disagree.
    """
    pattern = re.compile(
        r"""parents\[\d+\]\s*/\s*["']docs["']\s*(?:/\s*["'][^"']+["']\s*)+""",
        re.X,
    )

    roots = [
        ROOT / d for d in re.findall(r"^COPY\s+([\w./-]+)/\s+\./", DOCKERFILE, re.M)
        if (ROOT / d).is_dir()
    ]
    assert roots, "no directory COPY lines found in the Dockerfile — has its shape changed?"

    needed: dict[str, str] = {}
    for root in roots:
        for py in root.rglob("*.py"):
            for m in pattern.finditer(py.read_text("utf-8")):
                parts = re.findall(r"""["']([^"']+)["']""", m.group(0))
                needed["/".join(parts)] = py.relative_to(ROOT).as_posix()

    assert needed, \
        "no runtime docs/ reads found — if that is now true, delete this test " \
        "rather than letting it pass vacuously"

    for path, reader in sorted(needed.items()):
        assert path in DOCKERFILE, (
            f"{path} is read at runtime by {reader}, but no COPY in the "
            f"Dockerfile puts it in the image. It will raise FileNotFoundError "
            f"the first time that code path runs — which may be long after "
            f"deploy, and on a machine you are not watching."
        )
        assert f"!{path}" in DOCKERIGNORE, (
            f"{path} is COPYed by the Dockerfile but `.dockerignore` excludes "
            f"docs/ without re-including it, so the build context has no such "
            f"file and the COPY fails."
        )
