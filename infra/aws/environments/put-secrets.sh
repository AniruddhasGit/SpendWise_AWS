#!/usr/bin/env bash
# =============================================================================
# Mirrors a worktree's .env into that environment's SSM parameter path.
#
#   usage:  bash put-secrets.sh dev uat          # one or more of: dev uat prod
#
# .env is the source of truth on this machine; SSM is what ECS reads. This
# script is the one-way copy between them, and it reads the file directly so it
# works both before and after the database credentials are rotated - rotation
# rewrites .env, and re-running this pushes the new values up.
#
# Values are read and written inside this process. They are never echoed, never
# passed through a pipe, and never appear in shell history.
#
# THE PATHS ARE THE ISOLATION BOUNDARY. /spendwise/dev/* is readable only by
# spendwise-ecs-exec-dev (see exec-policy-dev.json). Put a value on the wrong
# path and a container quietly reads another environment's database.
#
# Idempotent: --overwrite replaces the value and keeps the parameter history.
# =============================================================================
set -euo pipefail

[ $# -gt 0 ] || { echo "usage: put-secrets.sh <dev|uat|prod> [...]" >&2; exit 1; }

REGION=ap-south-1

# ---------------------------------------------------------------------------
# Git Bash rewrites any argument that looks like an absolute POSIX path into a
# Windows path before handing it to a native binary. An SSM parameter name
# starts with a slash and is NOT a path, so /spendwise/dev/DATABASE_URL arrives
# at the AWS CLI as C:/Program Files/Git/spendwise/dev/DATABASE_URL and the API
# rejects it with "Parameter name must be a fully qualified name" - an error
# that says nothing about the real cause.
#
# Harmless everywhere else; the variable is simply ignored off Windows.
# ---------------------------------------------------------------------------
export MSYS_NO_PATHCONV=1

# The three worktrees are SIBLINGS, not nested:
#
#   D:\Project\SpendWise\
#       main\   <- this script lives at main/infra/aws/environments/
#       dev\
#       uat\
#
# so the folder holding all three is four levels up, not three. Getting this
# wrong is a clean failure ("no such file") rather than a silent one, because
# the script checks the .env exists before reading it.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

# environment -> (worktree folder, SSM path segment)
folder_for() { case "$1" in dev) echo dev;; uat) echo uat;; prod) echo main;; esac; }
segment_for() { case "$1" in dev) echo dev;; uat) echo uat;; prod) echo ecs;; esac; }

# Read one KEY= line out of a .env without sourcing the file. Sourcing would
# execute it, and a stray backtick in a password is not a thing worth finding
# out about the hard way.
read_env() {
  sed -n "s/^$2=//p" "$1" | head -n 1 | tr -d '\r'
}

for ENV in "$@"; do
  FOLDER="$(folder_for "$ENV")"
  SEG="$(segment_for "$ENV")"
  [ -n "$FOLDER" ] || { echo "unknown environment: $ENV" >&2; exit 1; }

  ENVFILE="${ROOT}/${FOLDER}/.env"
  [ -f "$ENVFILE" ] || { echo "no such file: $ENVFILE" >&2; exit 1; }

  echo
  echo "== ${ENV}  (${FOLDER}/.env  ->  /spendwise/${SEG}/)"

  for KEY in DATABASE_URL MIGRATION_DATABASE_URL JWT_SECRET; do
    VALUE="$(read_env "$ENVFILE" "$KEY")"
    if [ -z "$VALUE" ]; then
      echo "   ${KEY}: MISSING from ${FOLDER}/.env" >&2
      exit 1
    fi

    aws ssm put-parameter --region "$REGION" --type SecureString --overwrite \
        --name "/spendwise/${SEG}/${KEY}" --value "$VALUE" >/dev/null

    # Report the shape, never the value. The database name and role are enough
    # to confirm the right thing landed on the right path; the password is not.
    case "$KEY" in
      *DATABASE_URL)
        # ------------------------------------------------------------------
        # `sed` leaves NON-MATCHING input unchanged. So an extractor that
        # selects the safe part fails OPEN: miss the pattern and it prints the
        # whole connection string, password included. That is not theoretical -
        # it happened in this project on 2026-09-13 and put two live passwords
        # in a transcript (bugs/sessions/2026-09-13_the-pipeline.md).
        #
        # So the result is CHECKED before it is printed. If either field still
        # looks like a URL, the extraction missed and we say so instead of
        # helpfully displaying the secret.
        # ------------------------------------------------------------------
        WHO="$(printf '%s' "$VALUE" | sed -E 's#^[a-z+]+://([^:]+):.*#\1#')"
        DB="$(printf '%s' "$VALUE" | sed -E 's#.*/([^/?]+)(\?.*)?$#\1#')"
        case "${WHO}${DB}" in
          *://*|*@*|*:*) echo "   ${KEY} -> set (could not parse shape safely)" ;;
          *)             echo "   ${KEY} -> ${WHO} @ ${DB}" ;;
        esac
        ;;
      JWT_SECRET)
        echo "   ${KEY} -> set (${#VALUE} chars)"
        ;;
    esac
    unset VALUE
  done
done

echo
echo "done. Confirm the paths without revealing values:"
echo "  aws ssm describe-parameters --query 'Parameters[].Name' --output table"
