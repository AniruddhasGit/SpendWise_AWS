# syntax=docker/dockerfile:1
#
# SpendWise — one image, one service, one deploy (`SW-ADR-020`).
#
# Written late and deliberately: `SW-ADR-011` chose option B — the build session
# writes this, but only once the application is otherwise ready. The recorded
# cost of that choice is that the clean-clone evidence is WEAKER than it would
# have been, and it is labelled weaker rather than quietly upgraded.
#
# Two stages, per `SRC-001 §11.1`:
#
#   > Multi-stage Dockerfile. First stage is `node:20-alpine` and builds the
#   > React app. Second stage is `python:3.12-slim`, installs dependencies, and
#   > copies the built frontend in from the first stage. **Only the results
#   > carry over, not the Node toolchain.**
#
# The second stage never sees node, npm or node_modules — which is the point of
# the split and also most of the image size.


# ═══ Stage 1 — the client ════════════════════════════════════════════════════
#
# `$BUILDPLATFORM`, not a fixed one: this stage runs on whatever machine is
# doing the building, at native speed. What it emits is JavaScript and CSS,
# which have no CPU architecture — so there is nothing here to match to the
# server, and pinning it would only force slow emulation on an ARM laptop.
FROM --platform=$BUILDPLATFORM node:20-alpine AS client

WORKDIR /build/client

# The lockfile on its OWN layer, before the source. Copying all of `client/` in
# one step makes every source edit re-run `npm ci`, which is the slow half of
# this stage. `npm ci` not `npm install`: ci installs exactly the lockfile and
# fails if package.json and the lock disagree, where install would quietly
# resolve something newer and produce a different image from the same commit.
COPY client/package.json client/package-lock.json ./
RUN npm ci

COPY client/ ./
RUN npm run build
# -> /build/client/dist  (index.html + assets/, hashed filenames)


# ═══ Stage 2 — the application ═══════════════════════════════════════════════
#
# Patch pinned, not just the minor. `docs/30 Deployment/RUNTIME_VERSIONS.md`:
# "Base image: python:3.12.10-slim. Pin the patch, not just 3.12." A floating
# `3.12` means two builds of the same commit can differ, which is the property
# a lockfile exists to remove one layer up.
#
# `-slim`, never `-alpine`. `SW-ADR-016` locks the stack; alpine's musl libc
# also forces source builds of wheels that ship manylinux binaries.
#
# `--platform=linux/amd64` is pinned here and NOT left to the builder. This
# stage ships compiled things — CPython itself, and the wheels behind asyncpg
# and bcrypt — so the image only runs on the CPU it was built for. The target
# is a t3.micro, which is x86. Built on an Apple Silicon laptop without this,
# the push succeeds, ECS places the task, and the container dies with
# `exec format error` — after the deploy looks like it worked, and (until the
# log group exists) with nothing anywhere recording why.
FROM --platform=linux/amd64 python:3.12.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# tini — `SRC-001 §11.2` asks for it by name: "Use tini as the entrypoint so
# SIGTERM gets forwarded and ECS can stop tasks cleanly." PID 1 in a container
# does not get default signal handlers, so without an init the stop signal is
# dropped and ECS waits out its timeout before killing the task.
#
# curl — `SW-ADR-127` specifies the ECS health check as
# `CMD-SHELL curl -f http://localhost:{port}/healthz || exit 1`. The slim base
# does not ship curl, so a health check written to that ADR would fail for want
# of the binary and the task would be reaped as unhealthy while serving fine.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# `requirements.lock`, never `pyproject.toml`. RUNTIME_VERSIONS.md: ranges
# "resolve differently on different days". The lock pins every transitive
# dependency; pyproject carries floors.
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Application code and migrations. Note what is NOT here: `tests/`, `docs/`,
# `evidence/`, `goals/` and `handoffs/` are excluded by `.dockerignore` — they
# are the project's memory, not its runtime.
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

# The one document that is runtime, not memory.
#
# `app/core/errors.py:28` and `app/modules/categories/service.py:12` both read
# this file when the app runs — the error-code table and the seeded category
# list are loaded from the spec of record instead of being transcribed into
# Python, so the two can never drift. That makes it a runtime dependency, and
# the path is load-bearing: errors.py resolves `parents[2]/"docs"/"03 PRD"/
# "api"/"contract.json"`, which from /app/app/core/errors.py is exactly this.
#
# Omitting it produces an image that passes /healthz and 500s on every error
# path, including the handler that formats the error — so the failure reports
# itself as a FileNotFoundError inside the error reporter. Observed in
# production on 2026-09-13.
COPY ["docs/03 PRD/api/contract.json", "./docs/03 PRD/api/contract.json"]

# The second one, which hid behind an already-migrated database.
#
# `alembic/versions/0002_cr001_soft_delete_and_admin_daily.py:36` resolves
# `parents[2]/"docs"/"06 DataModel"/"security.sql"` and reads the generated
# SECURITY DEFINER function bodies out of it during the migration, rather than
# keeping a second copy of them in Python.
#
# Migrations run from docker-entrypoint.sh, in this container, so the file has
# to be here. It was missing for five weeks without symptom because every
# database it met was already at head. The first database that was NOT — CI's,
# which is created empty on every run — failed on migration 0002.
COPY ["docs/06 DataModel/security.sql", "./docs/06 DataModel/security.sql"]

# The built client, from stage 1 and nothing else from it.
#
# The destination path is NOT arbitrary. `app/core/spa.py` resolves its
# directory as `Path(__file__).resolve().parents[2] / "client" / "dist"` — from
# `/app/app/core/spa.py` that is `/app/client/dist`. Copy it anywhere else and
# the API still starts, still serves JSON, and returns 404 for every page: the
# mount is skipped with a warning rather than failing, so the container looks
# healthy and the product is invisible.
COPY --from=client /build/client/dist ./client/dist

# `SRC-001 §11.2`: "Run as a non-root user."
#
# Created AFTER the installs so pip writes as root into site-packages and the
# application cannot modify its own dependencies at runtime. `spendwise` owns
# nothing under /app — it only reads.
RUN useradd --system --create-home --shell /usr/sbin/nologin spendwise \
 && chmod +x /app/docker-entrypoint.sh
USER spendwise

EXPOSE 8000

# The ECS task definition's health check is the authoritative one
# (`SW-ADR-127`, prep-queue item 9) and overrides this when set. This mirrors
# it exactly so the two cannot disagree, and so `docker run` locally behaves
# the way the deployed task will. `--start-period` covers boot-time migrations:
# a shorter one reports a task unhealthy while it is correctly migrating.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=120s \
  CMD curl -f http://localhost:8000/healthz || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]
