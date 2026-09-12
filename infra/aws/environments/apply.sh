#!/usr/bin/env bash
# =============================================================================
# Creates the dev and uat environments in AWS:
#   - one ECS execution role each, scoped to that environment's secrets
#   - the task definition
#   - the service
#
# Run AFTER:
#   1. phase_a_roles.py       (per-environment database logins exist)
#   2. put-secrets.sh         (SSM holds /spendwise/{dev,uat}/*)
#   3. infra/aws/oidc/apply.sh (not required by this script, but by the pipeline)
#
# Idempotent. Safe to re-run.
# =============================================================================
set -euo pipefail

ACCOUNT=944483082287
REGION=ap-south-1
CLUSTER=spendwise-cluster
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ECS_DIR="$(cd "${HERE}/../ecs" && pwd)"

# ---------------------------------------------------------------------------
# Git Bash reports this script's directory as a POSIX path (/d/Project/...),
# but the AWS CLI on Windows is a native binary that cannot resolve one - it
# fails with "Unable to load paramfile". cygpath -m converts to C:/Project/...,
# which file:// accepts. On Linux and macOS there is no cygpath and the path is
# already correct, so this is a no-op there.
# ---------------------------------------------------------------------------
if command -v cygpath >/dev/null 2>&1; then
  HERE="$(cygpath -m "$HERE")"
  ECS_DIR="$(cygpath -m "$ECS_DIR")"
fi

say() { printf '\n== %s\n' "$*"; }

for ENV in dev uat; do
  ROLE="spendwise-ecs-exec-${ENV}"
  SERVICE="spendwise-${ENV}"

  # -------------------------------------------------------------------------
  # The execution role is what ECS uses to START the task: pull the image and
  # fetch the secrets. It is NOT what the application runs as.
  #
  # There is one per environment for a single reason: a shared role would let a
  # compromised dev container read /spendwise/ecs/DATABASE_URL and reach the
  # production database. Splitting them is the difference between three
  # environments and three copies of one environment.
  # -------------------------------------------------------------------------
  say "execution role ${ROLE}"
  if aws iam get-role --role-name "$ROLE" >/dev/null 2>&1; then
    echo "   already present"
  else
    aws iam create-role --role-name "$ROLE" \
      --assume-role-policy-document "file://${HERE}/trust-ecs-tasks.json" \
      --description "ECS pulls the image and reads /spendwise/${ENV}/* as this" >/dev/null
    echo "   created"
  fi
  aws iam put-role-policy --role-name "$ROLE" \
    --policy-name "exec-${ENV}" \
    --policy-document "file://${HERE}/exec-policy-${ENV}.json"
  echo "   permissions attached"

  say "task definition spendwise-${ENV}"
  TD=$(aws ecs register-task-definition \
         --cli-input-json "file://${ECS_DIR}/taskdef-${ENV}.json" \
         --query 'taskDefinition.taskDefinitionArn' --output text)
  echo "   ${TD}"

  # -------------------------------------------------------------------------
  # maximumPercent 100 / minimumHealthyPercent 0 is not a preference. The host
  # is a t3.micro with 916 MiB and three services on it. The ECS default starts
  # the replacement task BEFORE stopping the old one, which needs double the
  # memory for the overlap - memory that does not exist here. The deploy would
  # not fail; it would sit in "unable to place task" until the timeout, every
  # single time.
  #
  # The cost is a few seconds of downtime per deploy. On a demo host that is
  # the right trade; behind a load balancer with room to spare it would not be.
  #
  # The circuit breaker rolls back automatically when the new task cannot come
  # up healthy, instead of leaving the service parked on a broken revision.
  # -------------------------------------------------------------------------
  say "service ${SERVICE}"
  if aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
       --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
    aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
      --task-definition "$TD" --desired-count 1 \
      --deployment-configuration 'maximumPercent=100,minimumHealthyPercent=0,deploymentCircuitBreaker={enable=true,rollback=true}' \
      --query 'service.serviceName' --output text
    echo "   updated"
  else
    aws ecs create-service --cluster "$CLUSTER" --service-name "$SERVICE" \
      --task-definition "$TD" --desired-count 1 --launch-type EC2 \
      --scheduling-strategy REPLICA \
      --deployment-configuration 'maximumPercent=100,minimumHealthyPercent=0,deploymentCircuitBreaker={enable=true,rollback=true}' \
      --query 'service.serviceName' --output text
    echo "   created"
  fi

  echo "   waiting for it to come up healthy..."
  if aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"; then
    echo "   ${SERVICE} is stable"
  else
    echo "   ${SERVICE} did NOT stabilise. Most recent service events:"
    aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
      --query 'services[0].events[:8].message' --output text
    exit 1
  fi
done

say "all done"
echo "  uat  http://3.7.37.251:8001"
echo "  dev  http://3.7.37.251:8002"
