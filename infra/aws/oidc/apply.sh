#!/usr/bin/env bash
# =============================================================================
# Creates the GitHub Actions OIDC trust and the three deploy roles.
#
# WHY OIDC AND NOT ACCESS KEYS
#   An access key in a GitHub secret is a password that lives forever and is
#   worth stealing. OIDC issues a token that is minted per job, expires in
#   minutes, and is bound to ONE repository and ONE environment. There is
#   nothing left behind for anyone to find.
#
# THE ONE LINE THAT MATTERS is the `sub` condition in each trust-*.json:
#
#     repo:AniruddhasGit/SpendWise:environment:production
#
#   It says: only a job that GitHub has admitted into the `production`
#   environment may assume this role. It deliberately does NOT also allow
#   `...:ref:refs/heads/main`. That alternative looks harmless and is not —
#   it would let ANY workflow running on main assume the production role,
#   which is every future workflow anyone ever adds, gate or no gate.
#
# THE SUBJECT IS THE IMMUTABLE FORM, AND THAT IS NOT OPTIONAL HERE.
#   This repository has immutable subject claims switched on:
#
#     gh api repos/AniruddhasGit/SpendWise/actions/oidc/customization/sub
#     -> "use_immutable_subject": true
#        "sub_claim_prefix": "repo:AniruddhasGit@169955520/SpendWise@1334397382"
#
#   so a real token says repo:OWNER@169955520/REPO@1334397382:environment:dev,
#   carrying numeric ids rather than names. The plain form every tutorial shows
#   - repo:owner/name:environment:dev - never matches. The only symptom is
#   "Not authorized to perform sts:AssumeRoleWithWebIdentity", which names no
#   condition and points at nothing. Cost: one failed deploy to find.
#
#   The ids are worth keeping: unlike a name, they cannot be re-registered by
#   someone else after a rename.
#
# Idempotent. Safe to re-run.
# =============================================================================
set -euo pipefail

ACCOUNT=944483082287
PROVIDER="arn:aws:iam::${ACCOUNT}:oidc-provider/token.actions.githubusercontent.com"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Git Bash reports this script's directory as a POSIX path (/d/Project/...),
# but the AWS CLI on Windows is a native binary that cannot resolve one - it
# fails with "Unable to load paramfile". cygpath -m converts to C:/Project/...,
# which file:// accepts. On Linux and macOS there is no cygpath and the path is
# already correct, so this is a no-op there.
# ---------------------------------------------------------------------------
if command -v cygpath >/dev/null 2>&1; then
  HERE="$(cygpath -m "$HERE")"
fi

say() { printf '\n== %s\n' "$*"; }

say "OIDC identity provider"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVIDER" >/dev/null 2>&1; then
  echo "   already present"
else
  aws iam create-open-id-connect-provider \
    --url "https://token.actions.githubusercontent.com" \
    --client-id-list "sts.amazonaws.com" \
    --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" >/dev/null
  echo "   created"
fi

for ENV in dev uat production; do
  ROLE="spendwise-gha-deploy-${ENV}"
  say "role ${ROLE}"

  if aws iam get-role --role-name "$ROLE" >/dev/null 2>&1; then
    aws iam update-assume-role-policy \
      --role-name "$ROLE" \
      --policy-document "file://${HERE}/trust-${ENV}.json"
    echo "   trust policy updated"
  else
    aws iam create-role \
      --role-name "$ROLE" \
      --assume-role-policy-document "file://${HERE}/trust-${ENV}.json" \
      --max-session-duration 3600 \
      --description "GitHub Actions deploys to the ${ENV} environment" >/dev/null
    echo "   created"
  fi

  # Inline, not managed: this policy has exactly one consumer. A managed policy
  # would invite a second one, and the blast radius is the whole point here.
  aws iam put-role-policy \
    --role-name "$ROLE" \
    --policy-name "deploy-${ENV}" \
    --policy-document "file://${HERE}/policy-${ENV}.json"
  echo "   permissions attached"

  aws iam get-role --role-name "$ROLE" --query 'Role.Arn' --output text
done

say "done"
