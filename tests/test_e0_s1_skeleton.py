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
