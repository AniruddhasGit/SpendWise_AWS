# BUG_LEDGER.md — every defect this project has recorded

> Read `README.md` in this folder first — it explains why these are kept and how to add one.
>
> **160 defects**, recovered from `GOTCHAS.md`, `PROGRESS.md`, the nine handoffs, the 154 ADRs,
> the test docstrings, and the design-review log. Every entry happened. None are hypothetical.

Grouped by **shape** rather than by component, because the shape is what transfers. You will not
meet this project's Dockerfile again. You will absolutely meet another check that passed because it
examined an empty list.

## Contents

- [Silent failure](#silent-failure) — 36
- [The check was wrong](#the-check-was-wrong) — 34
- [False green](#false-green) — 32
- [Wrong assumption](#wrong-assumption) — 32
- [The fix caused it](#the-fix-caused-it) — 15
- [Environment](#environment) — 11

---

# Silent failure

*It appeared to work and did not. Nothing went red, nothing was logged, and the wrong answer looked exactly like the right one.*

**36 recorded.**

### The per-user database setting is transaction-scoped, and losing it returns zero rows instead of an error

**Believed.** Calling `set_config('app.user_id', <the id>, true)` at the start of a request tells Postgres who is asking. The row-level security rules — database rules that filter every query down to rows belonging to that user — then apply for the rest of that request.

**Actually.** The third argument, `true`, scopes the setting to the CURRENT TRANSACTION only. If any repository opens a second transaction, the setting simply does not exist there. The security rule then compares each row against an empty value, matches nothing, and every protected query returns zero rows. No error is raised, no log line appears, nothing goes red. As the ledger puts it, an empty dashboard is indistinguishable from a person who has spent nothing.

**Caught by.** Identified while writing the isolation design (SW-ADR-136), before it could ship. The resulting rule is structural rather than advisory: one database session and one transaction per request, with the setting issued as the very first statement inside the authentication dependency.

> **Lesson.** Ask what your security check does when its input is missing. If it fails to "no rows" rather than an exception, absence of data becomes a plausible-looking answer and no alarm will ever sound. Prefer designs where a missing security context raises; where you cannot, assert in tests that real rows come back, not merely that nothing crashed.

`GOTCHAS.md:109-118 (SW-ADR-136)`

---

### The architecture document specified the login sequence backwards — authentication that could never succeed

**Believed.** The published sequence in `03_security_isolation.md` read: look up the session row to discover which user is making the request, then set `app.user_id` from it. A natural order — you must know the user before you can announce them.

**Actually.** The sessions table is itself protected by the same row-level security rule. So the lookup runs UNDER the policy, and with `app.user_id` not yet set the policy matches nothing. The lookup returns zero rows for every request ever made. Implemented as written, nobody could ever log in, and there would be no error to read — just a permanently unauthenticated application. The order has to be reversed: set the value first, then look up the session.

**Caught by.** Caught by reading the architecture document against the security model before any code was written from it; recorded in GOTCHAS.md:119-121 as a correction to the published diagram.

> **Lesson.** A numbered sequence in a design document is code that has not been typed yet, and it deserves the same scrutiny. Watch specifically for a step that needs a permission an earlier step is supposed to grant — and for a security rule applied to the very table you use to work out who the user is. That chicken-and-egg is invisible when you read either piece on its own.

`GOTCHAS.md:119-121 (docs/07 Architecture/for_llm/03_security_isolation.md)`

---

### An owner filter in WHERE turned a LEFT JOIN into an INNER JOIN and deleted the zero-spend days

**Believed.** The day-by-day chart query generates one row per calendar day and attaches matching expenses. Whether the "only this person's expenses" condition sits in the join's `ON` clause or in the `WHERE` clause makes no difference.

**Actually.** A LEFT JOIN keeps every generated day even when no expense matches it — but on those kept rows the expense columns are NULL, so `WHERE e.user_id = :uid` throws them away. The LEFT JOIN collapses into an ordinary INNER JOIN: days with zero spending vanish and the series shortens from 31 rows to only the days that had spending. The total and the daily average stay correct, because the rows that disappeared contributed nothing to either.

**Caught by.** Exactly one test in the whole suite would have caught it: SIT-E0-S9-05, "the day series contains 31 rows, including days with zero spending" (docs/08 SIT/SIT_TestCases.tsv:48). Every other test stays green, so without that single row-counting assertion this ships as a chart that is subtly missing days.

> **Lesson.** In a LEFT JOIN, a condition on the optional table belongs in `ON`; put it in `WHERE` and you have silently cancelled the LEFT. More generally: when a defect shows up as missing rows rather than wrong values, only a test that counts rows can catch it — so write the count assertion, not just the value assertion.

`GOTCHAS.md:123-128; app/modules/expenses/repository.py:94; docs/08 SIT/SIT_TestCases.tsv:48`

---

### Three admin GET endpoints each perform a write, so they cannot be cached or moved to a read replica

**Believed.** `/api/admin/users`, `/api/admin/sessions` and `/api/admin/audit` are GET requests. GETs are reads, so the standard speedups apply: serve them from a read-only database connection, a read replica, or a cache.

**Actually.** Each of the three inserts one row into the admin audit log on EVERY request, in the same transaction as the read, and the response is only serialised after the database commits. On a read-only connection the INSERT fails outright. On a replica the write and the read cannot be made atomic across machines. From a cache the request never reaches the database at all — so an administrator views user data with no record that they viewed it, breaking the requirement in SRC-001 §10.8. An empty result still has to be audited, because the admin still looked.

**Caught by.** Caught in design review and written down (SW-ADR-135) precisely because the optimisation is so tempting and the breakage is invisible: a cached response is byte-for-byte identical to a real one, so no test anywhere would go red.

> **Lesson.** The HTTP verb tells you nothing about what a handler actually does. Before treating any endpoint as a read, look at what it writes — audit rows, counters, last-seen stamps — because those side effects are exactly what caching and read replicas throw away, silently and by design.

`GOTCHAS.md:92-107 (SW-ADR-135, SRC-001 §10.8)`

---

### Re-running the ledger generator wipes the hand-edited build status its own header seems to promise to keep

**Believed.** The generator's header says the engineering ledger is derived and that "exactly one column is hand-edited: Status". That reads as a promise: Status is yours, regeneration will preserve it.

**Actually.** It is not preserved. `main()` copies `Status` straight from the Bible row and rewrites `EvidencePath` to the literal string `evidence/{ID}/`. So a single regeneration silently resets the entire record of what has actually been built back to whatever the Bible claims, and deletes every note explaining why a story sits where it does.

**Caught by.** Found by reading the generator source (docs/10 EngineeringLedger/generate_ledger.py:80). Nothing automated would have caught it: this ledger is the one derived artifact NOT in consistency_check.py's regenerate-and-compare list, so the check that verifies every other generated file leaves this one unguarded. The standing fix is to hand-edit the ledger and sync single rows, never to regenerate.

> **Lesson.** When two files hold the same column, one of them is being overwritten — decide which direction truth flows and say it in words that cannot be misread ("hand-edited" is not the same promise as "preserved"). Better still, make the generator refuse to clobber rather than documenting that it will.

`GOTCHAS.md:150-162; docs/10 EngineeringLedger/generate_ledger.py:80`

---

### The login rate limiter behind a load balancer rate-limits the load balancer

**Believed.** slowapi's per-IP limit stops one attacker hammering the login endpoint, because each client gets its own budget of attempts.

**Actually.** slowapi's default key is `request.client.host` — the address of whoever opened the TCP connection. Behind a load balancer or proxy that is always the proxy's own address, identical for every user on earth. So everyone shares one bucket: an attacker's traffic is hidden among everybody else's, and ordinary users get locked out by strangers. The limiter still returns 429 responses, so it looks like it is working while protecting nothing.

**Caught by.** One of the two false rate-limiter premises inherited from the requirements dump; found by checking slowapi's actual default before building on it. The fix is to run uvicorn with `--proxy-headers --forwarded-allow-ips=<the proxy's subnet>` so the forwarded client address is trusted and used.

> **Lesson.** A security control that produces plausible output is more dangerous than one that is simply absent, because it stops anyone asking. For any rate limit, quota or lockout, ask what value it keys on and whether that value still distinguishes one user from another after the request has passed through your infrastructure.

`GOTCHAS.md:40-43`

---

### bcrypt silently cuts passwords at 72 bytes, and cost 12 freezes the whole worker

**Believed.** Hashing passwords with bcrypt at cost factor 12 inside the async login handler is both secure and fine for performance, and longer passwords are simply stronger.

**Actually.** Two separate problems. First, bcrypt ignores everything past the 72nd byte of a password without any warning, so two different long passwords can unlock the same account and nothing reports it. Second, cost 12 is roughly 300 milliseconds of pure processor work; performed inside an `async def` handler it blocks the event loop, so every other request being served by that worker simply stops until it finishes. On a 0.25-vCPU container a handful of simultaneous logins is a visible outage.

**Caught by.** Recorded in the trap ledger before the authentication module was written. The fixes: run the hash via `asyncio.to_thread` so it happens off the event loop, and explicitly reject or pre-hash passwords longer than 72 bytes rather than letting the library quietly discard the remainder.

> **Lesson.** Writing `async def` does not make processor work asynchronous — it only yields at an `await`, so any long computation inside one stalls everything sharing that worker. And a library that truncates instead of raising turns a security property into a silent one: find the limits your dependencies impose and enforce them yourself at the boundary.

`GOTCHAS.md:49-52`

---

### Three admin powers returned a believable answer and did nothing

**Believed.** A PostgreSQL function marked SECURITY DEFINER — meaning it runs with the permissions of whoever created it rather than whoever calls it — would let an administrator count another person's expenses, list who is signed in, and force someone out, even though row-level security normally hides other people's rows.

**Actually.** SECURITY DEFINER only changes which database role runs the function. It does not exempt that role from row-filtering rules, and this project had deliberately switched on FORCE ROW LEVEL SECURITY, which applies the rules to the table's owner too. The rules key on a per-transaction setting holding the caller's user id, so the function saw exactly what the calling admin could already see. Counting someone's expenses returned (0, NULL). 'Who is signed in' returned an empty list, reading as 'nobody is signed in'. Force-sign-out updated zero rows, returned 200 OK, wrote an audit entry saying 'signed user #2 out of 0 session(s)', and left the session live.

**Caught by.** Nothing went red — row-level security filters rows, it never raises an error. A human opened the admin dashboard during the M4 build and saw '0 expenses' against every account. By then the function had been written, generated, migrated and shipped in that state.

> **Lesson.** When a permission system hides rows instead of refusing the request, a privilege you do not actually hold fails silently and successfully. Every capability that crosses a person boundary needs a test asserting a non-empty, non-zero result for a different user — asserting the shape of the response proves nothing, because the shape is correct either way.

`docs/01 ADR/all-ADRs/SW-ADR-149.md`

---

### A database rule meant to allow 'counts only' handed over every column

**Believed.** Adding a row-level security policy on the expenses table for admin connections would give administrators counts without amounts or descriptions. The specification described it as 'aggregate reads only' and claimed the privacy promise was structurally true.

**Actually.** A row-level security policy is exactly that: row-level. It has no column dimension. The generated SQL was an unqualified permissive policy, and permissive policies are combined with OR, so any connection with the admin flag set could read every column of every row — amount and description included. The decision was not implementable in the form it specified.

**Caught by.** A reviewer with no prior context, reading the generated security.sql during the exit gate. The decision record states plainly that no test in the plan could have caught it: every test asserts on the API response shape, and the API would have kept returning the right fields from a query that was permitted to read everything.

> **Lesson.** Check that the mechanism can express the rule before trusting the rule. 'Aggregate only' is a shape a function's return type can enforce and a row policy cannot. And a test suite that only inspects outputs is blind to a query holding more permission than it uses.

`docs/01 ADR/all-ADRs/SW-ADR-129.md`

---

### The app started rewriting its users' own email addresses in capitals

**Believed.** Adding the .entry-meta class to the list that receives the uppercase monospace micro-label style was a purely visual change.

**Actually.** .entry-meta is not a label class. It renders a person's own category name, their email address in the sidebar and in the admin table, the days-elapsed figure the day-one gate reads, and every chart caption. An address stored as a@spendwise.test was displayed as A@SPENDWISE.TEST, and a category someone typed as Coffee came back as COFFEE. The application had started editing its users' own data.

**Caught by.** Six browser criteria, including the day-one gate, because they assert the exact stored string. A screenshot review would never have caught it — uppercase looks like a deliberate design choice.

> **Lesson.** A styling rule that transforms text is editing content, not presenting it. Only tests that assert the exact string a person entered can tell a style apart from a corruption.

`client/src/styles/app.swiss.css:40-47`

---

### The written sign-in sequence would have failed for every request ever made

**Believed.** The security design document's order of operations for looking up a session was correct.

**Actually.** The sessions table is protected by a rule keyed on a per-transaction setting holding the user's id. The document showed the session lookup running before that setting is written, so the setting was empty, the rule matched nothing, and the lookup returned zero rows. Authentication would never have succeeded for anyone, and nothing would have raised an error. A second problem sat in the same place: no document named which field of the token carried the user id, so there was no value to set even if the order had been right.

**Caught by.** A zero-context agent asked to plan one end-to-end slice. Four separate document review passes over the same material had missed it, because it is invisible until somebody tries to build.

> **Lesson.** Order matters when a query depends on state the same transaction must set first — and a filtering rule with nothing to match returns an empty result, not an error. Empty and denied look identical, so walk the sequence literally rather than reading it for intent.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md:56-58; GOTCHAS.md`

---

### Every screenshot in the evidence folder showed fonts the application never loaded

**Believed.** The design system's named typefaces were what the application rendered, and the screenshots kept as evidence showed the real product.

**Actually.** There was no @font-face rule anywhere in the repository. The font families were named in CSS and never loaded, so every browser fell back to whatever it had installed — meaning every screenshot under evidence/ predating 2026-08-21 shows operating-system fallbacks. Separately, the rupee sign lives in the latin-ext character subset rather than latin, so the incoming design bundle's one-file-per-family setup would have drawn every rupee sign from a fallback font sitting next to digits from the intended one, in an application whose whole job is columns of money.

**Caught by.** Reading the incoming design bundle's font configuration closely enough to check which character subset the currency symbol belongs to. That check led to the discovery that no font was being loaded at all.

> **Lesson.** Visual evidence proves what the machine that captured it could render, not what the design specifies. And when fonts are split into subsets, verify that every character you actually display is in a subset you ship.

`handoffs/HANDOFF_2026-08-21_1605_aniruddha-jathar.md:38-43`

---

### Three admin actions returned HTTP 200 while doing nothing at all

**Believed.** Marking a database function `SECURITY DEFINER` (run it with the privileges of whoever created it rather than whoever calls it) was believed to let admin features step around row-level security and read other people's rows.

**Actually.** `SECURITY DEFINER` changes which role runs the function; it does not exempt that role from row policies, and `FORCE ROW LEVEL SECURITY` deliberately subjects even the table's owner to them. So counting a person's expenses returned `(0, NULL)`; listing who is signed in returned `[]`; and force-sign-out matched zero rows, returned 200, and wrote an audit entry reading "signed user #2 out of 0 session(s)".

**Caught by.** Running the features against a real database after they had already passed review. Nothing raised an error — row-level security filters, it does not refuse — so every response was a success response with an empty body.

> **Lesson.** A privilege you cannot exercise fails silently and successfully. Any feature that deliberately crosses from one user's data to another's needs a test asserting a non-empty, non-zero result for a different user; asserting "no error" proves nothing.

`SW-ADR-149; HANDOFF_2026-08-06_0442_ani87.md`

---

### Every screenshot of evidence showed fonts the product had never loaded

**Believed.** The app had been using its specified typefaces since the design system was written, and the client's new bundle shipped one web font file per family, which looked complete.

**Actually.** Two things were wrong. There was no `@font-face` rule anywhere in the repository before that day — the families were named in CSS and never loaded — so every screenshot filed under evidence/ up to that point shows the operating system's fallback fonts, not the product's. And the rupee sign ₹ (U+20B9) lives in the `latin-ext` character subset, not `latin`, so the bundle's single file per family would have drawn every rupee sign from a fallback font sitting right beside digits from JetBrains Mono — in an app whose entire job is columns of money.

**Caught by.** Checking the bundle's font files against the specific characters the app renders, while wiring up the first real `@font-face` rules. Six font files now ship, two subsets per family, with their licences alongside.

> **Lesson.** Naming a font is not loading it, and a font that loaded is not a font that covers your characters. Verify the specific glyphs your product depends on, and treat a screenshot as evidence only of what was actually rendered, never of what was specified.

`HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### The rate limiter ran after the database connection it was meant to protect

**Believed.** Once rate limiting was added to the auth endpoints, a throttled request was believed to be refused cheaply, before it could consume server resources.

**Actually.** The limiter was declared as a parameter on the endpoint function, sitting after the database session in the signature. FastAPI resolves dependencies in declaration order, so every request that was about to be refused first checked out a database connection. A brute-force attempt still drained the connection pool; the limiter protected the login logic and nothing else.

**Caught by.** An acceptance test that counted how many times the database stub was reached — 10 times across 11 attempts — rather than only checking status codes. Fixed by moving the limiter to route-level `dependencies=[...]`, the same shape the admin guard already used.

> **Lesson.** In a dependency-injection framework, declaration order is execution order. Declare a guard before the resource it guards, and write the test to count the resource's use, not the response code.

`app/core/ratelimit.py; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### A stylesheet rule uppercased users' own email addresses and category names

**Believed.** A restyle added a list of CSS classes to render as uppercase monospace micro-labels, and `.entry-meta` was put in that list as though it were one of them.

**Actually.** `.entry-meta` renders users' own content: their category names, their email address in the navigation rail and the admin table, the days-elapsed figure the day-one gate reads, and every chart caption. An address stored as a@spendwise.test was displayed as A@SPENDWISE.TEST; a category typed as "Coffee" came back as "COFFEE". The app had started visibly editing what people had written.

**Caught by.** Six browser acceptance criteria that assert the exact stored string, including the day-one gate's. The handoff notes it would never have surfaced in a screenshot review, because A@SPENDWISE.TEST reads as a deliberate design choice.

> **Lesson.** Styling that transforms text is indistinguishable from corrupted data to the person reading the screen. Keep presentational transforms off any class that can carry user-entered content, and assert exact strings rather than "contains".

`client/src/styles/app.swiss.css:40-41; HANDOFF_2026-09-01_1302_aniruddha-jathar.md`

---

### An architecture document specified an order that means authentication can never succeed

**Believed.** The security architecture document showed the per-request sequence as: look up the session, then set the database variable that tells row-level security who the current user is.

**Actually.** That order is backwards. The session lookup itself runs under a row policy, so with the variable not yet set it returns zero rows — for every request ever made. Built as written, it is authentication that can never succeed. The surrounding trap is worse: the variable is set with a transaction-scoped call, so any repository that opens a second transaction loses it, and every protected query then returns zero rows instead of raising an error.

**Caught by.** The document review rounds, before any code was written from it. The failure mode is why it matters: an empty dashboard is indistinguishable from a person who has spent nothing, so nothing would have gone red.

> **Lesson.** When a security mechanism's failure mode is "returns nothing" rather than "raises", ordering mistakes become invisible. Set the identity as the first statement of the single request transaction, and write a test that asserts a non-empty result rather than a lack of errors.

`GOTCHAS.md:109-121; SW-ADR-136; SW-ADR-144`

---

### An outer join filtered in the wrong clause, and the zero-spend days quietly disappeared

**Believed.** Filtering the day-by-day spending series by owner in the WHERE clause is equivalent to filtering it in the join's ON clause.

**Actually.** The series is a generated list of dates LEFT JOINed to expenses. Putting the owner test in WHERE discards the placeholder rows the outer join created for empty days, collapsing it into an inner join: days with zero spending vanish and the chart silently shortens. Totals and averages remain correct, so every test but one still passes.

**Caught by.** A single acceptance case that asserts the shape of the series rather than its totals. The handoff lists it among traps that had already cost a full review round.

> **Lesson.** An outer join's filter belongs in ON; the same condition in WHERE cancels the outer join. More generally, when a bug removes rows rather than corrupting them, only a test asserting the expected row count will ever see it.

`GOTCHAS.md:123-128`

---

### Three admin powers returned 0, [], and 200 OK — and none of them worked

**Believed.** A Postgres `SECURITY DEFINER` function — one that runs as the role that created it rather than the role that called it — would let an administrator count another person's expenses, list their live sessions, and force them signed out.

**Actually.** The project had turned on `FORCE ROW LEVEL SECURITY`, which makes Postgres apply its per-row access rules to the table's owner as well. `SECURITY DEFINER` only changes *which* role runs the query; it does not exempt that role from the rules. The rules filter on a per-connection setting (`app.user_id`) that still held the *caller's* id, so the function saw exactly what the admin could already see: their own rows. The count came back `(0, NULL)` for every other account, the session list came back empty (reading as 'nobody is signed in'), and the forced sign-out matched zero rows and reported success — the audit log recorded 'signed user #2 out of 0 session(s)' while that person's session stayed live.

**Caught by.** Not by a test. `admin_expense_stats` had been written, generated, migrated and shipped in that state. A human building the admin dashboard noticed it showed 0 expenses for every account except the one they were signed in as. Every test passed, because every test asserted the *shape* of the response, and the shape was correct.

> **Lesson.** Row-level filtering does not raise an error — it just returns fewer rows. A permission you do not actually hold therefore fails silently and looks like success. Every capability that crosses a person boundary needs a test asserting a non-empty, non-zero result for a *different* user than the caller; asserting the response shape proves nothing, because the shape is right either way.

`docs/01 ADR/all-ADRs/SW-ADR-149.md`

---

### Authentication, as specified, could never have succeeded for anybody

**Believed.** The architecture document laid out the login sequence — verify the token signature, look up the session row, check revocation and expiry, then set the per-connection `app.user_id` that the database's per-row rules read, then query. It had a diagram.

**Actually.** The `sessions` table is itself protected by those per-row rules, keyed on `app.user_id`. At the moment of the session lookup that value is unset, so the rule evaluates to NULL rather than true and the lookup returns zero rows — for every request ever made. And the value could not have been set earlier: no document specified a token claim carrying the user's id, so there was nothing to put in it. A genuine chicken-and-egg deadlock, not an ordering preference.

**Caught by.** Two people reading the document set cold, three hours apart, reached the same conclusion independently — and both had to invent a token claim name to get past it. Fixed by adding a `sub` claim and making `set_config` the first statement of the request transaction.

> **Lesson.** A diagram makes an order look considered. If a lookup runs under the very access rule it is supposed to establish, you have a bootstrap deadlock — and the symptom is zero rows, not an error. Trace the first statement of a request by hand.

`docs/01 ADR/all-ADRs/SW-ADR-136.md`

---

### 'Admins can see counts only' was implemented as a rule that returns every column

**Believed.** An extra Postgres row-level security policy on the expenses table, 'consulted only when the admin flag is set, permitting aggregate reads only', would let an administrator count someone's expenses without ever seeing amounts or descriptions. The generated `security.sql` implemented it.

**Actually.** A row-level security policy is exactly that — row level. It has no column dimension; you cannot express 'this role may read this table but only these columns' as a policy. `FOR SELECT USING (current_setting('app.is_admin') = 'true')` is an unconditional permissive rule that returns **every column of every row**, amounts and descriptions included. The decision was not implementable in the form it was specified, and shipping it would have made the client's stated privacy value false at the database while a specification claimed it was 'structurally true'.

**Caught by.** A cold reader planning the admin slice. The record states plainly that no stated test would have caught it: every test asserts on the API response shape, and the API would have kept returning exactly the right fields from a query that was allowed to read everything.

> **Lesson.** Before writing a control down as done, confirm the mechanism you picked can actually express it. Here the working construct was a function rather than a policy, because a function has a return type: `RETURNS TABLE (expense_count, last_activity)` makes an amount unable to come back at all, whereas a policy merely makes it unasked-for.

`docs/01 ADR/all-ADRs/SW-ADR-129.md (superseding SW-ADR-077)`

---

### The dashboard's category breakdown was not guaranteed to sum to its own headline total

**Believed.** The summary endpoint returns a headline total and a per-category breakdown, and four documents assert unconditionally that the breakdown sums exactly to the headline. The tests passed.

**Actually.** The original requirement was one round trip for the browser; that was satisfied by splitting the work into three SQL statements, and nothing re-established atomicity. Under Postgres's default READ COMMITTED isolation each statement takes a fresh snapshot, so an expense inserted between the headline query and the breakdown query makes the two disagree.

**Caught by.** The fifth cold-reader run, by reasoning rather than by a failure. The record spells out why nothing else would have: it is invisible in every single-user test and fails only in production, intermittently, on the one number the product exists to show.

> **Lesson.** Splitting one logical read into several statements quietly drops the guarantee that they see the same data. Bugs of this shape are unreachable by tests that run one user at a time — you either reason about them or force a single snapshot. 'One round trip for the browser' is a request about HTTP, not a licence to make three independent queries.

`docs/01 ADR/all-ADRs/SW-ADR-142.md (Decision F)`

---

### Three typefaces were specified, documented, screenshotted — and never actually loaded

**Believed.** The app rendered in Bricolage Grotesque, DM Sans and JetBrains Mono. The design system named them, the CSS variables named them, and the evidence screenshots showed the result.

**Actually.** There was no `@font-face` rule and no font file anywhere under `client/`. A CDN had been ruled out earlier, so the families were always meant to be self-hosted, and nobody ever did the hosting. Every browser fell back to system fonts throughout — including in every screenshot filed under `evidence/`.

**Caught by.** A later design change that went looking for the font files. Six woff2 files (168 KB) were then added. A second trap surfaced in the same pass: the rupee sign ₹ (U+20B9) lives in the `latin-ext` subset, not `latin`, so the obvious latin-only build would have rendered every rupee sign from a fallback font next to digits from JetBrains Mono — in an application about columns of money.

> **Lesson.** Naming a font is not loading a font, and the failure mode is a page that looks fine. Anything that silently falls back — fonts, locales, character subsets, feature flags — needs a check that asserts the intended thing is in use, not merely configured. Screenshots are evidence of what rendered, not of what you specified.

`docs/01 ADR/all-ADRs/SW-ADR-152.md (section 'The fonts were never loaded, and now are'); client/public/fonts/`

---

### Data migrations would have reported success and changed nothing

**Believed.** `FORCE ROW LEVEL SECURITY` plus a separate table-owning migration role was a safe arrangement: the owner runs migrations, the restricted runtime role serves requests.

**Actually.** `FORCE ROW LEVEL SECURITY` subjects the table *owner* to the policies too. So any data migration — a backfill, or the currency column an erratum adds to existing rows — runs with the per-request user id unset and either errors or silently affects zero rows. The silent branch is the dangerous one: the migration reports success, the migration chain advances past it, and the data is untouched.

**Caught by.** The adversarial review of the design documents (QA FINDING-16), before any migration ran. Fixed with `SET LOCAL row_security = off` on the migration connection only — the migration role may do that because it owns the tables; the runtime role cannot, because it lacks BYPASSRLS.

> **Lesson.** 'Zero rows affected' is a success in SQL. Any bulk operation running under row-filtering rules should assert how many rows it expected to touch. Note also that the record that created this hazard had itself warned about 'a collapse that could happen without anything turning red' — and the hazard was reachable straight through its own design.

`docs/01 ADR/all-ADRs/SW-ADR-081.md (superseding SW-ADR-044)`

---

### Three admin features ran, returned 200, and did nothing at all

**Believed.** A PostgreSQL function marked SECURITY DEFINER (meaning it runs with the permissions of whoever created it, not whoever calls it) would let an admin read across the privacy wall that normally keeps each person's rows to themselves. Counting someone's expenses, listing who is signed in, and forcing a sign-out were all built on that assumption, reviewed, generated, migrated and shipped.

**Actually.** SECURITY DEFINER changes which database role runs the function. It does not exempt that role from the row-filtering rules, and this project deliberately turned on FORCE ROW LEVEL SECURITY, which applies those rules to the table's own owner too. The rules key off a setting holding the CALLER's user id, which the function never changed. So the function saw exactly what the admin could already see: counting another person's expenses returned (0, NULL); 'who is signed in' returned an empty list, which reads as 'nobody'; and force-sign-out ran an UPDATE that matched zero rows, raised nothing, returned HTTP 200, wrote an audit entry reading 'signed user #2 out of 0 session(s)', and left the session live.

**Caught by.** Not by any test — every test asserted on the shape of the API response, and the shape was correct. It was caught by a human opening the admin dashboard and seeing 0 expenses for every account except their own. It had already passed review and been migrated into the database.

> **Lesson.** Row-filtering security does not raise errors, it removes rows. So a permission you cannot actually exercise fails silently AND successfully: empty results and zero-row updates both look like a healthy answer. Any feature that reads or writes across an isolation boundary needs a test asserting a non-empty, non-zero result for a DIFFERENT user than the caller — never just 'the endpoint returned 200'.

`docs/01 ADR/all-ADRs/SW-ADR-149.md`

---

### The container shipped without a file the error handler reads, so errors could not describe themselves

**Believed.** The first real deployment was healthy: the container built, started, and its health endpoint answered HTTP 200. Continuous integration was green.

**Actually.** The build configuration excludes the docs/ folder, but two modules read a specification file out of it at runtime — the error-code table in app/core/errors.py and the seeded category list in the categories service — deliberately, so code and specification cannot drift apart. Nothing copied that file back into the image. Every error path raised FileNotFoundError INSIDE the handler whose job is formatting errors, so the resulting 500 could not even say what went wrong. The health endpoint touches none of that, and the smoke test polls only the health endpoint, so it stayed green.

**Caught by.** The real deployment, by hitting an error path. Afterwards a test was written that scans app/ for any code path reading a file under docs/, and fails unless every such path is both copied into the image and re-included in the ignore file.

> **Lesson.** A health check that only proves the process is listening proves the process is listening. Know which files your code reads at runtime, and check they survive packaging — import-time checks cannot see a file opened later. Write the guard against the PATTERN (any runtime read of an excluded folder), not against the one file you just found, so the next module that does it is caught on the commit that adds it.

`tests/test_container.py:235`

---

### A styling rule quietly rewrote what users had typed

**Believed.** A visual restyle added a CSS class to the list of 'mono uppercase micro-label' styles, alongside genuine labels. Purely cosmetic, no code changed.

**Actually.** That class was not a label class. It renders people's own category names, their email address in the sidebar and in the admin table, the days-elapsed figure the day-one gate reads, and every chart caption. An address stored as a@spendwise.test was DISPLAYED as A@SPENDWISE.TEST; a category the person typed as 'Coffee' came back as 'COFFEE'. The application had started editing its users' own data on screen.

**Caught by.** Six browser test criteria, including the day-one gate's, which assert the exact stored string. The handover notes explicitly that this would never have been caught in a screenshot review — A@SPENDWISE.TEST looks like a deliberate design choice.

> **Lesson.** Text transforms applied by class are a blunt instrument: check what actually carries that class, not what it is named after. And a whole category of defect — the product altering user-supplied content — is invisible to human visual review because the wrong output looks intentional. Only an assertion against the exact stored value exposes it.

`handoffs/HANDOFF_2026-09-01_1302_aniruddha-jathar.md:94`

---

### The three chosen typefaces were never actually loaded, and every screenshot recorded it

**Believed.** The design specified three font families by name, and an earlier decision had ruled out loading them from an external service, so they were to be self-hosted. The design system, the token file and the screenshots archive all treated the typography as shipped.

**Actually.** There was no @font-face rule and no font file anywhere under client/. The families were named in the stylesheet and never fetched, so the application rendered operating-system fallback fonts throughout. Every screenshot in the evidence folder predating the fix shows a design nobody chose. A related trap sat beside it: the supplied font snippet ships one file per family, which is the 'latin' subset — and the rupee sign is in 'latin-ext', not 'latin'. Followed literally it would have drawn every ₹ from a fallback font next to digits from the intended one, in an application whose entire subject is columns of money.

**Caught by.** Reading the repository during an unrelated restyle. Nothing failed — naming a font you have not loaded produces a page that renders perfectly in the wrong typeface. The rupee issue was caught by running it and measuring in the browser: ₹ is 20.00px in the intended font against 21.99px in the fallback.

> **Lesson.** Declaring a resource is not loading it, and a missing font degrades into something that looks fine. Verify in the browser that the face is actually in use. And when you subset fonts, check that every character your product actually prints is inside the ranges you shipped — currency symbols in particular are scattered across subsets in ways that are easy to get wrong.

`docs/15 ChangeRequest/CR-002_visual-identity.md, sections 'The second defect' and 'A standing fact this change corrected'`

---

### The architecture document showed the two authentication steps in the order that never authenticates anyone

**Believed.** The sequence for identifying a request looked interchangeable: look up the session row, and set the database setting holding the user id. A published architecture document showed them in that order.

**Actually.** The sessions table is protected by a rule keyed on that setting, and the setting is scoped to the current transaction. Look up the session BEFORE setting it and the setting is absent, the rule's condition evaluates to unknown, and the lookup returns zero rows — for every request ever made. Authentication that never succeeds, with no error to explain it. The same hazard has a second form: if any repository opens a SECOND transaction, the setting is gone there too, and every protected query returns zero rows instead of raising.

**Caught by.** Caught by review of the architecture document against the security rules, before it became code; the correct order is now pinned in a module docstring and the session factory raises rather than quietly handing back a second session.

> **Lesson.** Filtering rules fail by returning nothing, not by raising, so an ordering mistake produces an empty result rather than an error — and an empty dashboard is indistinguishable from a person who has spent nothing. When a setting is transaction-scoped, make setting it the first statement of the transaction, and make a second transaction per request impossible by construction rather than by convention.

`app/core/deps.py:6, and GOTCHAS.md:109`

---

### The documented login sequence would have returned zero rows for every request ever made

**Believed.** The order of the two steps at the start of a request — look up the session row named by the cookie, and set the database variable holding the current user's id — was a matter of preference.

**Actually.** The sessions table has forced row-level security with a policy keyed on that variable. At the moment of the lookup the variable is unset, so the policy's lookup evaluates to NULL and the query matches zero rows — every time, for every user, forever. Nobody could ever have logged in. And no document named a claim inside the login token that carried the user id, so there was nothing to set the variable from in the first place: a genuine chicken-and-egg deadlock, not an ordering nit.

**Caught by.** The second fresh-engineer run. Four earlier review passes over the same documents had found 21 contradictions between documents and missed this one entirely, because it is invisible until somebody traces a real request through the system.

> **Lesson.** Row-level security filters; it does not raise. A missing identity produces an empty result, not an error, so the failure looks exactly like "this person has no data". Trace one complete request end to end, naming every value and where it comes from, before believing a security design.

`docs/07 Architecture/for_llm/03_security_isolation.md · SW-ADR-136 · 03_CONFLICT_MAP.tsv row S2-C9 · GOTCHAS.md:109-121`

---

### Filling in a bookkeeping field silently withdrew the decision every primary key rests on

**Believed.** The decision "every table uses a BIGINT identity primary key" was live, and it was cited fourteen times across the corpus as current authority.

**Actually.** A later record exists only to label six other records as "reasoned, not observed". Someone put the first of those six into its Supersedes field, and the tooling that reads that field flipped the primary-key decision to SUPERSEDED in the decision ledger. A decision that nothing replaced had been withdrawn as a side effect of filing, and every schema in the project rested on it.

**Caught by.** A topic-coherence audit of all 22 supersession links at the exit gate. The check that already existed proved all 931 references resolved to files that exist — it had no opinion whatsoever on what those files were about.

> **Lesson.** Metadata fields drive automation, so a metadata field is a claim, and claims need checking. "This record replaces that one" should fail review when the two share no subject.

`docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv · SW-ADR-088 vs SW-ADR-023 · SW-ADR-132 · 02_ROOT_CAUSE_REGISTER.tsv row RC-4`

---

### A dashboard whose parts could disagree with its own total, but only when two people act at once

**Believed.** The summary endpoint returns a consistent picture: the headline total and the per-category breakdown arrive in the same response, so they must agree.

**Actually.** The requirements asked for one network round trip; a decision satisfied that by splitting the work into three separate SQL queries, and nothing re-established that the three see the same data. At PostgreSQL's default isolation level, an expense inserted between the headline query and the breakdown query makes the categories fail to sum to the total.

**Caught by.** The fifth fresh-engineer run, purely by reasoning about two requests happening at once. It is invisible in every test in the suite, because every test in the suite has one user doing one thing at a time.

> **Lesson.** "One request" is not "one transaction". If a response is assembled from several queries and a reader will add them up, they need a single snapshot. Faults that require two actors at once will never surface in a test suite that only ever has one.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md (slice 5) · SRC-001 §7.4 · SW-ADR-142 F`

---

### Three admin features returned plausible answers and did nothing at all

**Believed.** Wrapping the admin queries in a SECURITY DEFINER function — one that runs with the privileges of whoever defined it, here the table owner — let an admin see across accounts.

**Actually.** Forced row-level security applies to the table owner too, and the policies key on the current user's id, which is still the *caller's*. So the function ran as the owner and saw exactly what the admin could already see. Counting another person's expenses returned (0, NULL). Listing their sessions returned an empty list, which reads as "nobody is signed in". Force-sign-out ran an UPDATE that matched zero rows, returned HTTP 200, and wrote an audit entry saying "signed user #2 out of 0 session(s)" while the session stayed live.

**Caught by.** Actually running the admin dashboard and noticing every account but the caller's reported zero expenses. The code had been written, generated, migrated, shipped and reviewed by eye in that state.

> **Lesson.** SECURITY DEFINER changes which role runs the query, not which rows the policies permit. In a system built on row-level security, a privilege you cannot exercise fails silently *and successfully* — so every cross-account feature needs a test asserting a non-empty, non-zero result for a *different* user than the one calling.

`docs/01 ADR/all-ADRs/SW-ADR-149.md · docs/06 DataModel/security.sql:86-108`

---

### A styling rule quietly rewrote people's email addresses on screen

**Believed.** A restyle added the `.entry-meta` class to the list of label classes that get small uppercase lettering, on the assumption it was a label class.

**Actually.** It is not. It renders a person's own category names, their email address in the side rail and in the admin table, the days-elapsed figure the day-one proof reads, and every chart caption. An address stored as `a@spendwise.test` was being displayed as `A@SPENDWISE.TEST`. The application had started editing its users' own data.

**Caught by.** An acceptance criterion that asserts the exact stored string appears on screen. It would never have surfaced in a screenshot review, because uppercase reads as a design choice rather than a defect.

> **Lesson.** Presentation rules that transform text — uppercase, title-case, truncation — are data changes wherever they land on user-entered content. Scope them by what the text means, not by what is convenient to select, and keep at least one test asserting an exact stored value rather than a case-insensitive or partial match.

`client/src/styles/app.swiss.css:36-46 · PROGRESS.md, session 2026-09-01`

---

### Regenerating the progress ledger would silently revert the entire build frontier

**Believed.** The ledger's own header says it is a derived file and that "exactly one column is hand-edited: Status" — which reads as a promise that Status survives regeneration.

**Actually.** The generator copies Status straight from the upstream story file and rewrites the evidence path to a literal template. Re-running it destroys every hand-edited status and every note recording why a story is where it is, reverting the recorded build progress to whatever the story document happens to say.

**Caught by.** Reading the generator before running it. Nothing would have caught it afterwards: the ledger is the one derived artifact not in the consistency checker's regenerate-and-compare list, which is exactly what makes running the generator both tempting and expensive.

> **Lesson.** "Derived" and "hand-edited" in the same file is a data-loss bug waiting for someone to run the obvious command. If a human authors one column, the generator must read that column back — and the round trip has to be tested, or the header is a comment rather than a guarantee.

`docs/10 EngineeringLedger/generate_ledger.py · GOTCHAS.md:150-165`

---

### Moving one condition from ON to WHERE deleted the empty days from the chart

**Believed.** In the query that builds the daily spending chart — a generated series of dates left-joined to the expenses table — it makes no difference whether the owner condition sits in the join's ON clause or in the WHERE clause.

**Actually.** In the WHERE clause it turns the LEFT JOIN into an inner join: days with no spending have no matching expense row, so the owner condition is null for them and they are discarded. The chart's series silently shortens.

**Caught by.** Exactly one test, the one that asserts there is one row per calendar day. The totals and the daily average both stay correct, so every other test in the suite still passes.

> **Lesson.** In a LEFT JOIN, a condition on the optional table belongs in ON; in WHERE it throws away the very rows the join was asked to keep. Note also what saved this: a test asserting the *shape* of the result, not only its numbers.

`GOTCHAS.md:123-128 · test case SIT-E0-S9-05`

---


# The check was wrong

*The thing meant to catch errors was itself broken. These are the worst, because they consume the trust you were relying on.*

**34 recorded.**

### The confidentiality gate printed "scrub OK" for months because it could never match anything

**Believed.** The gate that scans content for confidential strings before it leaves the project reads a blocklist file line by line and compares. When it prints "scrub OK", the content is clean.

**Actually.** The blocklist file was saved with Windows line endings (a carriage return plus a newline, CRLF). Reading it line by line left an invisible carriage return stuck on the end of every entry, so no entry ever matched any text. The gate had never refused anything on Windows. A genuine pass and a completely broken check produced identical output.

**Caught by.** Caught on this project when someone asked what the gate had ever rejected and the answer turned out to be: nothing, ever. Two fixes were applied — a repository-root `.gitattributes` containing `* text=auto eol=lf` so line endings are normalised, and the practice of red-proofing every gate: plant a real violation, watch the gate fire, revert it, then verify the revert. `tools/consistency_check.py` now ships a `--selftest` that plants each violation and proves each check actually fires (tools/consistency_check.py:795-913).

> **Lesson.** A check that has never failed is not evidence of cleanliness — it is an untested code path wearing a green badge. Prove every gate can go red before you trust it green. Separately: invisible characters (carriage returns, byte-order marks, trailing spaces) break string comparisons by returning "no match" rather than an error, which is the worst way for a comparison to be wrong.

`GOTCHAS.md:74-78; tools/consistency_check.py:795-913; d:\Project\SpendWise\.gitattributes`

---

### The colour checker measured the light theme twice and reported two themes

**Believed.** tools/contrast.py measured every text-on-background colour pair in both the light and the dark theme.

**Actually.** The first version tracked a flag and switched to 'dark' on any line beginning with :root that did not contain the word 'dark'. The dark block's own selector is :root:not([data-theme="light"]) — which matches that description exactly. Every dark value landed in the light table, and the two generated tables came out byte-identical.

**Caught by.** The two rendered tables being identical. The tool now refuses to run if the two themes resolve to the same values, on the stated grounds that a checker silently measuring one theme twice is worse than no checker at all.

> **Lesson.** Classifying by what a name does not contain is fragile — one selector written defensively broke it. When a check produces two results that must differ, make the check itself assert that they differ.

`tools/contrast.py:110-116 and 150-156`

---

### The readability check looked for the letters 'rgba' and computed no ratio at all

**Believed.** A browser test enforced the rule that text on the app's translucent cards stays readable, with a contrast floor of 4.5 to 1.

**Actually.** The assertion checked whether the card's background colour string contained 'rgba' — that is, whether the surface was see-through at all. It never calculated a contrast ratio. A translucent card whose text composited down to unreadable mud would have passed it.

**Caught by.** The client's third visual revision made every surface fully opaque, which made the old assertion impossible to satisfy and forced someone to read what it actually did. The replacement reads the colours the browser painted and does the arithmetic in both themes, and was deliberately made to fail both ways — forced translucent, and forced opaque at 3.46 to 1 — before being trusted.

> **Lesson.** A check that tests a stand-in for the property instead of the property will pass for the wrong reason. 'Is it translucent' was never the requirement; 'is it readable' was.

`docs/01 ADR/all-ADRs/SW-ADR-154.md; SW-ADR-147.md amendment banner`

---

### The same failing colour was found, fixed, and left in place under a different name

**Believed.** Contrast had been checked by hand and the design system's published figures were accurate.

**Actually.** The token --sw-border-strong was #a8a29e, which measures 2.36 to 1 against the page background — below the 3 to 1 that a visible interface element needs, and the token's own stated use is focus-adjacent borders and table rules. An earlier decision had measured that exact hex, found that exact figure, and darkened it — for the Uncategorised category band. The identical value sat in the identical file doing a job with the identical floor and was never re-checked, because the checking was per-token and done by a person: somebody listed the bands, measured the bands, fixed a band. Nothing listed the borders.

**Caught by.** The first run of tools/contrast.py, once checking became a program instead of a person. The tool covers pairs nobody thought to list, which is precisely how the border surfaced.

> **Lesson.** A hand-maintained check measures what somebody remembered to list. When you fix one instance of a bad value, search for every other copy — and the durable fix for that whole class of miss is automation, not more care.

`docs/01 ADR/all-ADRs/SW-ADR-147.md`

---

### A workflow file with two identical keys parsed cleanly and was rejected outright

**Believed.** The continuous-integration workflow file was valid, because it had been parsed locally with PyYAML without error.

**Actually.** The file contained two 'image:' keys — a smoke-test job pasted below another job instead of replacing it. Duplicate keys are legal YAML and the last one wins, so PyYAML accepted the file happily. GitHub validates against a schema and refused it. The run finished in zero seconds with no jobs at all, and its display name was the file path rather than 'CI', because GitHub never got as far as reading the name field.

**Caught by.** The first push. The only signals were a zero-second run with no jobs and a run title that was a filename.

> **Lesson.** Parsing is not validating. A parser tells you the text is well formed; only a schema check tells you the document means what its consumer requires. The gap between those two is a whole class of bug.

`PROGRESS.md, session 2026-08-25; .github/workflows/ci.yml`

---

### A requirements document cited two withdrawn decisions as live authority, and would have reinstated a fixed critical bug

**Believed.** The automated consistency checker passed the business requirements document, so its citations were sound.

**Actually.** The document cited two decision records as the authority for the product's central security promise. Both had been superseded earlier in the same session. Writing the next document down the chain from one of them would have put the password-reset table back behind a row-security rule keyed on a verified user id — which is the exact defect that made account recovery impossible, reintroduced one document later.

**Caught by.** A reviewer with no prior context. The mechanical checker passed the document in both versions, because 'does this reference resolve?' and 'is the thing it points at still true?' are different questions. An adr-status check was added afterwards, and 931 references had resolved before it existed.

> **Lesson.** A reference checker that only tests whether a link resolves will certify a document built entirely on retracted decisions. Whether the target is still current has to be part of what gets checked.

`PROGRESS.md, GOAL_03 block; docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md`

---

### The session-start tool reported the truth about the wrong copy of the repository

**Believed.** The automatic start-of-session summary showed the project's current state: the newest handoff was 2026-08-06, so the Dockerfile was unwritten, rate limiting was not built, and a known input-validation bug was unfixed.

**Actually.** This checkout was five weeks and sixteen commits behind the live remote. The tool truthfully reported the newest handoff in this directory, which is not the newest that exists. All three conclusions were wrong: the Dockerfile exists, rate limits shipped and closed their milestone, and the validation bug was fixed. There were two checkouts of the project on one machine, out of sync, and the remote the tooling assumed was live returns 'Repository not found'.

**Caught by.** Comparing the local branch against the upstream remote partway through the session, after the frontier report looked implausible. Corrected in the handoff rather than dropped.

> **Lesson.** A tool that summarises local files is only as current as those files, and being truthful about stale input still yields a wrong answer. Any orientation step that decides what to work on next must first confirm the working copy matches the remote it is reasoning about.

`PROGRESS.md, session 2026-09-12; handoffs/HANDOFF_2026-09-12_1341_ani87.md`

---

### The confidentiality gate had never refused anything, and printed 'scrub OK' every time

**Believed.** The inherited method's confidentiality gate scanned content against a blocklist of forbidden terms and passed.

**Actually.** The blocklist file had Windows line endings, and the gate read it line by line without stripping them, so every entry carried a trailing carriage return and matched nothing. The gate has never refused anything on Windows — a clean result and a check that cannot fail look identical.

**Caught by.** Deliberate red-proofing: planting a violation and watching whether the gate fired. It did not. The repository-wide fix was a .gitattributes setting normalising line endings, plus a standing rule that every gate is red-proofed before its green is trusted.

> **Lesson.** A check that cannot fail looks exactly like a clean result. Before trusting any gate, plant a violation, watch it fire, revert, and verify the revert — otherwise you are reading silence and calling it safety.

`GOTCHAS.md, 'Process traps (already hit on this project)'`

---

### The contract check ran one way, so seven live routes were undocumented for weeks

**Believed.** An automated `route-contract` check was believed to keep the API contract file and the shipped code in step with each other.

**Actually.** It only verified one direction — that every documented route is served — and never the reverse. Seven routes were live in production code and completely absent from contract.json, the file the PRD's route table is generated from: PATCH /me, POST /password, POST /deactivate, DELETE /me, GET /export, GET /admin/overview, GET /admin/users/{id}/spending.

**Caught by.** By accident. New wording in an unrelated story mentioned DELETE /api/auth/me and tripped the check from the documented side, prompting an audit. A new `route-coverage` check now reads the routers' decorators statically and fails on served-but-undocumented — and also fails if it extracts zero routes.

> **Lesson.** A check comparing two lists must run in both directions, and must fail when it finds nothing to compare. A one-directional check silently permits everything on the side it never reads.

`tools/consistency_check.py; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### The contrast checker went green for a colour the application never draws

**Believed.** After the "uncategorised" category colour was darkened to clear its readability floor, `contrast.py --check` reported 3.07:1 and the issue was considered closed.

**Actually.** Three separate files held that colour and the tool read one of them. The value the browser actually paints comes from the API response — `UNCATEGORISED_COLOR` in app/modules/expenses/summary.py:23, rendered into the bar and donut charts — and it still held the old, failing value. The check was truthfully green about a colour the product never renders.

**Caught by.** Tracing what the running app paints rather than what the design files declare. Caught in the same session; the handoff calls it "the one that would have shipped". All three copies were corrected and a new `band-colour-agreement` check now fails if they ever diverge again.

> **Lesson.** A check must read the exact value the product uses. When one fact lives in several files, your check is measuring a copy — so the first thing to automate is that the copies agree.

`app/modules/expenses/summary.py:23; client/src/components/Ribbon.jsx:119; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### A colour already found failing and fixed, still failing under a second name

**Believed.** The contrast checker was green, therefore every colour pair in the design system met its readability floor.

**Actually.** `--sw-border-strong` measured 2.36:1 against a 3.0 floor. The identical hex had already been measured, found failing, and darkened once — under a different token name. The fix existed; the second user of that colour simply was not on the checker's hand-written list of pairs to measure.

**Caught by.** A later audit that recomputed the pairs from scratch. Until then the check measured only what somebody had remembered to list.

> **Lesson.** A check driven by a hand-maintained list has a hole shaped exactly like whatever was forgotten. Enumerate the population to check from the source of truth — every token actually used — rather than from memory.

`SW-ADR-147; HANDOFF_2026-08-06_0442_ani87.md`

---

### A readability check that looked for the text "rgba" instead of measuring readability

**Believed.** A browser test enforced the readability floor on the app's translucent cards by checking that the card's computed background contains `rgba` — the marker of a transparency level that had once been measured as safe.

**Actually.** It computed no contrast ratio at all and could not detect an unreadable card. It also blocked an approved restyle for the wrong reason: the new style makes every card fully opaque, so no code change could satisfy the check — passing it meant abandoning the design.

**Caught by.** The restyle, which turned the check red while the product was demonstrably readable. It was escalated rather than deleted or waived. The replacement measures painted ink-on-card contrast in the browser in both themes, and was proved to fail in both directions before being trusted: forced translucent it names the transparency, forced opaque at 3.46:1 it names the ratio.

> **Lesson.** Assert the property you care about, not a marker that used to accompany it. A proxy check both misses real failures and blocks legitimate change — and it is usually the second symptom that finally reveals the first.

`SW-ADR-154 (amending SW-ADR-147 D); HANDOFF_2026-09-01_1302_aniruddha-jathar.md`

---

### An auto-cancel rule cancelled the very CI run being waited on, twice

**Believed.** Setting `cancel-in-progress: true` on the workflow would only save runner minutes on superseded pushes, and the re-run being awaited would report a real result.

**Actually.** A later push landed on the same branch and cancelled the awaited re-run — twice. The image job's last recorded state is "cancelled", which is not a result at all, so its true state has been unverified across two handoffs; the last clean signal on it was an unrelated registry 500 error.

**Caught by.** Waiting for a verdict that never came, then reading the run status. The proposed fix is to scope cancellation so the main branch always runs to completion.

> **Lesson.** "Cancelled" is neither green nor red — it is absence of information, and it accumulates unnoticed because it is not coloured like a failure. Never let an automatic policy cancel the runs you depend on for evidence.

`HANDOFF_2026-08-25_1715_aniruddha-jathar.md; .github/workflows/ci.yml`

---

### A generator that silently destroys the hand-edited column its own header promises to keep

**Believed.** The engineering ledger's header says the file is derived and that exactly one column is hand-edited — Status — which reads as a promise that regenerating preserves it.

**Actually.** The generator copies Status straight from the upstream story file and rewrites the evidence path to a literal template, so regenerating reverts the entire build frontier to whatever the story file says and deletes every note recording why a story sits where it does. It is also the one derived artifact that the consistency checker does not verify by regeneration — which is precisely what makes running the generator both tempting and expensive.

**Caught by.** Reading the generator's code before running it. It is recorded as an unexploded landmine rather than a fired bug: the standing instruction is "do not run it", and the underlying defect is still unfixed.

> **Lesson.** "Hand-edited" and "preserved on regeneration" are different claims, and a header that blurs them invites data loss. If a generator can destroy hand-entered state, make it refuse or merge — do not rely on a comment being read.

`GOTCHAS.md:150-162; docs/10 EngineeringLedger/generate_ledger.py`

---

### A green secret scanner that could not see the secret that was actually leaked

**Believed.** Secrets were covered: a CI job runs a secret scanner over the repository's entire history, and it is green.

**Actually.** An AWS access key for an account with full administrative control — including billing and identity management — was pasted into a chat window on 2026-08-25. It never entered the repository, so the scanner that proves secrets are absent from git had nothing to say about it, and green stayed green. Three handoffs later the key still had not been rotated, and a second full-administrator key for a different account now sits in the same machine's CLI configuration.

**Caught by.** The session that exposed it wrote it down as an outstanding action, and each subsequent handoff copied it forward. That is the finding: four handoffs of a carried to-do is evidence that no mechanism sits behind it.

> **Lesson.** Know what each check does not cover. A repository secret scanner says nothing about secrets in chat logs, terminals, screenshots or CLI configuration — and a security action that keeps being copied forward unchanged is not a plan, it is a record of not doing it.

`HANDOFF_2026-08-25_1715_aniruddha-jathar.md; HANDOFF_2026-09-12_1341_ani87.md`

---

### The new contrast checker measured the light theme twice and called it two themes

**Believed.** A new tool, `tools/contrast.py`, computed the text-on-background contrast ratio for every colour pair in both the light and the dark theme, replacing figures that had been checked by hand.

**Actually.** The first version of its CSS parser tracked which theme block it was inside by flipping a flag on any line starting with `:root` that did not contain the word 'dark'. The dark theme's own selector is `:root:not([data-theme="light"])` — it starts with `:root` and contains no 'dark'. So the parser filed every dark value into the light table, and the two generated tables came out byte-identical.

**Caught by.** The author noticing that two supposedly different tables were the same bytes. The tool now raises if the two themes resolve equal.

> **Lesson.** When a check compares two things that must differ, make it fail loudly when they come out identical. A checker that silently measures one input twice is worse than no checker, because it manufactures confident wrong evidence.

`docs/01 ADR/all-ADRs/SW-ADR-147.md (Consequences)`

---

### The same failing colour was fixed in one place and left sitting in another

**Believed.** `#a8a29e` had been measured, found to fail the 3:1 contrast floor, and darkened. That problem was handled.

**Actually.** It was handled for exactly one token — the 'Uncategorised' category band. The identical hex sat in the identical file as `--sw-border-strong`, whose own documented use is 'focus-adjacent borders, table rules', a job with the identical 3:1 floor. It measured 2.36:1. Nobody re-checked it, because the measurement had been done per-token and by hand: someone listed the bands, measured the bands, fixed a band. Nothing listed the borders.

**Caught by.** The first honest run of the automated contrast tool, which enumerates every pair rather than the pairs someone remembered. Darkened within the same hue to `#8a837b`, 3.50:1.

> **Lesson.** A hand-maintained check measures what someone remembered to include. That is not a failure of care, it is the ceiling of care — and the fix for that class is never 'be more diligent', it is 'enumerate the population automatically'.

`docs/01 ADR/all-ADRs/SW-ADR-147.md (section 'The defect this found on its first honest run')`

---

### `--check` printed PASS by comparing the generator's output with the generator's output

**Believed.** `generate_api.py --check` proved that the PRD — the document whose own header says 'this is the document the code is written from' — matched the API specification it is generated from.

**Actually.** It regenerated the document and compared the result to the file on disk. It never compared either against what the *specification* actually contained. So when `render_request_models()` was defined and then never called, twelve request models never reached the page, there was no section §6.4 at all, and `--check` still printed PASS. Separately, `render_codes()` read four keys of a five-key object, so the paragraph that makes the validation ordering correct existed in the spec and reached no page. A patch script meant to wire §6.4 in printed '§6.4 wired in' while its text replacement silently failed to match.

**Caught by.** The sixth cold-reader run, which checked the specification's cells against the documents they cite one by one. A new `spec-completeness` check was added — and later tightened from per-block to per-key, because a block that rendered four of its five keys still looked covered.

> **Lesson.** A round-trip check ('regenerate and compare') only proves the generator is deterministic. Completeness needs a different assertion: for every entry in the source of truth, assert it actually appears in the artifact it claims to feed. And never trust a tool that prints its own success message without verifying the result.

`docs/01 ADR/all-ADRs/SW-ADR-143.md (Context items 2 and 3)`

---

### The coverage matrix proving nothing was missing was missing the same row as everything else

**Believed.** The API route list was complete, and `CROSS_PERSON_COVERAGE.tsv` proved every route had at least one test for one person trying to read another person's data. It declared every route COVERED.

**Actually.** `GET /api/expenses/{expense_id}` did not exist in any contract document, despite being required by a P0 acceptance criterion, by a system-integration test, and by `NEG-X-01`, a severity-one cross-person case. The PRD route table listed only PATCH and DELETE on that path; the surface route map listed the same; and the coverage matrix — written at the same review gate three hours earlier — listed PATCH and DELETE, omitted `NEG-X-01` entirely, and declared full coverage.

**Caught by.** The third cold-reader run. The fix made the route list machine-readable data in one file and added a checker that extracts every `METHOD /api/…` string named anywhere in the stories, tests and journeys and fails if one does not resolve to a declared route. On the day it was written it checked 78 named routes against 28 declared.

> **Lesson.** Three hand-maintained copies of one table will all be missing the same row — including the copy whose entire purpose is to prove nothing is missing. Derive the list from one source and check the other documents against it, in the direction where the tests are allowed to be right. (Normalising `{id}`, `{expense_id}` and `{A's id}` to one route mattered too: a checker that treated them as three would have produced noise instead of this finding.)

`docs/01 ADR/all-ADRs/SW-ADR-140.md`

---

### The contrast gate would have certified a colour the browser never drew

**Believed.** Darkening the `--sw-cat-uncat` token in the stylesheet fixed the failing category colour, and `tools/contrast.py` confirmed 3.07:1.

**Actually.** That colour lives in three places. The donut and ribbon charts render `b.color` straight from the summary API response, so the colour a user actually sees comes from `UNCATEGORISED_COLOR` in the backend; `contract.json` holds a third copy. `tools/contrast.py` reads only the stylesheet, so it would have reported a passing figure for a hex the browser never painted.

**Caught by.** The author noticing the duplication while making the change. A new `band-colour-agreement` check now fails unless all three agree, and it was red-proofed by planting the exact divergence and watching it fire.

> **Lesson.** A gate proves a property of the artifact it reads. If a value lives in three artifacts and the gate reads one, the gate is measuring documentation rather than behaviour. Either collapse the copies to one source, or add a check that the copies agree.

`docs/01 ADR/all-ADRs/SW-ADR-152.md (section 'The band colour lives in three artifacts'); app/modules/expenses/summary.py:23`

---

### The readability test checked how readability was achieved, never that it was

**Believed.** A browser test guarded card readability. Its assertion was `assert "rgba" in style["bg"]` — the card must be translucent, because a measured alpha of 0.78 was where muted text still cleared 4.5:1.

**Actually.** That assertion computed no contrast ratio at all. A translucent card compositing down to unreadable mud would have passed it. It tested the *mechanism* someone happened to choose, not the *property* anyone wanted. When a later restyle deliberately made surfaces opaque, the test went red and could not be made green by fixing code — the only way to satisfy it was to abandon the approved restyle.

**Caught by.** The restyle colliding with it. The replacement asserts the painted ink-on-card ratio is at least 4.5:1, measured in the live browser, and reports translucency separately so a regression says which assumption broke. It was red-proofed both ways — card forced translucent, card forced opaque but low-contrast — then reverted.

> **Lesson.** Assert the property you want, not the implementation you chose to get it. A test written against a mechanism blocks every legitimate change of mechanism while failing to catch the thing you actually care about — and it will eventually put you in the position of choosing between a red test and an approved change.

`docs/01 ADR/all-ADRs/SW-ADR-154.md`

---

### A block of security tests inherited one templated expectation, and it was wrong for a create

**Believed.** `NEG-X-10`, a severity-one cross-person test, expected `POST /api/expenses {user_id: A}` sent by person B to return 404.

**Actually.** A create has no target to be denied access to — the owner is taken from the verified identity and a forged `user_id` is simply discarded, so the correct answer is 201 with the stored row stamped to the caller. The 404 got there because the negative suite's cross-person block shared one templated `expected_status` across all sixteen cases, so a *read* expectation landed on a *create*. Three other documents already said the forged field is ignored; the suite contradicted them.

**Caught by.** A cold reader planning the slice (GUESS #5, BLOCKING). `NEG-X-10` was corrected to expect 201 and to assert that the stored row carries the caller's user id — the property that actually matters, and one a 404 would never have proved.

> **Lesson.** Templating an expectation across a family of test cases copies it into the cases where it is wrong, and it still reads as a deliberate expectation on file. Notice too that the corrected assertion is stronger than the original: a status code is a weak proxy for the property you care about.

`docs/01 ADR/all-ADRs/SW-ADR-130.md`

---

### The test that proves the security test works refused to fail, because it broke the wrong switch

**Believed.** The isolation guarantee — person B cannot read person A's expenses — was proven green by a test. To prove that green meant something, a second test deliberately turns the protection off, watches the first test go red, turns it back on, and watches it go green again. The first version of that red-proof used 'ALTER TABLE expenses NO FORCE ROW LEVEL SECURITY'.

**Actually.** There are two separate switches with similar names. ENABLE/DISABLE is what stands between person B and person A. FORCE only controls whether the table's OWNER is subject to its own policies. The runtime role that the test connects as does not own the table, so the policies applied to it either way, and switching FORCE off changed nothing that role could observe.

**Caught by.** The red-proof refused to go red. That refusal is how the mistake surfaced — had the sabotage been silently ineffective in a way that still produced a passing result, the project would have reported a proven gate forever on the strength of a check that never sabotaged anything.

> **Lesson.** When you deliberately break something to prove a check can detect breakage, confirm the break actually happened — read the setting back from the system afterwards, do not trust that the command 'ran successfully'. The red-proof in this repo now reads pg_class both after breaking and after reverting, and keeps the revert in a finally block, because a half-reverted test database silently switches the guarantee off for every run that follows.

`tests/test_gate_redproof.py:21`

---

### The colour checker certified 3.07:1 for a colour the application never drew

**Believed.** A category colour failed a readability floor at 2.99:1, was darkened in the stylesheet, and the contrast tool then reported it passing at 3.07:1. The design system document was regenerated to say so. Three separate green checks agreed the problem was fixed.

**Actually.** That colour lives in three places. The chart and the ribbon paint it inline from the API response, and that value comes from a Python constant in app/modules/expenses/summary.py; the API contract file holds a third copy. The stylesheet token is read only by the category swatch picker. The contrast tool measures the stylesheet. So for about twenty minutes the tool published a passing number, with a measurement beside it, for a hex the browser never used — while the chart kept drawing the failing 2.99:1 value it was supposed to replace.

**Caught by.** By grepping for the old hex outside the stylesheet, rather than by trusting three green gates. Nothing automated would have found it.

> **Lesson.** A check proves a property of the artifact it READS, not of the product. If one value lives in several files, a green tick beside a precise number can be worse than no check at all, because the number lends it authority. The durable fix was a new check that reads all three sources and fails unless they are identical — one value, one reader is the bug; one value, three homes, no one comparing them is the shape.

`docs/15 ChangeRequest/CR-002_visual-identity.md, section 'The third defect — and the one that would have shipped'`

---

### A confidentiality gate that had never refused anything, on any run

**Believed.** A gate scanned content against a list of forbidden terms and printed 'scrub OK' on every run. It was treated as a working control.

**Actually.** The list file had Windows line endings (carriage return plus newline). Read line by line, every term carried an invisible trailing carriage return, so no term ever matched any content. The gate could not fail. It had never refused anything on that platform — and a check that cannot fail looks exactly like a clean result.

**Caught by.** Recognised as a process trap and written into the project's trap ledger, with two fixes applied: a repository-root .gitattributes normalising line endings to LF, and a standing rule that every gate must be red-proofed — plant a violation, watch the gate fire, revert, and verify the revert.

> **Lesson.** A clean report from a check you have never seen fail is not evidence. Invisible characters (carriage returns, byte-order marks, non-breaking spaces) silently defeat exact matching, and the failure mode is always the reassuring direction: nothing matched, so nothing is wrong. Red-proof every gate before you trust a green from it.

`GOTCHAS.md:74`

---

### Seven live routes were missing from the API specification because the check only ran one way

**Believed.** A consistency check guarded the API specification file, which is the source the route tables and error tables are generated from. It had been passing.

**Actually.** It ran in one direction only: it failed when a DOCUMENT named a route the specification did not have. Nothing ran the other way — a route the application actually serves but the specification has never heard of. That is the direction that rots, because it degrades every time someone ships something rather than every time someone writes something. Seven approved, working, released routes were absent, including account deletion and the admin spending view.

**Caught by.** By accident. New wording for an unrelated story happened to mention one of the seven by name, which tripped the one-way check; the audit that followed found the other six. The durable fix reads the router decorators statically and fails on served-but-undocumented routes — and also fails when it extracts ZERO routes, because an empty comparison passes for the wrong reason.

> **Lesson.** Ask which direction your consistency check runs in, and whether the other direction is the one that decays. Reality drifting ahead of the specification is usually the likelier rot than the reverse. And the static-parsing choice matters: the check reads the source text rather than importing the application, because a check that needs a valid configuration to run is a check that quietly stops running.

`docs/12 DesignReview/FINDING_seven-shipped-routes-absent-from-the-contract.md`

---

### A test failed on the comment explaining why it existed

**Believed.** A startup script must not retry a failed database migration — a retry loop turns a broken migration into a container that flaps forever with no alarm. A test scanned the script for retry-shaped constructs to enforce that.

**Actually.** The first version scanned the whole file, including comments — and matched the word 'retry' inside a comment QUOTING the decision record that forbids retrying. The test failed on its own rationale.

**Caught by.** Immediately, by failing on correct code. The fix strips comment lines before scanning, so the check reads what runs rather than what is written about what runs.

> **Lesson.** A text-scanning check reads everything in the file, including prose about the rule it enforces. Strip comments and documentation before pattern-matching over source, or your check will be triggered by the explanation of itself — and the near-miss version of this is worse: the same scan could just as easily PASS because a forbidden construct sat inside a string or a comment where it looked harmless.

`tests/test_container.py:146`

---

### The anti-drift column reported drift on all 128 rows and could not have reported real drift

**Believed.** Two ledger columns recorded whether each decision had actually landed in the downstream story and data-model documents. The project constitution calls this the anti-drift mechanism.

**Actually.** They read NOT_INCLUDED on 128 of 128 rows while those documents visibly cited dozens of the decisions. The signal was inverted and constant: it reported drift where there was none, and would have reported none if a decision had genuinely gone missing. The mechanism named as the drift detector was structurally incapable of detecting drift.

**Caught by.** The exit gate, by reading the downstream documents and counting the citations actually present rather than reading the column. The columns are now derived from citations that exist, with the carrying file named.

> **Lesson.** A hand-maintained status column is a rumour. If a field is meant to detect a mismatch between two things, derive it from both — and prove it works by removing something and watching the field change.

`docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv · 02_ROOT_CAUSE_REGISTER.tsv row RC-8`

---

### One correct expectation copied down sixteen rows made sixteen tests unable to fail

**Believed.** The sixteen cross-person negative tests — one person trying to touch another person's data — all expected an HTTP 404, which is the right answer for reading someone else's record.

**Actually.** The sixteen cases are not the same shape. They include single-record reads, creations and validation failures. One of them expected 404 on a create that the specification says should *succeed* while ignoring the forged owner field — so the test accepted the response the specification forbids, and two documents the build must satisfy could not both pass.

**Caught by.** The cross-artifact sweep, comparing each test's expected result against the specification it claims to test. No automated check did this; nothing in the project compared a test expectation to a spec.

> **Lesson.** Copying one expectation down a column is how a test suite quietly stops testing. Every case needs the assertion that matters for that case, and identical expectations across differently-shaped cases should read as a warning sign.

`docs/09 NegativeTesting/SIT_NegativeCases.tsv rows NEG-X-01…16 · SW-ADR-130 · 02_ROOT_CAUSE_REGISTER.tsv row RC-6`

---

### The review reported the wrong side of a mismatch, confidently and with evidence

**Believed.** Finding 14 of a well-evidenced 21-finding review reported that the project guide claimed 76 business requirements while the artifact held 77, and that the coverage map agreed with 77.

**Actually.** There are 76. Counted directly: 76 row ids in the requirements document, 76 in the coverage map, exactly the same set with nothing in either that is missing from the other. The guide had been right all along and the coverage map's "77" was the error — the reverse of what the review reported.

**Caught by.** Recomputing every count in the review rather than accepting any of them. This was the only one that moved, which is why the reviewer wrote it up against itself rather than quietly correcting it.

> **Lesson.** A confident, well-evidenced finding can be backwards. When a review says "document A says X and document B says Y", it has told you where to look, not which one is right — go and count.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/08_REVIEWER_SELF_CHALLENGE.md §1 · 03_CONFLICT_MAP.tsv row EXIT-G4`

---

### The route check ran in only one direction, so seven live endpoints were undocumented

**Believed.** An existing route-contract check in the consistency script kept the API specification and the running code in step.

**Actually.** It only failed when a *document* named a route the contract lacked. Nothing ever checked the other direction — a route the application actually serves that the contract never learned about. That is the direction that rots, because it degrades every time somebody ships, not every time somebody writes. Seven approved, working, released endpoints were missing from the specification that the published route table is generated from.

**Caught by.** By accident. New wording for an unrelated story happened to mention DELETE /api/auth/me by name, which tripped the one-way check, and the audit that followed found the other six. The replacement reads the route decorators statically with Python's ast module rather than importing the application, because a check that needs a full working configuration is a check that quietly stops running.

> **Lesson.** A comparison between two lists needs both directions, and the missing direction is usually the one that decays fastest. Also worth copying: the new check fails if it extracts zero routes, because an empty comparison passes for the wrong reason.

`docs/12 DesignReview/FINDING_seven-shipped-routes-absent-from-the-contract.md · tools/consistency_check.py (route-contract vs route-coverage)`

---

### The contrast check looked for the letters "rgba" and never computed a ratio

**Believed.** An acceptance criterion enforced a minimum contrast ratio on the translucent card surfaces, so text on glass was guaranteed readable.

**Actually.** The assertion checked whether a background style string contained the substring "rgba" and computed no ratio at all. A translucent card compositing down to unreadable mud would have passed it.

**Caught by.** A client restyle that set every surface fully opaque, which made the criterion impossible to satisfy and forced somebody to read what it actually did. The replacement reads the painted colours and does the contrast arithmetic in both themes, and was proved both ways before being trusted: forced translucent it names the transparency, forced opaque at 3.46:1 it names the ratio, reverted it goes green.

> **Lesson.** A check that tests for the *presence of a technique* is not a check on the *property you care about*. If the rule is a number, the check must compute the number.

`SW-ADR-154 (amends SW-ADR-147 D) · PROGRESS.md, session 2026-09-01`

---

### A workflow file with two identical keys parsed cleanly locally and was rejected outright

**Believed.** The continuous-integration workflow file was valid — it parsed locally with PyYAML without a murmur.

**Actually.** A job had been pasted below another instead of replacing it, leaving two `image:` keys in one file. Duplicate keys are legal YAML and the last one wins, so the local parser was perfectly happy. GitHub rejected the file outright: the push failed in zero seconds with no jobs at all, and the run's display name was the file path rather than the workflow name, because GitHub never got as far as reading the name field.

**Caught by.** Pushing it. The tell-tale sign was the display name showing a path.

> **Lesson.** A local parse is not a schema check, and the gap between them is a whole class of bug. Confirming a file *is* valid YAML says nothing about whether it is a valid workflow — run the schema-aware linter for the system that will actually consume it.

`.github/workflows/ci.yml · PROGRESS.md, session 2026-08-25`

---

### A confidentiality gate had never refused anything, and that looked exactly like a clean result

**Believed.** A gate scanned documents against a blocklist of forbidden terms before release and printed "scrub OK" each time.

**Actually.** The blocklist file has Windows line endings and is read line by line, so every entry carries an invisible trailing carriage return and matches nothing. The gate had never refused a single thing on Windows.

**Caught by.** Deliberately planting a violation to watch the gate fire — and it did not. Fixed with a repository-level .gitattributes normalising line endings, and the project adopted the habit of proving every gate this way (15 of 15 at the exit gate, later 18 of 18).

> **Lesson.** A check that cannot fail looks identical to a check that keeps passing. Red-proof every gate: plant a violation, watch it fire, revert, and verify the revert. Invisible characters — line endings, trailing whitespace, byte-order marks — are a common way for a text comparison to silently match nothing.

`GOTCHAS.md:74-79`

---


# False green

*A test or gate passed while proving nothing — usually by examining an empty set.*

**32 recorded.**

### app.routes is not the list of routes — a test passed by examining an empty list

**Believed.** To check that no endpoint accepts a forbidden field, you can walk the application's routes with `[r for r in app.routes if r.path.startswith("/api/...")]` and inspect each one.

**Actually.** This version of FastAPI does not put the real endpoints in `app.routes`. Each router that was included is kept as an `_IncludedRouter` wrapper object that has no `.path` and no `.routes` at all — only `.original_router`, which holds the actual endpoints one level down. So on an application with roughly 40 endpoints the filter matched nothing, the list came back empty, and `assert not offenders` on an empty list passes happily. The test reported success having looked at zero endpoints.

**Caught by.** Hit on 2026-08-21 while writing story E6-S5. It was only noticed because a companion assertion checked that the population searched was non-empty before checking the search came back clean. The fix has two halves and both are load-bearing: descend through `.original_router` (the `flatten` helper at tests/test_admin.py:24-42) AND assert the result is non-empty (tests/test_capabilities_absent.py:214). The descent on its own would have been silently re-emptied by the next refactor.

> **Lesson.** A test that proves something is ABSENT must also prove that it looked. Assert the size of the population you searched before you assert the search came back clean — otherwise "found no violations" and "found nothing at all" produce exactly the same green tick. This applies to every scan, lint, grep-based check and reflection-based test you will ever write.

`GOTCHAS.md:167-174; tests/test_admin.py:24-42; tests/test_capabilities_absent.py:214`

---

### `from __future__ import annotations` turned every type into a string, so the scanner inspected zero models

**Believed.** To find every request body model, walk each handler's parameters and keep the ones where `isinstance(param.annotation, type)` and the type is a Pydantic model — then check none of them has an `email` field, which would let someone change the identity their account is keyed on.

**Actually.** Every module under `app/` begins with `from __future__ import annotations`. That Python feature stops annotations being evaluated into real classes and leaves them as plain strings at runtime. `isinstance("ProfileUpdate", type)` is False, always. The loop therefore matched no parameter on any handler, collected no models, found no offenders, and reported success having examined nothing.

**Caught by.** Found minutes after the `app.routes` bug above, in the same file, by the same guard: `assert examined` before `assert not offenders` (tests/test_capabilities_absent.py:197-215). The fix is `inspect.signature(fn, eval_str=True)` (or `typing.get_type_hints(fn)`) so the strings are resolved back into classes.

> **Lesson.** Code that inspects its own structure at runtime — reflection — is quietly broken by language features that change that structure. When you write such code, count what you inspected and fail on a count of zero. A zero count is the tell that separates "clean" from "never ran".

`tests/test_capabilities_absent.py:193-215; GOTCHAS.md:176-181`

---

### A table's owner bypasses row-level security silently, so the isolation test passes in one environment and fails in another

**Believed.** Row-level security policies are written and look correct, and a test proves that user B cannot read user A's rows. Therefore the database enforces isolation.

**Actually.** In PostgreSQL the role that OWNS a table is exempt from that table's security policies unless the table is explicitly forced. Migrations are usually run by the owning role, so if the application connects as that same role the policies do nothing — while still existing, still being readable in the schema, and still looking like protection. The denial test then passes on a machine where the application role happens to differ and fails where it does not.

**Caught by.** Not hit on this project. GOTCHAS.md marks it [UNPROVEN HERE] — found by reading PostgreSQL's own documentation before the isolation layer was built, which is why the project requires `ALTER TABLE … FORCE ROW LEVEL SECURITY` on every protected table plus a separate runtime role that does not own the tables, is not superuser, and lacks BYPASSRLS, verified by querying the database catalogue rather than assumed.

> **Lesson.** A security rule that the database is entitled to skip for some callers is not a security rule until you have checked WHICH caller you are. Verify the property by querying the system's own catalogue, and prove the protection can go red — disable the policy on purpose, watch the denial fail, restore it, and confirm the restore.

`GOTCHAS.md:14-19 (marked [UNPROVEN HERE]; SW-ADR-082, SW-ADR-078)`

---

### The never-waivable gate passed on exactly one day in history

**Believed.** test_gate_75810.py proved the daily-average calculation returns exactly 75810 paise — the project's one acceptance number that can never be waived.

**Actually.** The divisor is 'days of August elapsed so far', taken from the machine's clock. Written and run on 2026-08-05 with 5 days elapsed, it gave 75810. On 6 August the same correct code gives 63175; on 1 September, 12227. The API contract stated the request, the range, the field, the rounding rule and even three wrong answers a plausible implementation would produce — and never the date the whole thing is evaluated on.

**Caught by.** Midnight. Four assertions went red mid-build with no code change behind them. The browser tests had always pinned APP_TODAY_OVERRIDE=2026-08-05, because a browser test cannot reach an in-process override and someone had worked that out; the in-process tests silently inherited the machine's date and nobody noticed, because the day they were written was the day they were pinned to.

> **Lesson.** Any test asserting a value derived from 'today' must state which today, and take it from the specification rather than the clock. A value was pinned and the thing it was pinned to was not — and the only evidence either way was a test that passed.

`docs/01 ADR/all-ADRs/SW-ADR-146.md; tests/test_gate_75810.py:35`

---

### The database self-check printed all-green against a role that could not read a single row

**Believed.** verify_invariants.sql proved the application's runtime database role was correctly locked down.

**Actually.** All eight checks asked what the role cannot do: not a superuser, cannot bypass row security, cannot delete users. Until 2026-08-05 the schema contained no GRANT statements at all, so the runtime role could not read one row from any table. Every check passed, because nothing asked whether the role could do anything.

**Caught by.** A zero-context agent asked to plan one end-to-end slice — sign in, create an expense, load the dashboard — noticed there were no GRANTs anywhere. Checks 9 to 11, the positive direction, were added afterwards and the file now carries a comment explaining why.

> **Lesson.** A check that tests only one direction passes happily against something completely inert. Every 'cannot' assertion needs a matching 'can' assertion, or the safest possible system — one that does nothing at all — scores perfectly.

`docs/06 DataModel/checks/verify_invariants.sql:46-52`

---

### A privacy test passed against a screen that had not finished loading

**Believed.** assert "Groceries" not in text proved the admin detail pane never shows a person's category names — the exact boundary the client's change request exists to hold.

**Actually.** The pane draws its header, status and period chips from data the accounts table already had, then shows 'Loading…' until the spending request answers. The test read the pane's text as soon as the pane element appeared, so it was asserting that a category name was absent from a pane that had rendered nothing at all.

**Caught by.** The test's own author while writing it. The race fails asymmetrically: an assertion that something is present would have reported 'no line plot' and been investigated, while an assertion that something is absent passes quietly. The fix waits for a specific element that only exists once the real figures arrive.

> **Lesson.** Absence assertions on a screen are the ones a loading race silently turns into nothing. Wait for an element that can only exist after the data has arrived, then assert the absence.

`tests/browser/test_the_shell.py:513-523`

---

### A contract rule that could never fire, guarded by a test comparing two wrong answers to each other

**Believed.** Both summary endpoints implemented the contract's range.required error for a missing date range, and a test proved they behaved the same.

**Actually.** Both endpoints declared 'from' and 'to' as required query parameters, so the web framework rejected the request before any of this project's own rules ran, and every caller got a generic field.required instead. The rule had been specified since the contract was written and was unreachable in both places.

**Caught by.** Found by hand on 2026-08-21 while writing a shared helper, not by the suite. It survived 224 tests because the only test covering it asserted that the two endpoints answer identically — which they did, both wrongly.

> **Lesson.** A test that compares two implementations to each other proves consistency, not correctness. At least one side must be checked against the written specification.

`app/modules/expenses/router.py:24-35; handoffs/HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### The contrast tool certified a colour the application never draws

**Believed.** After darkening the 'Uncategorised' category colour in the design tokens file, the tool reported 3.07 to 1 and the failing band was fixed.

**Actually.** The two chart components paint that band from the colour the API sends back, not from the stylesheet. The same hex value lived in three places — the design tokens, a Python constant in the summary module, and a generated test fixture — and the tool reads one of them. The screen kept drawing the old, failing colour while the gate read green.

**Caught by.** Reading the two components that consume the API response, after the token fix had already gone green. A new consistency check, band-colour-agreement, now fails when the three copies disagree, and was deliberately broken to confirm it fires.

> **Lesson.** Before believing a checker, confirm it reads the copy that actually renders. One value stored in three files is three values until something asserts they agree.

`handoffs/HANDOFF_2026-08-21_1605_aniruddha-jathar.md:44-49 (Ribbon.jsx:119, Donut.jsx:51, summary.py)`

---

### A test that searched 40 endpoints for forbidden capabilities searched none of them

**Believed.** Looping over the application's route list and filtering by path prefix would inspect every API endpoint for capabilities that must not exist.

**Actually.** This version of FastAPI keeps each included router inside a wrapper object that has no path and no routes attribute — only original_router. The list comprehension returned nothing on an application with 40 endpoints, and the test passed against an empty list.

**Caught by.** The test's own author on the same day, only because the test asserted the searched population was non-empty before asserting it was clean. A helper in another test file already descended into the wrapper correctly.

> **Lesson.** A test that proves an absence must also prove that it looked. Assert the size of the population you searched — otherwise 'found no violations' and 'found nothing at all' produce the same green.

`GOTCHAS.md, section 'Two ways a route-table test passes while examining nothing'`

---

### A test inspecting function signatures found no data models, because every annotation was a string

**Believed.** Checking isinstance(param.annotation, type) would identify which handler parameters are typed as request models.

**Actually.** Every module in the application begins with 'from __future__ import annotations', which turns every type annotation into a plain string at runtime. The isinstance check was therefore false for every parameter of every handler, and the test reported success having inspected zero models.

**Caught by.** The same author, minutes after the previous one, and again only because the test counted what it had examined and asserted that count was non-empty before asserting the offender count was zero.

> **Lesson.** Runtime inspection of types depends on how the file was written, not only on what it declares. Resolve annotations explicitly, and always count what you examined.

`GOTCHAS.md, section 'Two ways a route-table test passes while examining nothing'`

---

### A document generator's own --check flag printed PASS for a section that was never rendered

**Believed.** The generated specification was complete, because the generator's --check mode passed.

**Actually.** A function named render_request_models was defined and never called, so an entire block of the specification never reached the page. The check regenerates the document and compares it to the file on disk — so both sides were missing the same section and agreed perfectly.

**Caught by.** A later review pass. A spec-completeness check was then added to the project's consistency checker specifically for this, and, like all the others, deliberately broken once to confirm it fires.

> **Lesson.** Regenerate-and-compare proves the output is reproducible, not that it is complete. Something independent must assert that every expected section is actually present.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md:102-115`

---

### A specified error code that could never fire, guarded by a test that compared two wrongs

**Believed.** The API contract had specified a `range.required` error for a missing date range since it was written, the two summary endpoints implemented it, and a test covered them.

**Actually.** Both endpoints declared the `from` and `to` query parameters as required, so FastAPI rejected the request before any rule in the application ran. Every caller got `field.required` instead. The specified rule was unreachable code that had never executed once.

**Caught by.** A later audit, not the test suite. It survived 224 tests because the covering test asserted only that the two endpoints answer identically — which they did, both wrongly. Fixed with one shared `require_range` helper used by both routers.

> **Lesson.** A test that compares two implementations to each other proves they agree, not that either is right. At least one side of any comparison must be an independently written expected value.

`app/modules/expenses/schemas.py:150; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### Two security tests that passed having inspected zero objects

**Believed.** Two new tests proved the app exposes no endpoint letting a person change their own email, display name or password. They walked the route list and the handler signatures and reported no violations.

**Actually.** Both examined nothing. `app.routes` is not the route table in this FastAPI version — each included router is wrapped in an `_IncludedRouter` with no `.path` and no `.routes`, so filtering by path returned an empty list from an app with 40 endpoints. Separately, every module uses `from __future__ import annotations`, which turns type annotations into plain strings, so `isinstance(param.annotation, type)` was False for every parameter of every handler.

**Caught by.** The author, minutes apart, by adding an assertion that the searched population was non-empty before asserting it was clean. Both tests were green when written and would have shipped as proof of a security property.

> **Lesson.** A test that proves an absence must also prove it looked. Count what you examined and assert that count is above zero — otherwise "found no violations" and "found nothing at all" are the same green.

`GOTCHAS.md:164-184; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### A privacy assertion that passed against a pane which had rendered nothing

**Believed.** A test asserting `"Groceries" not in text` proved an administrator cannot see a person's category names — the exact privacy boundary the CR-001 change request exists to hold.

**Actually.** The admin detail pane renders its header before its figures, so the assertion ran against a pane that had not rendered its content yet. It would have passed equally happily if the pane were broken, empty, or removed entirely.

**Caught by.** The test's own author, in the same session. It never reached a reviewer.

> **Lesson.** When testing that something is hidden, first assert something that should be visible. A negative assertion against an unrendered page is indistinguishable from a genuine privacy check.

`HANDOFF_2026-08-06_0442_ani87.md`

---

### A duplicate YAML key that parsed locally and was rejected by the server

**Believed.** The CI workflow file was valid — it had been parsed locally with PyYAML without a single complaint before being pushed.

**Actually.** The file contained two `image:` job keys: a full smoke-test job had been pasted below another job instead of replacing the build-only one, at four-space indent where jobs live at two. Duplicate keys are legal YAML and the last one wins, so PyYAML accepted it happily. GitHub rejected the file outright — the run finished in 0 seconds with no jobs, displayed under the file's path rather than its name, because GitHub never reached the `name:` field.

**Caught by.** Pushing it and seeing a zero-second run with no jobs. Nothing in the project checks the workflow file itself; adding a workflow linter is still an open item.

> **Lesson.** Parsing is not validating. A parser tells you the text is well-formed; only a schema-aware linter tells you the document means what you intended. And a pipeline run that finishes in zero seconds is a failure wearing the wrong colour.

`HANDOFF_2026-08-25_1556_aniruddha-jathar.md; .github/workflows/ci.yml`

---

### A stray local PostgreSQL that would have made the isolation gate pass for the wrong reason

**Believed.** A placeholder .env pointing the test suite at 127.0.0.1:5432 was harmless, since no project database was configured there.

**Actually.** A real PostgreSQL server was running on that port, and the only thing stopping the suite from connecting was a wrong password. A local PostgreSQL hands you a superuser account, and a superuser bypasses row-level security entirely — so the isolation gate, the single guarantee this product exists to make, would have gone green for exactly the wrong reason.

**Caught by.** Noticing the listening port while setting up the environment. Fixed by repointing the placeholder at db.invalid, a domain reserved by standard so it can never resolve, making database tests skip instead of connecting somewhere wrong. It also cut the suite from 366 seconds to 46, because a name that cannot resolve fails in 0.03s where a refused port took 2.

> **Lesson.** A test suite that can reach the wrong database will cheerfully prove the wrong thing. Make the wrong target impossible to reach rather than merely unconfigured — an address that cannot resolve is safer than one that merely refuses.

`GOTCHAS.md:21-23; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### 209 tests skipping en masse, reported as a clean run

**Believed.** The test run finished without failures, so the suite ran and the code is proven.

**Actually.** The RDS firewall admits exactly one IP address. When the developer's home IP changes — and home IPs move — every database-backed test skips rather than fails, and the output reads like "no database configured". 209 tests quietly did not execute while the run still looked successful.

**Caught by.** Repeated re-diagnosis across several sessions, until the handoffs began naming it first in the resume protocol: check your public IP against the security group before assuming anything is broken.

> **Lesson.** Skipped is not passed. If unreachable infrastructure turns your suite from proving something into proving nothing, make that condition loud — print the skip count, or fail the run — because a quiet skip has the same colour as success.

`HANDOFF_2026-08-06_0442_ani87.md; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### The never-waivable gate test only passed on the day it was written

**Believed.** `test_gate_75810.py` proved the project's single most important number — a daily average of 75810 paise against a fixed seeded fixture. It was green, so the arithmetic was right.

**Actually.** The average is total divided by days elapsed, and days elapsed is counted from the start of the range up to *today*. The test read the machine's clock. On 2026-08-05 the divisor was 5 and the answer was 75810; on 2026-08-06 the divisor was 6 and the answer would be 63175; on 2026-09-01 it would be 12227. The contract file specified the request, the range, the field, the expected value, the rounding rule, and even three wrong answers a sloppy implementation would produce — and never said which date the whole thing is evaluated on.

**Caught by.** Midnight. Four assertions went red mid-build with no code change behind them. The browser tests had always pinned the date with `APP_TODAY_OVERRIDE=2026-08-05`; the in-process tests inherited the machine's date and nobody noticed, because the day they were written was the day they were pinned to. The project's sixteen automated consistency checks could not catch this class at all.

> **Lesson.** Any test asserting a value derived from 'today' must state which today, in the spec and in the fixture. The general shape: a value was pinned and the thing it depended on was not, and the only evidence either way was a test that passed. The clock is a dependency like any other.

`docs/01 ADR/all-ADRs/SW-ADR-146.md`

---

### The runtime database role had no permissions at all, and the invariant check was happy

**Believed.** `security.sql` configured the runtime database role correctly, and `verify_invariants.sql` proved it: the role does not own the tables, is not a superuser, and cannot bypass row-level security. All green.

**Actually.** `security.sql` contained no `GRANT` on any table. Its only privilege statements were a `REVOKE` on the audit log and one `GRANT EXECUTE`. The runtime role `spendwise_app` therefore held no privilege on any table, and every query the application makes would have failed with 'permission denied'. The invariant check asserted three things the role *cannot* do and nothing about what it *can* do, so it passed happily against a role that could not read a single row.

**Caught by.** A cold reader planning an implementation purely from the documents (the project's 'uncoached slice' exercise, run 2), not by running anything. The check now asserts the positive direction too.

> **Lesson.** A safety check that only tests the negative direction ('this role can't do the dangerous thing') passes against a role that can do nothing at all. Assert the capabilities you need as well as the ones you forbid. Related: row-level rules only narrow what a grant already allows — with no grant, the elaborate per-row protection was guarding a door already welded shut, which is exactly why nothing downstream noticed.

`docs/01 ADR/all-ADRs/SW-ADR-137.md; grants now at docs/06 DataModel/security.sql:265-267`

---

### Two live documents specified opposite validation orders, and every test passed either way

**Believed.** The rule for which validation error wins when a request body breaks two rules at once was settled, and the negative-test suite covered validation thoroughly.

**Actually.** One approved record said the tie-break follows the order fields appear in the example payload; another said it follows the order the request model declares them. Both were live, the two orders differ in real cases, and the older one carried no marker saying it had been changed. No test could tell the difference: every negative case in the suite varies exactly one input, so a body breaking two rules at once was never sent. Two engineers could ship opposite behaviour and both go green.

**Caught by.** The seventh cold-reader run. The project's constitution already required superseded text to be marked where it stands — and that was the one rule with no automated check behind it. A new `amendment-marker` check now fails the build if a record declares it amends another and the other does not carry a banner naming it.

> **Lesson.** If every test varies one variable, any rule about *interactions* between variables is untested no matter how many tests you have. And a documentation rule with no automated enforcement is a rule that gets broken silently — the check fired on the very record that created it.

`docs/01 ADR/all-ADRs/SW-ADR-144.md (Context item 4)`

---

### The project's single never-waivable number passed for exactly one day

**Believed.** The headline proof of this whole product is that a seeded set of expenses produces a daily average of exactly 75810 paise. Four tests asserted it, they were green, and the value was treated as verified.

**Actually.** The average is the total divided by 'days elapsed so far', so the answer depends on what today's date is: 75810 on 2026-08-05, 63175 on the 6th, 12227 by 1 September. The tests read the machine's clock. They were written on 2026-08-05 and passed on 2026-08-05, and would have failed on every other day in history. The specification document stated the request, the range, the rounding rule and even three wrong answers a bad implementation would produce — and never stated the date the whole thing is evaluated on.

**Caught by.** Midnight. The wall clock rolled over mid-build and four assertions went red with no code change behind them. Notably the browser-driven tests had always pinned the date explicitly, because a browser test cannot reach inside the app to override a dependency; the in-process tests inherited the system clock and nobody noticed, because the day they were written was the day they were pinned to.

> **Lesson.** When you pin an expected value, pin everything it depends on — especially time. A test whose inputs include 'whatever today is' is not reproducible, and its green tells you only that it ran on the right day. Write the date into the contract as a fact, and have the test read it from there rather than typing it twice.

`docs/01 ADR/all-ADRs/SW-ADR-146.md, and tests/test_gate_75810.py:38`

---

### A privacy assertion passed against a screen that had not finished loading

**Believed.** The product's central promise is that an admin can see how much someone spent but never what they spent it on. A browser test opened the admin's detail view for another person and asserted that no category name appeared in the text — and it passed.

**Actually.** That pane draws its header, status and period buttons immediately from data the accounts table already had, then shows 'Loading…' for the total, the count, the average and the chart until a second request answers. The test read the text in that gap. An assertion that something is ABSENT passes trivially against a pane that has rendered nothing — so the strongest privacy check in the suite was being satisfied by an empty box.

**Caught by.** The test's own author, while writing it. The failure is asymmetric and that is what gave it away: assertions that something is PRESENT failed in the same race with the misleading message 'no line plot', which prompted a closer look at why the absence assertions were so comfortable.

> **Lesson.** Any test that proves an absence must first prove it looked. Wait for a positive signal that the thing under test has actually rendered or returned — here, waiting for the total to appear — before asserting that something else is missing. 'Found no violations' and 'found nothing at all' produce the identical green.

`tests/browser/test_the_shell.py:521`

---

### An error rule that could never fire, and a test that could never notice

**Believed.** The API specification says a request missing its date range must return the error 'range.required', naming which of the two dates is missing. It had been specified since the contract was written and was assumed implemented. A test covered it.

**Actually.** Both endpoints declared the two dates as REQUIRED query parameters, so the web framework rejected the request during validation before any project code ran, and every caller got the generic 'field.required' instead. The contract itself names this exact outcome as the condition that makes 'range.required' dead text. It survived a suite of 224 tests because the test that existed asserted only that the person's endpoint and the admin's endpoint answered IDENTICALLY — and they did, both wrongly.

**Caught by.** Carried as a known defect through two handover documents before anyone implemented it; the shared helper fix came with tests that assert the actual error code rather than agreement between two callers.

> **Lesson.** A test that asserts two implementations agree can only fail when someone fixes exactly one of them. Consistency checks are not correctness checks. Assert the value the specification names, not the relationship between two things that share a bug.

`tests/test_range_required.py:1`

---

### Two tests that reported success having examined zero things

**Believed.** Two new tests proved absences: that no route matched a forbidden path prefix, and that no request handler accepted a particular kind of parameter. Both passed.

**Actually.** Both had searched nothing. First: this web framework stores each included router inside a wrapper object with no .path and no .routes, only .original_router — so filtering app.routes for paths starting with '/api/...' returns an empty list on an application with 40 endpoints, and the loop over it finds no violations because it never sees a route. Second: every module in the project starts with 'from __future__ import annotations', which turns every type annotation into a plain string — so 'isinstance(param.annotation, type)' is False for every parameter of every handler, and a test walking signatures for model classes finds none.

**Caught by.** Only because the second test counted what it had examined and asserted that count was non-empty BEFORE asserting the offenders list was empty. Both were written in the same file within minutes of each other.

> **Lesson.** Prove that you looked before you claim you found nothing. Assert the size of the population you searched. Note that descending into the real route table was NOT the fix on its own — without the non-empty assertion, the next refactor silently empties it again and the green comes back.

`GOTCHAS.md:166`

---

### A duplicate key made a pipeline file valid to the parser and invalid to the service

**Believed.** A continuous-integration configuration file had been edited and parsed locally without complaint, so it was believed correct and was pushed.

**Actually.** A job block had been pasted below another instead of replacing it, leaving two entries with the same key at the wrong indentation level. Duplicate keys are legal in this file format and the local parser accepted them happily, last one wins. The hosting service rejected the file outright: the run finished in 0 seconds with no jobs at all, and was displayed under the file's path rather than its name, because the service never got as far as reading the name field.

**Caught by.** The push itself — a run with zero jobs and a wrong display name. Diagnosing it took reading the run's metadata rather than any error message, since a rejected file produces no job log to read.

> **Lesson.** Parsing is not validating. A file can be syntactically legal and still violate the schema the consumer requires, and a local parse gives false confidence precisely because it succeeds. If a configuration file governs a service, run that service's own schema linter — the gap between 'it parses' and 'it is a valid configuration' is an entire class of bug.

`handoffs/HANDOFF_2026-08-25_1556_aniruddha-jathar.md:61`

---

### The database had no permission grants at all, and the check for that printed all-green

**Believed.** The boot-time invariant script passed all eight of its checks, so the database privileges for the application's runtime role were correct.

**Actually.** There were no GRANT statements anywhere. The runtime role could not read a single row of a single table — every query it ever made would have failed with "permission denied", and the application could never have served one request.

**Caught by.** The second fresh-engineer run, trying to plan one end-to-end feature. The reason the script was happy is that all eight checks asked what the role *cannot* do: not a superuser, no bypass privilege, owns no tables. A role with no privileges whatsoever passes every single one of those.

> **Lesson.** A check built only from negative assertions passes perfectly against something completely inert. Always pair "it cannot do the forbidden thing" with "it can do the required thing" — otherwise dead and correct look identical.

`docs/06 DataModel/checks/verify_invariants.sql checks 1–8 · SW-ADR-137 · 03_CONFLICT_MAP.tsv rows S2-G13 and S2-G13b`

---

### All 931 references resolved; eighty of them pointed at decisions that had been withdrawn

**Believed.** The consistency checker passed every one of 931 citations, so the project's cross-references were sound.

**Actually.** The checker asserted only that the referenced file exists. Eighty citations pointed at records that had been superseded or withdrawn — including the constitution's own article resting the product's central security promise on a decision the ledger records as dead.

**Caught by.** The exit-gate authority audit, which compared each citation against the ledger's status column instead of against the filesystem. A new gate now fails any citation of a non-approved record unless the surrounding sentence narrates it as history.

> **Lesson.** Existence is not validity. A link checker written to catch typos will happily certify a corpus of confident references to dead decisions. Check the *state* of the thing referenced, not just that something is there.

`02_ROOT_CAUSE_REGISTER.tsv row RC-1 · tools/consistency_check.py check 10 (adr-status)`

---

### A whole section of the specification was generated and never printed, and the checker said PASS

**Believed.** An approved record stated that the API request models were "rendered as PRD §6.4", and the generator's --check mode reported PASS, so the published document matched its source.

**Actually.** The function that renders those models was defined and never called. There was no §6.4. The --check mode compares the committed document against *what the generator emits*, never against *what the source contains*, so a block that never reaches the page is invisible to it by construction. A sibling function had the same shape: it read four keys of a five-key object, silently dropping the one paragraph that makes the published error-precedence order correct.

**Caught by.** The sixth fresh-engineer run, which went cell by cell through the contract checking whether each claim was actually true of the documents it cited. Every reference involved resolved cleanly, so the reference checker passed both.

> **Lesson.** A round-trip check — "the committed file equals what I produce" — proves the file is current, not that the generator does everything it was supposed to do. Pair it with a completeness check: every block of the input must appear somewhere in the output.

`docs/01 ADR/all-ADRs/SW-ADR-143.md §2 (Context) · tools/generate_api.py · tools/consistency_check.py (spec-completeness gate)`

---

### The project's most important test read the system clock and passed only on the day it was written

**Believed.** The never-waivable expected value of 75810 was fully pinned. The contract stated the request, the date range, the field, the rounding rule, and even three wrong answers a careless implementation would produce.

**Actually.** It never stated the date the whole thing is evaluated on. The divisor is "how many days of August have happened", so the assertion holds on 2026-08-05 and on no other day in history — six days gives 63175, thirty-one gives 12227. The in-process tests inherited the machine's date. At midnight, four assertions went red with no code change behind them.

**Caught by.** The wall clock rolling over mid-build. The browser half of the suite had always been right — it pinned the date from its first line, because a browser test cannot reach an in-process override — and the in-process half simply never did, because the day they were written was the day they were pinned to.

> **Lesson.** A value was pinned and the thing it depends on was not. Any expected number derived from "today" needs that date recorded as a fact and injected into the test. And if one half of your suite already handles something and the other does not, that asymmetry is the bug report.

`docs/01 ADR/all-ADRs/SW-ADR-146.md · tests/test_gate_75810.py · docs/03 PRD/api/contract.json (gate.as_of)`

---

### A test that inspected every handler's parameters inspected none, and passed

**Believed.** A test walked every route handler's signature looking for request models that wrongly accept an email field, found no offenders, and passed.

**Actually.** Every module in the application starts with `from __future__ import annotations`, which turns every type annotation into a plain string. So the test's `isinstance(param.annotation, type)` check was false for every parameter of every handler, the loop examined zero models, and "no offenders found" really meant "nothing was looked at".

**Caught by.** The test's own author, and only because the test asserted that the list of things it had *examined* was non-empty before asserting the list of offenders was empty. Without that one guard it would have passed forever. Fixed by asking Python to evaluate the annotation strings.

> **Lesson.** A test that proves an absence must also prove it looked. Count the population you searched and assert that count is not zero — otherwise "found no violations" and "found nothing at all" are the same green.

`tests/test_capabilities_absent.py:194-216 · GOTCHAS.md:176-183`

---

### The route table a test walked was not the route table

**Believed.** Listing the application's endpoints is a one-liner: filter app.routes by path prefix.

**Actually.** This version of FastAPI keeps each included router as a wrapper object with no path attribute and no routes attribute — only a reference to the original router. So the filter returned nothing on an application with forty endpoints, and the test passed against an empty list.

**Caught by.** The same session that found the annotations bug, minutes apart in the same file, and again only because the author had begun asserting that each walk found something. The fix descends into the wrapper *and* asserts the result is non-empty — the descent alone is not enough, because the next refactor can silently empty it again.

> **Lesson.** When a framework hands you a convenient-looking collection, confirm it contains what you think before you filter it. A filter over an empty list is the quietest pass there is.

`tests/test_capabilities_absent.py:46-62 · GOTCHAS.md:170-175`

---

### A privacy assertion passed against a panel that had not rendered yet

**Believed.** `assert "Groceries" not in text` proved the admin detail panel does not disclose what a person spent their money on — the exact boundary the whole change request exists to hold.

**Actually.** The panel renders its header before its figures. The assertion ran against a panel that had rendered nothing at all, so it would have passed whether or not the category name was ever shown.

**Caught by.** The test's own author, re-reading it before shipping. It is the same family as the two route-table false greens found two weeks later, and led to the rule being written down.

> **Lesson.** "The forbidden string is absent" is only meaningful once you have proved the content is present. Assert something that must be there, then assert the thing that must not be.

`handoffs/HANDOFF_2026-08-06_0442_ani87.md:65-67`

---


# Wrong assumption

*A belief that was reasonable, widely held, and false.*

**32 recorded.**

### The requirements document stated as settled fact that Alembic takes a lock. It does not.

**Believed.** The client's requirements dump asserted, with no hedging, that Alembic (the database migration tool) takes an advisory lock, so two containers starting at the same time can both safely run `alembic upgrade head`.

**Actually.** Alembic takes no such lock. Two ECS tasks booting together race on the same migration; the result is a half-applied schema or a duplicate-object error, at deploy time, on the production database.

**Caught by.** The build session verified the premise instead of inheriting it, and logged the result as erratum E-4 against the frozen source document — one of ten errata — then ruled it in SW-ADR-019. The fix is to take `pg_advisory_xact_lock` explicitly in `alembic/env.py`.

> **Lesson.** Confidence in a requirements document is not evidence. Two more false technical facts came out of the same dump, both about the rate limiter. Verify any technical claim that a design is about to rest on: an inherited premise nobody checked is a bug with a very long fuse, and it detonates as a specification rather than as code.

`GOTCHAS.md:29-32; docs/00 SourceOfTruth/SRC-001 erratum E-4; SW-ADR-019`

---

### "5 attempts per 15 minutes" was really 5 × workers × containers

**Believed.** The number written in the rate-limit configuration is the number of attempts actually allowed.

**Actually.** slowapi's default storage lives in memory, inside one process. With 2 uvicorn worker processes on each of N containers, every process keeps its own independent count, so the real allowance is 5 × 2 × N — and it silently grows every time the service is scaled out. The configured number and the enforced number drift apart as a side effect of an unrelated operational decision.

**Caught by.** Found by reading slowapi's defaults rather than trusting the requirements dump. The project decided not to add a shared store (Redis) and instead recorded the true enforced number as an accepted, named open item (CONSTITUTION.md Article X, OPEN-RATE-01).

> **Lesson.** Any counter held in memory multiplies by the number of processes holding it. If you cannot share the state, write down the number you are genuinely enforcing. A weakness that is accepted and documented is a decision; the same weakness unnoticed is a bug that will be discovered by whoever attacks you.

`GOTCHAS.md:45-47; CONSTITUTION.md Article X (OPEN-RATE-01)`

---

### SUM() over a bigint money column returns a decimal, not an integer

**Believed.** Amounts are stored as whole paise in a bigint column, and the project's rule is that money is an `int` everywhere. So `SUM(amount)` gives back an `int`.

**Actually.** PostgreSQL returns `numeric` for a sum of bigints, to avoid overflow. That arrives in Python as a `Decimal`, which then either fails to serialise into JSON or mixes with plain `int` in arithmetic and produces a total that is wrong while still looking like a perfectly ordinary number on screen.

**Caught by.** Hit on this project during the summary work; recorded unqualified in the trap ledger (it carries no [UNPROVEN HERE] marker). The fix is to cast the aggregate to `BigInteger` in the query so a real `int` comes back.

> **Lesson.** The type of a column is not the type of an aggregate over that column — databases promote types to stay safe, and the promotion is invisible until the value reaches your language. In a system whose entire job is adding numbers up, check the type that actually comes back.

`GOTCHAS.md:25-27`

---

### "This month" computed on the server is wrong by five and a half hours at both ends

**Believed.** The server can work out which expenses fall in "this month" for the dashboard's period selector.

**Actually.** The server runs in UTC; the users are in India, at UTC+5:30. A month boundary in UTC sits five and a half hours away from the user's month boundary, so an expense logged late in the evening of the last day of a month lands in the wrong month's total — at both the start and the end of every range. The fix is that the browser, which knows the user's timezone, turns the chosen period into explicit `from` and `to` dates and sends those; the server never guesses.

**Caught by.** Caught during specification rather than in production. It was ruled as OPEN-TZ-01 and flagged to the client for review specifically because it is irreversible on the write path — once dates are stored under the wrong interpretation, you cannot tell afterwards which reading was meant.

> **Lesson.** A relative date range ("this month", "last 7 days") is a question about the user's clock, not the server's. Resolve it where the timezone is actually known — the browser — and make the API accept explicit boundaries only. Any API that accepts the phrase instead of the dates has hidden a timezone bug inside its own convenience.

`GOTCHAS.md:64-66 (OPEN-TZ-01)`

---

### "Daily average" has three defensible meanings whose answers differ by ten times

**Believed.** "Average daily spending" is a self-explanatory figure; any competent implementation will compute the same number.

**Actually.** There are three reasonable denominators — days elapsed so far, days on which money was actually spent, or total days in the selected range — and on real data they differ by as much as ten times. Each one is defensible in isolation, so two people can implement "the same" feature, both be sure they are right, and disagree by an order of magnitude with no error anywhere.

**Caught by.** Caught during specification and ruled explicitly: days ELAPSED, capped at today (SW-ADR-010), with a worked example. The ruling is pinned by an expected value the never-waivable day-one proof checks against — the summary must return exactly 75810 paise against the seeded fixture, and the gate additionally proves the number is computed rather than fixtured by changing a seeded amount and watching the average move.

> **Lesson.** When a derived figure has more than one reasonable definition, ambiguity is a defect in the specification, not a detail for the implementer. Choose one meaning, write a worked example, and pin the exact expected number in a test — otherwise every later reimplementation silently picks its own definition.

`GOTCHAS.md:68-70 (SW-ADR-010); docs/10 EngineeringLedger/engineering_ledger.tsv:10`

---

### Password reset was made impossible by the security rule protecting it

**Believed.** Putting the password_resets table behind a row-level security rule keyed on the signed-in user's id was consistent with protecting every other table the same way.

**Actually.** Completing a password reset is unauthenticated by definition — the person is locked out, which is the entire reason the feature exists. There is no signed-in user id to key the rule on, so it matched no rows and account recovery was dead. A sibling decision had already spotted this exact class of problem for the users table and fixed it only there.

**Caught by.** A fresh-context quality pass over the decision records, before any code was written. Classified CRITICAL and fixed by taking that table out of row-level security, with the root cause named once rather than patched twice.

> **Lesson.** When applying a protective rule uniformly, check each path's caller. The one path that runs before authentication is exactly the path a rule based on identity silently switches off. And when you find a bug of this shape, name the class rather than the instance — the first fix repaired one table and left the other broken.

`PROGRESS.md GOAL_02 QA block; docs/01 ADR/all-ADRs/SW-ADR-071.md`

---

### The rate limiter opened a database connection for every request it then refused

**Believed.** Declaring the rate limiter as a parameter of the endpoint function placed it early in the request's path, before anything expensive happened.

**Actually.** Dependencies resolve in the order they appear in the signature, and the limiter sat after the database session. So every throttled request checked out a database connection and only then got refused — defeating the point of a limiter, whose job is to protect exactly that resource when a flood arrives.

**Caught by.** The acceptance test, which counts how many times the database stub is reached and asserts it was touched 10 times across 11 attempts. Fixed by moving the limiter to a route-level dependency, the same shape the admin permission check already used.

> **Lesson.** Where a check sits in the resolution order is part of what the check does. Test the cost of a rejected request, not only its status code.

`app/modules/auth/router.py:36,52,96; handoffs/HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### The never-waivable acceptance number was not deterministic, because nobody defined what a date range includes

**Believed.** The day-one gate's agreed value of 75,810 paise was a fixed, reproducible target that any correct implementation would hit.

**Actually.** No document said whether a date range from 1 August to 31 August includes both ends or excludes the last day. A half-open range — including the start, excluding the end — returns 94,762 against the same fixture. Two reasonable implementations would disagree by 25 percent on the one number the project treats as unfalsifiable. Two related gaps sat beside it: no timezone was named, so 'capped at today' was wrong for five and a half hours of every day on a UTC server, and the row-level security as written covered reads only.

**Caught by.** A sweep by five zero-context agents over the frozen requirements, each reading through a different lens. It was found before any code existed; the range is now ruled inclusive at both ends with a worked example.

> **Lesson.** An acceptance number is only an acceptance number once every input that determines it is written down. 'Everyone knows what a date range means' is where a quarter of the answer went missing.

`PROGRESS.md, GOAL_02 block; docs/01 ADR/all-ADRs/SW-ADR-085.md`

---

### An admin "count only" database policy returned every column, amounts included

**Believed.** A PostgreSQL row-level security policy (a rule attached to a table deciding which rows a connection may see) named `expenses_admin_count` was believed to let an administrator count someone's expenses without seeing what they cost, and a privacy requirement claimed this was structurally guaranteed.

**Actually.** Row-level security has no column dimension — it selects rows, never columns — and when several permissive policies apply they combine with OR, so the widest one wins. Any connection with `app.is_admin` set to 'true' could read every column of every expense row, amounts and descriptions included. The requirement that admins never see money was false at the database.

**Caught by.** A human reading the generated security.sql during the consolidated exit gate, after the whole document set was written. The handoff states plainly that no stated test could have caught it: the API returns the correct fields either way, so every test and screenshot looked right. Closed by SW-ADR-129, which replaced the policy with a function whose return type is the guard — it can only hand back a count.

> **Lesson.** Put a restriction at the layer that can actually express it. A row filter cannot enforce a rule about columns, and a test that only inspects the API response will never see the difference between "the database refuses" and "the API happens not to ask".

`HANDOFF_2026-08-05_1907_ani87.md; SW-ADR-129`

---

### A colour failed contrast by 0.01 because the background moved, not the colour

**Believed.** The client's new visual bundle listed the nine category band colours under "do not change" and predicted that if any pair failed readability it would be `--sw-border-strong`.

**Actually.** `--sw-border-strong` was indeed tightest at 3.33:1 — and passed. `--sw-cat-uncat` failed at 2.99:1 against a 3.0 floor, a miss by one hundredth. The band colour had not moved at all; the paper underneath it had. Contrast is a property of a pair, so changing one side re-tests everything on the other.

**Caught by.** Running `contrast.py --check` after the re-skin rather than trusting the bundle's own prediction. The replacement was picked at 3.07:1 and a closer candidate at 3.029:1 was deliberately rejected, because landing on a threshold with 0.029 of headroom is how the earlier contrast defect happened.

> **Lesson.** When you change a background you have changed every foreground. Recompute the whole set, not the items you touched, and leave real headroom above a threshold instead of just clearing it.

`SW-ADR-152 (CR-002); HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### Splitting a rate limit across workers with integer division lost an attempt

**Believed.** Dividing a rate limit across worker processes is plain division: each of the two workers gets `effective // workers` of the allowance.

**Actually.** Integer division rounds down, so 5 // 2 == 2 where the ruling table says 3. The formula reproduced six of the ADR's seven (effective, configured) pairs and got registration wrong. Rounding up reproduces all seven.

**Caught by.** A test written against the decision record's own table of numbers rather than against a rounding rule the author preferred. The handoff is explicit that this is the only reason it surfaced.

> **Lesson.** When a specification lists concrete values, test against those values. A test written against your restatement of the formula will agree with whatever formula you wrote, including the wrong one.

`app/core/ratelimit.py:94; SW-ADR-128; HANDOFF_2026-08-21_1605_aniruddha-jathar.md`

---

### A thorough, accurate AWS audit of entirely the wrong database

**Believed.** A session audited an RDS database instance in detail — engine version, availability zone, storage autoscaling, security group, snapshots — and reported the findings as the project's database.

**Actually.** It was a different instance in a different AWS account entirely: spend-wise-dev-db in account 545620235339, while the project's real database is spendwise-db in 944483082287. The credentials on that machine cannot see the project's database at all. Every observation was accurate; every one was about the wrong server. The audit did turn up something real — that instance is an orphan from an earlier session, still billing, with storage autoscaling to 1000 GB and a manual snapshot, and no project document mentions it.

**Caught by.** Comparing the observed values line by line against the AS BUILT record in the deployment prep queue: different account, engine version, availability zone, master user and security group.

> **Lesson.** Identify a resource by a key you recorded earlier, not by its name looking familiar, and do that before you audit it. Accurate data about the wrong object is more dangerous than no data, because it carries all the confidence of genuine observation.

`HANDOFF_2026-09-12_1341_ani87.md; docs/30 Deployment/AWS_PREP_QUEUE.md`

---

### A generated database bootstrap script that could not run at all

**Believed.** The generated rds_bootstrap.sql was ready to create the database roles and databases on RDS. It was written, generated, reviewed and committed.

**Actually.** It cannot run as written, for three separate reasons. psql does not substitute :'variables' inside a dollar-quoted DO $$ ... $$ block, so the password placeholder reaches the server literally and fails with a syntax error. PostgreSQL 16 and later require granting the owner role to the creating role before CREATE DATABASE ... WITH OWNER, which the script never does. And the script and the AWS prep queue disagree on the development database's name, with the queue being the wrong one.

**Caught by.** Trying to run it for the first time, weeks after it was written. It was worked around by hand; the fix belongs in the generator and is still outstanding.

> **Lesson.** A generated script that has never been executed is a draft, however carefully it was reviewed. Run it once against a throwaway target before recording it as a deliverable.

`docs/30 Deployment/rds_bootstrap.sql; HANDOFF_2026-08-25_1715_aniruddha-jathar.md`

---

### Two individually correct decisions that put a write inside a read-only snapshot

**Believed.** Two decisions, each sound alone: run the three dashboard aggregates in one consistent snapshot (REPEATABLE READ) so the breakdown adds up to the headline, and have the authentication dependency update the user's last-seen timestamp.

**Actually.** Together they place a write inside a repeatable-read snapshot. Two concurrent requests that both see the timestamp as stale both try to update the row; under REPEATABLE READ the loser gets PostgreSQL error 40001 and the request dies. The dashboard fires several requests at once, so this is an intermittent HTTP 500 that only appears under real concurrency. A second surprise fell out of it: the isolation level cannot be set with SET TRANSACTION ISOLATION LEVEL, because the identity call is already the first statement and PostgreSQL then raises error 25001.

**Caught by.** The document review rounds, by reasoning about two already-approved decisions in combination. The fix runs the timestamp update inside its own savepoint and carries on if it loses, and the isolation level is chosen when the connection is taken, before the transaction begins.

> **Lesson.** Two individually correct decisions can be wrong together, and the combination is nobody's review item. Hunt specifically for writes hiding inside things you declared read-only, and for shared per-request work that silently joins every transaction.

`GOTCHAS.md:130-148; SW-ADR-142 F; SW-ADR-143; SW-ADR-144`

---

### Thirteen decision records cited a source that existed only in a chat window

**Believed.** Thirteen of the first 22 architecture decision records cited "Client statement, 2026-08-05" as their authority, which reads like a proper citation and passed casual review.

**Actually.** It resolved to nothing on disk. The only evidence for those thirteen decisions was a chat transcript no future session would ever have, so each one was effectively unsourced while looking sourced — and a later session could neither verify nor safely reverse them.

**Caught by.** A citation checker written to resolve every reference to an actual clause in an actual file. It reported 84 citations across 48 files with zero unresolved only after the client's rulings were captured into a frozen, hash-stamped document and all 13 records were re-pointed at real clauses.

> **Lesson.** A citation is only a citation if it resolves to something a stranger can open. Capture verbal decisions into a durable document at the moment they are made, and run a checker that follows every reference rather than one that trusts its format.

`HANDOFF_2026-08-05_0433_ani87.md; docs/00 SourceOfTruth/SRC-002`

---

### A "generated, do not hand-edit" document whose hand-written prose had gone false

**Believed.** RUNTIME_VERSIONS.md carries a "GENERATED — do not hand-edit" banner, so its contents were treated as current, machine-maintained fact.

**Actually.** Its prose paragraphs are hand-written and never regenerate. Line 7 states "The build session does not write the Dockerfile", contradicting both a verbatim client instruction and an approved decision record saying the build session does write it — and contradicted by the repository itself, since the Dockerfile now exists and the build session wrote it. Line 83 says "no frontend exists yet"; the client app is built and pinned. Its database table records only the local PostgreSQL version and misses that local 18.3 and the project's RDS 17.9 disagree — the exact disagreement the document says is the fact that matters.

**Caught by.** A later session reading the file while orienting. Still unfixed. The risk is concrete and stated: a fresh session with no context reads the document, believes it, and refuses work it is actually authorised to do.

> **Lesson.** A "generated, do not edit" banner over a file that also contains hand-written commentary gives the commentary the trust of the generated part and the staleness of prose. Generate the facts; keep the narrative somewhere it will actually be reviewed.

`docs/30 Deployment/RUNTIME_VERSIONS.md:7 and :83; HANDOFF_2026-09-12_1341_ani87.md`

---

### A paraphrase of another document overrode the frozen requirements

**Believed.** The seed fixture needed a third account, an administrator, because — as the specification file's own justification cell said — '`P-ACC-02` refuses to start with zero admins'.

**Actually.** `P-ACC-02` actually reads: 'If no administrator exists **and the variable is unset**, the application refuses to start.' Setting `BOOTSTRAP_ADMIN_EMAIL` with zero administrators starts perfectly well. On that misreading the seed block overrode the frozen source's erratum E-6 ('two users seeded'), the constitution, and a binary acceptance criterion reading 'exactly 2 people' — the top of the authority order overridden by a document below it, inside the one artifact created to end such failures.

**Caught by.** The fifth cold-reader run. The record is blunt about why nothing else caught it: the misreading would have been caught by a human opening the file, and nothing in the pipeline opened it. A `contract-refs` check now resolves every specification id the contract names.

> **Lesson.** A 'why' cell that paraphrases another document is a citation, and citations deserve the same checking as code references. When you justify a decision by quoting a rule from memory, open the rule and read the whole sentence — the conditions are usually where the meaning lives.

`docs/01 ADR/all-ADRs/SW-ADR-142.md (Context item 1)`

---

### The colour that failed contrast had not changed — the background behind it had

**Believed.** The client's new palette explicitly listed the nine category band colours under 'do not change', so those nine were out of scope and their previously measured contrast figures still held.

**Actually.** Contrast is a property of a *pair*. `#948c87` measures 3.51:1 against the old paper `#faf7f2` and 2.99:1 against the new `#f2f5e9` — under the 3:1 floor. A palette decision that never mentioned category bands silently re-opened all nine of them.

**Caught by.** `tools/contrast.py`, which recomputes every pair rather than trusting the ones marked unchanged. It failed exactly one pair. The band was darkened within the same hue to `#928a85` (3.07:1); a candidate at 3.029:1 was rejected, because shipping 0.029 above a floor is its own trap.

> **Lesson.** When a value's correctness depends on two inputs, changing either one invalidates it. 'This side did not change' is not the same as 'this pair is still fine' — recompute the whole set, not the part that moved. A handoff that says 'do not change these' is describing inputs, not conclusions.

`docs/01 ADR/all-ADRs/SW-ADR-152.md (section 'Why the one band moved')`

---

### Account recovery was dead, because the recovery table was protected from the person recovering

**Believed.** Putting `password_resets` behind a row-level policy keyed on the verified user id was consistent with protecting every other table the same way.

**Actually.** Completing a password reset is unauthenticated by definition — the person is locked out, which is the entire reason the feature exists. With no verified user id the policy's key is unset, the token lookup matches nothing, and the update is denied. Account recovery could never have worked. The identical root cause had already been recognised and solved for the `users` table alone, and never generalised.

**Caught by.** The adversarial design review (QA FINDING-1, CRITICAL). A second instance of the same root cause survived all the way into shipped code: `POST /api/auth/reset/complete` opened a session with no identity set, so the session revocation it performs matched zero rows — leaving every session of a possibly-compromised account live while the response said the reset succeeded.

> **Lesson.** Access rules keyed on 'who is logged in' cannot serve any path that runs before login. Enumerate your pre-authentication paths — sign-in, registration, reset issue, reset redemption — and check each one against every rule that keys on identity. Fixing one instance of a root cause is not fixing the root cause.

`docs/01 ADR/all-ADRs/SW-ADR-071.md; second instance in SW-ADR-149.md Decision E`

---

### 'All timestamps NOT NULL DEFAULT now()' meant every session was born already revoked

**Believed.** A clean, uniform rule: every timestamp column is TIMESTAMPTZ, NOT NULL, defaulting to now().

**Actually.** Read literally it makes `sessions.revoked_at` non-null at insert — so every session is revoked the moment it is created — and `password_resets.used_at` non-null, so every reset token is born used. A sibling decision written in the same pass created a partial index on `revoked_at IS NULL`: an index over a condition its neighbour had made unsatisfiable. The same record also claimed there were eleven timestamp columns; there are ten.

**Caught by.** The adversarial design review (QA FINDING-10). Fixed by stating nullability per column and listing all ten by name rather than describing them.

> **Lesson.** A rule stated as a sweeping generalisation ('all X are Y') usually hides the exceptions that matter most. Enumerating the actual members is both the check and the fix — and a miscount in the summary is a strong signal that nobody ever enumerated.

`docs/01 ADR/all-ADRs/SW-ADR-076.md (superseding SW-ADR-024)`

---

### `ON DELETE SET NULL` on a composite key would have nulled a NOT NULL column

**Believed.** A composite foreign key on (user_id, category_id) enforces that an expense's category belongs to the same owner, and deleting a category should null the expense's `category_id` — which is what `ON DELETE SET NULL` does.

**Actually.** On a composite key, `ON DELETE SET NULL` nulls **every** referencing column, including `user_id`, which is NOT NULL — so the delete fails. The column-list form `ON DELETE SET NULL (category_id)` does the right thing but requires PostgreSQL 15, and no document pinned a version; the deployment queue was still asking the client which one they would create.

**Caught by.** The adversarial design review (QA FINDING-3, CRITICAL). Resolved with `ON DELETE NO ACTION` plus an explicit UPDATE inside the same transaction, requiring no version floor.

> **Lesson.** Referential actions on composite keys do not behave like the single-column case you are picturing. And a fix that depends on a database version nobody has chosen yet is a dependency, not a detail — before this record, not one foreign key in the schema stated its action at all.

`docs/01 ADR/all-ADRs/SW-ADR-072.md (superseding SW-ADR-035)`

---

### A security rule kept for a reason that turned out to be false

**Believed.** An upper bound on expense amounts was justified by the claim that `SUM()` over a bigint column raises 'bigint out of range'.

**Actually.** It does not. Postgres's `sum(bigint)` returns `numeric` precisely so that it cannot overflow — which the frozen source cited in that record's own sources says outright. The real overflow risk is the project's mandated cast of that sum *back* to a 64-bit integer, and the CHECK constraint is what keeps that cast safe.

**Caught by.** The adversarial design review (QA FINDING-13). The decision was right; only its stated reason was wrong.

> **Lesson.** A right decision propped up by a false reason is fragile in a specific way: the next person verifies the claim, watches large sums come back cleanly, concludes the rule was alarmist, and relaxes a control that is genuinely needed. Reasons get reused downstream — check them the way you check decisions.

`docs/01 ADR/all-ADRs/SW-ADR-079.md (superseding SW-ADR-036)`

---

### 'Not pinning the JWT algorithm is a total authentication bypass' — not on the version installed

**Believed.** An unpinned `jwt.decode` call is a complete authentication bypass, so passing `algorithms=['HS256']` was the control that protected the app.

**Actually.** On PyJWT 2.x — which the rest of the stack forces — `algorithms` is a required argument and omitting it raises an error. The described bypass is real only on PyJWT 1.x, which the record never mentioned and which nothing in the project prevented being installed. The control that was actually missing was a minimum version.

**Caught by.** The adversarial design review (QA FINDING-15). The explicit pin was kept (it costs nothing and is correct on any version) and `PyJWT>=2.4` was added to the pinned dependencies.

> **Lesson.** A vulnerability claim is only as true as the library version it was written about. When you inherit a security rule, find out which version makes it true and pin that version — otherwise you have performed the ritual without acquiring the protection.

`docs/01 ADR/all-ADRs/SW-ADR-080.md (superseding SW-ADR-045)`

---

### Every new user's first screen would have shown ₹0.00 where the spec required an em-dash

**Believed.** The PRD's `P-UND-06` described the empty-dashboard state: the daily average shows null, and the day series shows the full range of zero-valued days.

**Actually.** Those two cannot both hold. A full day series means time has elapsed, and the average formula then yields 0, not null. The underlying rule states 'null *when elapsed is zero*'; the PRD sentence dropped the qualifier. Built exactly as written, a new account opening the 1–31 August range on the 5th renders ₹0.00 where another specification requires an em-dash — on the first screen every new user sees.

**Caught by.** The fourth cold-reader run, as a side finding while pulling the error path into the generated contract.

> **Lesson.** Dropping a qualifier when restating a rule creates two specifications that look compatible and are not. When you paraphrase a rule into a second document, carry its conditions with it — and check any state described in two places against the formula that actually produces it.

`docs/01 ADR/all-ADRs/SW-ADR-141.md (Consequences)`

---

### A row-level security policy has no idea what a column is, so it leaked every column

**Believed.** An approved decision said the expenses table would get a database rule permitting admins 'aggregate reads only' — counts and totals, never the amount or the description of any single purchase. The written specification claimed this privacy promise was structurally true, enforced by the database itself rather than by application code.

**Actually.** PostgreSQL row-level security is exactly that — ROW level. A policy decides which rows you may see; it has no column dimension at all. The generated policy 'FOR SELECT USING (current_setting(app.is_admin) = true)' was an unqualified permissive policy, and permissive policies are combined with OR, so it handed back every column of every row — amounts and descriptions included — to any connection with that flag set. The decision as written was not implementable in the form it specified.

**Caught by.** A fresh reviewer working through the system with no prior context, during an uncoached review pass. The project explicitly recorded that no test in the suite could have caught it, because every test asserted on the API response fields and the API would have kept returning the right fields from a query that was allowed to read everything underneath.

> **Lesson.** Check that your security mechanism can express the restriction you wrote down, not just that it is switched on. Here the fix was to replace the policy with a function whose RETURN TYPE has only a count column — because a function has a signature and a policy does not, so 'an amount cannot come back' becomes a fact about the interface rather than a promise. Also: tests that only inspect the response shape prove nothing about what the query was permitted to read.

`docs/01 ADR/all-ADRs/SW-ADR-129.md`

---

### The same hex, in the same file, failing the same floor — fixed once, missed once

**Believed.** Colour readability had been checked by hand and the design system opened with a promise that every contrast figure was computed rather than asserted. An earlier decision had already found the colour #a8a29e failing and darkened it.

**Actually.** That earlier fix was applied to the Uncategorised category band only. The identical hex sat in the identical file as --sw-border-strong, doing a job with the identical 3:1 floor, measuring 2.36:1 — and was never re-checked, because the hand measurement was per-token: someone listed the bands, measured the bands, fixed a band. Nothing listed the borders.

**Caught by.** The first honest run of a new tool that computes every pair automatically, including pairs nobody thought to list. It found the border immediately.

> **Lesson.** A hand-maintained check measures what someone remembered to list, and that is its ceiling — the fix for the class is never more diligence, it is enumerating the population mechanically. The project's own framing is worth keeping: the earlier decision was not a failure of care, it was the limit of care.

`docs/01 ADR/all-ADRs/SW-ADR-147.md:76`

---

### Rounding the wrong way made one rate limit quietly looser than the rule said

**Believed.** Rate limits are counted per worker process because the counter lives in memory, so the configured per-process limit is the ruled limit divided by the worker count. Plain integer division seemed obviously right.

**Actually.** Floor division reproduces six of the seven ruled pairs and gets registration wrong: 5 divided by 2 gives 2, where the decision record says 3. Ceiling division reproduces all seven. Nothing would have failed — the throttle would simply have been stricter than recorded for one endpoint, with no log line and no error.

**Caught by.** A test asserting against the decision record's own table of (effective, configured) pairs, rather than against whatever rounding rule the implementer preferred. That framing is the only reason it surfaced.

> **Lesson.** When a specification lists concrete expected values, test against the list, not against the rule you think generated the list — the discrepancy between them is exactly where the bug is. A related trap in the same file: the worker count lives in two places (the startup command and the setting the limiter divides by), so a test asserts they are the same number, because one value with two homes and nobody comparing them is how limits silently drift.

`tests/test_rate_limits.py:234`

---

### A generator whose header promises to preserve a column, and whose code overwrites it

**Believed.** The engineering ledger's own header says it is derived from the story list and that 'exactly one column is hand-edited: Status' — which reads naturally as 'Status is preserved when you regenerate'. Regenerating looked like a safe way to pick up changes.

**Actually.** main() copies Status straight from the source story row and rewrites the evidence path to a fixed literal. So a regeneration silently reverts the entire build frontier to whatever the story list says and deletes every hand-written note recording WHY a story sits where it does. Two files hold the same column and the generator treats the other one as the source of truth.

**Caught by.** Reading the generator before running it, prompted by the trap ledger. It is also the one derived file the consistency checker does NOT verify by regenerate-and-compare — which is precisely what makes running the generator both tempting and expensive, since nothing would flag the loss.

> **Lesson.** Read what a generator actually does with your hand-edited data before you run it; a header sentence is documentation, not behaviour. Watch for the combination of two files holding the same field and one tool treating one of them as authoritative — and be most careful with the derived artifact that is NOT covered by your regenerate-and-compare check, because that is the one where damage leaves no trace.

`GOTCHAS.md:150, and docs/10 EngineeringLedger/generate_ledger.py:9 versus line 80`

---

### A privacy rule was written as a database policy that has no way to express it

**Believed.** Administrators could only read counts and dates. The guarantee was said to be enforced "structurally" at the database by a row-level security policy on the expenses table — the kind of policy that decides which rows a connection may see.

**Actually.** Row-level security works on rows, not columns; a policy has no way to say "these columns only". Worse, permissive policies for the same command are combined with OR, so the policy widened access instead of narrowing it: any connection with the admin flag set could read amount_paise and description for every row belonging to every person. The decision record that specified it conceded the problem in its own Consequences paragraph — "the reason it is safe is the response shape, not the policy" — while its Decision line said "aggregate reads only". Both sentences were in the same document.

**Caught by.** A cross-artifact contradiction sweep before any application code existed. Critically, no test in the project could have caught it: every test asserts on the shape of the API response, and the API would have kept returning exactly the right fields — from a query that was allowed to read everything. The defect lived one layer below every assertion in the project. The analysis is reasoned from documented PostgreSQL behaviour, not observed against a running database; a negative test exists to settle it.

> **Lesson.** A rule does not become true by being written carefully in a mechanism that cannot carry it. Before trusting a control, check the mechanism has the dimension your rule needs — and when a document argues against itself in two paragraphs, believe the pessimistic one. The durable fix was to make the guarantee a return type: a function that returns (count, last_activity) cannot leak an amount because there is no column for one.

`docs/06 DataModel/security.sql (policy expenses_admin_count) · SW-ADR-077 → SW-ADR-129 · docs/12 DesignReview/EX_Consolidated-Exit-Gate/01_CONSOLIDATED_EXIT_REPORT.md §1`

---

### Two approved decisions that could not both be carried out

**Believed.** Two records approved on the same day were each correct on its own: set the user-identity variable as the very first statement of the request transaction, and run dashboard requests at the stricter REPEATABLE READ isolation level so the parts of the summary agree with its total.

**Actually.** PostgreSQL rejects SET TRANSACTION ISOLATION LEVEL once any query has run in the transaction, with error 25001, "must be called before any query". Executed literally, the dashboard either fails on every request or silently stays at the weaker isolation level — which is precisely the intermittent bug the isolation requirement was written to prevent.

**Caught by.** The sixth fresh-engineer run, which verified the contract's cells against the records they cite one at a time. The fix selects the isolation level on the connection at checkout, before the transaction opens.

> **Lesson.** Two rules can each be approved and jointly impossible. Whenever a decision says "this must run first", search for every other decision that says the same thing, and check they are not both talking about the same slot.

`docs/01 ADR/all-ADRs/SW-ADR-143.md §1 · SW-ADR-136 B · SW-ADR-142 F · GOTCHAS.md:131-148`

---

### Three tests asserted the product does not do something it was deliberately built to do

**Believed.** An acceptance criterion read "no endpoint lets a person change their own email, display name or password", and four test cases were written from it.

**Actually.** Two thirds of it was false of the shipped product, and the falsity was approved: endpoints for changing a display name and changing a password were both added later by an approved, released decision. A second criterion specified its own verification method as "grepping for a delete-user operation", which now finds the soft-delete route and fails against correct code — even though the substance of the criterion still holds, since no row is ever destroyed and the runtime role holds no delete permission on the users table.

**Caught by.** The build session, while preparing to implement the story. The trap is that the obvious way to make the tests green is to delete the approved features. The session marked the story blocked and escalated rather than editing the definition of done to match what had been built.

> **Lesson.** When a test fails against code you believe is correct, check the dates before changing either — the test may be older than the decision that authorised the code. And a criterion that names its own method ("grep for X") ages badly: it can become literally false while what it means remains true.

`docs/12 DesignReview/FINDING_E6-S5_acceptance-criteria-contradict-SW-ADR-148.md · docs/05 Bible/SpendWise_Bible.csv story E6-S5 · SW-ADR-148, SW-ADR-153`

---

### The requirements document stated a false technical fact with complete confidence

**Believed.** The client's requirements said Alembic takes an advisory lock during migrations, so two containers starting at the same time could not both run the same migration. This is widely believed.

**Actually.** It does not. Two tasks booting together can both run the upgrade and race. The fix is to take a PostgreSQL advisory lock explicitly in the migration environment file. Two further claims in the same document, about how the rate limiter behaves, were also wrong.

**Caught by.** Deliberately verifying the load-bearing technical claims in the requirements before letting them become specification. Each was recorded as a numbered erratum against the frozen source rather than edited into it.

> **Lesson.** A premise inherited without checking is a bug with a long fuse. Confidence in a requirements document is not evidence, and the claims worth verifying first are the ones the design rests on.

`GOTCHAS.md:29-33 · docs/00 SourceOfTruth/SRC-001 erratum E-4 · SW-ADR-019`

---


# The fix caused it

*A repair that broke something else. In five of seven design-review rounds on this project, at least one finding was introduced by the previous round.*

**15 recorded.**

### The fix that made the dashboard numbers consistent gave the dashboard intermittent 500s

**Believed.** Putting the three summary figures in one snapshot — REPEATABLE READ, a mode where a transaction sees one frozen picture of the data throughout — fixes the category breakdown not adding up to the headline total, and costs nothing else (SW-ADR-142 F).

**Actually.** A separate, separately-approved decision (SW-ADR-136) had the authentication step update a `last_seen_at` timestamp — a WRITE — inside that same transaction. The dashboard deliberately fires several requests at once (documented in journey J-U-09). When two of them both see the timestamp as stale, both try to update the same row; under REPEATABLE READ the loser is killed with Postgres error 40001, "could not serialize access due to concurrent update", and the request dies as a 500. Under the ordinary READ COMMITTED mode the second one would simply have waited its turn and succeeded. The failure is intermittent, needs concurrency to appear, and so shows up in production and not on a developer's machine.

**Caught by.** Found by reasoning across two decisions that were each correct in isolation, before the combination shipped. The repair: the timestamp update runs inside its own SAVEPOINT (a rollback point within a transaction), and on a 40001 the code rolls back just that savepoint and carries on. Losing one timestamp bump is harmless because whichever transaction won already performed it.

> **Lesson.** Two individually correct decisions can be wrong together, and nothing in a per-change review catches that. Raising an isolation level converts waiting into failing, so before you raise one, inventory every write that shares the transaction — including the small bookkeeping writes (counters, last-seen stamps, audit rows) that nobody thinks of as writes.

`GOTCHAS.md:130-144 (SW-ADR-142 F with SW-ADR-136)`

---

### The isolation level cannot be set inside the request, and the obvious workaround empties every query

**Believed.** To get the snapshot behaviour above, just issue `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` at the top of the request.

**Actually.** `set_config('app.user_id', …)` is already the first statement of the transaction, and PostgreSQL refuses to change the isolation level once a query has run — error 25001. The natural workaround, deciding the level during dependency resolution, opens a SECOND transaction, which loses the `app.user_id` setting and silently returns zero rows for every protected query, everywhere. The repair that ships: pick the level on the connection at checkout, before `BEGIN`, from a fixed table of routes — never from the order dependencies happen to resolve in.

**Caught by.** Worked out during design (SW-ADR-143, SW-ADR-144) while resolving the previous bug. Had the workaround been taken, the symptom would have been an application that returned empty results with no errors — the hardest possible thing to debug.

> **Lesson.** When two constraints each insist on being "first", neither belongs inside the request; push the decision out to connection setup. And treat any fix that quietly opens a second transaction as suspect — it silently discards everything scoped to the first one.

`GOTCHAS.md:145-148 (SW-ADR-143, SW-ADR-144)`

---

### The decision written to stop queries returning zero rows produced queries returning zero rows

**Believed.** Declaring the dashboard summary route's transaction settings in a second, route-specific dependency would set the database isolation level without disturbing anything else.

**Actually.** The identity value that row security depends on is transaction-scoped, and the dependency that sets it is declared at the router level. The web framework resolves router-level dependencies before a route's own parameters, so the identity landed in transaction one while every summary query ran in transaction two with no identity at all. Row security then returns nothing — an empty dashboard, indistinguishable from a person who has spent nothing.

**Caught by.** The seventh review pass, by someone implementing the record faithfully. Three of that round's seven findings were defects the previous two rounds had created.

> **Lesson.** A repair is new code and carries the same defect rate as any other. If a fix depends on framework ordering you have not verified, you have moved the bug rather than removed it — and the worst version of this bug answers with emptiness instead of an error.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md:88-96`

---

### Hand-written example payloads, labelled authoritative, became the largest source of new defects

**Believed.** The specification described behaviour in prose for about 2,500 lines and contained a single JSON example, which was the reviewers' dominant complaint; writing two worked example payloads and marking them normative would settle the ambiguity.

**Actually.** The next reviewer found, inside that one new section: a field five other documents assert on missing entirely, a 0 where six documents say null, two category names that do not exist, the words 'ordered descending' printed over an array that is not ordered, two required fields dropped, and the wrong decision cited for the one number that can never be waived. Seven of that round's twenty-one findings came from the fix for the previous round.

**Caught by.** The next fresh-context reviewer in the loop. Across seven rounds the counts went 18, 21, 15, 8, 8, 8, 7 — and in five of the seven, at least one finding was a defect introduced by the previous round's repair.

> **Lesson.** A hand-written example drifts out of date exactly as easily as the prose it replaces, and once it is labelled authoritative it drifts with authority. Examples belong in generated output, produced from the same source the code is checked against.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md:72-80`

---

### Adding rate limiting broke the browser suite, and nobody noticed for weeks

**Believed.** The browser-observed test suite — the gate that watches the product work in a real browser — was assumed simply not to have been run yet, because it was waiting on a database.

**Actually.** It could never have passed. Its fixture starts its own server with `SPENDWISE_DOTENV=0`, so the .env file is not read and `RATE_LIMIT_ENABLED` falls back to its field default of true. The suite registers dozens of accounts against a limit of 5 registrations per minute, so 34 test setups died on HTTP 429 before asserting anything at all. The fixture predates the story that added rate limiting, and nothing re-ran it afterwards.

**Caught by.** Running the browser suite to verify an unrelated one-line UI change. A single line in tests/browser/conftest.py fixed it, and the browser gate passed for the first time in the project's life.

> **Lesson.** Adding a global guard silently invalidates every test harness that predates it — above all harnesses that build their own environment instead of reading the shared one. After you add a limit, go and run the suites nobody has run lately.

`tests/browser/conftest.py:92; HANDOFF_2026-09-01_1302_aniruddha-jathar.md`

---

### A review loop that injected defects at roughly the rate it removed them

**Believed.** Repeatedly handing frozen documents to a fresh engineer who is forbidden to ask questions, then fixing every ambiguity they hit, would converge on zero guesses.

**Actually.** It did not converge. Seven rounds ran 18 → 21 → 15 → 8 → 8 → 8 → 7 guesses, and in five of the seven at least one finding was a defect introduced by the previous round's repair. Each fix added new surface for the next reader. The stated definition of done — zero guesses — was never reached, and is recorded as a failure rather than smoothed over.

**Caught by.** The log itself, by tracking where each round's findings originated. The decisive observation is that the late rounds' best findings — a bootstrap deadlock, no permissions granted on any table, an isolation-level error, a missing reset clause — would each have been caught in minutes by a Python interpreter and a real PostgreSQL.

> **Lesson.** Review loops over documents have their own defect-injection rate, so past a point more rounds stop buying correctness. When the remaining findings are things a compiler or a real database would catch in minutes, stop reviewing and run the thing.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md; HANDOFF_2026-08-05_1907_ani87.md`

---

### The fix for one isolation bug faithfully re-created the bug it was written to prevent

**Believed.** `SW-ADR-143` resolved a conflict between two rules — 'set the user id as the first statement in the transaction' and 'run the summary at REPEATABLE READ isolation' — by saying the isolation level comes from 'a second session dependency (`get_db_rr`) that only the summary route declares'.

**Actually.** Implemented literally, that opens two database transactions. `get_current_user` is attached to the whole router, and FastAPI resolves router-level dependencies before a path operation's own parameters — so the user id lands in transaction #1 and `get_db_rr` opens transaction #2. The per-connection setting is transaction-local, so every summary query in transaction #2 ran with no user id and the per-row rules returned zero rows: an empty dashboard indistinguishable from a person who has never spent anything.

**Caught by.** The seventh run of the cold-reader exercise. Three of that run's seven findings were defects the same session had introduced in the two previous rounds. Fixed by holding one session on `request.state.db` and resolving the isolation level from an explicit route table, with a boot assertion that fails closed if the table and the route markers disagree.

> **Lesson.** When you fix a bug by adding an indirection, trace the new execution order end to end — especially under a framework that resolves dependencies in an order you did not choose. Repeated review of the same artifact is what catches repairs that introduce defects; the count of findings going *up* in one round was the reason to trust the process, not to stop it.

`docs/01 ADR/all-ADRs/SW-ADR-144.md (amending SW-ADR-143 Decision A)`

---

### A live decision was withdrawn by a bookkeeping side effect, then the repair spread the error to fourteen places

**Believed.** The chain of 'this record supersedes that record' links in the decision log was accurate, and an automated consistency checker validated that every link resolved.

**Actually.** `SW-ADR-088` was a *labelling* record: it declared that AWS-related claims in six other records were reasoned rather than observed. It named those six in its Decision and put the first of them into its `Supersedes` field. The banner tooling then marked `SW-ADR-023` — 'BIGINT identity on every table', the authority behind every primary key in the schema — as SUPERSEDED, and the ledger followed. It was silently withdrawn by a clerical side effect, and then cited fourteen times as live authority, which was accidentally the correct reading. A second broken link had quietly dropped the module-to-table ownership map on the floor.

**Caught by.** A deliberate topic-coherence audit of all 22 supersession links, asking not 'does this link resolve?' but 'does the successor actually cover the subject of the record it replaces?'. Three of the 22 were broken. Before that audit, a repair pass had made it worse by re-pointing all fourteen citations to `SW-ADR-088`, a record about AWS-claim labelling that says nothing about primary keys.

> **Lesson.** A link that resolves is not a link that is true. And a repair pass that trusts upstream metadata inherits upstream defects — before mass-updating references, open the thing you are pointing them at and confirm it says what you think. A field named 'supersedes' means 'this replaces that', not 'this is about that'.

`docs/01 ADR/all-ADRs/SW-ADR-132.md`

---

### The snapshot that fixed the summary put a write inside it, turning the dashboard into an intermittent 500

**Believed.** Running the summary request at REPEATABLE READ isolation would make the breakdown sum to the headline, with no other effect.

**Actually.** The authentication dependency also bumps `sessions.last_seen_at` — a write, now inside that stricter snapshot. Two concurrent requests from one browser that both see the timestamp as stale will both update the same row; under REPEATABLE READ the loser gets Postgres error 40001, 'could not serialize access due to concurrent update', and the request dies. Under READ COMMITTED it would simply have waited and succeeded. The project's own journey document records the dashboard firing several requests at once, so this is a 500 on the main screen, intermittently, in production only.

**Caught by.** The sixth cold-reader run, reasoning about the interaction of two decisions made the same day by the same session. Fixed by running the timestamp bump inside its own SAVEPOINT and carrying on if it loses — losing one bump is harmless, because the transaction that won already did it.

> **Lesson.** Raising an isolation level is not a free correctness upgrade. It converts contention that used to block-and-succeed into errors the caller must handle, and it applies to every write that happens to sit inside the transaction, not only the reads you were thinking about.

`docs/01 ADR/all-ADRs/SW-ADR-143.md (Decision B)`

---

### Adding rate limiting broke the browser test suite, and nobody re-ran it for weeks

**Believed.** The browser-driven test suite — the half of the day-one proof that watches a real browser — was believed to be in working order. It was recorded in one handover as simply 'never run'.

**Actually.** The browser fixture starts its own web server with the .env file switched off, so the rate-limit setting fell back to its field default of ON. The suite registers dozens of accounts against a limit of five registrations per minute, and 34 test setups died on HTTP 429 before asserting anything. The fixture predated the commit that added rate limiting, and nothing re-ran it afterwards. The settings file already stated the intended rule — the test suite turns limiting off for everything except the rate-limit tests — the browser fixture just never obeyed it.

**Caught by.** A developer verifying an unrelated change (moving the sign-out button) actually ran the browser suite, and read the failures instead of dismissing them. One line in the fixture fixed it, and the browser half of the gate went green for the first time in the project's life.

> **Lesson.** When you add a cross-cutting protection, list every process that starts the application and check each one. A test suite that has 'never been run' is not neutral — it is an unknown, and it accumulates breakage from changes that were never checked against it. Defaults that differ between the real environment and the test harness are where this hides.

`handoffs/HANDOFF_2026-09-01_1302_aniruddha-jathar.md:52`

---

### Two correct decisions combined into an intermittent 500 on the busiest screen

**Believed.** One decision put the dashboard's three summary figures into a single consistent database snapshot, so the category breakdown always adds up to the headline total. A separate decision had the authentication step update a 'last seen' timestamp on the user's row. Each was reasonable on its own and each was approved.

**Actually.** The snapshot is a stricter isolation level (REPEATABLE READ), and the timestamp update is a WRITE that now happens inside it. The dashboard fires several requests at once. If two of them both see the timestamp as stale, both try to update the same row — and under REPEATABLE READ the loser gets error 40001, 'could not serialize access due to concurrent update', and the request dies. Under the ordinary isolation level it would simply have waited and succeeded. The result is an intermittent 500 on the dashboard, in production only.

**Caught by.** By reasoning about the interaction of two approved decisions while writing them up, not by a test — concurrency of this kind rarely shows up in a sequential suite. The fix wraps the timestamp update in its own savepoint and rolls back just that on 40001; losing one bump is harmless because the transaction that won already did it.

> **Lesson.** Two individually correct changes can combine into a defect that neither review would find, because each was reviewed alone. Stricter isolation is not free: it converts waiting into failing. Whenever you raise an isolation level, enumerate every write that now falls inside that scope — including small incidental ones like activity timestamps that nobody thinks of as writes.

`GOTCHAS.md:130`

---

### The fix for "the spec has no examples" was a hand-written example that then drifted with authority behind it

**Believed.** Round one's loudest complaint was that the specification described behaviour in about 2,500 lines of prose and contained one block of example JSON. The repair was to hand-write two worked response payloads and label them normative — meaning the code must match them exactly.

**Actually.** The next fresh reader found eight defects inside that one new section: an entire required field (the per-day breakdown) missing, though the frozen requirements ask for one row per calendar day and a test asserts on it by a name that did not exist; 0 where six other documents say null; a date range contradicting both the decision record and the executable test; two category names that are not on the approved list; the words "ordered descending" printed directly above an array that is not sorted; two required fields dropped; and the wrong record cited as the source of the one number the project can never get wrong.

**Caught by.** The very next round of the review loop, one iteration later. Seven of that round's twenty-one findings were created by the repair for the round before it — which is why this is recorded as the most valuable result the whole gate produced: it indicts the method rather than the artifact.

> **Lesson.** A hand-written example is exactly as able to drift as the prose it replaces, and once you label it normative it drifts with authority. The fix that held was to generate the example from the rule, so the two cannot disagree — the contradiction was made unrepresentable rather than corrected.

`docs/03 PRD §6.1 · SW-ADR-138 · docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md`

---

### The record written to prevent zero-row queries produced zero-row queries

**Believed.** Round six found that two approved decisions could not both be executed, so a new record was written to reconcile them. Its Decision A said the stricter transaction isolation the dashboard needs would come from "a second session dependency that only the summary route declares."

**Actually.** Implemented literally, that opens two database transactions. The current-user dependency is declared at the router level, and FastAPI resolves router-level dependencies before a path operation's own parameters — so the statement that sets the user identity lands in transaction one, while every dashboard query runs in transaction two with no identity set at all. The setting is transaction-local, so it is simply gone, and row-level security returns nothing. The project's own trap ledger calls this the worst failure shape in the system, because an empty dashboard is indistinguishable from a person who has spent nothing.

**Caught by.** The seventh fresh-engineer run, reading the record that had been written two rounds earlier specifically to prevent this failure. Three of that round's seven findings were defects introduced in rounds five and six.

> **Lesson.** Dependency-resolution order is part of your transaction boundary. When a fix depends on "this runs first", write down what actually guarantees the ordering — and prefer a mechanism that cannot be resolved out of order. The replacement puts one session on the request object and picks the isolation level at connection checkout, before the transaction begins.

`docs/01 ADR/all-ADRs/SW-ADR-143.md lines 3–12 (the amendment banner) · SW-ADR-144`

---

### A newly built artifact overrode the frozen requirements on a misreading of one clause

**Believed.** The test seed data needed a third person, and the block creating them justified itself in its own cell: "the specification refuses to start with zero admins."

**Actually.** The specification says the application refuses to start when no admin exists *and the bootstrap-admin email setting is unset*. Dropping that second condition turned a narrow rule into a general one. On that misreading the seed block overrode the frozen client requirements, the project constitution's own scope article, and a binary acceptance criterion — the top of the authority order overruled by a document one level below it, inside the very artifact built to stop exactly that.

**Caught by.** The fifth fresh-engineer run, which found all eight of its guesses inside the API contract file — the artifact created two rounds earlier as the repair for the hand-written-example problem.

> **Lesson.** When a document cites a rule as its justification, go and re-read the rule. A dropped qualifier is invisible and the citation makes the error look researched. Freshly written artifacts deserve more suspicion than old ones, not less.

`docs/03 PRD/api/contract.json (seed block) · docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md`

---

### The repair trusted the broken field and re-pointed fourteen citations at an unrelated record

**Believed.** The way to fix stale citations in bulk is to follow each record's Supersedes field to its successor and update the references.

**Actually.** That field was itself the defect. The pass moved fourteen citations from "primary keys are BIGINT identity columns" to "claims about AWS in build-session records are labelled reasoned rather than observed" — two subjects with nothing in common. For about twenty minutes the corpus was worse than before the repair started.

**Caught by.** A keyword heuristic that fired on the *result* of the repair rather than on the original defect, which prompted the audit that found three broken supersession links including this one. It is recorded in a decision record rather than quietly reverted.

> **Lesson.** A repair pass that trusts upstream metadata inherits upstream defects and spreads them wider than they started. Before a bulk edit, hand-check a sample of the source you are about to trust — and afterwards, run a check that looks at the output, not the input.

`docs/12 DesignReview/EX_Consolidated-Exit-Gate/08_REVIEWER_SELF_CHALLENGE.md §2 · SW-ADR-132`

---


# Environment

*The machine, the shell, or the platform — not the code.*

**11 recorded.**

### The browser test suite had never once run to completion, and the cause was one line in a fixture

**Believed.** The 55 browser criteria, including the day-one gate observed in a real browser, simply had not been run yet.

**Actually.** tests/browser/conftest.py starts its own web server with the dotenv loader disabled, so the .env file is never read and RATE_LIMIT_ENABLED falls back to its code default of true. The suite registers dozens of accounts against a limit of five registrations per minute, so 34 test setups died on a 429 Too Many Requests before asserting anything. The settings file already stated the intent — the test suite turns rate limiting off except for the rate-limit tests — and the browser fixture simply never obeyed a rule the in-process suite already followed.

**Caught by.** Someone verifying an unrelated interface change ran the browser suite and read the failures. The fixture predates the story that added rate limiting, and nothing re-ran it afterwards.

> **Lesson.** When a new feature changes behaviour globally, re-run every suite, not only the one you are writing. A test environment that assembles its own configuration will quietly drift away from the one the rest of the suite uses.

`tests/browser/conftest.py:85-92`

---

### The container refused to boot because the pipeline handed one superuser to both database URLs

**Believed.** Pointing both MIGRATION_DATABASE_URL and DATABASE_URL at the CI PostgreSQL service's single superuser was a harmless shortcut for tests.

**Actually.** The whole isolation design rests on two roles: an owner that runs migrations and owns the tables, and a runtime role that owns nothing and cannot bypass row security. One superuser for both makes every isolation test pass for the wrong reason, because a superuser is never filtered. alembic/env.py raises on exactly that condition and quotes the governing decision in the error text.

**Caught by.** The guard itself, written weeks before any pipeline existed to trip it — the application enforcing its own invariant against the pipeline configuring it. Fixed by creating the two roles the baseline migration grants to by name.

> **Lesson.** Write invariants into the application as startup checks, not only into documents. A guard that refuses to boot catches misconfiguration arriving from directions you never anticipated.

`alembic/env.py:55-60; PROGRESS.md session 2026-08-25`

---

### Four parallel agents sharing one test database deadlocked PostgreSQL

**Believed.** Splitting the change-request build across four agents working in parallel would be faster.

**Actually.** All four ran pytest against the same spendwise_test database. Each test begins by emptying the tables with TRUNCATE ... RESTART IDENTITY CASCADE, so one process's truncate landed in the middle of another process's seeding and PostgreSQL raised a genuine DeadlockDetectedError. No agent could obtain one clean full run of the suite while it was happening.

**Caught by.** The deadlock errors themselves. A clean sequential run of all 418 tests was only achieved afterwards, which is why the handoff records that green as first-time evidence rather than routine.

> **Lesson.** Test isolation that works by wiping shared state is only safe while nothing else shares that state. Parallel runs need a database per worker or a lock — and the cost of getting it wrong is that every run becomes untrustworthy, not that one test fails.

`PROGRESS.md, session 2026-08-06; handoffs/HANDOFF_2026-08-06_0442_ani87.md`

---

### A thorough database audit was run against the wrong database in the wrong cloud account

**Believed.** The database instance the session connected to and audited in detail was this project's live database.

**Actually.** The as-built record says spendwise-db, PostgreSQL 17.9, in account 944483082287. The session queried spend-wise-dev-db, PostgreSQL 18.3, in account 545620235339 — an orphan created on 2026-08-05 and abandoned when the project moved accounts. It is still running, with storage autoscaling up to 1000 GB, a manual snapshot, and two paid monitoring features switched on, in an account no document mentions. The local .env and a notes file still point at it.

**Caught by.** Comparing the queried instance's version and account id against the AS BUILT section of the deployment document. The version mismatch — 18.3 against a recorded 17.9 — was the tell.

> **Lesson.** Before auditing infrastructure, assert the identity of what you are connected to — account, region, instance name, version — against the written record. Stale local configuration points at real, running, billable things.

`PROGRESS.md, session 2026-09-12; docs/30 Deployment/AWS_PREP_QUEUE.md (AS BUILT)`

---

### The never-waivable acceptance gate read the wall clock and went red at midnight

**Believed.** The day-one gate — the proof that the dashboard totals exactly 75810 paise from seeded rows — was believed fully pinned down. The contract stated the expected value, its allowed range, the rounding formula, and three specific wrong answers.

**Actually.** It never stated the date the value is computed against. "Daily average" divides by days elapsed in the current month, so at midnight four assertions went red with no code change whatsoever.

**Caught by.** The clock. The same commit produced different results either side of midnight. Fixed by adding an explicit `gate.as_of` date to the contract.

> **Lesson.** Any expected number derived from "today" is a test that changes its own answer while you sleep. Freeze the evaluation date next to the expected value, or the test is measuring the calendar rather than the code.

`SW-ADR-146; HANDOFF_2026-08-06_0442_ani87.md`

---

### CI handed one superuser to both database roles and the app refused to boot

**Believed.** For CI it is fine to point both `MIGRATION_DATABASE_URL` and `DATABASE_URL` at the single superuser account the throwaway postgres service container provides. It is a disposable database.

**Actually.** One role for both means the connection serving traffic also owns the tables — and a table owner can switch off `FORCE ROW LEVEL SECURITY` on itself, dissolving the one guarantee this product exists to make. The container refused to start: the migration bootstrap raised on the two URLs being equal, naming the reason.

**Caught by.** The application's own startup assertion, firing against the pipeline that was configuring it. Fixed by creating the two separate roles in CI and pointing each URL at the right one.

> **Lesson.** Write your security invariants as assertions the program makes about itself at startup, not as instructions in a runbook. Then a convenient shortcut in the pipeline fails loudly instead of quietly weakening the guarantee production depends on.

`alembic/env.py (SW-ADR-081); HANDOFF_2026-08-25_1556_aniruddha-jathar.md`

---

### A whole session reasoned from a five-week-stale checkout and told the client five false things

**Believed.** The session-start tool reported the newest handoff in the repository, so the session believed it knew where the project stood and advised the client accordingly.

**Actually.** There are two checkouts of this project on the machine. This one sat 16 commits behind at a five-week-old commit, and the tool truthfully reported the newest handoff in this checkout. Five statements made to the client as fact were wrong: that no Dockerfile existed, that rate limiting was unbuilt and every auth endpoint unthrottled, that a specified error code was unimplemented, that a three-week-old plan was still the order of work, and that the local and RDS PostgreSQL versions agreed.

**Caught by.** Comparing against the upstream remote during session close-out, then rebasing. Every wrong claim was written into the handoff as an explicit correction rather than quietly dropped.

> **Lesson.** "Latest" from a local tool means latest locally. Before reasoning about where a project stands, fetch and confirm your checkout is at or past the upstream tip — especially on a machine that has more than one clone.

`HANDOFF_2026-09-12_1341_ani87.md`

---

### Parallel test agents deadlocked on one shared database, and none could get a clean run

**Believed.** Running four agents' test suites in parallel against one shared test database would simply be faster.

**Actually.** Each test resets state with `TRUNCATE ... RESTART IDENTITY CASCADE`, so one process's truncation landed in the middle of another's seeding and PostgreSQL raised a real DeadlockDetectedError. No agent could obtain a clean full run while the work was parallelised; the first clean sequential run of all 418 tests only happened afterwards.

**Caught by.** The deadlock errors themselves. The handoff is careful to record it as a fault in how the work was parallelised rather than in the code, and instructs future sessions not to parallelise the suite against this database without a per-worker database or a lock.

> **Lesson.** Per-test truncation and parallel workers on one shared database are mutually exclusive. Give each worker its own database or serialise — and when tests fail only under parallelism, suspect the harness before the code.

`HANDOFF_2026-08-06_0442_ani87.md`

---

### A whole session audited the wrong database, in the wrong cloud account, from a five-week-stale checkout

**Believed.** A working session read the newest handover note in its folder, oriented itself, and reported on the project's state and its cloud database in detail. Everything it said was internally consistent.

**Actually.** There were two checkouts of this repository on one machine. This one sat 16 commits and five weeks behind, so the 'newest handover' it found was genuinely the newest in THAT folder and not the newest that existed. Every conclusion about what was built was consequently wrong: it reported the container file as unwritten (it existed), rate limiting as unbuilt (it was done), and a defect as unfixed (it was fixed). Separately, the cloud credentials on that machine belonged to a different account entirely, so the database it audited thoroughly — version, availability zone, firewall, storage settings — was an abandoned instance from an earlier session, still running with storage autoscaling up to 1000 GB, billing in an account no project document mentions.

**Caught by.** The session itself, during close-out, by comparing what it had queried against the AS BUILT record in the deployment queue — two different instance names, two different account numbers, two different PostgreSQL versions. It then wrote a 'corrections to claims made during this session' table rather than quietly dropping the wrong statements.

> **Lesson.** Orientation tooling reports what is in front of it, truthfully, and that is not the same as what is true. Before trusting any state summary, confirm which checkout you are in and that it is current; before trusting any infrastructure finding, confirm the identity of the thing you queried against a written record. Observations can be accurate in content and completely wrong in relevance.

`handoffs/HANDOFF_2026-09-12_1341_ani87.md:42`

---

### The browser gate had never once run to completion, because the tests rate-limited themselves

**Believed.** The browser suite was just slow and awkward, and the day-one proof observed in a real browser simply had not been got to yet.

**Actually.** The browser fixture starts its own web server with the .env loader switched off, so the configuration file is never read and the rate-limiting flag falls back to its code default of true. The suite then registers dozens of accounts against a limit of five per minute, and 34 test setups died on an HTTP 429 before asserting anything at all. The fixture predates the change that added rate limiting, and nothing re-ran it afterwards.

**Caught by.** Sitting down to make the browser gate green for the first time. The cause was one line; setting the flag explicitly in the fixture's environment fixed it, and all 55 browser criteria then passed.

> **Lesson.** When a test process boots its own server with a deliberately empty configuration, every setting silently falls back to its code default — including settings introduced long after the fixture was written. Any feature that changes global behaviour should be checked against every place that starts the application, not just the main one.

`tests/browser/conftest.py:76 (SPENDWISE_DOTENV: "0") and :92 (RATE_LIMIT_ENABLED: "false")`

---

### A session audited the wrong database, in the wrong cloud account, and reported the wrong project state

**Believed.** The working copy was current, and the database instance being audited was this project's.

**Actually.** The checkout was five weeks and sixteen commits stale, so the start-of-session tooling truthfully reported the newest handoff *in this checkout* — which was not the newest that exists. Every conclusion about remaining work was wrong as a result: it reported the container file as unwritten (it exists), rate limiting as not started (done), and a validation fix as unimplemented (fixed). Separately, the instance audited was a different one, running PostgreSQL 18.3 in a different cloud account, an orphan from before the project moved accounts — still running, with storage autoscaling to 1000 GB, in an account no document mentions.

**Caught by.** Comparing the audit against the as-built record, which named PostgreSQL 17.9 where the audit had found 18.3.

> **Lesson.** Before trusting any status report, confirm you are looking at the current copy and the right resource. A tool that faithfully reports what it can see will confidently mislead you when what it can see is stale — and a version number is the cheapest way to notice you are pointed at the wrong thing.

`PROGRESS.md, session 2026-09-12 · handoffs/HANDOFF_2026-09-12_1341_ani87.md`

---

### A decorative glow widened the phone page by 11px, and no bounding-box check could see it

**Believed.** The overflow audit was complete: a script walked every element at 375px, found nothing whose `getBoundingClientRect().right` passed the window, so nothing could be making the page scroll sideways.

**Actually.** `scrollWidth` was 386 against a 375 window. The culprit was the soft glow behind the money tree, drawn by `.mt-stage::before` with `inset: -4% -8% 18%`. Pseudo-elements are not in `querySelectorAll`, so every element-walking check skipped it, while its box still counted toward the page's scrollable width. On a phone the dashboard's tree sits near the right gutter, and 8% past its side was 11px past the window.

**Caught by.** `test_nothing_overflows_at_375px`, which measures `scrollWidth - clientWidth` rather than walking elements, failing on the branch's first browser run (2026-10-20). Fixed by keeping the glow inside the tree's own width (`inset: -4% 0 18%`).

> **Lesson.** An audit that enumerates elements cannot see pseudo-elements, so it can report "nothing overflows" while the page overflows. Measure the outcome (`scrollWidth` against the viewport), not just the parts you can list, and keep decoration inside its host's width unless something clips it on purpose.

`client/src/styles/screens/money-tree.css (.mt-stage::before) · tests/browser/test_the_website.py`

---

### Eleven browser criteria failed on untouched main, because a fresh Chromium enforces the CSP against the test tool's own predicates

**Believed.** The browser criteria that call `page.wait_for_function("...")` with a string were a stable part of the gate, and a red run on a feature branch meant the feature had broken something.

**Actually.** The app's CSP is `script-src 'self'` with no `'unsafe-eval'`, which is correct. Playwright evaluates a STRING predicate inside the page, and the Chromium build current on 2026-10-20 refuses that under this CSP (`EvalError: Evaluating a string as JavaScript violates ... 'unsafe-eval'`). It fails identically with Playwright 1.64 and with the recorded 1.62.0 (`docs/30 Deployment/RUNTIME_VERSIONS.md`). Running the same criteria against untouched `main` (commit c331e94, built in a separate worktree) reproduced every one of these failures. The feature branch was not the cause.

**Caught by.** Refusing to read the branch's red run as either "my change broke it" or "it's flaky", and building untouched main to get a baseline before trusting either story.

> **Lesson.** Before attributing a red run to your change, run the same tests on the code without your change, in the same environment. An environment that has drifted since the last green (a new browser build here) fails the baseline too. The difference between the two runs is the only signal that belongs to your change. The fix here is not to loosen the CSP or edit the criteria, but to pin the browser build the gate was last green on. Rewriting those predicates as JS function strings (`"() => ..."`) might avoid the in-page `eval`; that is **unverified** and was not tried.

`tests/browser/test_the_shell.py · tests/browser/test_the_website.py · app/core/headers.py:28-39 · session 2026-10-20`

> **Correction, same day (2026-10-20), to the entry above on the CSP failures.** The cause was not a
> newer browser build. `script-src 'self'` arrived in `app/core/headers.py` on **2026-10-18**
> ("Harden the service and fix the summary's serialization 500"), and the browser suite, last run
> green on 2026-09-01, was not re-run after that hardening. Playwright polls a bare EXPRESSION string
> with an in-page `eval`, which the CSP refuses as soon as the predicate is false on its first check.
> **Verified** against the running app: the same check written as a FUNCTION string (`"() => (...)"`)
> polls without `eval` and passes. All 18 expression predicates were wrapped verbatim, no assertion
> changed. The broader lesson stands, with one addition: a security change (a CSP, a header, a
> permission) is a change to every test that drives the browser, and the browser suite must be re-run
> as part of it.

---

### The landing page measured 833px too wide at 375px once, in one full browser run, and never again

**Believed.** The gloomy landing (SW-ADR-159) was proven to fit a phone: `.landing` and `.landing-scene` both clip horizontally, and the 375px test had passed on that build.

**Actually.** Unexplained, and recorded as unexplained. In one full run on 2026-10-20 (the Appearance move, a change that does not touch the landing), `test_the_landing_page_does_not_overflow_at_375px` read `scrollWidth - clientWidth = 833`. The same test passed three times in isolation, the next full run was 57/57, and a probe of the live site at 375px with mobile emulation, sampled every 100ms for 1.2s across six loads, never saw any overflow. One unverified guess: under suite load the test measured before the stylesheet applied, when the unclipped tree reflection image lays out at its natural width.

**Caught by.** That test, measuring `scrollWidth` rather than walking elements (the lesson of the entry above).

> **Lesson.** An intermittent red is still a red. If it comes back, capture `getComputedStyle` of `.landing` and the widest box at the moment of failure before re-running anything.

`client/src/styles/screens/landing.css · tests/browser/test_the_website.py`

---

### The sign-in card stayed invisible: GSAP read a CSS entrance's first frame as the card's resting state

**Believed.** A GSAP `from()` entrance on `.gate-card` would end where the card naturally rests, fully visible and unmoved.

**Actually.** `glass.css` already gave `.gate-card` a CSS `sw-rise` animation that starts at `opacity: 0; translateY(10px)`. Both started on the same frame, so GSAP measured the card's "current" style mid-CSS-animation and recorded opacity 0, y 10px as its end values. The card animated in, then settled at 0% opacity. It was found on 2026-10-21 by a frame-by-frame trace of the card's inline style during the landing-to-sign-in carry (SW-ADR-160).

**Caught by.** Flow screenshots (the card was missing on the finished sign-in page), then a per-frame trace of `.gate-card`'s style. The browser tests passed through it, because Playwright treats an opacity-0 element as visible. Fixed by switching the CSS rise off where GSAP owns the entrance (`.gate.scene .gate-card { animation: none }`).

> **Lesson.** Never let a CSS animation and a GSAP `from()` start on the same element in the same frame. GSAP reads the computed style, which mid-animation is the keyframe, not the resting state. One owner per element's entrance. A visible-in-the-DOM check does not prove a human can see it, so look at the screenshot.

`client/src/screens/Gate.jsx · client/src/styles/glass.css (.gate-card) · client/src/styles/screens/shell.css`

---

### Ad-blockers kept the always-on front on "Almost there" for ever: the wake check asked a URL blockers block

**Believed.** Polling `/healthz` from the landing page was a neutral, harmless way to learn when the sleeping server had woken (SW-ADR-160), and the only failure mode was a slow server.

**Actually.** Brave's Shields, and the uBlock-style filter lists behind it, block requests to URLs named like health checks. Every `/healthz` call failed with `net::ERR_BLOCKED_BY_CLIENT`, the check never said "up", and the countdown sat on "Almost there" indefinitely. The site was unusable on the owner's brother's laptop (2026-10-21). The test suite could not see it, because a test browser has no blocker. The flow test's simulated sleep also failed the call *temporarily*, which hid that a *permanent* failure had no way out.

**Caught by.** The owner, on another machine, with a DevTools screenshot. Fixed by asking `/api/auth/me` instead: any JSON answer means up, HTML means the host's waking page. After three fast network-level failures in a row the site opens anyway, rather than trapping the visitor. Verified for a normal visit (1.9s), a sleeping server (opens when it wakes) and a blocked check (6.2s).

> **Lesson.** A loop that waits for a signal needs an exit for "the signal can never arrive", not just "it is late". And a request a page depends on must not have a name a privacy tool would block (`/healthz`, `/metrics`, `/track`, `/analytics`, `/ads`). Ask the endpoint the page needs anyway.

`client/src/lib/scene.js`
