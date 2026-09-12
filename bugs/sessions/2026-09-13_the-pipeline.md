# 2026-09-13 — building the three-environment pipeline

Eight entries. One ran and did damage, one cost a failed deploy, and the other six were caught
while reading a draft rather than while debugging a failure. That ratio is the point of this
file: every cheap catch came from someone asking "what would this actually do?" before running
it.

Context: dev / uat / production as three isolated environments, with a promotion path that cannot
be jumped. GitHub Actions, OIDC, ECS, and per-environment database credentials.

---

## The one that ran

### A redaction that printed the secret it was redacting

**Shape:** the-check-was-wrong

**Believed.** A command was about to print connection strings, so it was written to strip the
credentials first and show only the shape: user, host, database. The `sed` pipeline extracted each
field separately, and the database-name extractor was:

```
sed -E 's#.*/([a-z_]+)$#\1#'
```

Take everything after the last slash, if it is lowercase letters and underscores to the end of the
line. That describes `spendwise_dev` exactly.

**Actually.** The URLs end `?ssl=require`. The pattern is anchored with `$`, so it did not match —
and `sed` leaves non-matching input **unchanged**. The "database name" field printed the entire
original connection string, including both passwords, for all three environments.

The other two extractors on the same line worked perfectly, which made the output look deliberate
rather than broken.

**Caught by.** Reading the output. Nothing failed; the exit code was zero.

**Lesson.** This is a redaction written inside out. It selects what to KEEP and assumes everything
else disappears — but `sed` without a match is a pass-through, so the failure mode of "keep the
safe part" is "emit everything." A redaction must be written as a removal: match the secret and
replace it, so that a pattern miss shows an unredacted field you can see, rather than silently
shipping the whole line. Better still, never route a secret through a terminal at all — read it in
one process and write it to its destination in the same process, as `phase_a_roles.py` does.

**Where.** This session, while preparing to copy `.env` values into SSM Parameter Store.
Consequence: both shared database passwords are in the session transcript and must be rotated.
Mitigating fact, established afterwards and not before: the RDS security group admits port 5432
from one `/32` address and the ECS host's security group only, so `PubliclyAccessible: true` on the
instance does not mean reachable from the internet.

---

## The seven caught while reading

### The production trust policy had a second door

**Shape:** wrong-assumption

**Believed.** A draft OIDC trust policy for the production deploy role listed two acceptable
subjects:

```
repo:AniruddhasGit/SpendWise:ref:refs/heads/main
repo:AniruddhasGit/SpendWise:environment:production
```

Reasonable-looking: production deploys run on `main`, in the `production` environment.

**Actually.** Those are alternatives, not requirements. The first one grants the production deploy
role to **any** workflow running on `main` — including every workflow anyone adds later, none of
which pass through the environment and its approval gate. The environment claim is the only thing
carrying the human approval; accepting the ref as a substitute discards it.

**Caught by.** Reading the draft before applying it.

> **Lesson.** In an OIDC trust policy, a list under one condition key is an OR. Adding a claim that
> "should also be true" does not tighten the policy — it widens it. The `sub` claim is the entire
> security boundary, and the only correct production value is the environment form.

---

### Role membership would have made the isolation theatre

**Shape:** the-check-was-wrong

**Believed.** Giving each environment its own database login, as a member of the shared role, would
isolate them: each login gets `CONNECT` on exactly one database, and inherits table grants from the
parent so migrations keep working unchanged.

**Actually.** `CONNECT` is a privilege like any other, and members inherit it. `spendwise_app_dev`
would have inherited the parent's `CONNECT` on the production database. Every login would have
reached every database, and the verification step would have reported success on the part that
worked while the part that mattered was open.

**Caught by.** Writing the "dev must be refused by production" check before running the script, and
then asking whether it would actually pass.

> **Lesson.** `NOINHERIT` is what makes this design work: the login holds only what is granted
> directly, and `SET role` — which runs after authentication — restores the shared privileges for
> the session. The order matters because PostgreSQL checks `CONNECT` at the door, before session
> settings apply. Whenever isolation is built out of a hierarchy, the question is always what the
> hierarchy hands down for free.

---

### Revoking PUBLIC first would have taken production down

**Shape:** fix-caused-it (averted)

**Believed.** Granting each environment `CONNECT` on its own database, then revoking `CONNECT` from
`PUBLIC`, closes the boundary.

**Actually.** The grants only matter once `PUBLIC` is revoked — but the *running* production task
authenticates as the old shared role, which may have been relying on `PUBLIC` for its access. The
correct-looking sequence would have locked out the live site, and it would not have failed at
revoke time. It would have failed at the next task restart, minutes or days later, with an error
pointing at the database rather than at the change that caused it.

**Caught by.** Asking what the live system is authenticating as right now.

> **Lesson.** Write the explicit grant before the revoke, and verify the *current* credential still
> works afterwards, in the same script. A security tightening that is not immediately followed by
> "and the thing that was working still works" is a change with a delayed fuse.

---

### workflow_run would have made every deploy fail as "wrong branch"

**Shape:** wrong-assumption

**Believed.** CD should trigger when CI finishes green — the obvious wiring is
`on: workflow_run: workflows: [CI], types: [completed]`.

**Actually.** A `workflow_run`-triggered run reports `github.ref` as the **default branch**,
whatever branch actually changed. Each GitHub environment here is bound to exactly one branch, and
that binding is checked against `github.ref`. Every dev and uat deploy would have been rejected for
coming from `main` — and the rejection surfaces as an environment protection error, which reads
like a permissions problem and sends you to the wrong place entirely.

**Caught by.** Checking what `github.ref` holds under that trigger before building on it.

> **Lesson.** CI is called as a reusable workflow (`workflow_call`) from CD instead, so the ref
> stays true and one definition of "green" serves both pull requests and releases.

---

### The AWS default profile pointed at an availability zone

**Shape:** environment

**Believed.** `aws sts get-caller-identity` failing with
`Could not connect to the endpoint URL: "https://sts.ap-south-1c.amazonaws.com/"` looked like a
network or credentials fault.

**Actually.** `~/.aws/config` had `region = ap-south-1c` under `[default]`. `ap-south-1c` is an
availability **zone**; the region is `ap-south-1`. One trailing character, and the SDK builds a
hostname that does not exist. The working profile is `dynpro`.

> **Lesson.** "Could not connect to the endpoint URL" almost always means the endpoint was
> constructed wrong, not that the network is down — read the hostname in the error before
> investigating anything else. Also worth knowing: the `default` profile here holds keys for a
> different account (545620235339) than the project's (944483082287), so an unqualified `aws`
> command is not merely misconfigured, it is pointed somewhere else.

---

### The OIDC subject was the documented one, not the real one

**Shape:** wrong-assumption

**Believed.** A GitHub Actions OIDC trust policy identifies the caller by its `sub` claim, which
for an environment-scoped job is:

```
repo:AniruddhasGit/SpendWise:environment:dev
```

That is the form in GitHub's documentation, in AWS's documentation, and in every worked example.
The three trust policies were written against it and read carefully for the *shape* of the
condition - an earlier draft allowed a `ref` alternative, which was caught and removed.

**Actually.** This repository has **immutable subject claims** enabled, which nothing in the
workflow, the policy, or the AWS console mentions:

```
gh api repos/AniruddhasGit/SpendWise/actions/oidc/customization/sub
{"use_default":true,"use_immutable_subject":true,
 "sub_claim_prefix":"repo:AniruddhasGit@169955520/SpendWise@1334397382"}
```

Real tokens carry `repo:AniruddhasGit@169955520/SpendWise@1334397382:environment:dev` - the numeric
owner id and repository id, not the names. The documented form never matches.

**Caught by.** The first pipeline-driven deploy. CI passed, the environment gating worked, uat and
production were correctly skipped, and the deploy died at the first step with:

```
Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

That message names no condition, no claim and no value. It is identical whether the audience is
wrong, the subject is wrong, the provider is missing, or the thumbprint is stale.

> **Lesson.** The policy was reviewed for whether it said the right thing and never for whether it
> matched the actual token. Those are different questions, and only the second is decidable by
> looking at the token. When a policy compares against a claim, print the claim - GitHub exposes the
> template at `/actions/oidc/customization/sub`, and one API call before writing the policy would
> have cost nothing.
>
> Keep the feature rather than switching it off, which was the other available "fix": a numeric id
> cannot be re-registered by someone else after a rename, and a name can.

---

### Superseding an ADR the frozen sources cite cannot pass the gate

**Shape:** the-check-was-wrong

**Believed.** `SW-ADR-005` ("the build session touches no AWS") had been overtaken by events, so the
method's own procedure applies: write a superseding record, mark the old one SUPERSEDED, update the
ledger.

**Actually.** `tools/consistency_check.py` gates on no live document resting authority on a
non-APPROVED record - correctly, since an earlier review found the constitution resting the
product's central security promise on a withdrawn ADR. Marking `SW-ADR-005` superseded turned
**seventeen** citations into failures at once.

Fifteen are ordinary documents that can be annotated. Two are `SRC-001` and `SRC-002`, which are
frozen and SHA-256-fingerprinted; changing a byte invalidates every artifact derived from them. They
carry `Carried into: SW-ADR-005` provenance pointers that can never be updated.

So superseding this particular ADR cannot pass the gate - not because anything is wrong, but because
the check has no exemption for documents that are definitionally unupdatable. It already exempts
`all-ADRs/` and the ledger on exactly that reasoning.

**Caught by.** Running `consistency_check.py` before committing, as `CLAUDE.md` requires.

> **Lesson.** The tempting fix was one `continue` for `docs/00 SourceOfTruth/`, and the argument for
> it is decent - a frozen source's forward pointer records what was derived from it, not a claim
> that the target is still authority. But narrowing a quality check is **reserved**, and "the gate
> is wrong" is exactly what someone says when the gate is right. Reverted and referred to the
> client, with the draft record kept outside the repository rather than half-applied. A gate that
> blocks something legitimate is a design question, not a thing to route around at the moment it
> becomes inconvenient.

---

## Shape counts for this session

| Shape | Count |
|---|---|
| the-check-was-wrong | 3 |
| wrong-assumption | 3 |
| fix-caused-it (averted) | 1 |
| environment | 1 |

Six of eight were found by reading a draft aloud against the question "what does this actually do,
line by line?" — not by running anything. The one that got through was the one nobody read back
before it executed.
