# 2026-09-13 — the first deployment to AWS

Nine bugs in one session. Five were caught before they ran, four ran. They are grouped by how close
each came to shipping, because that is the part worth learning from.

Context: SpendWise had never been deployed. This session installed the container tooling, audited
the AWS account, and took the app from a laptop to a running service on ECS.

---

## The one that shipped

### The image passed its health check and was broken

**Shape:** silent-failure · false-green

**Believed.** The container image was complete. It had been built, inspected, and verified —
correct CPU architecture, the right library versions, the compiled web page in the right place,
running as a non-root user. CI's smoke test started it against a real Postgres and polled
`/healthz` until it answered 200. It answered. The deploy to ECS then reported the task
**HEALTHY**, `/readyz` returned `{"status":"ready"}`, and the web page loaded.

**Actually.** `app/core/errors.py:28` reads `docs/03 PRD/api/contract.json` **at runtime** — the
table of error codes is loaded from the specification rather than transcribed into Python, so the
two can never drift. It is a good design. But `.dockerignore` excludes `docs/`, on the entirely
sensible grounds that four megabytes of specification has no business in a runtime image.

So the file was not there. Every request that touched an error path raised `FileNotFoundError` —
**including the handler whose job is to format errors.** The 500 could not describe itself. The
first sign of trouble was a bare `Internal Server Error` on `POST /api/auth/register`.

**Caught by.** Trying to log in. Nothing before that touched an error path: `/healthz` returns a
bodiless 200 and opens no database session, `/readyz` touches the database but never constructs an
`ApiError`, and the web page is a static file. Three separate green signals — a passing CI smoke
test, a HEALTHY ECS task, and a loading page — all of which were true and none of which exercised
the broken code.

The CloudWatch log group had existed for about ten minutes at that point. Without it the 500 would
have been a blank wall: the container's logs would have died with the container.

> **Lesson.** A health check only proves the code path the health check runs. `/healthz` was
> deliberately built to touch nothing — which is correct for a liveness probe, and exactly why it
> cannot tell you the application works. If a smoke test never provokes an error, it has not tested
> error handling, and error handling is where the untested code lives.
>
> The second, sharper lesson: **a runtime dependency that is a documentation file will be excluded
> by anyone tidying the image, and they will be right to try.** If code reads a file at runtime, it
> is not documentation, whatever folder it lives in.

**Fixed in.** `Dockerfile` — an explicit `COPY` with the reason in a comment; `.dockerignore` — a
negation with the same reason. A new test, `test_every_docs_file_read_at_runtime_is_actually_in_the_image`,
scans `app/` for *any* runtime read under `docs/` and asserts the Dockerfile copies it — written
against the pattern rather than this one file, so the next module that does this is caught on the
commit that adds it. Red-proofed: the `COPY` was removed, the test watched failing, the `COPY`
restored.

---

## The ones that were caught before they ran

These were found by an adversarial review pass — a second agent given the first agent's work and
told to assume it was wrong. All four would have failed at deploy time.

### Log permissions on the wrong role

**Shape:** wrong-assumption

**Believed.** `logs:CreateLogStream` and `logs:PutLogEvents` belong on the ECS **task execution
role**. Every tutorial says so, and on Fargate it is true.

**Actually.** On the **EC2** launch type the `awslogs` log driver is invoked by the Docker daemon
running on the host, using the **container instance's** credentials — not the task's. Without the
permission on the instance role, every task dies at container start with a logging-driver
`AccessDenied`.

> **Lesson.** The same service behaves differently under different launch types, and the difference
> is invisible in the documentation you are most likely to read. When a permission is exercised by
> infrastructure rather than by your code, ask *which process actually makes the call*. And note the
> cruelty of this one: the broken thing is logging, so the failure cannot log itself.

### The task definition omitted `executionRoleArn`

**Shape:** silent-failure

**Believed.** Wiring secrets via `secrets`/`valueFrom` in the container definition is sufficient.

**Actually.** Without a top-level `executionRoleArn`, registration succeeds, service creation
succeeds, and then every task transitions `PENDING → STOPPED` with *"unable to pull secrets or
registry auth"*. Because the container never starts, the log group stays empty — so the natural
next move, tailing the logs, shows nothing at all.

> **Lesson.** Two green steps followed by a red one does not mean the third step is where the
> mistake is. Configuration validated at *registration* time and configuration used at *run* time
> are different sets, and only the first gives you an error message worth reading.

### `BOOTSTRAP_ADMIN_EMAIL` treated as optional

**Shape:** silent-failure

**Believed.** It is documented as optional, so the deploy can proceed without it.

**Actually.** It is optional for *starting*. Without it, the first person to sign up is created as
an ordinary user — and since promoting anyone to admin requires an existing admin, the system
reaches a state with **no administrator and no path to one**. No error, no warning, no failed
health check. It quietly breaks the project's own definition of success, which includes an admin
resetting a password.

> **Lesson.** "Optional" usually means "the program starts without it". It rarely means "the
> product works without it". For any setting that seeds an initial state, ask what happens on the
> *first* run, not the hundredth — first-run-only bugs are unreachable once you are past them.

### PowerShell's `Out-File -Encoding utf8` writes a byte-order mark

**Shape:** environment

**Believed.** Writing a JSON file with `Out-File -Encoding utf8` produces a UTF-8 JSON file the AWS
CLI can read.

**Actually.** Windows PowerShell 5.1 writes UTF-8 **with a byte-order mark** — three invisible bytes
at the start. The AWS CLI reads `file://` payloads as raw bytes and a BOM is not valid JSON. It
fails with *"Invalid JSON received"*, pointing at the JSON, which looks perfect.

Had this been run as drafted, it would have applied the security group's *inbound* rules and
silently skipped the *egress* file — leaving the host able to reach Postgres on 5432 and nothing
else. No port 443 means the ECS agent cannot reach the control plane, the instance de-registers
itself, and the console reports only *"no container instances available."*

> **Lesson.** Invisible characters break comparisons by returning "no match" rather than an error.
> On Windows, write files other tools will parse with
> `[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))`.
> This project has been bitten by this family twice — see the CRLF blocklist entry in
> `BUG_LEDGER.md`, where a gate silently matched nothing for months.

---

## The ones that were mine

Recorded because the point of this folder is not to look good.

### I reported a stale checkout's contents as current

**Shape:** wrong-assumption

**Believed.** The repository in front of me was current. The session-start hook reported the newest
handoff and I reasoned from it.

**Actually.** The checkout was **sixteen commits and five weeks stale**, and `origin` pointed at a
repository that no longer exists. The hook was telling the truth — that *was* the newest handoff
in that checkout. It was not the newest that existed. I told the user the Dockerfile did not exist
(it had for three weeks), that rate limiting was unimplemented (it was done), and that
`range.required` was unfixed (it was fixed).

**Caught by.** `git push` being rejected at the end of the session — after the wrong conclusions
had already been delivered as fact.

> **Lesson.** Freshness is not a property of a file, it is a property of a file *relative to its
> source*. Before reasoning from local state, check it against the remote. A tool that reports "the
> latest X" is answering "the latest X **I can see**", and the gap between those is invisible from
> the inside.

### I called a metric a discrepancy when I had misread it

**Shape:** wrong-assumption

**Believed.** `docker image inspect --format '{{.Size}}'` returned 140 MB where the handoff recorded
563 MB, so one of them was wrong.

**Actually.** Under Docker 29's image store, `inspect` reports the *compressed* size while
`docker images` reports *uncompressed*. Both numbers were right. I raised a discrepancy that did not
exist, and briefly cast doubt on a correct record.

> **Lesson.** Before reporting that two sources disagree, check they are measuring the same thing.
> A unit mismatch looks exactly like a contradiction.

### I stated a free-tier fact I had inferred rather than tested

**Shape:** wrong-assumption

**Believed.** The account had no free tier at all — inferred from Cost Explorer unit prices and from
the Free Tier API returning only one unrelated entry.

**Actually.** Partly right, importantly wrong. The account *is* on a restricted free plan, which
does not grant 12-month allowances but **does impose limits**. Raising RDS backup retention from 1
day to the specified 7 fails outright with `FreeTierRestrictionError`. So the 1-day retention I had
reported as a misconfiguration to fix is a **platform restriction**, not an oversight — and my
recommended fix was impossible.

**Caught by.** Trying to apply the fix.

> **Lesson.** Inferring a capability from pricing data tells you what is being *charged*, not what
> is *permitted*. The only reliable test of "can I do X" is doing X. Label inferences as inferences
> until then — and when the fix fails, correct the finding, not just the plan.

---

## The meta-lesson

Nine bugs. **Five were caught by a second pass that assumed the first pass was wrong**, three by
actually running the thing, and one by a `git push` failing.

Not one was caught by the thing that was supposed to catch it. CI was green. The health check was
green. The task was HEALTHY. Every one of those signals was *true* — and none of them covered the
broken part.

That is the whole argument for red-proofing, stated in this project's constitution long before this
session went looking for trouble: **a gate nobody has watched fail is decoration.**
