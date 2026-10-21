---
version: 1
slug: "client-src-screens-dashboard-jsx"
primary_target: "client/src/screens/Dashboard.jsx"
related_targets: ["client/src/styles/screens/dashboard.css"]
---

# Dashboard surface brief

Scope: the signed-in dashboard (`client/src/screens/Dashboard.jsx`) and the app shell around it; the palette change reaches every screen through the shared tokens. Visitor mode: Operate.

Audience and job: one person reading their own rupee spending for a period and logging new expenses fast. Content: the period total, count, biggest, daily average, projection, comparison, category breakdown, daily and weekday patterns, the entry list. Constraints: content cards stay opaque, chrome is glass; every figure's text is final immediately; reduced motion is instant; 375px with no sideways scroll; 44px targets.

Memorable moment: the money tree. Bills drift down by default, a brush over the canopy shakes more loose, and logging an expense drops a bill with its category and amount.

Unresolved: none blocking. Default falling bills use the person's own recent entries, with labelled examples only when there are none (owner's call delegated, decided 2026-10-20).

## Direction contract

THESIS: The dashboard is a festival poster for your month. The total is the headline act, set in chunky extruded emerald numerals, and the money tree is the poster's centrepiece. It refuses the category default of a grid of equal KPI tiles under a page title.

OWN-WORLD: Warm Ivory paper ground with fine risograph grain; Emerald as the ink of headlines and the extruded numerals' face with a deep emerald shadow side; Vermilion only for money leaving (falling bills, spend accents, the new-entry mark) and the condensed headline line. Thin vermilion orbit lines and small spark stars connect the tree to the figures. Glass is the chrome: frosted ivory panes with an inner highlight edge for the sidebar, the top bar and the tree's frame; content cards stay solid paper.

STORY: In one look the person knows how much left their pocket this period and on what. They feel their money moving (bills falling), and adding an expense rewards them with a bill dropping from the tree carrying exactly what they logged.

FIRST VIEWPORT: Left two thirds: the money tree, large, standing on a glass ground disc with roots fading out below, bills drifting; one orbit line loops from the canopy across to the total. Right third: the period label in condensed vermilion caps, the total in extruded emerald numerals at the largest size on the page, the comparison line beneath, then the primary "Add expense" action. Category roster and charts begin just below the fold line on desktop; on phones the tree stacks above the total.

FORM: The Festival Poster, position 1 on my ordered list (the owner chose my pick over the roll), seed key fa51c12e.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
