#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""consistency_check.py — the mechanical half of the cross-artifact gate.

Every check here answers one question: **does this cross-reference actually resolve?**
It exists because four of the twenty-four findings in GOAL_02's adversarial review needed no
intelligence at all — a dangling ADR id, a dangling OPEN id, an erratum claimed but never
written, and four prep-queue rows claimed but never added. That is the
"I reported an action I did not perform" class, it is a K1 breach, and it is fully
machine-detectable. An expensive reviewer should never be spent on it again.

This is the CHEAP layer. It cannot see a semantic contradiction between two documents that
each resolve fine — that is what the fresh-agent cross-artifact pass in GOAL_13 is for.

    py tools/consistency_check.py            run every check against the repo
    py tools/consistency_check.py --selftest plant each violation, prove each check fires

Exit 0 = every cross-reference resolves. Non-zero = at least one does not.

A check that has never been observed failing proves nothing, so --selftest is not optional
decoration: it plants a real violation of each rule in a scratch copy and asserts the checker
goes red. Run it before trusting a green.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

TEXT_EXT = {".md", ".txt", ".tsv", ".csv", ".json", ".py", ".sql", ".yaml", ".yml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist"}

# What this checker governs is the DOCUMENT SET — the artifacts that make claims about each
# other. Deliberately out of scope:
#   tools/     is code, and this file in particular contains planted violations as literals;
#              scanning it makes the checker fail on its own selftest fixtures.
#   PROGRESS.md, handoffs/, goals/
#              are narrative. Their job is to record what happened, INCLUDING defects — a
#              handoff that quotes "claims ERRATUM E-8 is filed" is reporting the defect, not
#              committing it. Flagging those would punish exactly the honesty K2 requires.
SKIP_PATHS = {"PROGRESS.md"}
SKIP_PREFIXES = ("tools/", "handoffs/", "goals/")


def in_scope(relpath: str) -> bool:
    return relpath not in SKIP_PATHS and not relpath.startswith(SKIP_PREFIXES)


# ── plumbing ────────────────────────────────────────────────────────────────────
class Report:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str]] = []
        self.notes: list[str] = []

    def fail(self, check: str, detail: str) -> None:
        self.failures.append((check, detail))

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def ok(self) -> bool:
        return not self.failures


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def walk(root: str) -> list[str]:
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in TEXT_EXT:
                out.append(os.path.join(base, f))
    return out


def rel(root: str, p: str) -> str:
    return os.path.relpath(p, root).replace("\\", "/")


# ── the checks ──────────────────────────────────────────────────────────────────
def check_all(root: str) -> Report:
    r = Report()
    sot = os.path.join(root, "docs", "00 SourceOfTruth")
    adr_dir = os.path.join(root, "docs", "01 ADR", "all-ADRs")
    ledger_p = os.path.join(root, "docs", "01 ADR", "ADR_DECISION_RELEASE_LEDGER.tsv")
    const_p = os.path.join(root, "CONSTITUTION.md")

    files = walk(root)
    corpus = {rel(root, p): read(p) for p in files if in_scope(rel(root, p))}

    # -- what actually exists -----------------------------------------------
    src_clauses: dict[str, set[str]] = {}
    errata: set[str] = set()
    for fn in sorted(os.listdir(sot)) if os.path.isdir(sot) else []:
        if not fn.endswith(".md"):
            continue
        key = fn.split("_")[0]                       # SRC-001 / SRC-002
        t = read(os.path.join(sot, fn))
        anchors = set(re.findall(r"^## §([0-9]+)\s*—", t, re.M))
        anchors |= set(re.findall(r"^\*\*§([0-9]+\.[0-9]+)\*\*", t, re.M))
        src_clauses[key] = anchors
        errata |= set(re.findall(r"^\*\*(E-[0-9]+) ·", t, re.M))

    adr_files = (
        {f[:-3] for f in os.listdir(adr_dir) if f.endswith(".md")}
        if os.path.isdir(adr_dir) else set()
    )

    ledger_rows: list[dict] = []
    if os.path.isfile(ledger_p):
        ledger_rows = list(csv.DictReader(io.StringIO(read(ledger_p)), delimiter="\t"))
    ledger_ids = {row["adr_id"] for row in ledger_rows} if ledger_rows else set()

    open_ids = set()
    if os.path.isfile(const_p):
        open_ids = set(re.findall(r"^\|\s*`(OPEN-[A-Z0-9-]+)`", read(const_p), re.M))

    # -- 1. source clause citations resolve ---------------------------------
    cite = re.compile(r"(SRC-00[0-9])\s*[§S]\s*([0-9]+(?:\.[0-9]+)?)\b")
    n = 0
    for f, t in corpus.items():
        for m in cite.finditer(t):
            n += 1
            src, cl = m.group(1), m.group(2)
            if src not in src_clauses:
                r.fail("source-citation", f"{f}: cites {src}, which does not exist")
                continue
            top = cl.split(".")[0]
            if cl not in src_clauses[src] and top not in src_clauses[src]:
                r.fail("source-citation", f"{f}: `{src} §{cl}` does not resolve")
    r.note(f"source clause citations checked: {n}")

    # -- 2. every ADR referenced anywhere exists (file AND ledger row) -------
    n = 0
    for f, t in corpus.items():
        for aid in set(re.findall(r"\bSW-ADR-(\d{3})\b", t)):
            n += 1
            full = f"SW-ADR-{aid}"
            if adr_files and full not in adr_files:
                r.fail("adr-reference", f"{f}: references {full}, which has no file")
            elif ledger_ids and full not in ledger_ids:
                r.fail("adr-reference", f"{f}: references {full}, which has no ledger row")
    r.note(f"distinct ADR references checked: {n}")

    # -- 3. every OPEN id referenced anywhere exists in Article X ------------
    n = 0
    for f, t in corpus.items():
        if f == "CONSTITUTION.md":
            continue
        for oid in set(re.findall(r"\b(OPEN-[A-Z0-9]+-\d+)\b", t)):
            n += 1
            if open_ids and oid not in open_ids:
                r.fail("open-reference",
                       f"{f}: references {oid}, which is not a row in CONSTITUTION.md Article X")
    r.note(f"distinct OPEN references checked: {n}")

    # -- 4. an erratum claimed as FILED must exist --------------------------
    # This is the K1 check: an ADR saying "Filed as ERRATUM E-8" when there is no E-8.
    claim = re.compile(r"(?:filed as|as)\s+ERRATUM\s+(E-[0-9]+)", re.I)
    n = 0
    for f, t in corpus.items():
        for eid in set(claim.findall(t)):
            n += 1
            if eid not in errata:
                r.fail("erratum-claim",
                       f"{f}: claims ERRATUM {eid} is filed — it does not exist in SRC-001 §E")
    for f, t in corpus.items():
        if not re.search(r"erratum candidate", t, re.I):
            continue
        # discharged if the same document also names an erratum that actually exists
        if any(e in t for e in errata):
            continue
        r.fail("erratum-claim",
               f"{f}: says 'erratum candidate' — a candidate is not a filing. "
               f"File it, or reference the erratum that discharges it.")
    r.note(f"erratum claims checked: {n} (errata that exist: {', '.join(sorted(errata)) or 'none'})")

    # -- 5. a prep-queue row claimed by an ADR must exist -------------------
    queue_p = os.path.join(root, "docs", "30 Deployment", "AWS_PREP_QUEUE.md")
    queue = read(queue_p) if os.path.isfile(queue_p) else ""
    KEYS = {
        "SecureString": "SecureString",
        "CORS": "CORS",
        "spendwise_test": "spendwise_test",
        "health check": "health check",
    }
    if queue:
        for aid in sorted(adr_files):
            t = corpus.get(f"docs/01 ADR/all-ADRs/{aid}.md", "")
            if not re.search(r"prep[- ]queue", t, re.I):
                continue
            for label, needle in KEYS.items():
                if re.search(re.escape(needle), t, re.I) and not re.search(re.escape(needle), queue, re.I):
                    r.fail("prep-queue-claim",
                           f"{aid}: says the prep queue must carry '{label}' — "
                           f"AWS_PREP_QUEUE.md does not mention it")
    r.note("prep-queue claims checked against AWS_PREP_QUEUE.md")

    # -- 6. ledger and ADR files agree, both directions ---------------------
    if adr_files or ledger_ids:
        for missing in sorted(ledger_ids - adr_files):
            r.fail("ledger-integrity", f"ledger row {missing} has no ADR file")
        for missing in sorted(adr_files - ledger_ids):
            r.fail("ledger-integrity", f"ADR file {missing} has no ledger row")
        ids = [row["adr_id"] for row in ledger_rows]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            r.fail("ledger-integrity", f"duplicate ledger row: {dup}")
        legal = {"NOT_DECIDED", "APPROVED", "REJECTED", "DEFERRED", "RETIRED", "SUPERSEDED"}
        for row in ledger_rows:
            if row["decision_status"] not in legal:
                r.fail("ledger-integrity",
                       f"{row['adr_id']}: illegal decision_status '{row['decision_status']}'")
        r.note(f"ledger rows: {len(ledger_rows)} · ADR files: {len(adr_files)}")

    # -- 7. frozen-source fingerprints match --------------------------------
    fp_p = os.path.join(sot, "fingerprints.json")
    if os.path.isfile(fp_p):
        fp = json.loads(read(fp_p))
        for fn, rec in sorted(fp.get("sources", {}).items()):
            path = os.path.join(sot, fn)
            if not os.path.isfile(path):
                r.fail("fingerprint", f"{fn} is fingerprinted but missing from disk")
                continue
            with open(path, "rb") as fh:
                live = hashlib.sha256(fh.read()).hexdigest()
            if live != rec["sha256"]:
                r.fail("fingerprint",
                       f"{fn} changed — every artifact derived from it is INVALID "
                       f"and must be re-derived (recorded {rec['sha256'][:16]}…, "
                       f"live {live[:16]}…)")
        r.note(f"frozen sources fingerprinted: {len(fp.get('sources', {}))}")

    # -- 8. no unresolvable 'Client statement' style dangling citation ------
    for f, t in corpus.items():
        if "docs/01 ADR/all-ADRs/" in f and "Client statement, 2026-08-05" in t:
            r.fail("dangling-citation",
                   f"{f}: cites 'Client statement' — cite a SRC-002 clause instead")

    return r


# ── selftest: plant each violation, prove each check fires ──────────────────────
PLANTS = [
    ("source-citation", "docs/01 ADR/all-ADRs/SW-ADR-001.md",
     lambda t: t + "\n\nPlanted: `SRC-001 §999.9` does not exist.\n"),
    ("adr-reference", "docs/01 ADR/all-ADRs/SW-ADR-001.md",
     lambda t: t + "\n\nPlanted: see `SW-ADR-994`.\n"),
    ("open-reference", "docs/01 ADR/all-ADRs/SW-ADR-001.md",
     lambda t: t + "\n\nPlanted: closes `OPEN-NOTREAL-01`.\n"),
    ("erratum-claim", "docs/01 ADR/all-ADRs/SW-ADR-001.md",
     lambda t: t + "\n\nPlanted: Filed as ERRATUM E-99 against SRC-001.\n"),
    ("ledger-integrity", "docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv",
     lambda t: t.replace("APPROVED", "TOTALLY_FINE", 1)),
    ("fingerprint", "docs/00 SourceOfTruth/SRC-001_requirements_2026-08-05.md",
     lambda t: t + "\n\nPlanted: a frozen source was edited.\n"),
    ("dangling-citation", "docs/01 ADR/all-ADRs/SW-ADR-002.md",
     lambda t: t.replace("| Sources |", "| Sources | `Client statement, 2026-08-05` ·", 1)),
]


def _count(rep: Report, check: str) -> int:
    return sum(1 for c, _ in rep.failures if c == check)


def selftest(root: str) -> int:
    """Red-proof: plant one real violation per rule and require the count for that rule to RISE.

    Deliberately does NOT require a clean baseline. A checker that can only be red-proofed
    when the repo is already green is a checker you cannot trust on the day you need it —
    which is precisely the day something is red.
    """
    baseline = check_all(root)
    print("baseline:", "clean" if baseline.ok
          else f"{len(baseline.failures)} pre-existing failure(s) — red-proofing by delta")
    print()

    passed = 0
    for check, target, mutate in PLANTS:
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "repo")
            shutil.copytree(root, work,
                            ignore=shutil.ignore_patterns(*SKIP_DIRS))
            path = os.path.join(work, *target.split("/"))
            if not os.path.isfile(path):
                print(f"  SKIP {check:20} target missing: {target}")
                continue
            original = read(path)
            planted = mutate(original)
            if planted == original:
                print(f"  FAIL {check:20} mutation was a no-op — the plant proved nothing")
                continue
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(planted)

            res = check_all(work)
            before, after = _count(baseline, check), _count(res, check)
            if after > before:
                print(f"  ok   {check:20} planted violation -> fired "
                      f"({before} -> {after})")
                passed += 1
            else:
                print(f"  FAIL {check:20} planted violation -> DID NOT FIRE "
                      f"({before} -> {after}). A check that cannot fail is decoration.")

    total = len(PLANTS)
    print(f"\nselftest: {passed}/{total} checks observed firing on a planted violation")
    return 0 if passed == total else 1


# ── entry point ─────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--selftest", action="store_true",
                    help="plant a real violation of each rule and prove each check fires")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if args.selftest:
        return selftest(args.root)

    r = check_all(args.root)
    for note in r.notes:
        print(f"  {note}")
    print()
    if r.ok:
        print("VERDICT: PASS — every cross-reference resolves.")
        print("         This is the cheap layer only. It cannot see a semantic contradiction")
        print("         between two documents that each resolve fine — see GOAL_13.")
        return 0

    by_check: dict[str, list[str]] = {}
    for c, d in r.failures:
        by_check.setdefault(c, []).append(d)
    for c in sorted(by_check):
        print(f"FAIL [{c}] — {len(by_check[c])}")
        for d in by_check[c]:
            print(f"   {d}")
        print()
    print(f"VERDICT: FAIL — {len(r.failures)} unresolved cross-reference(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
