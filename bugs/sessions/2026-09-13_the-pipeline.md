# 2026-09-13 — building the three-environment pipeline

Ten entries. One ran and did damage, two cost a failed deploy, and the other seven were caught
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

## The nine found in review, or by the pipeline refusing

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

### Splitting the execution roles left the deploy policies behind

**Shape:** fix-caused-it

**Believed.** Giving each environment its own ECS execution role closes a real hole: a shared one
lets a compromised dev container read `/spendwise/ecs/DATABASE_URL` and reach the production
database. The task definitions were updated to name `spendwise-ecs-exec-dev` and
`spendwise-ecs-exec-uat`, the roles were created, the services came up healthy. Done.

**Actually.** Registering a task definition that names an execution role requires `iam:PassRole` on
that role. The three deploy policies still listed the two roles from *before* the split:

```
spendwise-ecs-task-execution-role
spendwise-ecs-task-role
```

So the pipeline could deploy by hand-run script — which used admin credentials — but not through
GitHub Actions, which uses the scoped role. The deploy died on `RegisterTaskDefinition` with
`not authorized to perform: iam:PassRole on resource: .../spendwise-ecs-exec-dev`.

**Caught by.** The third pipeline run. Not by any check — by the permission boundary itself
refusing, which is what it is for.

Worth noticing what the error was *not*: the services were already running fine on those exact
roles, because they were created with admin credentials that had no such restriction. The gap
existed from the moment the roles were split and was invisible until something with real least
privilege tried to use them.

> **Lesson.** A security improvement is a change, and changes have a blast radius that runs
> downhill. Splitting an identity means finding everything that *names* the old one — not just the
> definitions that consume it. The fix here was to scope rather than widen: each environment may
> now pass only its own execution role. The old shared list was worse than incomplete, it was too
> broad, because it let the dev deploy role attach production's secrets-reading role to a task.
>
> Also: work done with admin credentials proves the resource is correct, never that the permissions
> are. Those are two different tests and only the pipeline runs the second one.

---

### The secret scan had never read the repository's history

**Shape:** false-green

**Believed.** CI runs `gitleaks/gitleaks-action@v2` with `fetch-depth: 0`, and the step is
commented: *"a secret committed three months ago and 'removed' last week is still in history, still
clonable, still live."* The intent is explicit and the checkout is correct. It had been green on
every run for weeks.

**Actually.** `fetch-depth: 0` controls what the CHECKOUT fetches, not what gitleaks scans. On a
`push` event the action scans only the commit range in the push payload — the new commits, nothing
else. The full history is sitting on disk and never gets read.

So the check had been answering "is there a secret in the commits you just pushed?" while its
comment, its name, and everyone reading it believed it answered "is there a secret in this
repository?" Anything committed before CI existed was never examined by it, not once.

**Caught by.** Triggering the pipeline with `workflow_dispatch` instead of a push, for an unrelated
reason — proving the production gate. A dispatch has no commit range, so the action falls back to
scanning everything, and a finding appeared in a commit from a previous session that had already
passed CI.

The finding itself was a false positive, and a pointed one. The flagged "secret" was:

```
on-secret variable, SPENDWISE_DOTENV=0.
```

— the middle of an English sentence, from a paragraph explaining that the variable is *not* a
secret. `generic-api-key` looks for `NAME=value` near a keyword and found one in prose.

Suppressing it had a tail. The first attempt was a `.gitleaksignore` fingerprint with the matched
text quoted in full, so the "false positive" claim could be re-checked rather than trusted. That
worked — and produced **three new findings**, two in the ignore file itself and one in this
paragraph, because quoting the matched text reproduces the pattern that matched. The fix is a
`.gitleaks.toml` allowlist on the token rather than fingerprints on the lines: fingerprints also go
stale the moment a line moves, so every edit to this file would have needed a new one.

> **Lesson.** The false positive cost twenty minutes. The false GREEN is the finding: a scan whose
> scope silently differs from its stated purpose, that had been passing for weeks without once doing
> the thing its own comment describes. `fetch-depth: 0` *looked* like the fix for exactly this
> problem, which is why nobody looked further — the presence of a mitigation is not evidence that
> the mitigation is connected to anything.
>
> Two thirds of the entries in `BUG_LEDGER.md` are failures of detection rather than of code. This
> is one: nothing was broken, and nothing would have told you.

---

## Shape counts for this session

| Shape | Count |
|---|---|
| the-check-was-wrong | 3 |
| wrong-assumption | 3 |
| fix-caused-it | 2 (1 averted) |
| environment | 1 |
| false-green | 1 |

Seven of ten were found by reading a draft against the question "what does this actually do, line by
line?" — not by running anything. The three that were not split cleanly by what kind of mistake they
were:

- **The one that did damage** was a `sed` nobody read back before it executed.
- **The two that cost a deploy** were both cases of a document being checked for whether it said the
  right thing, and never against the thing it was compared to at runtime — a trust policy versus the
  actual token, a PassRole list versus the roles the task definitions actually name. Reading cannot
  catch those. Only running can, which is the argument for a pipeline that fails loudly and early
  rather than one that is inspected carefully and then trusted.
