"""E0-S1 — Repository skeleton and typed settings.

Written BEFORE the code, per `CONSTITUTION.md` Art IX.1. One test per acceptance
criterion in Bible `E0-S1`; nothing here asserts on anything the story does not.

The AC text is quoted in each docstring so a reader can check the test against
the criterion without opening the Bible.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "app"

# SRC-001 §3.1 — the module list is closed. A seventh module is a scope change.
MODULES = ("auth", "users", "expenses", "categories", "receipts", "admin")
LAYERS = ("router.py", "service.py", "repository.py", "schemas.py", "models.py")


# ── AC1 ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("layer", LAYERS)
def test_ac1_every_module_has_every_layer(module: str, layer: str) -> None:
    """AC1: each of the six modules contains all five layer files.

    Parametrised rather than looped so a missing file names itself in the
    failure, instead of one opaque assertion failing on the first gap.
    """
    path = APP / "modules" / module / layer
    assert path.is_file(), f"missing {path.relative_to(REPO)}"


@pytest.mark.parametrize("module", MODULES)
def test_ac1_every_module_is_a_package(module: str) -> None:
    """A directory of files is not a module — it needs __init__.py to import."""
    assert (APP / "modules" / module / "__init__.py").is_file()


# ── AC2 ────────────────────────────────────────────────────────────────────
def test_ac2_core_exists() -> None:
    """AC2, first half: `app/core/` exists."""
    assert (APP / "core" / "__init__.py").is_file()


def test_ac2_no_package_named_platform_anywhere() -> None:
    """AC2, second half: there is NO package named `platform` in the tree.

    `platform` is a standard-library module. A local package by that name
    shadows it, and the failure surfaces somewhere unrelated — `CLAUDE.md`
    records this as a named trap, so it gets a test rather than a convention.
    """
    offenders = [
        p.relative_to(REPO).as_posix()
        for p in REPO.rglob("platform")
        if p.is_dir() and ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    assert not offenders, f"a package named `platform` shadows the stdlib: {offenders}"


# ── AC3 ────────────────────────────────────────────────────────────────────
def test_ac3_missing_required_key_exits_nonzero_and_names_it() -> None:
    """AC3: starting without a required var exits non-zero BEFORE binding the
    port, and prints the missing key by name.

    Run in a subprocess with a scrubbed environment: importing the settings in
    this process would either succeed from the developer's own .env or poison
    the module cache for every other test.

    `-c "import app.main"` is the whole test — if settings are validated at
    import time the failure happens here, which is what "before binding the
    port" means in practice.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DATABASE_", "JWT_"))}
    env["SPENDWISE_DOTENV"] = "0"          # do not fall back to a local .env
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60,
    )

    assert proc.returncode != 0, "startup succeeded with DATABASE_URL missing"
    combined = proc.stdout + proc.stderr
    assert "DATABASE_URL" in combined, (
        "the abort did not name the missing key; a loader that fails without "
        "saying which variable is missing is a silent failure with extra steps"
    )


# ── AC4 ────────────────────────────────────────────────────────────────────
def test_ac4_env_example_lists_every_variable_the_settings_class_reads() -> None:
    """AC4: `.env.example` lists every variable the settings class reads —
    asserted by importing the class and diffing the two.

    Both directions. A variable the code reads and the manifest omits is a
    deploy that fails at 3am; a variable the manifest lists and no code reads
    is a lie that a reader will try to set.
    """
    sys.path.insert(0, str(REPO))
    from app.core.settings import Settings          # noqa: PLC0415  (import after path fix)

    declared = {
        (f.alias or name).upper()
        for name, f in Settings.model_fields.items()
    }

    # A key must LOOK like an environment variable. The first version of this
    # parser took anything before an `=`, so prose in the file's own header —
    # "a variable the code reads and this file omits = a deploy that fails at
    # 3am" — was read as a variable name. The manifest was right; the test was
    # wrong. A commented-out example (`# APP_TODAY_OVERRIDE=...`) still counts
    # as documented, which is why the `#` is stripped before matching.
    env_key = re.compile(r"^#?\s*([A-Z][A-Z0-9_]*)\s*=")
    example = (REPO / ".env.example").read_text(encoding="utf-8")
    documented = {
        m.group(1)
        for line in example.splitlines()
        if (m := env_key.match(line.strip()))
    }

    assert not (declared - documented), (
        f".env.example is missing {sorted(declared - documented)} — the code reads them"
    )
    assert not (documented - declared), (
        f".env.example lists {sorted(documented - declared)} — no code reads them"
    )


def test_ac4_the_rds_template_declares_the_same_variables_as_the_manifest() -> None:
    """A second template is a second thing that drifts.

    `docs/30 Deployment/env.rds-template.txt` exists so the client can paste
    their endpoint and passwords into one place. It must declare **exactly** the
    variables the settings class reads — otherwise filling it in produces a
    `.env` that fails to load, or silently omits something, in the environment
    where a mistake is most expensive.
    """
    sys.path.insert(0, str(REPO))
    from app.core.settings import Settings          # noqa: PLC0415

    declared = {(f.alias or name).upper() for name, f in Settings.model_fields.items()}

    env_key = re.compile(r"^#?\s*([A-Z][A-Z0-9_]*)\s*=")
    template = (REPO / "docs" / "30 Deployment" / "env.rds-template.txt").read_text("utf-8")
    documented = {m.group(1) for line in template.splitlines()
                  if (m := env_key.match(line.strip()))}

    assert not (declared - documented), (
        f"the RDS template is missing {sorted(declared - documented)} — filling it "
        f"in would produce a .env that aborts at startup")
    assert not (documented - declared), (
        f"the RDS template lists {sorted(documented - declared)} — no code reads them")


def test_ac4_the_rds_template_keeps_the_asyncpg_ssl_spelling() -> None:
    """`?ssl=require`, never libpq's `sslmode=require`.

    RDS forces SSL. asyncpg does not understand `sslmode=`, and treats it as an
    unknown server setting — the connection then fails with an error that never
    mentions SSL, which is an afternoon lost. Asserted so a well-meaning edit
    to the "more standard" spelling fails here instead.
    """
    template = (REPO / "docs" / "30 Deployment" / "env.rds-template.txt").read_text("utf-8")
    urls = [ln for ln in template.splitlines() if ln.startswith(("DATABASE_URL=",
                                                                "MIGRATION_DATABASE_URL="))]
    assert len(urls) == 2
    for u in urls:
        assert "?ssl=require" in u, f"missing asyncpg's SSL parameter: {u}"
        assert "sslmode=" not in u, f"libpq spelling, which asyncpg ignores: {u}"
        assert u.startswith(("DATABASE_URL=postgresql+asyncpg://",
                             "MIGRATION_DATABASE_URL=postgresql+asyncpg://"))


def test_ac4_the_rds_template_uses_two_different_roles() -> None:
    """`SW-ADR-081`. One role for both is the mistake that makes the runtime
    connection own the tables — and an owner can `ALTER TABLE … NO FORCE ROW
    LEVEL SECURITY`, which is the isolation guarantee removing itself."""
    template = (REPO / "docs" / "30 Deployment" / "env.rds-template.txt").read_text("utf-8")
    assert "spendwise_app:" in template
    assert "spendwise_owner:" in template


def test_ac4_the_manifest_actually_loads_as_a_dotenv() -> None:
    """`.env.example` must not merely LIST the right names — it must work when
    copied to `.env` and filled in.

    Matching names is necessary and not sufficient. The first version of this
    file listed every variable correctly and still failed to load, because an
    unset optional is written `KEY=` and an empty string is not a valid date.
    A manifest that fails on the one action it exists for is worse than none:
    it fails at deploy time, in the environment nobody tests.
    """
    import subprocess

    env = {k: v for k, v in os.environ.items() if not k.startswith(("DATABASE_", "JWT_", "APP_"))}
    env["PYTHONPATH"] = str(REPO)
    env["SPENDWISE_DOTENV"] = "1"

    proc = subprocess.run(
        [sys.executable, "-c",
         "import shutil, pathlib, os;"
         "src = pathlib.Path('.env.example').read_text('utf-8');"
         # fill the three required values the way a deployer would
         "src = src.replace('CHANGE_ME', 'x');"
         "pathlib.Path('.env.probe').write_text(src, encoding='utf-8');"
         "os.environ['SPENDWISE_DOTENV']='1';"
         "from pydantic_settings import SettingsConfigDict;"
         "from app.core.settings import Settings;"
         "Settings.model_config = SettingsConfigDict(env_file='.env.probe',"
         " env_file_encoding='utf-8', case_sensitive=True, extra='ignore');"
         "Settings();"
         "print('MANIFEST LOADS')"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60,
    )
    (REPO / ".env.probe").unlink(missing_ok=True)
    assert "MANIFEST LOADS" in proc.stdout, (
        f".env.example does not load as a .env:\n{proc.stdout}\n{proc.stderr}")


def test_the_dotenv_is_found_from_any_working_directory() -> None:
    """`.env` is anchored to the REPOSITORY, not to the shell's cwd.

    `env_file=".env"` resolves relative to the working directory, so
    `py -m uvicorn app.main:app` run from `client/` — the directory you are
    already standing in after `npm run build` — found nothing and aborted 78
    naming three variables that were one level up. The message was accurate
    and the diagnosis it invites is wrong: it reads as "your configuration is
    missing", not "you are in the wrong place".

    Asserted structurally rather than by chdir-ing: the path must be absolute
    and must be the repository's own, whatever the caller's cwd happens to be.
    """
    import os

    from app.core import settings as mod

    assert os.path.isabs(mod.DOTENV), "the dotenv path is relative to the cwd"
    assert mod.DOTENV == os.path.join(mod.ROOT, ".env")
    assert os.path.isdir(os.path.join(mod.ROOT, "app")), (
        f"ROOT resolved to {mod.ROOT!r}, which does not look like the repository")

    configured = mod.Settings.model_config["env_file"]
    if os.getenv("SPENDWISE_DOTENV", "1") != "0":
        assert configured == mod.DOTENV
    else:
        # The escape hatch still works — the AC3 test needs a genuinely empty
        # environment, and an absolute path would defeat it just as well as a
        # relative one.
        assert configured is None
