# `bugs/` — the mistake ledger

**This folder exists so the same mistake is not made twice, and so a person can learn from them
rather than just survive them.**

It is not a bug tracker. There is no status column, nothing to close, no triage. Every entry here
is a bug that **already happened and is already fixed**. What is kept is the *reasoning* — what was
believed, what was actually true, and what caught it — because that is the part that transfers to
the next project and the fix does not.

---

## If you are a Claude session reading this

Read this folder **before** you write code that touches something it covers, not after you have
spent an hour debugging. `GOTCHAS.md` is the short, sharp version for the code you are about to
write. This folder is the long version, with the reasoning intact.

Three obligations, in order of how much they matter:

**1. When you cause or discover a bug, write it down here before you move on.** Not when the task
ends — then, while you still remember what you believed five minutes ago. The "what was believed"
field is the whole point and it is the first thing you forget.

**2. Write the general lesson, not the specific fix.** "Added the file to the Dockerfile" teaches
nothing. "A health check that does not exercise the code path it is guarding will pass against a
broken image" is worth having. If the lesson does not transfer to a different project in a
different language, you have not found it yet.

**3. Never delete an entry.** A bug that recurs gets a note appended saying it recurred, which is
itself the most valuable signal in the folder. Entries are immutable for the same reason ADRs are.

**Do not** fill this with hypotheticals, near-misses you imagined, or things you merely worried
about. An invented bug is worse than no bug, because it costs a future reader real attention. If
you cannot say when it happened and how it was caught, leave it out.

---

## Why these particular bugs are worth studying

This project is unusually honest about failure, and the pattern in what it recorded is stark.
Of the 161 defects mined out of its own history:

| Shape | Count | What it means |
|---|---|---|
| **silent-failure** | 36 | it appeared to work and did not |
| **the-check-was-wrong** | 35 | the thing meant to catch errors was itself broken |
| **false-green** | 32 | a test or gate passed while proving nothing |
| **wrong-assumption** | 32 | a belief that was reasonable and false |
| **fix-caused-it** | 15 | the repair broke something else |
| **environment** | 11 | the machine, not the code |

**Almost two thirds are failures of *detection*, not of code.** Something was broken and nothing
said so. That is the lesson the whole folder is really about: writing correct code is the easy
half, and knowing whether your code is correct is the hard half.

The single most repeated pattern here is a check that passed because it examined nothing — an empty
list, a collection that was never populated, a comparison that could never match. It happened with
route inspection, with type annotations, with a blocklist whose entries all carried an invisible
carriage return. Each time, "found no problems" and "never looked" produced an identical green tick.

Hence this project's rule, and the most useful thing in it:

> **A check that has never been seen to fail is decoration.**
> Break it on purpose. Watch it go red. Put it back. Watch it go green.
> That is called *red-proofing*, and it is not optional here.

---

## What is in this folder

| File | What it holds |
|---|---|
| `BUG_LEDGER.md` | every defect recovered from the project's own history, grouped by shape |
| `sessions/` | one file per session that hit bugs, written up while the memory was fresh |

`BUG_LEDGER.md` is generated from the project's records — `GOTCHAS.md`, `PROGRESS.md`,
`handoffs/`, the ADRs, the test docstrings, and the design-review log. Those sources stay
authoritative; this is the index that makes them readable in one sitting.

---

## The entry format

Six fields. All six are required, and the first two are the ones people skip and shouldn't.

```markdown
### <a concrete title that names the failure, not the area>

**Shape:** silent-failure | false-green | the-check-was-wrong | fix-caused-it |
           wrong-assumption | environment

**Believed:** what everyone thought was true, stated as they would have stated it
**Actually:**  what was true
**Caught by:** what actually found it — and how close it came to shipping
**Lesson:**    the general rule, phrased so it survives leaving this project
**Where:**     file:line, or an ADR id, or a document name
```

**Believed** and **Actually** are separate fields on purpose. A bug is the gap between them. Write
only the fix and you have recorded a patch; write the gap and you have recorded an education.

**Caught by** matters more than it looks. "Caught by a test" and "caught by a user in production
three weeks later" are the same bug and completely different lessons. Say which, and say how near
it came to escaping — that is what tells a future reader whether their safety net has a hole in it.

---

## How to add one

Append to `BUG_LEDGER.md` under the matching shape, or start a new file in `sessions/` if you hit
several in one stretch and the story of how they connected is worth keeping. Use today's date.
Cite the file and line. If the bug is the sort that will bite the very next person to touch that
code, add the short version to `GOTCHAS.md` too — that is the file every session is told to read
first, and this one is not.
