# The weaknesses this design accepted

Every one of these is a real weakness. Each was chosen, written down, and given a condition that
would make it wrong. **None is hidden, and none is a defect** — a defect is something nobody
decided.

## 1. The deployed site has no HTTPS

**What it means:** a password typed into the deployed environment travels across the network in
clear text. Anyone positioned between the browser and the server could read it.

**Why:** HTTPS needs a load balancer or a certificate on a domain, and both cost money.
`SW-ADR-014` removed everything that bills.

**Contained by:** that environment is **never called production in any document**, and it should
never hold anyone's real password but yours.

**Revisit when:** any real person other than you signs up. At that point this stops being a
learning environment and HTTPS is mandatory, not a preference.

## 2. Rate limiting is weaker than it looks

**What it means:** limits are counted separately inside each worker process, so the real limit is
roughly double the stated one, and it resets every restart.

**Why:** a shared counter needs another billable service.

**Contained by:** the numbers were chosen knowing they double. Sign-in is also limited per email,
not only per address, so one attacker cannot lock out a whole network.

**Revisit when:** the app has strangers on it, or ever runs more than one instance.

## 3. One person holds every approving role

**What it means:** you are the client, the money-signer, and the builder's counterpart. The
decision *queue* that this whole method makes visible never actually forms, because you can answer
yourself instantly.

**Why:** it is your personal project.

**Contained by:** every irreversible decision gets a fresh independent second opinion before it is
acted on — which is what caught two decisions the build session made that it should not have.

## 4. Two tables are protected by the application only

**What it means:** the accounts table and the reset-code table are guarded by application code
alone, not also by the database — unlike expenses and categories, which are guarded twice.

**Why:** sign-in has to read the accounts table *before* it knows who is signing in. A rule keyed
on "who is asking" cannot answer a question asked before anyone is known.

**Contained by:** four specific controls, and the money itself is on the tables that keep both
layers.

**This one is yours to confirm** — `OPEN-USERSRLS-01`. The stricter alternative exists and costs a
third database credential.

## 5. Every deploy is an outage

One instance, one port: the replacement cannot start until the old one stops. A minute or two of
downtime, every deploy. *(Reasoned, not observed — nobody has run it.)*

## 6. Nobody watches it

There is a health check and an alarm for "the app stopped running". There is no external monitor.
If the site is up but wrong, **you find out by looking.** Accepted explicitly rather than left
unnoticed.
