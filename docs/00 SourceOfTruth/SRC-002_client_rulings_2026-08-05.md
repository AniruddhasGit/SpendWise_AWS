# SRC-002 — SpendWise client rulings, session of 2026-08-05

```
Source type ....... Client rulings, captured in session
Session date ...... 2026-08-05
Author ............ the client (SpendWise owner)
Status ............ FROZEN — never edited
Citation form ..... SRC-002 §n
Companion ......... SRC-001 (the requirements statement)
```

> **FROZEN INPUT. DO NOT EDIT.** Thirteen ADRs cite clauses of this file. If it changes,
> every artifact derived from it is invalidated and must be re-derived, never silently
> reused (`CONSTITUTION.md` Art II.4).
>
> The **only** permitted modification is a clearly-marked `ERRATUM` block appended at the
> foot, which governs over the text it corrects.

## Why this file exists

`SRC-001` is what the client *wrote*. This is what the client *ruled* — the answers given
during the session of 2026-08-05, in response to questions the build session put to them.

Before this file existed, thirteen ADRs cited *"Client statement, 2026-08-05"*, which
resolved to nothing on disk. That is a dangling reference and it breaks `CONSTITUTION.md`
Art II.5: derived content must cite a source or carry an explicit `ASSUMED` flag. A ruling
whose only evidence is a chat log no future session will have is not evidenced at all.

## Reading rules — the provenance tags

Every clause below carries one of three tags. **The distinction is load-bearing and must
not be flattened.**

| Tag | Meaning |
|---|---|
| **`[VERBATIM]`** | The client typed these words. Quoted exactly, including original spelling and typos — they are not corrected, because a corrected quote is not a quote. |
| **`[SELECTED]`** | The client chose this option from a menu the build session wrote. **The wording is the build session's; the choice is unambiguously the client's.** Recorded separately because calling it verbatim would attribute authorship of the words to the client, and calling it a paraphrase would understate that they definitively chose it. |
| **`[PARAPHRASE]`** | Reconstructed by the build session from the surrounding record. Weakest class. Never quote a `[PARAPHRASE]` clause as the client's words. |

> **Deviation from `GOAL_01`, declared.** The goal specified two tags, `[VERBATIM]` and
> `[PARAPHRASE]`. A third — `[SELECTED]` — was added because seven of these rulings arrived
> through a multiple-choice interface where the build session authored the option text.
> Forcing those into either existing tag would have been inaccurate in a way that matters:
> it would either credit the client with words they did not write, or downgrade a decision
> they definitively made. `CONSTITUTION.md` Art VII.6 requires saying plainly what was
> changed and why; this note is that.

---

## §1 — Project framing and the AWS intent  `[VERBATIM]`

> "this is my personal project which i want you to build end to end with this ai-sdlc
> process. what we generally do is have client meeting get all the meeting minutes and feed
> it to the claude code. then we make the documents that are mentioned to make the actual
> app. so here considering his is my personal project. i will act as a client once the whole
> app is ready i will practice the DevOps role which you dont need to worry about as I will
> be doing it on some other claude code. Just keep in mind this app will be using RDS, ECR,
> ECS, AND S3 if needed.Route53 maybe IAM and other basic aws tools for learning. I will try
> to make a full CI/CD pipeline for this project."

**Carried into:** `SW-ADR-001` (the client is the client), `SW-ADR-005` (the DevOps role is
practised by the client, in a separate session), `SW-ADR-007` (the meeting-minutes working
pattern).

**Note on §1's AWS list.** `ECS` and `S3 if needed` survive. `Route53 maybe` was never
reached. The list is an *intent*, not an authorisation — `SW-ADR-014` later removed several
of the components the intent implied, because they bill.

## §2 — Who holds which role  `[SELECTED]`

**Asked:** who holds which hat — client decider, money-signer, and the person who signs the
governing document.

**Answered:** *"I'm all three."* The client is the sole decider, the money-signer, and the
person who will sign the Constitution. The build session is builder, analyst and QA.

**Carried into:** `SW-ADR-001`.

**Still open:** the client's exact full name for the ratification block, and a backup
decider. Tracked as `OPEN-NAME-01`. A name inferred from a git identity is not a signature.

## §3 — Greenfield confirmation  `[SELECTED]`

**Asked:** is there anything SpendWise replaces today — a system, a tool, or a spreadsheet
someone actually runs the work on?

**Answered:** *"Nothing — clean slate."*

**Carried into:** `SW-ADR-002`.

## §4 — Deadline  `[SELECTED]`

**Asked:** is there a date, and is anything real attached to it?

**Answered:** *"No fixed date."* Quality over speed; nothing external attached.

**Carried into:** `SW-ADR-003`.

## §5 — Initial spend posture  `[SELECTED]`

**Asked:** what may be spent without coming back for another signature?

**Answered:** *"Nothing yet — local only."* Local development and free tiers only.

**Carried into:** `SW-ADR-004`. **Superseded within the same session by §9 and §15.**

## §6 — The build / DevOps boundary  `[VERBATIM]`

**Asked:** where does the line run between the build session and the client's separate
DevOps work?

**Answered:**

> "The line is that you only keep in mind and make thing such that it can work in AWS while
> wrting the code. I will have DEV, UAT and PROD for this on AWS. I want to manually work on
> AWS so i can practice DevOps role. So whenever we need something tell me in chat that I
> need to do this next and give me a headups so i will prepare it as the code is being made.
> It has to be such that while you write code I can prepare the DevOps stuff with your
> instructions. Make the documents such that i am ddoing this AWS manually must not matter."

**Carried into:** `SW-ADR-005` in full — the code-only boundary, the advance-notice
obligation, and the requirement that documents never assume automation.

**Note.** "I will have DEV, UAT and PROD" is the client's stated intent. `SW-ADR-008`
records that the free tier fits approximately one always-on RDS instance, so three live
environments do not fit inside it. The intent stands; the cost of satisfying it is recorded
against it.

## §7 — How much process ceremony to keep  `[SELECTED]`

**Asked:** parts of the borrowed method are built for a consultancy billing a client — what
gets cut?

**Answered:** *"Cut the money stuff only."* No contract, pricing, invoices or scoping
agreement. **Every quality control stays**, including the never-waivable day-one gate.

**Carried into:** `SW-ADR-006`.

## §8 — How requirements arrive  `[SELECTED]`

**Asked:** dump, interview, or dump-only?

**Answered:** *"Dump, then I interrogate."* The client writes it out however it comes; the
build session converts it to cited rows and returns with everything the dump did not settle.

**Carried into:** `SW-ADR-007`. Executed the same day: the dump became `SRC-001`, and the
interrogation produced five contradictions, seven gaps and three factual errors.

## §9 — When RDS enters, and the request that preceded it  `[VERBATIM]` + `[SELECTED]`

**The client's question, verbatim** — recorded because it states the goal the ruling
optimises for:

> "I need some easy eli18 language recommendations from you as to what would be the best RDS
> from the start or after? what happens in companies what do they do? local postgres first or
> rds from the get go? i want to mimic that also keep in mind i am on AWS free tier.."

**The build session recommended** local Docker Postgres first, with one RDS instance for DEV
later, on the grounds of a faster inner loop and zero cost. It stated a kill condition: *if
practising AWS matters more than shipping SpendWise, work against real RDS from day one.*

**Answered `[SELECTED]`:** *"One RDS from day one."* The recommendation was **overruled**, on
the kill condition the build session itself named.

**Carried into:** `SW-ADR-008`, recorded as an overturn rather than smoothed into agreement.

## §10 — How the clean-clone requirement is met without CI  `[SELECTED]`

**Asked:** the day-one checklist requires that everything ran on a clean clone, not just one
machine. With CI owned by the client's DevOps work, how is that honoured?

**Answered:** *"Clean container now, you close CI later."* A labelled substitute now, with
the real CI and hosted-runner ticks left formally open.

**Carried into:** `SW-ADR-009`, and downgraded further by §12's deferral of the Dockerfile.

## §11 — The daily-average denominator  `[VERBATIM]`

**Asked:** the summary endpoint returns a daily average, but `SRC-001 §7.4` does not define
the denominator. Three readings differ by an order of magnitude — days elapsed (₹758.10),
days with spending (₹1,263.50), or days in range (₹122.27), against the same worked example.

**Answered:**

> "B3: consider the one you recommended."

The build session's recommendation was **days elapsed, capped at today**, computed in
integer minor units and rounded half-up.

**Carried into:** `SW-ADR-010`, whose agreed acceptance value is **75,810 paise**.

## §12 — When the Dockerfile gets written  `[VERBATIM]`

> "A2: yes i will ask you to write the docker file but do not write it that will be done when
> the app is ready."

**Carried into:** `SW-ADR-011`. The build session writes it, but late — which weakens the
clean-clone evidence of §10, and `SW-ADR-009` records the weaker ladder rather than hiding it.

## §13 — Password reset  `[VERBATIM]`

> "B1:No only the admin will have the button to reset the pasword."

**Carried into:** `SW-ADR-012`, and filed as `ERRATUM E-3` against `SRC-001 §7.1`. There is
no email anywhere in the stack, so a self-service token had no delivery route.

## §14 — Currency  `[VERBATIM]`

> "B5:This app will only have INR till .00 then round it off."

Read as: Indian Rupees only, two decimal places, rounded for display.

**Carried into:** `SW-ADR-013`, which additionally snapshots the currency onto each expense
row so a later change cannot silently reinterpret history.

## §15 — Nothing paid  `[VERBATIM]`

> "A5:We will not use ALB or Fargate if it is paid this is a app for learning"

and, in a later message:

> "i have aws free tier account and this is for my learning so i think we can manage this
> build."

**Carried into:** `SW-ADR-014`, which **overrides the client's own written stack** at
`SRC-001 §2.3` and `§11.4`, and is filed as `ERRATUM E-1`. This clause supersedes §5's
"local only" posture and constrains §6's three-environment intent.

**Note on what was not settled here.** No monthly ceiling was ever named. `SW-ADR-014`
therefore fixes the posture at *nothing paid* rather than at a number, and the billing alarm
in `docs/30 Deployment/AWS_PREP_QUEUE.md` item 0 is left for the client to set.

## §16 — The standing delegation  `[VERBATIM]`

> "further if you get any questions make decisions as this is a practice app."

**Carried into:** `SW-ADR-015` — which rests on this clause **entirely**, and which
deliberately does not implement it in full. The reserved floor is held: technical questions
are the build session's; reversible reserved matters are decided then batched for reversal;
reserved-and-irreversible still stops and waits. The reasoning is in that ADR: a blanket
delegation would quietly repeal the constitution being adopted.

## §17 — DoorNexa is a blueprint, not a source  `[VERBATIM]`

> "Only consider the contents of the doornexa for your learning as to how all the docs are
> working togethre so that we can build the whole app with pure LLM's. the doornexa is ment
> to be the blueprint for all projects for the future and hwo documetns must be kept and
> managed and used to code afterwards."

and, from the message that set the document structure:

> "i want you to specifically follow the processes we did in this project not the one you
> just made"

**Effect:** the numbered document structure, the provenance grammar, the status law, the
fail-closed ledger and the `included_in_*` incorporation columns are adopted from that
reference project. **No content is.** Every word in this repository's documents is about
SpendWise.

This clause carries no ADR. It governs how the document set is *shaped*, which is recorded
in `CONSTITUTION.md` Art XI and `docs/README.md`.

---

## §E — ERRATA

*(none — this file has not yet required correction)*
