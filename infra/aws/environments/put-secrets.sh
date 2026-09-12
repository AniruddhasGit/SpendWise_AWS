#!/usr/bin/env bash
# =============================================================================
# Writes each environment's three secrets into SSM Parameter Store.
#
# Reads the credentials produced by phase_a_roles.py, which never prints them.
# The values go from a file straight into SSM; they are not echoed, not passed
# as a visible argument, and not written to shell history.
#
#   usage:  bash put-secrets.sh /path/to/phase_a_result.json
#
# The parameter PATHS are the isolation boundary. /spendwise/dev/* is readable
# only by spendwise-ecs-exec-dev, and so on - see exec-policy-<env>.json. Get
# the path wrong and a container silently reads another environment's database.
#
# Idempotent: --overwrite replaces the value and keeps the parameter's history.
# =============================================================================
set -euo pipefail

RESULT="${1:?usage: put-secrets.sh <phase_a_result.json>}"
[ -f "$RESULT" ] || { echo "no such file: $RESULT" >&2; exit 1; }

REGION=ap-south-1

# environment key in the JSON -> SSM path segment
declare -A PATH_FOR=( [prod]=ecs [uat]=uat [dev]=dev )

for ENV in prod uat dev; do
  SEG="${PATH_FOR[$ENV]}"
  echo
  echo "== /spendwise/${SEG}/"

  ENDPOINT=$(jq -r ".${ENV}.endpoint"        "$RESULT")
  DB=$(jq -r ".${ENV}.database"              "$RESULT")
  APP_U=$(jq -r ".${ENV}.app_role"           "$RESULT")
  APP_P=$(jq -r ".${ENV}.app_password"       "$RESULT")
  OWN_U=$(jq -r ".${ENV}.owner_role"         "$RESULT")
  OWN_P=$(jq -r ".${ENV}.owner_password"     "$RESULT")

  APP_URL="postgresql+asyncpg://${APP_U}:${APP_P}@${ENDPOINT}:5432/${DB}?ssl=require"
  OWN_URL="postgresql+asyncpg://${OWN_U}:${OWN_P}@${ENDPOINT}:5432/${DB}?ssl=require"

  aws ssm put-parameter --region "$REGION" --type SecureString --overwrite \
      --name "/spendwise/${SEG}/DATABASE_URL" --value "$APP_URL" >/dev/null
  echo "   DATABASE_URL           -> ${APP_U}@${DB}"

  aws ssm put-parameter --region "$REGION" --type SecureString --overwrite \
      --name "/spendwise/${SEG}/MIGRATION_DATABASE_URL" --value "$OWN_URL" >/dev/null
  echo "   MIGRATION_DATABASE_URL -> ${OWN_U}@${DB}"

  # ---------------------------------------------------------------------
  # JWT_SECRET is deliberately NOT copied between environments. A session
  # cookie minted in dev must be meaningless in production - otherwise the
  # three environments share one identity space and "isolated" is a word we
  # are using rather than a thing we have.
  #
  # Production's existing secret is left exactly as it is. Rewriting it would
  # sign every logged-in user out for no reason.
  # ---------------------------------------------------------------------
  if [ "$ENV" = "prod" ]; then
    echo "   JWT_SECRET             -> left untouched (rewriting it logs everyone out)"
  elif aws ssm get-parameter --region "$REGION" \
         --name "/spendwise/${SEG}/JWT_SECRET" >/dev/null 2>&1; then
    echo "   JWT_SECRET             -> already set, left alone"
  else
    SECRET=$(head -c 48 /dev/urandom | base64 | tr -d '=+/' | cut -c1-48)
    aws ssm put-parameter --region "$REGION" --type SecureString \
        --name "/spendwise/${SEG}/JWT_SECRET" --value "$SECRET" >/dev/null
    unset SECRET
    echo "   JWT_SECRET             -> generated, unique to ${SEG}"
  fi
done

echo
echo "done. Verify paths without revealing values:"
echo "  aws ssm describe-parameters --query 'Parameters[].Name' --output table"
