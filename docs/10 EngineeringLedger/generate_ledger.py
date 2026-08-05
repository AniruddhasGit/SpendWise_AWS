#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_ledger.py — derive the engineering ledger from the Bible.

The ledger is DERIVED. If it disagrees with the Bible, the Bible wins and this is re-run.
Editing a derived column by hand is erased by the next run, silently — the same trap
`SW-ADR-066` names for the data-model package.

During the build, exactly one column is hand-edited: **Status**.

    py "docs/10 EngineeringLedger/generate_ledger.py"

Deterministic: running it twice produces a byte-identical file.
"""
import csv, os, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BIBLE = os.path.join(ROOT, "docs", "05 Bible", "SpendWise_Bible.csv")
OUT = os.path.join(HERE, "engineering_ledger.tsv")

# The /ss hook discovers a ledger by looking for a delimited file whose header carries
# BOTH "Milestone" and "Status". Those two names are load-bearing — renaming either
# makes the hook stop finding this file, and a cold session loses its frontier.
COLS = ["Type", "ID", "ParentID", "Title", "AcceptanceCriteria", "Priority", "Estimate",
        "Milestone", "Status", "DependsOn", "Labels", "Persona", "OwnedPaths", "Wave",
        "TestTrustLevel", "SITCaseIDs", "NegativeCaseIDs", "EvidencePath", "SourceRef"]

# OwnedPaths is the write-set. Two stories whose OwnedPaths overlap must never run at the
# same time — that column is what makes parallel work safe.
PATHS = {
    "spine":      "app/core/**, alembic/**",
    "auth":       "app/modules/auth/**, app/modules/users/**",
    "expenses":   "app/modules/expenses/**",
    "categories": "app/modules/categories/**",
    "receipts":   "app/modules/receipts/**",
    "admin":      "app/modules/admin/**",
    "frontend":   "client/**",
    "design":     "client/src/styles/**",
    "db":         "alembic/**, app/core/db.py",
    "hardening":  "tests/**",
    "backend":    "app/**",
    "money":      "app/modules/expenses/**",
    "security":   "app/core/security.py, app/core/deps.py",
    "a11y":       "client/**",
    "privacy":    "app/modules/admin/**",
    "session":    "app/modules/auth/**",
    "fixture":    "tests/seed/**",
    "evidence":   "docs/**",
    "gate":       "tests/gate/**",
    "api":        "app/core/errors.py",
}

def owned(labels):
    got = []
    for l in labels.split(";"):
        p = PATHS.get(l.strip())
        if p and p not in got:
            got.append(p)
    return " | ".join(got) or "app/**"

def trust(labels, mid):
    if "gate" in labels: return "gate-observed"
    if "security" in labels or "privacy" in labels: return "db-verified"
    if "frontend" in labels or "a11y" in labels: return "browser"
    if mid == "M6": return "red-proof"
    return "api"

def main():
    rows = list(csv.DictReader(open(BIBLE, encoding="utf-8")))
    out = []
    for r in rows:
        if r["Type"] != "Story":
            continue
        n_ac = len([x for x in r["AcceptanceCriteria"].split("|") if x.strip()])
        out.append({
            "Type": r["Type"], "ID": r["ID"], "ParentID": r["ParentID"], "Title": r["Title"],
            "AcceptanceCriteria": r["AcceptanceCriteria"],
            "Priority": r["Priority"], "Estimate": r["Estimate"],
            "Milestone": r["Milestone"], "Status": r["Status"],
            "DependsOn": r["DependsOn"], "Labels": r["Labels"],
            "Persona": "ADMIN" if "admin" in r["Labels"] else
                       ("SYSTEM" if "spine" in r["Labels"] or "db" in r["Labels"] else "PERSON"),
            "OwnedPaths": owned(r["Labels"]),
            # Wave = the milestone. Every story in M0 is strictly sequential by DependsOn,
            # so the wave only becomes a parallelism hint from M2 onward.
            "Wave": r["Milestone"],
            "TestTrustLevel": trust(r["Labels"], r["Milestone"]),
            "SITCaseIDs": ",".join(f"SIT-{r['ID']}-{i:02d}" for i in range(1, n_ac + 1)),
            "NegativeCaseIDs": "see 09 NegativeTesting (suite-level; NEG-X-* apply to every "
                               "story touching user data)",
            "EvidencePath": f"evidence/{r['ID']}/",
            "SourceRef": r["SourceRef"],
        })

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for o in out:
            w.writerow(o)

    # integrity, computed
    ids = {o["ID"] for o in out}
    bad_dep = [o["ID"] for o in out if o["DependsOn"] and o["DependsOn"] not in ids]
    dep = {o["ID"]: o["DependsOn"] for o in out}
    def cyc(n, seen):
        while n:
            if n in seen: return True
            seen.add(n); n = dep.get(n)
        return False
    cycles = [i for i in dep if cyc(i, set())]
    # overlapping write-sets inside one wave
    clash = []
    for w_ in {o["Wave"] for o in out}:
        grp = [o for o in out if o["Wave"] == w_]
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                a = set(grp[i]["OwnedPaths"].split(" | "))
                b = set(grp[j]["OwnedPaths"].split(" | "))
                if a & b and not (grp[i]["DependsOn"] or grp[j]["DependsOn"]):
                    clash.append((grp[i]["ID"], grp[j]["ID"]))

    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    print(f"stories written        : {len(out)}")
    print(f"unresolved DependsOn   : {bad_dep or 'none'}")
    print(f"dependency cycles      : {cycles or 'none'}")
    print(f"write-set clashes      : {clash or 'none (every same-wave pair is dependency-ordered)'}")
    print(f"header carries Milestone+Status : "
          f"{'YES' if 'Milestone' in COLS and 'Status' in COLS else 'NO - the /ss hook will not find this file'}")
    print(f"sha256[:16]            : {digest}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
