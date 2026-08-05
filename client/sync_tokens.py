#!/usr/bin/env python3
"""Copy the design system's tokens into the client build. GENERATED artifact.

`docs/05 B DesignSystem/tokens.css` is the source of record: every contrast
figure in `DESIGN-SYSTEM.md §2.1` and `§2.2` was **computed** from those hex
values, and one of the nine category bands failed the 3:1 floor and had to be
darkened. A second, hand-maintained copy inside `client/` would let a colour
drift away from the figure that was measured against it — and nothing would
notice, because the measurement lives in a different file from the value.

So the client's copy is generated, with a banner saying so, and
`consistency_check.py` runs this with `--check` on every build.

    py client/sync_tokens.py            # write
    py client/sync_tokens.py --check    # regenerate and compare; non-zero on drift

Importing the source path directly from Vite was the alternative. It was
rejected: it needs `server.fs.allow` pointed outside the project root, and the
Docker build stage copies `client/` alone — so the import would resolve on a
laptop and fail in the image, which is the worst place for a difference.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "docs" / "05 B DesignSystem" / "tokens.css"
TARGET = HERE / "src" / "styles" / "tokens.css"

BANNER = """/* GENERATED — do not edit.
 *
 * Source: docs/05 B DesignSystem/tokens.css
 * Regenerate: py client/sync_tokens.py
 *
 * Edit the design system, not this file. Every contrast figure in
 * DESIGN-SYSTEM.md was computed from the source values; a hex changed here
 * would be a number no measurement backs.
 */

"""


def render() -> str:
    return BANNER + SOURCE.read_text(encoding="utf-8")


def main(argv: list[str]) -> int:
    if not SOURCE.is_file():
        print(f"FAIL  {SOURCE} is missing")
        return 1
    want = render()
    if "--check" in argv:
        if not TARGET.is_file():
            print(f"FAIL  {TARGET.relative_to(ROOT)} has not been generated")
            return 1
        got = TARGET.read_text(encoding="utf-8")
        if got != want:
            print(f"FAIL  client/src/styles/tokens.css has drifted from the design system")
            return 1
        print("PASS  client/src/styles/tokens.css matches the design system")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(want, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)} ({len(want)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
