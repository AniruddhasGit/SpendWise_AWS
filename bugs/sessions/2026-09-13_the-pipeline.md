# 2026-09-13 — building the three-environment pipeline

Six entries. One of them ran and did damage; the other five were caught while reading a draft, not
while debugging a failure. That ratio is the point of this file: the cheap catches all came from
someone asking "what would this actually do?" before running it.

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

## The five caught while reading

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

## Shape counts for this session

| Shape | Count |
|---|---|
| the-check-was-wrong | 2 |
| wrong-assumption | 2 |
| fix-caused-it (averted) | 1 |
| environment | 1 |

Five of six were found by reading a draft aloud against the question "what does this actually do,
line by line?" — not by running anything. The one that got through was the one nobody read back
before it executed.
