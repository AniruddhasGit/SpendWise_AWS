# SpendWise — what is being built

**One page. No jargon.**

A website where a person signs up, records what they spend, and sees where it went. Everyone sees
only their own money. An administrator can manage accounts — unlock someone, sign them out,
deactivate a leaver — and **deliberately cannot see anyone's spending.**

## How it is put together

**One thing, not several.** A single container holds the website and the server that feeds it, so
there is one deploy and one thing to roll back. The database is a managed Postgres instance;
receipt images go to object storage; two secrets live in a parameter store. That is the whole
system.

## The one thing that must not break

**Nobody sees anyone else's money.** It is checked twice: once in the application, and again by
the database itself, independently. One check is not enough — a single forgotten filter in a
single query and it is gone. Two independent checks mean a mistake in one is caught by the other.

And the check is **watched failing on purpose** before it is trusted: the protection is switched
off, the test observed going red, then restored and the restoration verified. A check nobody has
seen fail is decoration.

## What it costs

**Nothing, if the free tier holds.** Everything that bills was deliberately removed — no load
balancer, no Fargate, no NAT gateway, no managed secrets service. Roughly $50 a month of
components that this project does not need.

**What that costs in return, stated honestly:** no load balancer means **no HTTPS**, so a password
travels in clear. That environment is never called production in any document. And with one
instance, **every deploy is a short outage.**

## What is deliberately not built

No mobile app · no reading bank messages · no bank integration (it needs a licence) · nothing
pulled from payment apps · no self-service password reset (there is no email in the system, so a
reset link would have nowhere to go).
