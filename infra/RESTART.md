# Bringing SpendWise back up

Everything was shut down on **2026-09-13** to stop it costing money between demos. Nothing was
deleted. This file brings it back.

Run everything with `AWS_PROFILE=dynpro`. Check you are in the right account before you start —
the `default` profile points at a different one:

```bash
AWS_PROFILE=dynpro aws sts get-caller-identity    # must say 944483082287
```

---

## Read this before you start

### RDS restarts itself after 7 days, whether you want it to or not

A stopped RDS instance is **automatically started by AWS after seven days**. That is not a setting
and cannot be turned off. So:

- If it has been under a week, it is still stopped and you start it below.
- If it has been longer, **it is already running and has been billing you.** Check first.

```bash
AWS_PROFILE=dynpro aws rds describe-db-instances \
  --db-instance-identifier spendwise-db \
  --query 'DBInstances[0].DBInstanceStatus' --output text
```

To keep it down for longer than a week, the options are to re-stop it every few days, or take a
final snapshot and delete the instance — which is cheaper but a real teardown, not a pause.

### The public IP will be different

The host has no Elastic IP, so stopping it gives the address back. It was `3.7.37.251`. It will not
be that again.

That address is written into `.github/workflows/cd.yml` (the environment links), `infra/README.md`,
`explanation/02_*.html` and the handoff. **None of it is load-bearing** — the pipeline talks to ECS
by service name and never uses the IP — so a stale address breaks no deploy. It only means the
links in the GitHub environment panel point at nothing until updated.

---

## The order matters

Start the database first. If the app comes up before the database is reachable, the container runs
its migrations, fails, and ECS restarts it in a loop until it happens to succeed.

### 1 — Start the database

```bash
AWS_PROFILE=dynpro aws rds start-db-instance --db-instance-identifier spendwise-db
AWS_PROFILE=dynpro aws rds wait db-instance-available --db-instance-identifier spendwise-db
```

Takes roughly five to ten minutes. Wait for it properly; do not skip the `wait`.

### 2 — Start the host

```bash
AWS_PROFILE=dynpro aws ec2 start-instances --instance-ids i-02f0c9426623427bf
AWS_PROFILE=dynpro aws ec2 wait instance-running --instance-ids i-02f0c9426623427bf
```

Then wait for the ECS agent to re-register it. The instance is running a minute or so before ECS
will place anything on it, and a service scaled up too early just reports that it cannot place a
task:

```bash
AWS_PROFILE=dynpro aws ecs list-container-instances --cluster spendwise-cluster
```

Repeat until it returns one ARN.

### 3 — Scale the services back up

```bash
for s in spendwise spendwise-uat spendwise-dev; do
  AWS_PROFILE=dynpro aws ecs update-service --cluster spendwise-cluster \
    --service "$s" --desired-count 1
done

AWS_PROFILE=dynpro aws ecs wait services-stable --cluster spendwise-cluster \
  --services spendwise spendwise-uat spendwise-dev
```

Each service still points at the task definition it was running, so they come back on the same
images with the same secrets. Nothing needs redeploying.

### 4 — Find the new address and check it

```bash
AWS_PROFILE=dynpro aws ec2 describe-instances --instance-ids i-02f0c9426623427bf \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

Then, with `IP` set to that:

```bash
for p in 8000 8001 8002; do curl -s "http://$IP:$p/readyz"; echo; done
```

All three should answer `{"status": "ready", ...}` with `build` reading `v1`, `uat` and `dev`
respectively. `:8000` is production, `:8001` uat, `:8002` dev.

### 5 — Turn the monitoring back on

Both were switched off at shutdown so they would not bill or fire into the void.

```bash
AWS_PROFILE=dynpro aws cloudwatch enable-alarm-actions --alarm-names spendwise-service-down
AWS_PROFILE=dynpro aws ecs update-cluster-settings --cluster spendwise-cluster \
  --settings name=containerInsights,value=enabled
```

Container Insights is the thing that measured real memory use (148–171 MiB against a 384 MiB
reservation). It is optional and it is billed per metric — leave it off if you only want the site
up for an hour.

### 6 — Update the address in the documents

Replace `3.7.37.251` in `.github/workflows/cd.yml`, `infra/README.md`,
`explanation/02_2026-09-13_three-environments.html`. Cosmetic, but a wrong address in a document is
how the next person loses twenty minutes.

---

## Shutting it down again

Reverse order, and drain the services first so tasks stop cleanly rather than dying with the host:

```bash
for s in spendwise spendwise-uat spendwise-dev; do
  AWS_PROFILE=dynpro aws ecs update-service --cluster spendwise-cluster \
    --service "$s" --desired-count 0
done
AWS_PROFILE=dynpro aws ecs wait services-stable --cluster spendwise-cluster \
  --services spendwise spendwise-uat spendwise-dev

AWS_PROFILE=dynpro aws cloudwatch disable-alarm-actions --alarm-names spendwise-service-down
AWS_PROFILE=dynpro aws ecs update-cluster-settings --cluster spendwise-cluster \
  --settings name=containerInsights,value=disabled

AWS_PROFILE=dynpro aws ec2 stop-instances --instance-ids i-02f0c9426623427bf
AWS_PROFILE=dynpro aws rds stop-db-instance --db-instance-identifier spendwise-db
```

---

## What still costs money while it is all stopped

Stopping is not the same as deleting. These continue:

| Thing | Size | Why it still bills |
|---|---|---|
| EBS volume `vol-01713a0ff8263d68f` | 30 GB gp3 | The host's disk exists whether or not the host runs |
| RDS storage for `spendwise-db` | 20 GB | Same — the data is still there |
| RDS snapshot `spendwise-db-manual-2026-09-13` | 20 GB | A manual snapshot, kept deliberately |
| ECR images | **1,042 MB** | Free tier is 500 MB, so ~542 MB is chargeable - about $0.05/month |
| Five S3 buckets | unmeasured | `ani-application-logs-2026`, `private-application-storage`, `spendwise-cloudtrail-944483082287`, `static-bucket-for-practice`, `user-uploads-2026` |
| CloudTrail `spendwise-trail` | — | Management events are free; the S3 storage under them is not |

Small per month, not zero. Going to actually-zero means deleting the instance and volume, and that
is a teardown with a restore step, not a pause.

### Two things worth a look when you next have time

- **ECR stores 1,042 MB, not the 2.4 GB `describe-images` appears to show.** That command reports a
  per-image total, and layers are shared between images built from the same Dockerfile - adding the
  per-image figures counts every shared layer once per image that references it. ECR bills for
  unique blobs. About $0.05/month over the free tier, so not worth pruning for cost.

  **The lifecycle policy was a different matter, and it has been fixed.** It kept only the 5 most
  recently pushed images, and `sha-cc90b35` - the image production AND uat both run - had already
  fallen to position 9. It was queued for deletion, and the restart above would have failed with
  nothing to pull. `infra/aws/ecr-lifecycle.json` now keeps 30 and expires untagged build
  by-products after a day. A count rule cannot know what is deployed, so the count has to stay
  comfortably above a working set. Before trusting one, check what is actually running:

  ```bash
  AWS_PROFILE=dynpro aws ecs describe-task-definition --task-definition spendwise \
    --query 'taskDefinition.containerDefinitions[0].image' --output text
  ```
- **There is a second AWS account, `545620235339`**, holding an orphaned RDS instance
  (`spend-wise-dev-db`) with storage autoscaling up to 1000 GB. It is not reachable from this
  profile — the credentials for it are invalid — so **nothing in this session could see whether it
  is costing you anything.** It has been flagged in three handoffs now. Log into that account
  directly and check.
