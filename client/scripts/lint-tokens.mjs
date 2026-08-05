/**
 * E3-S1, made falsifiable.
 *
 * Three of that story's acceptance criteria say "asserted by a grep". This is
 * the grep, and it exits non-zero:
 *
 *   1. no component declares a raw hex                    (`DESIGN-SYSTEM.md §2`)
 *   2. every number renders through one shared formatter  (`§3`)
 *   3. the focus rule is declared exactly once            (`SW-ADR-117`)
 *
 * A fourth is added because it is the same class of failure and costs nothing:
 * `outline: none` never ships without a replacement.
 *
 *   node scripts/lint-tokens.mjs
 */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = fileURLToPath(new URL('.', import.meta.url))
const SRC = join(HERE, '..', 'src')
// The design system's own file, generated into the client. It is where the hex
// values LIVE, so it is the one file exempt from rule 1 — and it is generated,
// so `py client/sync_tokens.py --check` is what guards its contents.
const TOKENS = join(SRC, 'styles', 'tokens.css')
// THE money formatter. Exempt from rule 2 for the same reason: it is the thing
// rule 2 exists to make singular.
const MONEY = join(SRC, 'lib', 'money.js')

const NEWLINE = String.fromCharCode(10)

function walk(dir) {
  const out = []
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) out.push(...walk(path))
    else out.push(path)
  }
  return out
}

/**
 * Blank out comments, KEEPING line numbers and line count.
 *
 * Written after the first run of this script flagged its own explanations: two
 * of the four rules are stated in prose immediately above the code that obeys
 * them, so a linter that reads comments reports the documentation as the
 * violation. Blanking rather than deleting keeps every reported line number
 * pointing at the line a reader will actually find.
 */
function stripComments(text) {
  const blank = (m) => m.split('').map((c) => (c === NEWLINE ? c : ' ')).join('')
  return text
    .replace(/\/\*[\s\S]*?\*\//g, blank)
    .replace(/(^|[^:])\/\/[^\n]*/gm, (m, p1) => p1 + blank(m.slice(p1.length)))
}

const source = (file) => stripComments(readFileSync(file, 'utf8')).split(NEWLINE)

const files = walk(SRC)
const problems = []
const rel = (p) => relative(join(HERE, '..'), p).replace(/\\/g, '/')

// ── 1. no raw hex outside tokens.css ───────────────────────────────────────
// Three, four, six or eight digits. `#3d5a80` in a component is the failure;
// so is `#fff`, which is the shorthand people reach for when they are in a
// hurry, which is exactly when this matters.
const HEX = /#[0-9a-fA-F]{3,8}\b/
for (const file of files) {
  if (file === TOKENS || !/\.(jsx?|css)$/.test(file)) continue
  source(file).forEach((line, i) => {
    const hit = line.match(HEX)
    if (hit) {
      problems.push(`${rel(file)}:${i + 1}  raw hex ${hit[0]} — use a token ` +
                    `(DESIGN-SYSTEM.md §2: "No component ever references a raw hex")`)
    }
  })
}

// ── 2. one money formatter ─────────────────────────────────────────────────
// The failure mode is not a wrong number. It is ₹1,234,567.89 on one screen
// and ₹12,34,567.89 on the next, which reads as a bug in the arithmetic.
const FORMATTERS = /Intl\.NumberFormat|toLocaleString/
for (const file of files) {
  if (file === MONEY || !/\.jsx?$/.test(file)) continue
  source(file).forEach((line, i) => {
    if (FORMATTERS.test(line)) {
      problems.push(`${rel(file)}:${i + 1}  a second number formatter — ` +
                    `import from lib/money.js (DESIGN-SYSTEM.md §3)`)
    }
  })
}

// Rule 2's other half: the client never divides by 100. `paise / 100` is a
// float the moment the number gets large, and money is integer paise
// throughout (`CONSTITUTION` Art V.1).
const DIVIDE = /(paise|amount_paise|total_paise)\s*\/\s*100\b/
for (const file of files) {
  if (file === MONEY || !/\.jsx?$/.test(file)) continue
  source(file).forEach((line, i) => {
    if (DIVIDE.test(line)) {
      problems.push(`${rel(file)}:${i + 1}  dividing paise by 100 — ` +
                    `money is integer paise; use rupees() from lib/money.js`)
    }
  })
}

// ── 3. the focus rule, exactly once ────────────────────────────────────────
let focusRules = 0
for (const file of files) {
  if (!file.endsWith('.css')) continue
  focusRules += (source(file).join(NEWLINE).match(/:focus-visible\s*\{/g) || []).length
}
if (focusRules !== 1) {
  problems.push(`the :focus-visible rule is declared ${focusRules} times, not once ` +
                `(SW-ADR-117: one global rule, never overridden without a replacement)`)
}

// ── 4. outline: none never ships ───────────────────────────────────────────
for (const file of files) {
  if (!file.endsWith('.css')) continue
  source(file).forEach((line, i) => {
    if (/outline\s*:\s*(none|0)\b/.test(line)) {
      problems.push(`${rel(file)}:${i + 1}  outline:none — ` +
                    `never ships without a replacement (SW-ADR-117)`)
    }
  })
}

if (problems.length) {
  console.error(`FAIL  ${problems.length} design-system violation(s):`)
  console.error('')
  for (const p of problems) console.error(`  ${p}`)
  process.exit(1)
}

console.log(`PASS  ${files.length} client files: no raw hex, one money formatter, ` +
            `one focus rule, no outline:none`)
