# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

An individual logging their own day-to-day spending in US dollars, on their own, in private. They
open SpendWise right after spending (a coffee, groceries, rent) to log it, and again when they want to
know where the month's money went. Confirmed by the owner on 2026-10-20.

A second, narrow audience is the admin, who manages accounts (reset a password, force a sign-out,
deactivate) and deliberately never sees anyone's amounts or descriptions.

## Product Purpose

A website where a person signs up, logs what they spend, and sees a correct dashboard of it. Success is
a person who can log an expense in seconds and read, at a glance, how much they have spent this period,
on what, and how it compares with before.

## Positioning

Privacy is structural, not a promise: everyone sees only their own money, enforced twice (every query
filters on the signed-in user, and the database's row-level security refuses anyone else's rows), and
even the admin cannot see amounts. Money is exact: stored as integer paise, never floats.

## Operating Context

- Used on desktop and on phones (tested at 1280x900 and 375x812).
- Light, dark, and follow-the-system appearance are all supported.
- Periods (this month, last month, custom range) are resolved in the browser and sent as explicit dates.
- Categories are per person: one person's categories are invisible to everyone else.

## Capabilities and Constraints

- Log, edit, and delete an expense: amount, date, optional category, optional note.
- Dashboard: period total, count, biggest expense, daily average (days elapsed, capped at today),
  projection, comparison with the previous period, category breakdown, daily and weekday patterns,
  and the list of entries.
- Categories screen, Settings, and an Admin area.
- Stack is locked by SW-ADR-016: React 18 + Vite with plain CSS and no UI framework; FastAPI +
  PostgreSQL. New dependencies and design-system changes are recorded as ADRs.
- Every figure's text in the page is its final value immediately (browser tests read totals at once);
  reduced motion means instant.
- Content cards stay opaque; translucent glass is for chrome only (SW-ADR-147, SW-ADR-154).
- Out of scope: native apps, reading bank SMS, bank or UPI integrations, self-service password reset.

## Brand Commitments

The owner pinned these on 2026-10-20 and they are binding:

- Palette from the owner's reference image: Warm Ivory `#F9EBD7`, Emerald Green `#046A38`,
  Vermilion `#E34222` (the "almost red").
- Glassmorphism as the interface language.
- A money tree on the dashboard: a painted tree whose leaves are banknotes. Bills fall from it on their
  own, more fall when the pointer brushes the canopy, and adding an expense drops a bill reading its
  category and amount (for example "Pizza $10"), written in vermilion.
- Amounts are shown in US dollars ($), formatted only by the app's single money formatter
  (`SW-ADR-157`, the owner, 2026-10-20; it replaced rupees).

## Evidence on Hand

- Seeded showcase accounts with synthetic expenses and about 27 categories per person (demo data, not
  real users).
- No testimonials, customers, press, or usage figures exist. Do not invent any.

## Product Principles

1. Your money is yours alone; nothing on screen may suggest otherwise.
2. A number on screen is exact and final the moment it appears.
3. Logging is fast; reading is calm.
4. Delight must never cost the task: decoration stays out of the way of entering and reading money.

## Accessibility & Inclusion

WCAG AA contrast is enforced by an automated check (`tools/contrast.py`) in both light and dark themes.
Touch targets are at least 44px. Reduced motion collapses animation to instant. Pages must not scroll
sideways at 375px.
