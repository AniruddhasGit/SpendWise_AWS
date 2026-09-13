# infra/ — the three environments and how a change reaches production

Everything in here is applied to AWS. Nothing in here is read by the running application.

---

## The shape

```
    feature branch
          |  pull request
          v
    dev  ──auto──>  dev env        port 8002   database spendwise_dev
          |
          |  fast-forward merge
          v
    uat  ──auto──>  uat env        port 8001   database spendwise_uat
          |
          |  fast-forward merge
          v
    main ──manual─> production     port 8000   database spendwise
```

All three run as ECS services on **one** t3.micro host, and all three talk to **one** RDS
instance — separate databases on it, with separate logins.

---

## The rule: you cannot skip a step

This repository is on a free GitHub plan, where rulesets and required reviewers are paid features.
So the promotion rule is **not** enforced by GitHub. It is enforced by the container registry.

1. A commit on `dev` gets built once and pushed as `spendwise:sha-<sha>`.
2. When the dev service comes up healthy, the pipeline adds a second tag: `dev-ok-<sha>`.
3. The uat deploy **refuses to run** unless `dev-ok-<sha>` already exists.
4. When uat comes up healthy, it adds `uat-ok-<sha>`.
5. The production deploy **refuses to run** unless `uat-ok-<sha>` exists.

Those tags are immutable in ECR — once written they cannot be moved to different bytes — and the
production deploy role has no `ecr:PutImage` permission at all, so production cannot stamp its own
approval.

The stamp is applied to the **same manifest digest** the deploy references, and the stamping step
verifies that before writing: it resolves the tag to a digest, fetches by digest, hashes the
returned manifest, and refuses unless the hash equals the digest it asked for. That check exists
because the first version did not have it and stamped a platform child manifest instead of the
image index — real tags, immutable, on the wrong object.

Merging straight from `dev` into `main` does not get you anything: the commit arrives with no
`uat-ok` tag and the deploy stops.

**Promotion must fast-forward.** A squash or rebase produces a *new* commit, which no environment
has ever seen, so no stamp exists for it and the gate refuses it. That is the intended behaviour,
not a limitation — the thing being promoted is a tested artifact, and rewriting the commit makes it
a different artifact.

**Honest limit.** The dev role *can* call `ecr:PutImage`, so a hand-written workflow running in the
dev environment could forge a `uat-ok` tag. Closing that needs one ECR repository per environment
so IAM can scope by ARN. This gate stops the mistake people actually make — merging to the wrong
branch — not someone who is already editing pipeline files.

---

## The gate, watched failing

A gate nobody has seen fail is decoration. On 2026-09-13 commit `cc90b35` was pushed to `main` and
released to production by hand — `workflow_dispatch`, confirm `deploy` — having never been through
uat. CI passed all four jobs. The production deploy role was assumed successfully. Then:

```
success  Assume the production deploy role
failure  Refuse anything that has not passed uat
skipped  Deploy
```

with:

```
REFUSING TO DEPLOY - this commit has not passed uat.
Looked for the tag : uat-ok-cc90b35
In the repository  : spendwise
Did not find it.
```

The important part is the middle line of the step list. The job held **valid production
credentials** and was refused anyway, because the refusal does not depend on who is asking — it
depends on whether an earlier environment left a mark that only it could leave. The `Deploy` step
never ran.

The same commit was then promoted properly: dev, then uat, then production. Same bytes, same tag,
three environments, one build.

---

## One image, not three builds

The image is built **once**, on `dev`. uat and production re-tag and redeploy that same image.
Nothing is rebuilt on the way up, so "we tested it" means the bytes in production are the bytes
that were tested — not a rebuild that ought to be identical.

---

## What the files are

```
infra/aws/oidc/          GitHub Actions' identity in AWS
  trust-<env>.json         who may assume the role: one GitHub environment, nothing else
  policy-<env>.json        what it may then do
  apply.sh                 creates the provider and the three roles. Idempotent.

infra/aws/environments/  each environment's own secrets identity
  exec-policy-<env>.json   ECS execution role: reads /spendwise/<env>/* and no other path
  trust-ecs-tasks.json     shared assume-role document for ECS tasks

infra/aws/ecs/
  taskdef-<env>.json       task definition per environment
```

### Why there is no task definition for production here

There is one, in AWS, and it stays there. The deploy pipeline reads whatever the service is
currently running, changes the image field, and registers that. It never writes a task definition
from a file in this repository.

That is deliberate. A task definition carries the environment's secret wiring — which SSM path it
reads, and therefore which database it talks to. Three near-identical copies of that file in git is
a setup where someone edits two and forgets the third, and the day that happens dev starts writing
to the production database. The pipeline is allowed exactly one opinion: which image to run.

`taskdef-dev.json` and `taskdef-uat.json` exist only to create those services the first time.

---

## Identities, and why there are so many

| Role | Held by | Can do |
|---|---|---|
| `spendwise-gha-deploy-dev` | the dev deploy job | build, push, deploy `spendwise-dev` |
| `spendwise-gha-deploy-uat` | the uat deploy job | re-tag, deploy `spendwise-uat` |
| `spendwise-gha-deploy-production` | the production deploy job | read image, deploy `spendwise` |
| `spendwise-ecs-exec-<env>` | ECS, to *start* the task | pull image, read `/spendwise/<env>/*` |
| `spendwise-ecs-task-role` | the app, while running | nothing — it holds no policies |

The execution roles are split per environment for one reason: a shared one would let a compromised
dev container read production's database URL out of Parameter Store. The task role is shared
because it grants nothing at all — the application makes no AWS calls.

No access keys are involved anywhere. GitHub mints a short-lived OIDC token per job, bound to one
repository and one environment, and it expires when the job ends.

---

## Memory, measured

The host registers **916 MiB**. Real usage per container is **148–171 MiB** (Container Insights,
six-hour window), against production's 512 MiB reservation — about 3× oversized.

| Service | Reserved | Hard limit | Workers |
|---|---|---|---|
| `spendwise` | 384 | 768 | 2 |
| `spendwise-uat` | 192 | 384 | 1 |
| `spendwise-dev` | 192 | 384 | 1 |
| | **768 of 916** | | 148 MiB spare |

Production was reserving 512 against a measured peak of 171 — three times what it uses — which left
only 20 MiB once dev and uat were added. Revision `spendwise:3` dropped it to 384, still 2.2x peak,
and the host went from 404 MiB free to 532.

Only the **soft** limit (`memoryReservation`) decides placement; the hard limit is the OOM ceiling
and is left at 768 deliberately. Lowering that too would shrink the crash margin and free nothing.

All three services run `maximumPercent: 100`, `minimumHealthyPercent: 0`: ECS stops the old task
before starting the new one. On a host this size there is no room to run two copies during a
deploy, and the default (start-then-stop) would wedge forever waiting for memory that never
arrives. The trade is a few seconds of downtime per deploy, which is the right trade here.

---

## Running it

```bash
# one-time, or after editing any trust/policy JSON
bash infra/aws/oidc/apply.sh
```

Requires credentials that can write IAM. Then the pipeline needs nothing else: no secrets to paste
into GitHub, because there are none.
