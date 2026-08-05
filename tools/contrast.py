#!/usr/bin/env python3
"""Compute every contrast figure in the design system. GENERATED artifact.

`DESIGN-SYSTEM.md` opens with a promise: *"Every contrast figure below was
**computed** from the hex values in `tokens.css`, not asserted."* That promise
was kept by hand for one theme. Adding a second theme and translucent surfaces
makes it unkeepable by hand — glass composites over whatever is behind it, so
the colour a person actually reads is not a value written anywhere.

So this computes it. WCAG 2.1 relative luminance, alpha-composited where a
surface is translucent, checked against the floor each pair is subject to:

* **4.5:1** for text (SC 1.4.3)
* **3:1** for a UI component or a large-text pair (SC 1.4.11, SC 1.4.3)

    py tools/contrast.py            # write CONTRAST.md
    py tools/contrast.py --check    # regenerate and compare; non-zero on drift

**It fails on a pair below its floor, not only on drift.** A generated table
that faithfully records a 2.4:1 would be a document doing its job while the
product fails the standard it claims.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TOKENS = ROOT / "docs" / "05 B DesignSystem" / "tokens.css"
TARGET = ROOT / "docs" / "05 B DesignSystem" / "CONTRAST.md"


# ── colour ─────────────────────────────────────────────────────────────────
def parse(value: str, table: dict[str, str] | None = None,
          _depth: int = 0) -> tuple[float, float, float, float]:
    """`#rrggbb`, `#rgb`, `rgb(r g b / a)` or `var(--sw-x)` -> (r, g, b, alpha).

    `var()` is followed, because `--sw-focus-color: var(--sw-pine)` is how the
    design system says "the focus ring IS the accent" and resolving it here is
    the only way to measure the thing that actually renders.
    """
    v = value.strip()
    m = re.fullmatch(r"var\(\s*(--sw-[a-z0-9-]+)\s*\)", v)
    if m:
        if table is None or m.group(1) not in table or _depth > 8:
            raise ValueError(f"cannot resolve {v!r}")
        return parse(table[m.group(1)], table, _depth + 1)
    if v.startswith("#"):
        h = v[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = re.match(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*(?:[/,]\s*([\d.]+))?\s*\)", v)
    if not m:
        raise ValueError(f"cannot parse colour {value!r}")
    a = float(m.group(4)) if m.group(4) else 1.0
    return (float(m.group(1)), float(m.group(2)), float(m.group(3)), a)


def over(fg: tuple[float, float, float, float],
         bg: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Source-over compositing. What the eye receives when a translucent
    surface sits on an opaque one — and the only colour a contrast figure for
    glass can honestly be computed from."""
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def luminance(c: tuple[float, float, float, float]) -> float:
    """WCAG 2.1 relative luminance. The 0.03928/12.92 branch is the sRGB
    transfer curve, not a rounding convenience."""
    def channel(x: float) -> float:
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = channel(c[0]), channel(c[1]), channel(c[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str, bg: str, base: str | None = None,
          table: dict[str, str] | None = None) -> float:
    """Contrast between two token values, compositing each over `base` first.

    `base` is what a translucent surface sits on. Passing it for an opaque
    pair changes nothing, which is why every call passes it.
    """
    b = parse(base, table) if base else None
    back = parse(bg, table)
    if b is not None and back[3] < 1:
        back = over(back, b)
    front = parse(fg, table)
    if front[3] < 1:
        front = over(front, back)
    l1, l2 = luminance(front), luminance(back)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# ── the token file ─────────────────────────────────────────────────────────
def tokens() -> dict[str, dict[str, str]]:
    """`{scope: {name: value}}` where scope is `light` or `dark`.

    Read from the file rather than transcribed, so a colour changed in
    `tokens.css` moves this table on the next run and nothing has to remember.
    """
    text = TOKENS.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {"light": {}, "dark": {}}

    # Blocks, not lines. The first version tracked a scope flag and flipped it
    # on any line starting `:root` that did not contain "dark" — which is
    # exactly what `:root:not([data-theme="light"])`, the dark block's own
    # selector, looks like. Every dark value landed in the LIGHT table, and the
    # two rendered tables came out byte-identical. That is a checker reporting
    # a theme it never read.
    #
    # A selector is dark if it is inside a dark media query or names
    # `data-theme="dark"`. Nothing else.
    dark_media = False
    depth = 0
    selector = ""
    for raw in text.split("\n"):
        s = raw.strip()
        if not s or s.startswith("--") is False and s.startswith("/*"):
            pass
        if s.startswith("@media"):
            dark_media = "prefers-color-scheme: dark" in s
            depth += s.count("{") - s.count("}")
            continue
        if "{" in s:
            selector = s.split("{")[0].strip() or selector
            depth += s.count("{")
        if "}" in s:
            depth -= s.count("}")
            if depth <= 0:
                depth = 0
                dark_media = False
                selector = ""

        m = re.match(r"(--sw-[a-z0-9-]+)\s*:\s*([^;]+);", s)
        if not m:
            continue
        is_dark = dark_media or 'data-theme="dark"' in selector
        out["dark" if is_dark else "light"][m.group(1)] = m.group(2).strip()

    # Dark inherits everything it does not restate — which is how the CSS
    # actually cascades, and why the dark block only lists what changes.
    merged = dict(out["light"])
    merged.update(out["dark"])
    out["dark"] = merged
    if merged == out["light"]:
        raise SystemExit(
            "the dark theme resolved to exactly the light one — the token file "
            "was parsed but no dark block was found, so this report would be a "
            "measurement of a theme that was never read")
    return out


# ── the pairs that must hold ───────────────────────────────────────────────
# (foreground, background, floor, why). `background` may be translucent; it is
# composited over the page surface before the figure is computed.
TEXT_PAIRS = [
    ("--sw-ink", "--sw-paper", 4.5, "body text on the page"),
    ("--sw-ink", "--sw-paper-raised", 4.5, "body text on a card"),
    ("--sw-ink", "--sw-paper-sunken", 4.5, "body text in a well"),
    ("--sw-ink", "--sw-glass", 4.5, "body text on glass"),
    ("--sw-ink-muted", "--sw-paper", 4.5, "labels and timestamps"),
    ("--sw-ink-muted", "--sw-paper-raised", 4.5, "labels on a card"),
    ("--sw-ink-muted", "--sw-glass", 4.5, "labels on glass"),
    ("--sw-pine", "--sw-paper", 4.5, "links and accent text"),
    ("--sw-pine", "--sw-paper-raised", 4.5, "accent text on a card"),
    ("--sw-pine", "--sw-glass", 4.5, "accent text on glass"),
    ("--sw-danger", "--sw-paper", 4.5, "validation errors"),
    ("--sw-warning", "--sw-paper", 4.5, "approaching a limit"),
    ("--sw-on-pine", "--sw-pine", 4.5, "text on a primary button"),
    ("--sw-on-pine", "--sw-danger", 4.5, "text on a destructive button"),
]

COMPONENT_PAIRS = [
    ("--sw-focus-color", "--sw-paper", 3.0, "the focus ring on the page"),
    ("--sw-focus-color", "--sw-glass", 3.0, "the focus ring on glass"),
    ("--sw-border-strong", "--sw-paper", 3.0, "table rules and strong hairlines"),
]

BANDS = [f"--sw-cat-{i}" for i in range(1, 9)] + ["--sw-cat-uncat"]


def rows(scope: str, t: dict[str, str]):
    """Every pair, measured. Bands are measured against the page surface —
    a band is a UI component, so the floor is 3:1, not 4.5:1."""
    page = t["--sw-paper"]
    out = []
    for fg, bg, floor, why in TEXT_PAIRS + COMPONENT_PAIRS:
        if fg not in t or bg not in t:
            out.append((fg, bg, None, floor, why, "MISSING"))
            continue
        r = ratio(t[fg], t[bg], page, t)
        out.append((fg, bg, r, floor, why, "PASS" if r >= floor else "FAIL"))
    for band in BANDS:
        if band not in t:
            out.append((band, "--sw-paper", None, 3.0, "category band", "MISSING"))
            continue
        r = ratio(t[band], page, page, t)
        out.append((band, "--sw-paper", r, 3.0, "category band", "PASS" if r >= 3.0 else "FAIL"))
    return out


HEADER = """# Contrast — measured

<!-- GENERATED by tools/contrast.py. DO NOT HAND-EDIT.
     Regenerate: py tools/contrast.py

     `DESIGN-SYSTEM.md` promises every figure here is computed rather than
     asserted. With one opaque theme that was keepable by hand. With two themes
     and translucent surfaces it is not: glass composites over whatever is
     behind it, so the colour a person actually reads is not a value written
     anywhere. This file is that promise, kept by arithmetic. -->

Every figure below is **computed** from `tokens.css` by WCAG 2.1 relative
luminance, alpha-composited where a surface is translucent. Floors: **4.5:1**
for text (SC 1.4.3), **3:1** for a UI component or a category band (SC 1.4.11).

`tools/contrast.py` **fails the build on a pair below its floor**, not only on
drift — a table that faithfully records a 2.4:1 would be a document doing its
job while the product fails the standard it claims.

`--sw-ink-faint` is deliberately absent. It is for placeholder and disabled
text only, where WCAG exempts the requirement, and it must never carry content.
"""


def render() -> str:
    t = tokens()
    parts = [HEADER]
    for scope in ("light", "dark"):
        measured = rows(scope, t[scope])
        parts.append(f"\n## {scope.capitalize()} theme\n")
        parts.append("| Foreground | Background | Measured | Floor | | Use |")
        parts.append("|---|---|---:|---:|---|---|")
        for fg, bg, r, floor, why, verdict in measured:
            shown = f"**{r:.2f}:1**" if r is not None else "—"
            parts.append(f"| `{fg}` | `{bg}` | {shown} | {floor} | {verdict} | {why} |")
        worst = min((r for *_, r, _, _, _ in [(0, 0, x[2], 0, 0, 0) for x in measured]
                     if r is not None), default=0)
        fails = [x for x in measured if x[5] != "PASS"]
        parts.append("")
        parts.append(f"**{len(measured) - len(fails)} of {len(measured)} pass.** "
                     f"Tightest margin: {worst:.2f}:1.")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    t = tokens()
    failures = []
    for scope in ("light", "dark"):
        for fg, bg, r, floor, why, verdict in rows(scope, t[scope]):
            if verdict != "PASS":
                failures.append(f"{scope}: {fg} on {bg} = "
                                f"{'missing' if r is None else f'{r:.2f}:1'}, needs {floor}:1 ({why})")

    want = render()
    if "--check" in argv:
        if failures:
            print(f"FAIL  {len(failures)} contrast pair(s) below floor:")
            for f in failures:
                print(f"        {f}")
            return 1
        if not TARGET.is_file():
            print("FAIL  docs/05 B DesignSystem/CONTRAST.md has not been generated")
            return 1
        if TARGET.read_text(encoding="utf-8") != want:
            print("FAIL  CONTRAST.md has drifted from tokens.css")
            return 1
        print("PASS  every contrast pair meets its floor and CONTRAST.md matches")
        return 0

    TARGET.write_text(want, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    for scope in ("light", "dark"):
        measured = rows(scope, t[scope])
        bad = [x for x in measured if x[5] != "PASS"]
        print(f"  {scope:<5} {len(measured) - len(bad)}/{len(measured)} pass")
        for x in bad:
            print(f"        FAIL {x[0]} on {x[1]} = "
                  f"{'missing' if x[2] is None else f'{x[2]:.2f}:1'} (needs {x[3]})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
