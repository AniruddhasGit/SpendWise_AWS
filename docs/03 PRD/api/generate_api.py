#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive the API contract's generated artifacts from `contract.json`.

Emits three things, all from one spec:

  docs/06 DataModel/seed/expected_summary.json   the full gate payload, COMPUTED
  docs/03 PRD/api/error_codes.md                 the registry SW-ADR-051 owed
  docs/03 PRD/SpendWise_PRD.md  §6.1             the worked payloads, injected

Why this exists. The PRD's §6.1 was hand-written into Markdown to answer a cold
reader who had asked eight variants of "what does the JSON actually look like?".
The next cold reader found that the hand-written answer omitted a field five
other documents require (`by_day`), contradicted itself on `null` versus `0`,
named two categories that do not exist, printed an array out of the order the
same page mandates, dropped two fields its own spec requires, and cited the
wrong ADR for the one number that is never waivable.

A hand-written example is exactly as driftable as the prose it replaces — and
once it is labelled "normative" it drifts with authority. So the example is
computed from the same spec that states the rules.

    py "docs/03 PRD/api/generate_api.py"           write
    py "docs/03 PRD/api/generate_api.py" --check   verify, write nothing
"""
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # api -> 03 PRD -> docs -> repo
SPEC = os.path.join(HERE, "contract.json")
PRD = os.path.join(ROOT, "docs", "03 PRD", "SpendWise_PRD.md")
EXPECTED = os.path.join(ROOT, "docs", "06 DataModel", "seed", "expected_summary.json")
CODES = os.path.join(HERE, "error_codes.md")

BEGIN = "<!-- BEGIN GENERATED §6.1 — py \"docs/03 PRD/api/generate_api.py\" -->"
END = "<!-- END GENERATED §6.1 -->"


def rupees(paise):
    return "%d.%02d" % (paise // 100, paise % 100)


def half_up(total, divisor):
    """Integer half-up. Decimal never enters; float never enters."""
    if divisor == 0:
        return None
    return (2 * total + divisor) // (2 * divisor)


def largest_remainder(parts, total):
    """Percentages that sum to exactly 100 (SW-ADR-055)."""
    if not total:
        return [0] * len(parts)
    exact = [p * 100 / total for p in parts]
    floors = [int(x) for x in exact]
    short = 100 - sum(floors)
    order = sorted(range(len(parts)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:short]:
        floors[i] += 1
    return floors


def compute_summary(spec):
    fx = spec["seed_fixture"]
    gate = spec["gate"]
    cats = {c["id"]: c for c in spec["categories"]["seeded"]}
    syn = spec["categories"]["synthetic"]

    d_from = dt.date.fromisoformat(gate["from"])
    d_to = dt.date.fromisoformat(gate["to"])
    today = dt.date.fromisoformat(fx["today_mocked"])

    rows = [e for e in fx["expenses"]
            if d_from <= dt.date.fromisoformat(e["spent_on"]) <= d_to]
    total = sum(e["amount_paise"] for e in rows)
    elapsed = max(0, (min(d_to, today) - d_from).days + 1)
    avg = half_up(total, elapsed)

    # by_category: real buckets by total desc then name asc, synthetic ALWAYS last
    agg = {}
    for e in rows:
        k = e["category_id"]
        a = agg.setdefault(k, {"total_paise": 0, "count": 0})
        a["total_paise"] += e["amount_paise"]
        a["count"] += 1
    real = sorted((k for k in agg if k is not None),
                  key=lambda k: (-agg[k]["total_paise"], cats[k]["name"]))
    order = real + ([None] if None in agg else [])
    pct = largest_remainder([agg[k]["total_paise"] for k in order], total)
    by_cat = []
    for i, k in enumerate(order):
        c = cats[k] if k is not None else syn
        by_cat.append({"category_id": k, "category_name": c["name"], "color": c["color"],
                       "total_paise": agg[k]["total_paise"], "count": agg[k]["count"],
                       "percent": pct[i]})

    # by_day: one row per calendar day INCLUDING empty ones (SRC-001 §7.4)
    by_day = []
    d = d_from
    while d <= d_to:
        same = [e for e in rows if e["spent_on"] == d.isoformat()]
        by_day.append({"date": d.isoformat(),
                       "total_paise": sum(e["amount_paise"] for e in same),
                       "count": len(same)})
        d += dt.timedelta(days=1)

    return {
        "from": gate["from"], "to": gate["to"],
        "total_paise": total, "total": rupees(total),
        "count": len(rows), "days_elapsed": elapsed,
        "daily_average_paise": avg,
        "daily_average": rupees(avg) if avg is not None else None,
        "by_category": by_cat, "by_day": by_day,
    }


def render_codes(spec):
    ec = spec["error_codes"]
    out = ["# Error code registry — GENERATED from contract.json. DO NOT HAND-EDIT.",
           "",
           "`SW-ADR-051` states in its own Consequences that *\"a stable `code` is the only thing",
           "that lets the PRD write a binary acceptance criterion for an error path, which the",
           "Definition of Done requires.\"* The registry that makes that true was never written, so",
           "`CONSTITUTION.md` Art IX.3 could not be met on any error path. `SW-ADR-138` writes it.",
           "",
           "**Envelope.** `" + ec["envelope"] + "`",
           "",
           ec["field_note"], "",
           "| `code` | Status | Carries `field` | When |", "|---|---|---|---|"]
    for c in ec["codes"]:
        out.append("| `%s` | %d | %s | %s |"
                   % (c["code"], c["status"], "yes" if c["has_field"] else "no", c["when"]))
    out += ["",
            "**A code not on this list cannot be returned.** The list is closed, in the same way",
            "the audit-log action allowlist is closed (`SW-ADR-105`): an unlisted value is a defect,",
            "not an extension point.",
            ""]
    return "\n".join(out)


def render_prd_block(spec, summary):
    g = spec["gate"]
    create_req = {"amount": "1250.00", "category_id": 3, "description": "Auto to office",
                  "spent_on": "2026-08-01", "user_id": 99, "id": 4242}
    create_res = {"id": 8801, "user_id": 7, "category_id": 3, "category_name": "Transport",
                  "amount": "1250.00", "amount_paise": 125000, "currency": "INR",
                  "description": "Auto to office", "spent_on": "2026-08-01",
                  "receipt_key": None, "created_at": "2026-08-01T09:14:22.481Z",
                  "updated_at": None}

    # the day series is long; show the shape and the days that matter
    shown = [d for d in summary["by_day"][:6]]
    trailer = ("    … %s … %s, all total_paise 0, count 0 — %d rows in total"
               % (summary["by_day"][6]["date"], summary["by_day"][-1]["date"],
                  len(summary["by_day"])))

    def j(o, indent=2):
        return json.dumps(o, indent=indent, ensure_ascii=False)

    body = summary.copy()
    body["by_day"] = "@@DAYS@@"
    rendered = j(body).replace('"@@DAYS@@"',
                               "[\n" + ",\n".join("    " + json.dumps(d, ensure_ascii=False)
                                                  for d in shown)
                               + ",\n" + trailer + "\n  ]")

    L = [BEGIN,
         "",
         "### §6.1 — Two worked payloads",
         "",
         "**Generated from `docs/03 PRD/api/contract.json`. Do not hand-edit — regenerate.**",
         "",
         "The first version of this section was hand-written to answer a cold reader who had asked",
         "eight variants of one question: *what does the JSON actually look like?* The next cold",
         "reader found that the hand-written answer omitted `by_day` (which `SRC-001 §7.4` requires",
         "and five other documents assert on), said `daily_average_paise: 0` where six documents say",
         "`null`, named two categories that do not exist, printed `by_category` out of the order the",
         "same page mandates, dropped `color` and `percent`, and cited the wrong ADR for the one",
         "number that is never waivable.",
         "",
         "**A hand-written example is exactly as driftable as the prose it replaces** — and once it",
         "is labelled normative it drifts with authority. So it is computed now, from the same spec",
         "that states the rules. These payloads are **normative**: where prose and payload disagree,",
         "that is a defect to be filed, not a choice.",
         "",
         "**Creating an expense.** `POST /api/expenses`, cookie-authenticated as user 7.",
         "",
         "```json", j(create_req), "```",
         "",
         "`amount` is a **decimal string**, in rupees, and is the only accepted form — a JSON number",
         "is rejected 422, because a float cannot hold ₹0.10 exactly `[SRC: SW-ADR-029]`. More than",
         "two decimal places is rejected, never rounded `[SRC: SW-ADR-112]`. `user_id` and `id` are",
         "**silently discarded before validation**: the owner is the verified identity, never the",
         "body `[SRC: SW-ADR-130]`. Response **201**:",
         "",
         "```json", j(create_res), "```",
         "",
         "`user_id` is **7**, not the forged 99, and `id` is server-assigned. Both `amount` (display,",
         "rupees) and `amount_paise` (the stored integer) are returned: the client never divides by",
         "100, and a test can assert on the exact integer. `created_at` is UTC with an offset; the",
         "*calendar* boundary is Asia/Kolkata `[SRC: SW-ADR-096]`.",
         "",
         "**The day-one summary.** `%s`" % g["request"],
         "",
         ("Against the seeded fixture, as person A, today mocked to `%s` Asia/Kolkata. **This is\n"
          "the payload the never-waivable gate asserts on**, and every value below is computed\n"
          "from `contract.json` — none is typed."
          % spec["seed_fixture"]["today_mocked"]),
         "",
         "```json", rendered, "```",
         "",
         "Every field, spelled out, because each was guessed at least once by a cold reader:",
         "",
         "- `total_paise` **%d** = %s. Integers throughout `[SRC: SW-ADR-029]`."
         % (summary["total_paise"],
            " + ".join(str(e["amount_paise"]) for e in spec["seed_fixture"]["expenses"])),
         "- `count` **%d** — the number of expense **rows**, not the number of days."
         % summary["count"],
         "- `days_elapsed` **%d** — `max(0, min(to, today) − from + 1)`, inclusive of both ends"
         % summary["days_elapsed"],
         "  `[SRC: SW-ADR-085]`, capped at today, evaluated in Asia/Kolkata `[SRC: SW-ADR-053]`.",
         "  **This is the divisor, and it is days, not rows.**",
         "- `daily_average_paise` **%d** — `%d / %d`, rounded **half-up** `[SRC: SW-ADR-010]`,"
         % (summary["daily_average_paise"], summary["total_paise"], summary["days_elapsed"]),
         "  in integers: `(2·total + elapsed) // (2·elapsed)`. Two wrong answers to avoid —",
         "  **%s** is what truncation gives, and **%s** is what dividing by `count` gives."
         % tuple(sorted(g["wrong_answers"])),
         "- `daily_average` **\"%s\"** — the same value as a display string, trailing zero kept."
         % summary["daily_average"],
         "- **`daily_average_paise` is `null`, never `0`, when `days_elapsed` is 0**",
         "  `[SRC: SW-ADR-053, SW-ADR-054]` — a future-dated range has no average, and `0` would",
         "  read as \"spent nothing\". `P-UND-02` renders it `—`; that dash is the client's.",
         "- `by_category` is ordered `total_paise` **descending**, then name ascending",
         "  `[SRC: SW-ADR-055]`, with the synthetic `null` bucket **always last regardless of size**",
         "  `[SRC: SW-ADR-131]`, labelled `Uncategorised` and rendered `%s`. It is a bucket, not a"
         % spec["categories"]["synthetic"]["color"],
         "  row in `categories`; nothing joins to it. `percent` is largest-remainder, so the printed",
         "  percentages sum to exactly 100.",
         "- `by_day` carries **one row per calendar day, including days with no spending**",
         "  `[SRC: SRC-001 §7.4]` — %d rows here. Build it with `generate_series` and a LEFT JOIN,"
         % len(summary["by_day"]),
         "  with the owner predicate in the **`ON`** clause: move it to `WHERE` and the LEFT JOIN",
         "  degenerates to an INNER JOIN, the zero days vanish, and only `SIT-E0-S9-05` notices.",
         "- Absent keys are absent, not null: a range with no rows returns `total_paise: 0`,",
         "  `count: 0`, `by_category: []`, and a `by_day` still full of zero rows.",
         "",
         "**Error codes** are enumerated in `docs/03 PRD/api/error_codes.md`, generated from the same",
         "spec. The list is closed: a code not on it cannot be returned.",
         ""]

    cv = spec.get("conventions")
    if cv:
        L += ["### §6.2 — Conventions a cold reader had to invent",
              "",
              "**Generated from `contract.json`. Do not hand-edit — regenerate.**",
              "",
              "Every row below is something an engineer with only these documents had to **guess**.",
              "A guess is a document defect, so each is ruled here rather than left to be",
              "re-invented differently by the next reader. The last column records which uncoached",
              "slice raised it — this table is a record of where the document set was thin, not",
              "only of what it now says.",
              "",
              "| | Question | Ruling | Why | Source | Raised by |",
              "|---|---|---|---|---|---|"]
        for r in cv["rules"]:
            L.append("| `%s` | %s | **%s** | %s | %s | %s |"
                     % (r["id"], r["question"], r["ruling"], r["why"], r["source"], r["asked_by"]))
        L += ["",
              "A convention absent from this table and from §6.1 is **not** a licence to choose one.",
              "It is an `OPEN` item: escalate, never invent (`CONSTITUTION.md` Art X).",
              ""]

    L.append(END)
    return "\n".join(L)


def build():
    with open(SPEC, encoding="utf-8") as f:
        spec = json.load(f)
    summary = compute_summary(spec)

    # the gate assertion must hold, or the spec disagrees with itself
    got = summary[spec["gate"]["assert_field"]]
    want = spec["gate"]["assert_value"]
    if got != want:
        raise SystemExit("FAIL  contract.json computes %s = %s but asserts %s"
                         % (spec["gate"]["assert_field"], got, want))

    expected = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    codes = render_codes(spec)
    block = render_prd_block(spec, summary)
    return spec, summary, expected, codes, block


def inject(prd_text, block):
    if BEGIN in prd_text and END in prd_text:
        return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block,
                      prd_text, flags=re.S)
    m = re.search(r"^## §7 — Cross-cutting floors", prd_text, re.M)
    if not m:
        raise SystemExit("FAIL  cannot find §7 to anchor the generated block")
    return prd_text[:m.start()] + block + "\n\n---\n\n" + prd_text[m.start():]


def main():
    spec, summary, expected, codes, block = build()
    with open(PRD, encoding="utf-8") as f:
        prd_now = f.read()
    prd_new = inject(prd_now, block)

    targets = [(EXPECTED, expected), (CODES, codes), (PRD, prd_new)]
    if "--check" in sys.argv:
        bad = 0
        for path, want in targets:
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            try:
                with open(path, encoding="utf-8") as f:
                    have = f.read()
            except FileNotFoundError:
                print("FAIL  %s does not exist" % rel)
                bad += 1
                continue
            if have != want:
                print("FAIL  %s has drifted from contract.json" % rel)
                bad += 1
            else:
                print("PASS  %-46s matches contract.json" % rel)
        print("PASS  gate assertion holds: %s = %d"
              % (spec["gate"]["assert_field"], summary[spec["gate"]["assert_field"]]))
        return 1 if bad else 0

    for path, text in targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s" % os.path.relpath(path, ROOT).replace("\\", "/"))
    print("gate: %s = %d over %d days, %d day rows"
          % (spec["gate"]["assert_field"], summary["daily_average_paise"],
             summary["days_elapsed"], len(summary["by_day"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
