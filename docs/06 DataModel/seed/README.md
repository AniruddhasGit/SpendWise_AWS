# seed/

The day-one fixture. **Lives under the test tree, never in the built image** (`SW-ADR-086`) —
a seeder reachable in a deployed environment is an unauthenticated account-creation backdoor on a
host that runs without TLS.

It drives the **real registration and expense endpoints**, not direct SQL: seeding by INSERT would
skip the eight-category creation and the password-hashing path, so the gate would prove less than
it claims.

**It refuses to run against any database not named `spendwise_test`.** Idempotency comes from the
test database being dropped and re-migrated between runs, not from deleting users — there is no
user-deletion path in v1 and the seeder does not acquire one by the back door.

## The fixture the gate computes against

Person **A**, four expenses, all in August 2026:

| Date | Amount | Paise |
|---|---|---|
| 2026-08-01 | ₹1,250.00 | 125000 |
| 2026-08-03 | ₹340.50 | 34050 |
| 2026-08-03 | ₹2,100.00 | 210000 |
| 2026-08-05 | ₹99.99 | 9999 |

**Total 379,049 · count 4 · days elapsed 5 (today mocked to 2026-08-05, Asia/Kolkata)**
**→ daily average = 75,810 paise.**

Person **B** exists with their own separate expenses, because **a single-person seed cannot prove
isolation** — and proving isolation is what the gate is for.
