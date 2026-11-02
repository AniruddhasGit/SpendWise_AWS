# Bringing SpendWise back up

Everything was shut down on **2026-09-13** to stop it costing money between demos. On
**2026-11-02** the database instance was **deleted** (with a final snapshot), because AWS kept
restarting it. Everything else is only stopped. This file brings it all back, database included.

Run everything with `AWS_PROFILE=dynpro`. Check you are in the right account before you start —
the `default` profile points at a different one:

```bash
AWS_PROFILE=dynpro aws sts get-caller-identity    # must say 944483082287
```

---

## Read this before you start

### The database was DELETED on 2026-11-02 — restore it from the snapshot first

A stopped RDS instance is **automatically started by AWS after seven days** (not a setting, cannot
be turned off). It had restarted itself and was found running and billing on 2026-11-02, so the
owner had it deleted with a final snapshot. **`spendwise-db` no longer exists; step 1 below restores
it instead of starting it.** Nothing is lost: the snapshot holds the data as of the deletion.

- Final snapshot: **`spendwise-db-final-2026-11-02`** (an older manual one, `spendwise-db-manual-2026-09-13`, is also kept).
- The full instance description at deletion: `D:\Project\SpendWise\db-backups\rds-spendwise-db-config-2026-11-02.json` (outside the repo).

**Restore with the same identifier and the same placement.** The endpoint hostname is derived from
the identifier, so restoring as `spendwise-db` gives back
`spendwise-db.c9y6yemgc4pn.ap-south-1.rds.amazonaws.com`, and the app's stored connection strings
work unchanged. Restoring into a different VPC, subnet group or security group gives a healthy
database the app cannot reach. Step 1 below has the exact command.

#### The instance as it was, recorded at deletion (observed with `describe-db-instances`, 2026-11-02)

| Setting | Value | Why it matters on restore |
|---|---|---|
| Identifier | `spendwise-db` | Same name → same endpoint → no secret changes |
| Endpoint | `spendwise-db.c9y6yemgc4pn.ap-south-1.rds.amazonaws.com:5432` | Written into the SSM `DATABASE_URL`s below |
| Account / region / AZ | `944483082287` / `ap-south-1` / `ap-south-1c` | |
| Engine | PostgreSQL **17.9** | The snapshot fixes it; restore cannot change the major version |
| Class | `db.t4g.micro` | Free-tier class; anything bigger bills |
| Storage | 20 GB **gp2**, encrypted | Pass `--storage-type gp2`, or the restore may pick a different default |
| KMS key | `alias/aws/rds` (`9b88a2b0-d909-42eb-89aa-ac176c8a4d6a`), AWS-managed | The snapshot carries it; nothing to pass |
| VPC | `vpc-0b41821a4c0b2026a` (the default VPC) | |
| Subnet group | `default` (subnets `subnet-09d8502d2eb7af87b` 1a, `subnet-04b8731cc8a0f7dae` 1b, `subnet-029c389ccf3db5e76` 1c) | |
| Security group | **`sg-09febaad6c66d18cd`** (`spendwise-db-sg`) | Inbound: **only** tcp 5432 from `sg-0d82a867e00a5ee91` (`spendwise-ecs-host`). Outbound: all. Its description still says "laptop access only"; the laptop rule (`27.107.64.142/32`) was revoked on 2026-09-13 and is not there |
| Publicly accessible | **true** | It has a public address, but the security group above admits only the ECS host. Restoring it the same way is not a change; making it reachable from anywhere else is a reserved decision (CLAUDE.md) |
| Parameter group / option group | `default.postgres17` / `default:postgres-17` | |
| Multi-AZ | no | |
| Master user | `swadmin` | Password: SSM `/spendwise/rds/MASTER_PASSWORD`. The snapshot keeps the password the instance had at deletion; that it equals the SSM value is **unverified** — if the master login fails, reset it with `modify-db-instance --master-user-password` from the SSM value |
| Initial DB name | `spendwise_dev` | The uat and production databases and their logins live **inside** the instance, so they come back with the snapshot |
| Backup retention / window | 1 day / `23:43-00:13` UTC | Check after restore; set back with `modify-db-instance --backup-retention-period 1` if it differs |
| Maintenance window | `mon:10:06-mon:10:36` UTC | |
| CA certificate | `rds-ca-rsa2048-g1` | |
| Deletion protection | off | |
| Performance Insights / enhanced monitoring | off / off | Both bill; leave off |
| Auto minor version upgrade | off | |

The full JSON is `D:\Project\SpendWise\db-backups\rds-spendwise-db-config-2026-11-02.json`.

#### Where the app's database settings live (SSM Parameter Store, all `SecureString`)

| Environment | Parameters |
|---|---|
| production (`:8000`) | `/spendwise/ecs/DATABASE_URL`, `/spendwise/ecs/MIGRATION_DATABASE_URL`, `/spendwise/ecs/JWT_SECRET` |
| uat (`:8001`) | `/spendwise/uat/DATABASE_URL`, `/spendwise/uat/MIGRATION_DATABASE_URL`, `/spendwise/uat/JWT_SECRET` |
| dev (`:8002`) | `/spendwise/dev/DATABASE_URL`, `/spendwise/dev/MIGRATION_DATABASE_URL`, `/spendwise/dev/JWT_SECRET` |
| RDS master | `/spendwise/rds/MASTER_PASSWORD` |

These were **not touched** by the deletion and still point at the endpoint above. Restore under the
same identifier and none of them needs editing.

If you ever stop the database again rather than delete it, remember the seven-day restart: it will
be running and billing a week later.

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

### 1 — Restore the database from its final snapshot

First confirm the snapshot is there and the name is free (the second command must say
`DBInstanceNotFound`):

```bash
AWS_PROFILE=dynpro aws rds describe-db-snapshots --region ap-south-1 \
  --db-snapshot-identifier spendwise-db-final-2026-11-02 \
  --query 'DBSnapshots[0].Status' --output text          # available
AWS_PROFILE=dynpro aws rds describe-db-instances --region ap-south-1 \
  --db-instance-identifier spendwise-db                   # DBInstanceNotFound
```

Then restore, every placement flag spelled out (values from the table above):

```bash
AWS_PROFILE=dynpro aws rds restore-db-instance-from-db-snapshot --region ap-south-1 \
  --db-instance-identifier spendwise-db \
  --db-snapshot-identifier spendwise-db-final-2026-11-02 \
  --db-instance-class db.t4g.micro \
  --storage-type gp2 \
  --db-subnet-group-name default \
  --vpc-security-group-ids sg-09febaad6c66d18cd \
  --db-parameter-group-name default.postgres17 \
  --availability-zone ap-south-1c \
  --publicly-accessible --no-multi-az \
  --no-deletion-protection --no-auto-minor-version-upgrade
```

Every flag above was checked against `aws rds restore-db-instance-from-db-snapshot help` on
aws-cli 2.36.17 (2026-11-02). Then wait:

```bash
AWS_PROFILE=dynpro aws rds wait db-instance-available --region ap-south-1 \
  --db-instance-identifier spendwise-db
```

(The CLI has `db-instance-available` and `db-instance-deleted` waiters but **no**
`db-instance-stopped` one; to wait for a stop, poll `DBInstanceStatus` until it reads `stopped`.)

Expect 10–20 minutes. Then check it came back where it was — all four must match:

```bash
AWS_PROFILE=dynpro aws rds describe-db-instances --region ap-south-1 \
  --db-instance-identifier spendwise-db --output text --query \
  'DBInstances[0].[Endpoint.Address,VpcSecurityGroups[0].VpcSecurityGroupId,DBSubnetGroup.VpcId,BackupRetentionPeriod]'
# spendwise-db.c9y6yemgc4pn.ap-south-1.rds.amazonaws.com  sg-09febaad6c66d18cd  vpc-0b41821a4c0b2026a  1
```

If the security group shows `default` instead, the app cannot connect; fix it with
`modify-db-instance --vpc-security-group-ids sg-09febaad6c66d18cd --apply-immediately`.

The whole restart, restore included, is about 30–45 minutes. Do not start the host before this
step finishes.

(If the database is ever only *stopped* again rather than deleted, this step is just
`aws rds start-db-instance --db-instance-identifier spendwise-db`, five to ten minutes.)

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
```

Then the database. **For anything longer than a week, delete it with a final snapshot** (what was
done on 2026-11-02); a stopped one restarts itself after seven days and bills until noticed. Record
its settings first, so the restore in step 1 is copied rather than guessed:

```bash
STAMP=$(date +%Y-%m-%d)
AWS_PROFILE=dynpro aws rds describe-db-instances --region ap-south-1 \
  --db-instance-identifier spendwise-db --output json \
  > "D:/Project/SpendWise/db-backups/rds-spendwise-db-config-$STAMP.json"
AWS_PROFILE=dynpro aws rds delete-db-instance --region ap-south-1 \
  --db-instance-identifier spendwise-db \
  --final-db-snapshot-identifier "spendwise-db-final-$STAMP"
AWS_PROFILE=dynpro aws rds wait db-instance-deleted --region ap-south-1 \
  --db-instance-identifier spendwise-db
```

Then update step 1 and the "Read this before you start" section with the new snapshot name, and
compare the new JSON against the settings table there. Deletion also removes the automated daily
backups; the final snapshot is the copy that matters.

For a pause of under a week, stopping is enough:
`AWS_PROFILE=dynpro aws rds stop-db-instance --db-instance-identifier spendwise-db`.

---

## What still costs money while it is all stopped

Stopping is not the same as deleting. These continue:

| Thing | Size | Why it still bills |
|---|---|---|
| EBS volume `vol-01713a0ff8263d68f` | 30 GB gp3 | The host's disk exists whether or not the host runs |
| RDS snapshot `spendwise-db-final-2026-11-02` | 20 GB | **The database itself** since the instance was deleted. Never delete it |
| RDS snapshot `spendwise-db-manual-2026-09-13` | 20 GB | A manual snapshot, kept deliberately (older data) |
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
- **There is a second AWS account, `545620235339`** ("Aniruddha_Personal"), which held an orphaned
  RDS instance (`spend-wise-dev-db`, Mumbai `ap-south-1`, storage autoscaling up to 1000 GB). It
  has nothing to do with the running project and none of its data is needed: the real data is in
  `spendwise-db-final-2026-11-02` in account `944483082287`. The CLI cannot reach it (the
  `default` profile's keys are invalid), so it is checked in the console only.

  **State on 2026-11-02, observed by the owner in the console, not by the CLI:**
  - RDS in **N. Virginia (us-east-1)**: 0 instances, 0 snapshots.
  - Tag Editor, **Mumbai only**, types `AWS::RDS::DBInstance` + `AWS::RDS::DBSnapshot`: **no
    instance**, but **four snapshots** that bill for storage:
    `rds:spend-wise-dev-db-2026-10-31-17-18` and `rds:spend-wise-dev-db-2026-11-01-17-18`
    (automated; the instance existed until at least 2026-11-01), plus the manual `snapshot` and
    `spend-wise-dev-db-snapshot`.
  - The owner was given the cleanup below. **That the account is now empty in every region has
    not been observed yet.** Until a screenshot of the all-regions search reading **(0)** exists,
    treat it as still billing.

  **Cleanup, in the console of `545620235339`, region Mumbai:**
  1. RDS → **Databases**: if `spend-wise-dev-db` is listed, Actions → Delete, untick *Create final
     snapshot* and *Retain automated backups*, type `delete me`.
  2. RDS → **Snapshots → Manual**: delete `snapshot` and `spend-wise-dev-db-snapshot`.
  3. RDS → **Automated backups → Retained**: delete `spend-wise-dev-db` (this removes the two
     `rds:` snapshots, which cannot be deleted from the Snapshots page).
  4. IAM → Users → `AWS_CLI` → Security credentials: no access key should be **Active** (the one
     that was on the laptop had `AdministratorAccess`).

  **How to confirm an account is empty across every region:** RDS only ever shows one region.
  Use **Tag Editor** (`https://console.aws.amazon.com/resource-groups/tag-editor/find-resources`;
  not "Create Resource Group", which looks similar but has no Regions box) → Regions: **all** →
  Resource types: `AWS::RDS::DBInstance`, `AWS::RDS::DBSnapshot` (or *All supported resource types*
  for everything; default VPCs and security groups are free) → leave Tags empty → **Search
  resources**. Results must read **(0)**. For what actually costs money, use Billing → **Bills** →
  *Charges by service*, which breaks each service down by region (about a day behind).
