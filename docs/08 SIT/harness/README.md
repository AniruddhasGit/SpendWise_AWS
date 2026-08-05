# harness/ — how a row becomes a runnable test

`SIT_TestCases.tsv` holds **195 cases, one per acceptance criterion in the Bible**. They are
written before the code, so the code is built to pass a test that already exists.

## The rules

**Every case cites a Bible story.** A case with no story is scope creep wearing a test's clothing:
delete it, or raise the missing story. Verified — zero uncited cases, zero uncovered stories.

**Never assert on a fixture.** Every case must exercise the application. On the project this
method came from, **191 of 191 acceptance fixtures that named both an expected and an actual
value set them equal** — they passed whatever the system did. That is the failure this rule
exists to prevent, and it is invisible in a green run.

**A case that cannot be executed is a FAILURE, not an omission.** If the harness cannot reach a
surface, that is a finding against the harness or the design, and it is reported as red.

**Expected values come from the sources, not from what the code happens to do.** The day-one
value is `75810` because `SW-ADR-010` says so and the client agreed the worked example — not
because that is what the endpoint returned the first time it ran.

## Evidence classes

Each row declares what proves it:

| `evidence_required` | Means |
|---|---|
| `DB query output` | the assertion is made **against the database**, not the API |
| `API response` | status and body |
| `browser session` | a real browser, not an API call that skips the interface |
| `log or audit row` | the record, read back |
| `command output` | a shell command and what it printed |

The `DB query output` class matters most: it is the only one that can prove the second isolation
layer exists. An API-only suite proves the application filter works today and says nothing about
what happens the day someone forgets one.

## Fixtures

Every case runs against the seed: person A and person B, eight categories each, and A's four
August expenses totalling 379,049 paise. **Two people, because a single-person seed cannot prove
isolation** — and isolation is what most of these cases are for.
