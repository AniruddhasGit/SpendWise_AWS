# State machines

## Session

```mermaid
stateDiagram-v2
    [*] --> Active: sign in
    Active --> Active: request within idle window (last_seen_at bumped, max 1/min)
    Active --> Revoked: sign out
    Active --> Revoked: admin force sign-out
    Active --> Revoked: admin issues a reset (same transaction)
    Active --> Revoked: account deactivated (same transaction)
    Active --> Revoked: role DEMOTED (same transaction)
    Active --> Revoked: signing secret rotated (at boot)
    Active --> Expired: idle window passed, or 30-day cap reached
    Revoked --> [*]
    Expired --> [*]
```

**Reactivation never resurrects a revoked session.** Promotion does *not* revoke — the role is
re-read from the record on every request, so a promotion applies immediately without a logout.

## Reset code

```mermaid
stateDiagram-v2
    [*] --> Issued: admin issues (invalidates any outstanding code, same transaction)
    Issued --> Used: redeemed -> password replaced, ALL sessions revoked
    Issued --> Expired: one hour
    Issued --> Superseded: a newer code issued
    Used --> [*]
    Expired --> [*]
```

Four **distinguishable** outcomes at redemption: recognised · already used · expired · not
recognised. A used code is spent and an expired one is dead, so telling them apart helps the
legitimate holder and gives an attacker nothing.

## Expense

```mermaid
stateDiagram-v2
    [*] --> Recorded: create
    Recorded --> Recorded: edit (endpoint exists; no screen in v1)
    Recorded --> WithReceipt: attach
    WithReceipt --> WithReceipt: replace (row commits, THEN the old object is deleted)
    WithReceipt --> Recorded: remove receipt
    Recorded --> [*]: delete (confirmed, naming the amount and date)
    WithReceipt --> [*]: delete (confirm also warns the receipt goes)
```
