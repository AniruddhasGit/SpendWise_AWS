"""Typed settings, loaded from the environment, that fail fast.

`P-OPS-01` / `SW-ADR-060`: every setting comes from an environment variable
through a typed loader, and a missing required key **aborts startup** rather
than defaulting silently. `.env.example` is the committed manifest and a test
diffs it against this class in both directions.

Two rules that look like details and are not:

* **A missing required key aborts. A missing optional key degrades and says so.**
  Today exactly one variable degrades — `S3_BUCKET`. Its absence disables receipt
  upload and logs one WARN naming the disabled feature; it does not stop the app.
* **There are two database URLs, not one** (`SW-ADR-081`). Migrations run as the
  owner; traffic runs as a role that owns no table and holds no `BYPASSRLS`. One
  URL for both would mean the runtime connection owns the tables, and an owner
  can `ALTER TABLE ... NO FORCE ROW LEVEL SECURITY` — which is the isolation
  guarantee removed by the thing it is guarding.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import date
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger("spendwise.settings")

# `app/core/settings.py` -> app/core -> app -> the repository root.
#
# ANCHORED TO THE FILE, not to the working directory. `env_file=".env"` is
# resolved relative to the CWD, so `py -m uvicorn app.main:app` from `client/`
# — the directory you are already in after `npm run build` — found no `.env`
# and aborted 78 naming three variables that were sitting one level up. The
# error was correct and the diagnosis it invites is wrong: it reads as "your
# configuration is missing", not "you are standing in the wrong place".
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV = os.path.join(ROOT, ".env")


class Settings(BaseSettings):
    """The whole configuration surface. Every field here must appear in
    `.env.example`, and every line of `.env.example` must appear here."""

    model_config = SettingsConfigDict(
        # SPENDWISE_DOTENV=0 disables the .env fallback. The AC3 test needs a
        # genuinely empty environment; without this it would silently pass by
        # reading the developer's own .env.
        env_file=DOTENV if os.getenv("SPENDWISE_DOTENV", "1") != "0" else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── required: the app refuses to start without these ──────────────────
    DATABASE_URL: SecretStr = Field(
        description="Runtime role. Owns no table, not superuser, no BYPASSRLS.")
    MIGRATION_DATABASE_URL: SecretStr = Field(
        description="Owner role. Migrations only — never serves a request.")
    JWT_SECRET: SecretStr = Field(
        description="Session signing secret. Rotating it revokes every session.")

    # ── optional: sensible defaults, no abort ─────────────────────────────
    BOOTSTRAP_ADMIN_EMAIL: str | None = Field(
        default=None,
        description="The one address that may claim admin while zero admins exist "
                    "(P-ACC-02). Unset AND no admin present is a refusal to start, "
                    "checked at boot rather than here.")
    COOKIE_SECURE: bool = Field(
        default=False,
        description="Sets Secure on the session cookie. FALSE by default because "
                    "SW-ADR-014 left the deployment without TLS — a recorded "
                    "weakness, never a default to copy.")
    APP_TIMEZONE: str = Field(
        default="Asia/Kolkata",
        description="The calendar every boundary is computed in (SW-ADR-096).")
    APP_TODAY_OVERRIDE: date | None = Field(
        default=None,
        description="Pins 'today' for the browser-observed gate (CV-14/CV-20). "
                    "MUST be absent in production.")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    EXPOSE_VERSION: str | None = Field(
        default=None,
        description="Build identifier returned by /readyz. Unset reports the "
                    "literal 'unset' and logs a WARN (SW-ADR-064).")

    # ── rate limits: SW-ADR-128's numbers, stated as EFFECTIVE ────────────
    # Every value here is the limit a PERSON experiences. The number handed to
    # the limiter is this divided by UVICORN_WORKERS, because the store is
    # per-process — see app/core/ratelimit.py. Keeping the ruled figure in the
    # setting and deriving the configured one means `.env` reads the way the
    # ADR reads, and nobody has to remember to halve anything by hand.
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Master switch. TRUE in production. The test suite turns it "
                    "off for everything except the rate-limit tests, so a case "
                    "that signs in eleven times does not fail for a reason "
                    "unrelated to what it asserts.")
    UVICORN_WORKERS: int = Field(
        default=2, ge=1,
        description="The divisor. SW-ADR-014 deploys two workers in one task; "
                    "each holds its own counters, so a limit configured at 5 "
                    "admits 10 in aggregate.")
    RATE_LIMIT_LOGIN_PER_MIN: int = Field(default=10, ge=1)
    RATE_LIMIT_LOGIN_EMAIL_PER_MIN: int = Field(default=10, ge=1)
    RATE_LIMIT_REGISTER_PER_MIN: int = Field(default=5, ge=1)
    RATE_LIMIT_REGISTER_PER_DAY: int = Field(default=20, ge=1)
    RATE_LIMIT_RESET_PER_MIN: int = Field(default=6, ge=1)
    RATE_LIMIT_API_USER_PER_MIN: int = Field(default=120, ge=1)
    RATE_LIMIT_API_IP_PER_MIN: int = Field(default=60, ge=1)

    # ── optional AND degrading: the one variable that disables a feature ──
    S3_BUCKET: str | None = Field(
        default=None,
        description="Receipt storage. Absent disables receipt upload and logs one "
                    "WARN naming the disabled feature — it does not abort.")

    @field_validator("JWT_SECRET")
    @classmethod
    def _secret_is_long_enough(cls, v: SecretStr) -> SecretStr:
        """RFC 7518 §3.2: an HMAC key must be at least as long as the hash
        output — 32 bytes for HS256.

        A shorter secret is brute-forceable offline from a single captured
        token, and every session in the system is signed with it. PyJWT only
        *warns*; a warning in a log nobody reads is not a control, so this
        refuses to start instead.
        """
        if len(v.get_secret_value().encode()) < 32:
            raise ValueError(
                "must be at least 32 bytes (RFC 7518 §3.2 for HS256). Generate one "
                'with: py -c "import secrets; print(secrets.token_urlsafe(48))"')
        return v

    @field_validator("BOOTSTRAP_ADMIN_EMAIL", "APP_TODAY_OVERRIDE", "EXPOSE_VERSION",
                     "S3_BUCKET", mode="before")
    @classmethod
    def _blank_is_unset(cls, v: object) -> object:
        """In a `.env` file, `KEY=` means **not set**, not "the empty string".

        Every deployment system writes an unset optional that way, and
        `.env.example` does too — so without this the committed manifest,
        copied verbatim to `.env`, fails to load with
        `APP_TODAY_OVERRIDE: input is too short`. Which is precisely the
        3am deploy failure the manifest exists to prevent, produced by the
        manifest.
        """
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("DATABASE_URL", "MIGRATION_DATABASE_URL")
    @classmethod
    def _must_be_async_postgres(cls, v: SecretStr) -> SecretStr:
        """A sync driver here fails much later, inside the event loop, as a
        blocking call nobody attributes to configuration."""
        url = v.get_secret_value()
        if not url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "must start with postgresql+asyncpg:// — the stack is locked to "
                "SQLAlchemy async + asyncpg by SW-ADR-016")
        return v

    @property
    def receipts_enabled(self) -> bool:
        """`P-ACC-06` returns this so the client can hide the receipt control
        rather than letting it fail."""
        return self.S3_BUCKET is not None


def load_settings() -> Settings:
    """Build the settings, or abort non-zero naming every missing key.

    Called at import time by `app.main`, so the failure happens **before the
    port is bound** — which is what `E0-S1` AC3 asserts. Pydantic's own error
    is readable but buries the variable names in a traceback; a deploy that
    fails at 3am needs the name on the first line.
    """
    try:
        return Settings()
    except ValidationError as exc:
        missing = sorted({
            str(e["loc"][0]) for e in exc.errors() if e["type"] == "missing"
        })
        invalid = [
            f"{e['loc'][0]}: {e['msg']}" for e in exc.errors() if e["type"] != "missing"
        ]
        lines = ["CONFIGURATION ERROR — the application did not start."]
        if missing:
            lines.append(f"  missing required environment variable(s): {', '.join(missing)}")
        for bad in invalid:
            lines.append(f"  invalid: {bad}")
        lines.append("  see .env.example for the full manifest.")
        print("\n".join(lines), file=sys.stderr, flush=True)
        raise SystemExit(78)          # EX_CONFIG


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The configured settings, built once.

    **Deliberately not a module-level `settings = load_settings()`.** That form
    makes `import app.core.settings` itself abort without a `.env`, so nothing
    can introspect the schema — not Alembic's `env.py`, not a schema dump, and
    not the test that diffs this class against `.env.example`. The E0-S1 AC4
    test found exactly that, which is the argument for writing the test first.

    The fail-fast is not weakened: `app.main` calls this at import, so a missing
    key still aborts **before the port is bound**, which is what AC3 asserts.
    """
    cfg = load_settings()
    logging.basicConfig(level=cfg.LOG_LEVEL)
    if not cfg.receipts_enabled:
        # P-OPS-01: exactly one WARN, naming the disabled feature. Not an abort.
        log.warning("S3_BUCKET is unset — receipt upload is DISABLED. Everything else runs.")
    return cfg
