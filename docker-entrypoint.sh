#!/bin/sh
# SpendWise container start sequence.
#
# Order is the whole content of this file, and it is not a preference:
#
#   1. migrate, as the OWNER role
#   2. then, and only then, serve — as the RUNTIME role
#
# `SW-ADR-093` (Fable 5, closing `OPEN-MIGRATE-01`): "Migrations run at
# container start, **before uvicorn binds the port**, wrapped in an explicit
# `pg_advisory_xact_lock`, with `SW-ADR-061`'s timeouts and **no retry, exit
# non-zero**." Binding the port first would put a task into service against a
# schema it has not finished migrating, and the ECS health check would call it
# healthy while it 500s.
#
# `set -e` is the no-retry half. A failed migration must stop the container so
# the deploy fails visibly — a retry loop here turns a broken migration into a
# task that flaps and an alarm nobody wired.
set -e

# The advisory lock is taken in `alembic/env.py`, NOT here. Alembic does not
# take one by itself — `SRC-001 §11.6` states it does and is wrong, recorded as
# erratum E-4 and ruled by `SW-ADR-019`. Two tasks booting together would
# otherwise race `upgrade head`.
#
# `env.py` also connects with `MIGRATION_DATABASE_URL`, the OWNER role, and
# issues `SET LOCAL row_security = off` — the owner is subject to its own
# policies under `FORCE ROW LEVEL SECURITY` (`SW-ADR-081`), so without that a
# data migration silently affects zero rows and reports success.
echo "[entrypoint] alembic upgrade head (owner role, advisory-locked in env.py)"
alembic upgrade head

# Two workers, and this number is load-bearing twice over.
#
# `SRC-001 §11.3`: "Run uvicorn with `--workers 2` and let ECS handle scaling
# beyond that by adding tasks. Don't put gunicorn in front."
#
# It must ALSO match `UVICORN_WORKERS` in the environment, because the rate
# limiter divides `SW-ADR-128`'s effective limits by that setting to get its
# per-process allowance (the store is in-process, so N workers hold N
# counters). Run three workers here against a setting of two and every auth
# limit is silently 1.5x what was ruled — nothing fails, nothing logs, and the
# throttle is simply looser than the record says it is.
WORKERS="${UVICORN_WORKERS:-2}"
PORT="${PORT:-8000}"
echo "[entrypoint] uvicorn on 0.0.0.0:${PORT}, ${WORKERS} worker(s)"

# `exec` so uvicorn REPLACES this shell as the process tini supervises.
# Without it the shell stays PID 2, tini signals the shell, the shell does not
# forward, and SIGTERM never reaches uvicorn — so in-flight requests are cut
# instead of drained and ECS waits out its stop timeout on every deploy.
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --no-server-header
