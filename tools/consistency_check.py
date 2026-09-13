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
import collections
import csv
import hashlib
import io
import glob
import json
import os
import re
import shutil
import subprocess
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
#   docs/12 .../EX_Consolidated-Exit-Gate/
#              is the same category as handoffs/: a conflict map, a root-cause register and a
#              self-challenge exist to QUOTE defects — a superseded ADR that was wrongly cited,
#              a count a reviewer got wrong, a value that fails the gate. Flagging those would
#              punish the record for containing the thing it was written to record. The clearest
#              case: 08_REVIEWER_SELF_CHALLENGE.md was flagged for "claims 77 BRD rows" in the
#              exact sentence stating that the reviewer claimed 77 and the artifacts hold 76.
#              Scoped to this one folder — the rest of docs/12 is checked normally.
SKIP_PATHS = {"PROGRESS.md"}
SKIP_PREFIXES = ("tools/", "handoffs/", "goals/",
                 "docs/12 DesignReview/EX_Consolidated-Exit-Gate/")


def in_scope(relpath: str) -> bool:
    return relpath not in SKIP_PATHS and not relpath.startswith(SKIP_PREFIXES)


# ── plumbing ────────────────────────────────────────────────────────────────────
class Report:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str]] = []
        self.reviews: list[tuple[str, str]] = []
        self.notes: list[str] = []

    def fail(self, check: str, detail: str) -> None:
        self.failures.append((check, detail))

    def review(self, check: str, detail: str) -> None:
        """A heuristic finding: worth a human glance, never a gate.

        Keyword overlap cannot reliably tell a wrong citation from a paragraph that
        legitimately discusses two ADRs at once. Failing the build on it would train
        everyone to ignore the tool, which is worse than not having the check.
        """
        self.reviews.append((check, detail))

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


def _title(corpus_all, aid):
    t = corpus_all.get("docs/01 ADR/all-ADRs/" + aid + ".md", "")
    m = re.search(r"^# SW-ADR-\d+ . (.+)$", t, re.M)
    return (m.group(1)[:48] if m else "?")


# ── the checks ──────────────────────────────────────────────────────────────────
def check_all(root: str) -> Report:
    r = Report()
    sot = os.path.join(root, "docs", "00 SourceOfTruth")
    adr_dir = os.path.join(root, "docs", "01 ADR", "all-ADRs")
    ledger_p = os.path.join(root, "docs", "01 ADR", "ADR_DECISION_RELEASE_LEDGER.tsv")
    const_p = os.path.join(root, "CONSTITUTION.md")

    files = walk(root)
    corpus_all = {rel(root, p): read(p) for p in files}
    corpus = {k: v for k, v in corpus_all.items() if in_scope(k)}

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


    # -- 9. TOPICAL DRIFT: a citation that RESOLVES but points at the WRONG ADR ----
    # The GOAL_04 review found 20 of these across six documents. Every one resolved —
    # the ADR existed — it just meant something else entirely. Check 2 cannot see this
    # class at all, which is exactly why it needs its own.
    STOP = set(("the a an and or of for to in on at is are be with by from that this it its "
                "not no never every each all any one two into out up down over under").split())

    def _kw(x):
        return {w for w in re.findall(r"[a-z0-9_]+", x.lower())
                if len(w) > 3 and w not in STOP}

    adr_kw = {}
    for aid in sorted(adr_files):
        t = corpus_all.get("docs/01 ADR/all-ADRs/" + aid + ".md", "")
        ttl = re.search(r"^# SW-ADR-\d+ . (.+)$", t, re.M)
        dec = re.search(r"## Decision\s+(.{0,400})", t, re.S)
        if ttl:
            adr_kw[aid] = _kw(ttl.group(1)) | (_kw(dec.group(1)) if dec else set())

    drift = 0
    for f, t in corpus.items():
        # In a delimited file every row is its own statement, so a character window
        # would span unrelated rows and manufacture false positives. Scope to the row.
        row_scoped = f.endswith((".tsv", ".csv"))
        for m in re.finditer(r"SW-ADR-(\d{3})", t):
            aid = "SW-ADR-" + m.group(1)
            if aid not in adr_kw:
                continue
            if row_scoped:
                ls = t.rfind(chr(10), 0, m.start()) + 1
                le = t.find(chr(10), m.end())
                window = t[ls: le if le != -1 else len(t)]
            else:
                window = t[max(0, m.start() - 260): m.end() + 60]
            ctx = _kw(window)
            if adr_kw[aid] & ctx:
                continue
            best = sorted(((len(adr_kw[a] & ctx), a) for a in adr_kw), reverse=True)[:1]
            if best and best[0][0] >= 7:
                drift += 1
                r.review("citation-topic",
                       f"{f}: cites {aid} ({_title(corpus_all, aid)}) but the surrounding "
                       f"text matches {best[0][1]} ({_title(corpus_all, best[0][1])})")
    r.note(f"topical drift: {len(adr_kw)} ADRs indexed, {drift} citation(s) to eyeball "
           f"(heuristic - reported, never a gate)")

    # -- 10. no live document rests authority on a non-APPROVED record ------
    # Check 2 proves a reference RESOLVES. It cannot prove the record is still
    # authority. X-01 found 80 references to superseded records, including
    # CONSTITUTION Art IV.1 resting the product's central security promise on a
    # withdrawn one - and every single reference passed check 2. This gates.
    dead = {row["adr_id"] for row in ledger_rows
            if row.get("decision_status") not in ("APPROVED", "")}
    # A record NAMING what it superseded is correct and must not fire. The
    # distinction is whether the sentence is about the past.
    # Stems, not whole words: "superseding" does not contain "supersede", and the
    # first version of this check failed a correctly-worded sentence for it.
    HIST = re.compile(
        r"supersed|supercede|withdraw|withdrew|amend|retir|histor|restat|"
        r"was ruled|no longer|replac|former|previous|used to|"
        r"not current authority|keeps its (?:original )?text|worked example",
        re.I)
    # A FROZEN source is exempt, for the same reason all-ADRs/ and the ledger
    # are: its mention of a record is provenance, not reliance.
    #
    # SRC-001 and SRC-002 carry "Carried into: SW-ADR-nnn" lines, which record
    # what was derived from that clause AT THE TIME. They are also sealed with a
    # SHA-256 in fingerprints.json, and check 7 fails the whole run if a single
    # byte changes - so they can never be annotated to say "superseded", now or
    # ever. That is by design and is not going to change.
    #
    # Without this exemption, superseding ANY ADR that a frozen source names is
    # impossible: the gate fails permanently, and the only way back to green is
    # to leave the ADR marked APPROVED after it has stopped being true. A check
    # that can only be satisfied by lying is worse than no check.
    #
    # Found on 2026-09-13 trying to supersede SW-ADR-005, which two frozen
    # sources name. Narrowed deliberately and with the client's approval, since
    # loosening a quality check is a reserved decision - never silently.
    frozen = set()
    if os.path.isfile(fp_p):
        for fn in json.loads(read(fp_p)).get("sources", {}):
            frozen.add("docs/00 SourceOfTruth/" + fn)

    stale = 0
    for f, t in corpus.items():
        if f.startswith("docs/01 ADR/all-ADRs/") or "LEDGER" in f or f in frozen:
            continue
        row_scoped = f.endswith((".tsv", ".csv"))
        for m in re.finditer(r"\bSW-ADR-(\d{3})\b", t):
            aid = "SW-ADR-" + m.group(1)
            if aid not in dead:
                continue
            if row_scoped:
                ls = t.rfind(chr(10), 0, m.start()) + 1
                le = t.find(chr(10), m.end())
                window = t[ls: le if le != -1 else len(t)]
            else:
                # a whole paragraph: a supersession is usually narrated a
                # sentence or two away from the identifier itself
                ps = t.rfind("\n\n", 0, m.start()) + 2
                pe = t.find("\n\n", m.end())
                window = t[ps: pe if pe != -1 else len(t)]
            if HIST.search(window):
                continue
            stale += 1
            r.fail("adr-status",
                   f"{f}: rests authority on {aid} ({_title(corpus_all, aid)}), which the "
                   f"ledger records as not APPROVED")
    r.note(f"citations of non-APPROVED records: {stale} (of {len(dead)} dead records)")

    # -- 11. a stated count matches the thing it counts ---------------------
    # Six of X-01's twenty-one findings were a number typed into prose that had
    # since drifted: 22 ADRs (130), seven errata (ten), 44 stories (48), 178
    # criteria (194), 76 BRD rows (77), nine admin endpoints (seven). A count
    # that is asserted rather than derived is a fact with no owner.
    bible_p = "docs/05 Bible/SpendWise_Bible.csv"
    bible_rows = list(csv.DictReader(io.StringIO(corpus_all.get(bible_p, "")))) \
        if bible_p in corpus_all else []
    n_stories = sum(1 for b in bible_rows if b.get("Type") == "Story")
    n_ac = sum(len([x for x in (b.get("AcceptanceCriteria") or "").split("|") if x.strip()])
               for b in bible_rows)
    brd_t = corpus_all.get("docs/02 BRD/SpendWise_BRD.md", "")
    n_brd = len(set(re.findall(r"^\|\s*`([RN]-[A-Z]+-\d+)`", brd_t, re.M)))
    live = len(ledger_ids) - len(dead)

    COUNTS = [
        (r"\*\*(\d+) decision records\*\*", len(adr_files), "ADR files"),
        (r"the (\d+) records in `docs/01 ADR/", len(adr_files), "ADR files"),
        (r"(\d+) of the (?:\d+) ADRs are\s*\n?\s*superseded", len(dead), "superseded ADRs"),
        (r"of the (\d+) ADRs are", len(ledger_ids), "ledger rows"),
        (r"\((\d+) live,", live, "live ADRs"),
        (r"\*\*(\d+) errata", len(errata), "errata"),
        (r"(\w+) errata now exist", len(errata), "errata"),
        (r"\*\*(\d+) business requirements", n_brd, "BRD rows"),
        (r"(\d+) BRD rows, all covered", n_brd, "BRD rows"),
        (r"\|\s*(\d+) stories,", n_stories, "Bible stories"),
        (r"\*\*(\d+) binary acceptance criteria\*\*", n_ac, "acceptance criteria"),
        (r"\*\*(\d+) positive cases\*\*", n_ac, "SIT positive cases"),
    ]
    WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    # A provenance line - "Drafted 2026-08-05 from the 22 records" - is a true
    # statement about the past, and SW-ADR-133 rules it must NOT be refreshed:
    # rewriting it would destroy a fact to fix a count.
    PROV = re.compile(r"\|\s*Drafted\s*\||drafted (?:on|from)|as of \d|at the time|"
                      r"originally|when (?:this|it) was (?:written|drafted)|v0\.\d marked", re.I)
    checked = 0
    for f, t in corpus.items():
        if f.startswith("docs/01 ADR/all-ADRs/"):
            continue           # an ADR states what was true when it was decided
        for rx, actual, what in COUNTS:
            if actual == 0:
                continue
            for m in re.finditer(rx, t, re.I):
                g = m.group(1).lower()
                claimed = WORDS.get(g, None) if not g.isdigit() else int(g)
                if claimed is None:
                    continue
                ls = t.rfind("\n", 0, m.start()) + 1
                le = t.find("\n", m.end())
                if PROV.search(t[ls: le if le != -1 else len(t)]):
                    continue   # historical provenance, not a live claim
                checked += 1
                if claimed != actual:
                    r.fail("stated-count",
                           f"{f}: claims {claimed} {what}; the artifacts hold {actual}")
    r.note(f"stated counts verified against the artifacts: {checked}")

    # -- 12. a file that says GENERATED really is ---------------------------
    # security.sql carried a GENERATED banner for a generator that no longer
    # existed. Under that cover it grew an admin policy absent from the spec of
    # record - the isolation hole SW-ADR-129 closes. The banner was the defect's
    # hiding place, so the banner is now executable.
    # -- 10b. Art II.6 — an amended record is MARKED where it stands ---------
    # "Superseded text MUST be marked superseded where it stands. An unmarked
    # contradiction between two live documents is a defect, not a reader's
    # judgement call." This was the one rule in the Constitution with no check
    # behind it, and it failed exactly as written: SW-ADR-141 C and SW-ADR-143 E
    # gave opposite answers, both APPROVED, 141 unmarked, and the resolution
    # lived only in a cell that reached no page. An engineer who resolves the
    # ambiguity the way this document set trains them to - by going to the ADRs -
    # implements the wrong one, and every negative case still passes, because
    # each varies exactly one input.
    amended = 0
    for aid in sorted(adr_files):
        t = corpus_all.get("docs/01 ADR/all-ADRs/" + aid + ".md", "")
        m = re.search(r"^\|\s*Amends\s*\|\s*(.+?)\s*\|$", t, re.M)
        if not m:
            continue
        for target in re.findall(r"SW-ADR-\d{3}", m.group(1)):
            amended += 1
            tt = corpus_all.get("docs/01 ADR/all-ADRs/" + target + ".md", "")
            head = tt[:900]
            if aid not in head or not re.search(r"⚠|AMENDED|SUPERSEDED|NOT CURRENT", head):
                r.fail("amendment-marker",
                       f"{aid} amends {target}, but {target} carries no banner naming {aid}. "
                       f"Art II.6: superseded text MUST be marked where it stands — an unmarked "
                       f"contradiction between two live records is a defect, not a reader's "
                       f"judgement call")
    r.note(f"amendment markers checked: {amended}")

    # -- 11b. the day-one acceptance value agrees with itself, everywhere ---
    # 75810 paise is the never-waivable gate, asserted across seventeen files and
    # derived from four fixture amounts. If the fixture ever changes, every one of
    # those goes stale at once. So the arithmetic is recomputed, not trusted.
    FIX = [125000, 210000, 34050, 9999]
    DAYS = 5
    total = sum(FIX)
    avg = (total * 2 + DAYS) // (DAYS * 2)          # half-up, in integers
    # A document that WARNS about the wrong value is doing its job. Only an
    # assertion of it is a defect - the same exemption shape as check 10.
    WARN = re.compile(r"\bnot\b|never|wrong|fail|truncat|instead of|gives|rather than|"
                      r"rounded|half-up|would be|mistak", re.I)
    seen, bad = collections.Counter(), []
    for f, t in corpus.items():
        for m in re.finditer(r"\b(7581[0-9]|758[0-9][0-9]|9476[0-9]|379,?049)\b", t):
            v = m.group(1).replace(",", "")
            seen[v] += 1
            if v in (str(avg), str(total)):
                continue
            # The LINE, not a character window: a document that warns about the
            # wrong value says so in the same sentence. A wider window would let
            # unrelated prose two paragraphs away excuse a bare assertion.
            ls = t.rfind("\n", 0, m.start()) + 1
            le = t.find("\n", m.end())
            if not WARN.search(t[ls: le if le != -1 else len(t)]):
                bad.append((f, v))
    for f, v in bad:
        r.fail("day-one-value",
               f"{f}: asserts {v} where the day-one gate is {avg} paise "
               f"(total {total} over {DAYS} days elapsed, half-up). {v} is what "
               f"truncation or dividing by the row count gives")
    r.note(f"day-one acceptance value recomputed: {total} / {DAYS} = {avg} paise "
           f"(asserted in {seen.get(str(avg), 0)} place(s))")

    # -- 12b. every route a test names exists in the contract -----------------
    # PRD §6's route table was hand-maintained and hand-copied into the route map
    # and the cross-person coverage matrix. All three omitted
    # GET /api/expenses/{expense_id}, which Bible E0-S7 AC1 and the SEV-1 case
    # NEG-X-01 both require - while the coverage matrix declared 25/25 covered.
    contract_p = os.path.join(root, "docs", "03 PRD", "api", "contract.json")
    if os.path.isfile(contract_p):
        contract = json.loads(read(contract_p))
        declared = set()
        for rt in contract.get("routes", {}).get("routes", []):
            # normalise the parameter name: {id} and {expense_id} are one route
            declared.add((rt["method"], re.sub(r"\{[^}]+\}", "{}", rt["path"])))
        named, unresolved = 0, []
        SOURCES = ("docs/05 Bible/", "docs/08 SIT/", "docs/09 NegativeTesting/",
                   "docs/11 Journeys/")
        for f, t in corpus.items():
            if not f.startswith(SOURCES):
                continue
            # a placeholder may be written {id}, {expense_id} or {A's id} — anything
            # up to the closing brace, apostrophes and spaces included
            for m in re.finditer(
                    r"\b(GET|POST|PATCH|DELETE|PUT)\s+(/api/(?:\{[^}]*\}|[A-Za-z0-9_/-])*)", t):
                named += 1
                key = (m.group(1), re.sub(r"\{[^}]*\}", "{}", m.group(2).rstrip("/")))
                if key not in declared:
                    unresolved.append((f, "%s %s" % m.groups()))
        for f, route in sorted(set(unresolved)):
            r.fail("route-contract",
                   f"{f}: names `{route}`, which is not a route in "
                   f"docs/03 PRD/api/contract.json")
        r.note(f"routes named by a test or journey: {named} across {len(declared)} declared")

        # -- 12c. the spec of record's own cross-references resolve ----------
        # contract.json became the least-reviewed document in the set: every
        # remaining defect the fifth slice found lived inside it, and each had
        # one shape - a hand-written cell asserting something about another
        # document, never checked against it. The generator proves
        # contract.json -> PRD in one direction. Nothing proved
        # contract.json -> the documents it cites.
        defined = set(contract.get("models", {})) | set(
            contract.get("request_models", {}).get("models", {}))
        for rt in contract.get("routes", {}).get("routes", []):
            for key in ("request_model", "response_model"):
                m = rt.get(key)
                if not m:
                    continue
                base = m.rstrip("[]")
                if base not in defined:
                    r.fail("contract-refs",
                           f"contract.json: route `{rt['method']} {rt['path']}` names "
                           f"{key} `{m}`, which no model block defines")

        # every P- row, SW-ADR, Bible story and OPEN id named anywhere in the
        # spec of record must resolve
        prd_specs = set(re.findall(r"\*\*`(P-[A-Z]+-\d+)`",
                                   corpus_all.get("docs/03 PRD/SpendWise_PRD.md", "")))
        bible_ids = set()
        bp = corpus_all.get("docs/05 Bible/SpendWise_Bible.csv", "")
        if bp:
            bible_ids = {b["ID"] for b in csv.DictReader(io.StringIO(bp))}
        blob = read(contract_p)
        for pid in sorted(set(re.findall(r"\b(P-[A-Z]+-\d+)\b", blob))):
            if prd_specs and pid not in prd_specs:
                r.fail("contract-refs",
                       f"contract.json: cites `{pid}`, which is not a specification in the PRD")
        for bid in sorted(set(re.findall(r"\b(E\d+-S\d+)\b", blob))):
            if bible_ids and bid not in bible_ids:
                r.fail("contract-refs",
                       f"contract.json: cites Bible story `{bid}`, which does not exist")
        r.note(f"spec-of-record cross-references: {len(defined)} models defined, "
               f"{len(set(re.findall(r'P-[A-Z]+-[0-9]+', blob)))} P- rows cited")

        # -- 12d. every block of the spec REACHES the page it feeds ----------
        # `contract-refs` is a REFERENCE check and both of these slipped past it:
        # `render_request_models` was defined and never called, so PRD §6.4 did
        # not exist while SW-ADR-141 asserted it did; and `render_codes` read
        # four keys of the five-key `precedence` object, so the registry stated
        # an order that made `range.required` unreachable and omitted the scope
        # text that prevents that reading. Every reference resolved. `--check`
        # printed PASS, because it asks whether the artifact matches what the
        # generator EMITS - never whether the generator emits what the spec
        # CONTAINS. This is a completeness check.
        prd_t = corpus_all.get("docs/03 PRD/SpendWise_PRD.md", "")
        codes_t = corpus_all.get("docs/03 PRD/api/error_codes.md", "")
        REACHES = [
            ("routes.routes", prd_t, "PRD §6",
             [rt["path"] for rt in contract.get("routes", {}).get("routes", [])]),
            ("conventions.rules", prd_t, "PRD §6.2",
             [c["id"] for c in contract.get("conventions", {}).get("rules", [])]),
            ("request_models.models", prd_t, "PRD §6.4",
             list(contract.get("request_models", {}).get("models", {}))),
            ("serialisation", prd_t, "PRD §6.3",
             [contract.get("serialisation", {}).get("amount_grammar", {}).get("pattern", "")]),
            ("error_codes.codes", codes_t, "error_codes.md",
             [c["code"] for c in contract.get("error_codes", {}).get("codes", [])]),
            ("error_codes.messages.rules", codes_t, "error_codes.md",
             [m["rule"] for m in
              contract.get("error_codes", {}).get("messages", {}).get("rules", [])]),
            ("error_codes.precedence.scope", codes_t, "error_codes.md",
             list(contract.get("error_codes", {}).get("precedence", {}).get("scope", {}).values())),
            ("error_codes.messages.by_code", codes_t, "error_codes.md",
             [c["message"] for c in contract.get("error_codes", {})
              .get("messages", {}).get("by_code", {}).get("codes", [])]),
            ("transaction", prd_t, "PRD §6.3",
             [contract.get("transaction", {}).get("isolation", "")]),
        ]
        # Per-KEY, not per-block: `precedence` rendered four of its five keys and
        # the block still looked covered, so the tie-break rule reached no page
        # while the page printed "(see tie_break)".
        for blk, target, where in (("error_codes.precedence", codes_t, "error_codes.md"),
                                   ("transaction", prd_t, "PRD §6.3"),
                                   ("serialisation", prd_t, "PRD §6.3")):
            obj = contract
            for part in blk.split("."):
                obj = obj.get(part, {}) if isinstance(obj, dict) else {}
            for k, v in (obj.items() if isinstance(obj, dict) else []):
                if not isinstance(v, str) or len(v) < 25:
                    continue
                # A `why`/`note`/`alternative` cell is RATIONALE, and rationale
                # belongs in the ADR that ruled it, not in a reference table. It
                # still has to reach a reader somewhere — an unpublished rationale
                # is how SW-ADR-141 C and SW-ADR-143 E ended up disagreeing with
                # the resolution visible in neither.
                rationale = k in ("note", "alternative") or k.startswith("why")
                haystacks = ([t for t in corpus.values()] if rationale else [target])
                if not any(v[:80] in h for h in haystacks):
                    r.fail("spec-completeness",
                           f"contract.json `{blk}.{k}`: its text reaches "
                           f"{'no document at all' if rationale else where}. "
                           f"A renderer that reads some keys of an object leaves the rest "
                           f"invisible while the block still looks covered")

        reached = 0
        for block, target, where, items in REACHES:
            missing = [str(x) for x in items if x and str(x)[:90] not in target]
            reached += len(items) - len(missing)
            if missing:
                r.fail("spec-completeness",
                       f"contract.json `{block}`: {len(missing)} of {len(items)} entries never "
                       f"reach {where} — e.g. {missing[0][:70]!r}. A block the generator does not "
                       f"emit is invisible to every reader of the document it was written into, "
                       f"and --check cannot see it because it compares the page against what the "
                       f"generator emits")
        r.note(f"spec-of-record blocks reaching their page: {reached} entries across "
               f"{len(REACHES)} blocks")

    # ── every route the app SERVES must be in the spec of record ──────────
    # The existing `route-contract` check runs one way: a document naming a
    # route the contract does not have. Nothing ran the other way, and that is
    # the direction that rots — a route gets built, ships, and the contract
    # that generates the PRD never learns about it. On 2026-08-21 that gap was
    # SEVEN routes wide: PATCH /api/auth/me, POST /api/auth/password,
    # POST /api/auth/deactivate, DELETE /api/auth/me, GET /api/auth/export,
    # GET /api/admin/overview and GET /api/admin/users/{user_id}/spending —
    # every one of them approved, shipped, and absent from the document the
    # PRD's §6 route table is generated from.
    #
    # Read STATICALLY, from the routers' decorators. Importing the app would
    # need a valid configuration, and a check that cannot run on a bare clone
    # is a check that quietly stops running.
    import ast as _ast
    served: set[tuple[str, str]] = set()
    router_files = sorted(glob.glob(os.path.join(root, "app", "modules", "*", "router.py")))         + [os.path.join(root, "app", "core", "health.py")]
    for rf in router_files:
        if not os.path.isfile(rf):
            continue
        try:
            tree = _ast.parse(open(rf, encoding="utf-8").read())
        except SyntaxError:
            r.fail("route-coverage", f"{os.path.relpath(rf, root)} does not parse")
            continue
        prefix = ""
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Call) and getattr(node.func, "id", "") == "APIRouter":
                for kw in node.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, _ast.Constant):
                        prefix = kw.value.value
        for node in _ast.walk(tree):
            if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, _ast.Call):
                    continue
                fn = dec.func
                if not isinstance(fn, _ast.Attribute) or getattr(fn.value, "id", "") != "router":
                    continue
                verb = fn.attr.upper()
                if verb not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    continue
                if dec.args and isinstance(dec.args[0], _ast.Constant):
                    served.add((verb, prefix + dec.args[0].value))
    if not served:
        r.fail("route-coverage",
               "no routes were extracted from any router — the extractor is "
               "broken, and an empty comparison would pass for the wrong reason")
    else:
        con = os.path.join(root, "docs", "03 PRD", "api", "contract.json")
        documented = set()
        if os.path.isfile(con):
            try:
                blob = json.load(open(con, encoding="utf-8"))
                documented = {(x["method"], x["path"])
                              for x in blob.get("routes", {}).get("routes", [])}
            except Exception:                               # noqa: BLE001
                pass
        undocumented = sorted(served - documented)
        if undocumented:
            listed = ", ".join(f"{m} {p}" for m, p in undocumented[:8])
            r.fail("route-coverage",
                   f"{len(undocumented)} route(s) are served but absent from the API "
                   f"spec of record: {listed}. contract.json generates the PRD's §6 "
                   f"route table and error_codes.md, so a route missing here is a "
                   f"shipped capability the specification does not describe")
        else:
            r.note(f"routes served and documented: {len(served)}")

    # ── the Uncategorised band is THREE artifacts, not one ────────────────
    # `CR-002` moved the palette and `--sw-cat-uncat` had to be darkened, because
    # the band's GROUND changed even though the band did not. Moving the token was
    # not enough and nothing said so: the ribbon and the donut paint `b.color`
    # straight from the summary response, so the colour a person actually sees is
    # a PYTHON constant, and `tools/contrast.py` — which reads the stylesheet —
    # reported PASS on a hex the browser never drew. A gate measuring the wrong
    # artifact is worse than no gate: it produces evidence.
    #
    # Three places hold this one colour. They must be one hex.
    uncat = {}
    tok = os.path.join(root, "docs", "05 B DesignSystem", "tokens.css")
    if os.path.isfile(tok):
        m = re.search(r"--sw-cat-uncat:\s*(#[0-9a-fA-F]{6})",
                      open(tok, encoding="utf-8").read())
        if m:
            uncat["the design-system token `--sw-cat-uncat`"] = m.group(1).lower()
    srv = os.path.join(root, "app", "modules", "expenses", "summary.py")
    if os.path.isfile(srv):
        m = re.search(r'UNCATEGORISED_COLOR\s*=\s*"(#[0-9a-fA-F]{6})"',
                      open(srv, encoding="utf-8").read())
        if m:
            uncat["the server constant `UNCATEGORISED_COLOR`"] = m.group(1).lower()
    con = os.path.join(root, "docs", "03 PRD", "api", "contract.json")
    if os.path.isfile(con):
        try:
            syn = json.load(open(con, encoding="utf-8"))
            for block in syn.values():
                if isinstance(block, dict) and isinstance(block.get("synthetic"), dict)                         and block["synthetic"].get("name") == "Uncategorised":
                    uncat["the API contract `synthetic.color`"] =                         str(block["synthetic"]["color"]).lower()
        except Exception:                                   # noqa: BLE001
            pass
    if len(uncat) < 3:
        r.fail("band-colour-agreement",
               f"only {len(uncat)} of the 3 Uncategorised colour sources could be read "
               f"({', '.join(uncat) or 'none'}) — a source this check cannot see is a "
               f"source it cannot hold to the floor")
    elif len(set(uncat.values())) != 1:
        detail = "; ".join(f"{k} = {v}" for k, v in sorted(uncat.items()))
        r.fail("band-colour-agreement",
               f"the Uncategorised band is {len(set(uncat.values()))} different colours: {detail}. "
               f"The ribbon and donut render the SERVER value, so the stylesheet can measure "
               f"3.07:1 while the browser draws something else — contrast.py would pass and the "
               f"product would fail (`CR-002`, `SW-ADR-152`)")
    else:
        r.note(f"Uncategorised band agrees across 3 artifacts: {next(iter(uncat.values()))}")

    ok = 0
    for gen in (os.path.join(root, "docs", "06 DataModel", "generate.py"),
                os.path.join(root, "docs", "03 PRD", "api", "generate_api.py"),
                os.path.join(root, "tools", "generate_docs_readme.py"),
                # The client's copy of the design tokens. Every contrast figure
                # in DESIGN-SYSTEM.md was COMPUTED from the source values, and
                # one of the nine category bands failed the 3:1 floor and had to
                # be darkened — so a hand-edited copy inside client/ would be a
                # colour that no measurement backs.
                os.path.join(root, "client", "sync_tokens.py"),
                # Every contrast figure in the design system, computed rather
                # than asserted — and it fails on a pair BELOW ITS FLOOR, not
                # only on drift. A generated table faithfully recording a
                # 2.36:1 would be a document doing its job while the product
                # fails the standard it claims (`SW-ADR-147`).
                os.path.join(root, "tools", "contrast.py")):
        if not os.path.isfile(gen):
            r.fail("generated-artifact",
                   os.path.relpath(gen, root).replace("\\", "/") + " is missing, so every "
                   "GENERATED banner it backs is an unfalsifiable claim")
            continue
        out = subprocess.run([sys.executable, gen, "--check"],
                             capture_output=True, text=True, cwd=root)
        if out.returncode != 0:
            for line in (out.stdout + out.stderr).strip().split("\n"):
                if line.strip():
                    r.fail("generated-artifact", line.rstrip())
        else:
            ok += out.stdout.count("PASS")
    # Derived, not typed. It read "of 8" while nine artifacts were verified,
    # because a fourth was added to generate.py and the literal did not follow —
    # the `stated-count` class, in the checker that catches it.
    r.note(f"generated artifacts verified by regeneration: {ok}")

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
    # The plant must carry enough of SW-ADR-119's own vocabulary to clear the
    # threshold, or this "red-proof" proves only that a weak signal is ignored.
    ("citation-topic", "docs/02 BRD/SpendWise_BRD.md",
     lambda t: t + (
         "\n\nPlanted: every destructive action confirms, naming the blast radius. "
         "Delete category names the count of expenses that become uncategorised; "
         "delete expense names the amount and date and warns the receipt goes; "
         "deactivate warns they will be signed out immediately; no undo exists, so "
         "the confirm is the protection, with no type-the-name friction anywhere. "
         "Per `SW-ADR-118`.\n")),
    ("dangling-citation", "docs/01 ADR/all-ADRs/SW-ADR-002.md",
     lambda t: t.replace("| Sources |", "| Sources | `Client statement, 2026-08-05` ·", 1)),
    # The plant must be a bare authority claim with NO historical framing, or it
    # proves only that the history exemption works.
    ("adr-status", "docs/02 BRD/SpendWise_BRD.md",
     lambda t: t + "\n\nPlanted: isolation is enforced twice, per `SW-ADR-018`.\n"),
    ("stated-count", "docs/02 BRD/SpendWise_BRD.md",
     lambda t: t + "\n\nPlanted: this pack holds **7 decision records**.\n"),
    ("generated-artifact", "docs/06 DataModel/security.sql",
     lambda t: t + "\nCREATE POLICY planted_hole ON expenses FOR SELECT USING (true);\n"),
    # The client's token copy, drifted by ONE hex digit — the exact shape this
    # check exists for: a colour in the shipped stylesheet that no longer
    # matches the one the design system measured 4.55:1 against.
    ("generated-artifact", "client/src/styles/tokens.css",
     lambda t: t.replace("#4a7c59", "#4a7c5a", 1)),
    # Asserted, with no warning framing anywhere near it — the shape that matters.
    ("day-one-value", "docs/02 BRD/SpendWise_BRD.md",
     lambda t: t + "\n\nPlanted: the daily average over the seeded fixture is 75809 paise.\n"),
    # A third key in `scope`, which render_codes does not read — the exact shape
    # of the bug: every reference resolves, and the text never reaches the page.
    ("spec-completeness", "docs/03 PRD/api/contract.json",
     lambda t: t.replace('"range_required":',
                         '"planted_third_key": "this text reaches no page", "range_required":', 1)),
    # Divergence between the stylesheet and the SERVER value — the exact shape
    # CR-002 shipped for a few minutes: contrast.py green, browser drawing 2.99:1.
    ("band-colour-agreement", "app/modules/expenses/summary.py",
     lambda t: t.replace('UNCATEGORISED_COLOR = "#928a85"',
                         'UNCATEGORISED_COLOR = "#948c87"', 1)),
    # A served route quietly dropped from the spec of record. This is the
    # direction nothing watched until 2026-08-21, when it was seven routes wide.
    ("route-coverage", "docs/03 PRD/api/contract.json",
     lambda t: t.replace('"path": "/api/auth/login"',
                         '"path": "/api/auth/login-RENAMED"', 1)),
    ("contract-refs", "docs/03 PRD/api/contract.json",
     lambda t: t.replace('"response_model": "Summary"',
                         '"response_model": "SummaryThatDoesNotExist"', 1)),
    ("route-contract", "docs/09 NegativeTesting/SIT_NegativeCases.tsv",
     lambda t: t + "NEG-Z-99\tplanted\tSEV-3\tplanted route\tPERSON B\t"
                   "PATCH /api/expenses/{id}/nonexistent\t404\t-\t-\tplanted\tNotRun\n"),
]


def _count(rep: Report, check: str) -> int:
    """Count BOTH channels.

    A check that reports into `review` still fires; it simply does not gate. Counting
    only `failures` would report it as decoration when it is doing its job — which is
    exactly the false green this selftest exists to catch, turned on itself.
    """
    return (sum(1 for c, _ in rep.failures if c == check)
            + sum(1 for c, _ in rep.reviews if c == check))


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
    if r.reviews:
        print(f"REVIEW [citation-topic] — {len(r.reviews)} citation(s) worth an eyeball.")
        print("  Heuristic, not a gate. A paragraph may legitimately discuss two ADRs.")
        for _, d in r.reviews:
            print(f"   {d}")
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
