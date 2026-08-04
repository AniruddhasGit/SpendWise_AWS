# goals/ — the unit of work

One goal file = one thing you want built. You write the goal; the session builds it; you stop
whenever you like and `/tt` records exactly where it stopped.

## The loop, every session

```
/ss                    orient — reads the newest handoff, PROGRESS, CLAUDE.md, GOTCHAS,
                       reconciles them against git, and recommends ONE restart point
      ↓
write a goal           copy _TEMPLATE.txt → goals/GOAL_<thing>.txt, or just say it in chat
      ↓
build                  the session works the goal until its Definition of Done is met
      ↓                (stop whenever you want — mid-story is fine, that is what handoffs are for)
/tt                    writes handoffs/HANDOFF_<stamp>_<you>.md, appends PROGRESS.md,
                       commits and pushes to GitHub
```

Next session — **any machine, any Claude account** — starts with `/ss` and is fully oriented from
the repo alone. Nothing lives in a chat history.

## Writing a good goal

The template asks for six things. Two of them are what make it work:

**The write-set.** The exact files this goal may touch. Two goals whose write-sets overlap must
never run at the same time — that is how parallel work stays safe, and grouping "by topic" is not
good enough. If the work needs a file outside the list, the session stops and asks rather than
widening quietly.

**A binary Definition of Done.** Every line either passes or fails, and names the command that
proves it. "The dashboard works" is not a DoD. "`GET /api/summary?from=2026-08-01&to=2026-08-31`
returns `daily_average_paise: 75810` against the seeded fixture" is.

## The shortcut

If you don't want to write the goal yourself, paste this and let the session write it for you:

> Build me a goal file for: `<the task>`. Use the template in `goals/_TEMPLATE.txt`, read
> `CLAUDE.md` and `CONSTITUTION.md` first, and make every Definition-of-Done line binary.

Then read it, correct it, and run it. Reading a goal takes a minute; a wrong goal costs an evening.

## Naming

`GOAL_<short-slug>.txt` — e.g. `GOAL_freeze-source-of-truth.txt`, `GOAL_day-one-proof.txt`.
Keep finished ones. They are the record of what was actually asked for, which is not always what
the backlog said.
