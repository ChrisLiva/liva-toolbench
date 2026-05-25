---
name: effective-html
description: User-summoned. When the user invokes this skill, treat the answer-medium question as already decided — produce a single-file HTML artifact (not markdown, not a web app). Covers the WHEN/WHY rubric for HTML-vs-markdown, the no-build-no-CDN constraint, the up-front "pick a visual direction" step, and the "always end with an export button" mandate for throwaway editors. Assumes you already know how to write HTML/CSS/JS.
disable-model-invocation: true
argument-hint: "<what to make as HTML>"
---

The user has explicitly chosen HTML as the output medium for `$ARGUMENTS`. Don't second-guess that or ask "are you sure you don't want markdown?" — the choice is made. Your job is to produce a *good* HTML artifact, not to debate the format.

The non-obvious stuff is below. Things you already know — semantic tags, flexbox, grid, SVG basics, ARIA, how to write an event listener — are assumed and not repeated.

## What HTML actually buys you (and where the value comes from)

Markdown is a linear scroll. It's great when the reader will read top-to-bottom once. The moment the reader needs to **compare, navigate, toggle, drag, or come back tomorrow and re-skim**, markdown collapses. HTML lets you put spatial information in space, give the reader a verb to use, and ship the whole thing in one file they can save, email, or drop on a server.

The decision rubric: prefer HTML when **at least one** of these is true.

- **Comparison is the point.** Three approaches side-by-side. Before/after. Variant sheets. Linear prose forces the reader to hold options in working memory; HTML doesn't.
- **The artifact is genuinely spatial.** Diffs with margin notes. Module maps with arrows. Timelines. Diagrams. Calendars. Things that lose meaning when flattened to lines.
- **The reader wants a verb.** "Toggle this flag." "Drag these tickets." "Watch this transition at 220ms." "Add a node to the ring and see what happens." If the reader's response is "let me try…", they need an artifact, not a description.
- **It's a recurring document.** Weekly status, post-mortem, design system, PR write-up. The structure pays for itself across many reads.
- **You want them to react to it, not imagine it.** Visual designs, motion, layout options. If you find yourself writing "imagine a sidebar that…", stop and build the sidebar.

Stay with markdown (or plain prose) when:

- The content is short and linear and the reader will read it once.
- The user will want to **co-author** by editing the text — markdown is friendly to that, HTML is hostile.
- The output is going to feed another tool or LLM downstream.
- You'd just be wrapping prose in `<p>` tags. That's not a win, that's overhead.

## The "single file, no build, no CDN" constraint

The artifacts are valuable precisely because they're *files*, not *apps*. One `.html`, save-and-share, email-safe, works offline, opens on the recipient's machine in two seconds with no install. This constraint is load-bearing — break it and you lose most of the value.

- **One file.** All CSS in a `<style>` tag, all JS in a `<script>` tag. No external stylesheets, no module imports.
- **No CDN, no `<script src="https://…">`.** Don't pull in React, Tailwind, Chart.js, htmx, Alpine, D3, lucide, fontawesome, mermaid, Google Fonts, anything. The first time the recipient opens it on a plane it's broken.
- **No `fetch` to remote services.** The data is in the file or comes from the user's interaction.
- **No build step, no preprocessor, no transpile.** What you write is what runs.
- **Vanilla JS, ES2015+ is fine.** Wrap in an IIFE (`(function(){ … })();`) so globals don't leak — these files often get pasted into other contexts.
- **No localStorage / cookies / service workers** unless the user specifically asks. These artifacts are throwaway by design; persistence is a surprising side effect.

If the user asks for a real web app, that's a different task — don't apply these rules then.

## The "always end with an export button" mandate (for editor artifacts)

This is the single most common failure mode for editor-style artifacts (triage boards, flag toggles, prompt tuners, drag-and-drop rankers, anything where the user *changes state*). The agent builds something beautiful, the user spends ten minutes interacting with it, and then realizes there is no way to get the result back out. The session ends with the user copy-typing the screen into a doc.

Fix: every editor artifact ends with a **copy/export button**. Always.

- The button copies the user's work as **markdown or plain text** (occasionally JSON if structured data), not as HTML. The user is moving it into a doc, a PR description, a Slack message, a follow-up prompt to you. They want text.
- Use `navigator.clipboard.writeText(...)` with a `document.execCommand('copy')` fallback on a hidden `<textarea>` — clipboard API silently no-ops in some contexts.
- Give the button visible feedback. Swap the label to "Copied ✓" for ~1.2s on success.
- Put it in a sticky toolbar at the top of the page so it's always reachable, not at the bottom where the user has to scroll past their work to find it.
- For more complex editors (filter flags, etc), also offer a "Copy as diff" — markdown showing only what *changed* from the starting state. That's almost always what the user actually wants to share.

If the artifact has no editable state — it's a report or an explainer — no export button is needed. The artifact itself is the output.

## Pick a visual direction with the user first

There's no single "right" look for these artifacts — a deploy-pipeline flowchart wants a different aesthetic than the all-hands deck or a sprint-cleanup triage board. **Before you start writing HTML, sketch 3–4 distinct style directions in chat and let the user pick one** (or describe their own). This takes ten seconds and prevents you from defaulting to the same beige sans-serif every time you're invoked.

Each direction is one line — palette, type, overall feel. Tailor the menu to the artifact: pick directions that actually suit what you're about to build, don't just rattle off the same four every time. Some directions that tend to work, mix and match or invent your own:

- **Editorial / magazine** — generous margins, serif headlines, restrained palette with one accent. Reads as careful and finished.
- **Academic paper** — narrow column, serif body, dense footnotes, monospace code, almost no color. Reads as rigorous.
- **Terminal / retro CRT** — dark background, single monospace stack, phosphor green or amber, optional scanline overlay. Fits debugging, infra, anything that smells of the command line.
- **Cyberpunk / synthwave** — saturated magenta+cyan on near-black, hard shadows, blocky display type, neon glow. Bold and modern.
- **Cartoon / friendly** — rounded corners, playful color (think children's-book palette), heavier weights, hand-drawn SVG accents. Good for explainers aimed at non-experts.
- **Minimalist stripe-docs** — black on white, one serif + one sans, lots of whitespace, no chrome.
- **Brutalist** — chunky sans, raw underlines, exposed grid lines, off-white background, almost no border radius. No-nonsense.
- **Data-dense dashboard** — small type, tight rows, muted color bands and chips. For status reports and metric pages.
- **Hand-drawn sketch** — inline SVG with `stroke-dasharray` wobble, sketchy borders, mostly monochrome. Pairs well with concept explainers.
- **Newspaper / broadsheet** — multi-column layout, drop caps, hairline rules, condensed serif headlines.
- **Zine / risograph** — limited two-color palette (one bright, one dark), grain texture, intentionally rough alignment.

Once they pick, commit to it: palette, type stack, spacing rhythm, motion vocabulary — keep the whole artifact consistent. Inconsistency is what makes an artifact read as LLM-slop.

**Invoke `frontend-design:frontend-design` to handle the actual rendering.** Call `Skill(name="frontend-design:frontend-design", args="<the picked direction> + <a short brief of the artifact>")` and let that skill produce the HTML. It is substantially better than you are at avoiding generic-AI aesthetics, and the user reached for HTML precisely because they want a polished artifact — not a serviceable one. Pass it the direction the user picked so it composes within that frame instead of imposing its own.

This is the default. Skip it only when one of the following is concretely true:

- The artifact is a one-screen widget under ~150 lines (a single input-and-preview throwaway, a one-button utility).
- You've already invoked `frontend-design:frontend-design` earlier in this same conversation for the same direction, and you're iterating on a minor tweak.

"It feels small enough," "the direction is clear enough from this skill," or "the overhead isn't worth it" are *not* valid reasons to skip — that's the trap that produces forgettable, generic output. When in doubt, invoke it.

One hard constraint from the no-CDN rule still applies regardless of direction: **no webfont imports.** Use the system stacks (`ui-serif, Georgia, "Times New Roman", serif` / `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` / `ui-monospace, "SF Mono", Menlo, Monaco, monospace`) and lean on weight, size, color, and tracking to differentiate. System fonts give more range than people realize — a serif-only layout reads completely differently from a mono-only one even though both are "free."

## Page header pattern

Most artifacts benefit from a three-line opener that establishes context before the reader looks at anything else:

```html
<header class="page-head">
  <div class="eyebrow">CATEGORY · CONTEXT</div>
  <h1>Title</h1>
  <p class="sub">One-line subtitle, max-width ~620px.</p>
</header>
```

The eyebrow is doing the work — it tells the reader at a glance what *kind* of artifact this is ("PR review", "weekly status", "design exploration") before they read the title. Style it according to the direction the user picked; the pattern (eyebrow → title → subtitle) is what matters.

## Plausible-fake data, never lorem ipsum

The example data in your artifact is part of what makes it feel intentional. Don't fill it with `lorem ipsum` or `Foo Bar` or `placeholder1`. Use names, dates, ticket IDs, code snippets, and numbers that look like they came from a real team — even if the entire context is fictional. "BIR-249 · Recurring tasks · timezone edge cases" reads as serious; "Item 1, Item 2, Item 3" reads as a demo.

## A small catalog of artifact types worth producing

When the user describes what they want, map it to the closest of these and lean on the conventions that work for it:

- **Side-by-side options** (exploring approaches, comparing libraries). Three-column grid of cards; each card has a name, a code or visual sample, a small pro/con table, and metadata chips. End with a recommendation aside.
- **PR review / code review.** Render the diff inline with margin notes; severity tags (critical / warning / nit); in-page jump links to each finding; a summary panel at the top. **The summary panel must carry an at-a-glance visualization**: a chip strip with severity counts (e.g. `1 critical · 2 warning · 3 nit`), and either a per-file finding-density bar (small inline SVG showing where in the diff findings cluster) or a mini map of changed files with dots for finding count. Every finding gets a margin pin (severity-colored circle or square in the gutter) so the reader can scan vertical density before reading any prose.
- **Implementation plan.** A milestone timeline (horizontal stripe of phases), a data-flow diagram (inline SVG), inline mockups, a risk table at the bottom.
- **Status / incident report.** Eyebrow → title → "what shipped / what slipped / what we watched". **Lead with a header strip of summary tiles** (counts, deltas, sparkline trends as inline SVG `<polyline>`). For incidents, a minute-by-minute timeline strip with log excerpts pinned to each tick and a follow-up checklist.
- **Concept explainer.** Live, mutate-able diagram as the centrepiece (SVG that responds to clicks or inputs). Collapsible deep-dives via `<details>/<summary>`. Glossary linked from hover/click on jargon.
- **Slide deck.** A series of `<section class="slide">` with `min-height: 100vh`. Keyboard nav with arrow keys + space (`document.addEventListener('keydown', …)`). An `IntersectionObserver` to update a "3 / 6" counter. That's the whole deck — no framework.
- **Throwaway editor.** Whatever the editing surface is (drag-and-drop list, toggle grid, template with live preview), surround it with a sticky toolbar containing the **export button**. Native HTML5 drag (`draggable="true"` + `dragstart/dragover/drop`) works fine — no library.

When the user's ask doesn't fit cleanly, pick the closest pattern and adapt. The goal is intentional structure, not literal adherence.

## Earn the HTML form — visualize before you write prose

The reason a recipient is reading this as HTML and not markdown is that you've promised them something paragraphs alone can't deliver. Three classes of visual element earn that promise, and every artifact should carry at least one from each:

1. **A concept diagram that teaches.** Inline SVG that *carries information* — a flow, a ring, a tree, a state machine, a force diagram, a 2×2, a system schematic. Not decoration. The diagram should be the thing a reader could screenshot and still understand the point. For explainers it's the centrepiece; for everything else (yes, even PR reviews and status reports) at least one such diagram belongs somewhere — a "shape of the change" schematic for a PR review, a system-state map for an incident, a dependency strip for a plan. If you can't think of one for your artifact, you haven't thought hard enough about what's actually being communicated.

2. **An ambient summary visualization.** A header band that lets a reader pre-load the shape of the content before reading: severity chips with counts, a sparkline of the last seven days, a density bar showing where findings cluster, a tiny stacked bar of what-shipped vs what-slipped. Hand-write the SVG (`<polyline>`, `<rect>`, `<circle>`) — two lines of math, no chart library. The point is that the reader's eye lands on the summary visual *first* and primes them for the prose.

3. **Margin / gutter structure.** Findings, comments, sections, log entries — give them a gutter element so the page reads as a *spatial document* rather than a vertical scroll of paragraphs. Severity-colored pins next to PR findings. Tick marks beside timeline rows. Tiny status glyphs next to checklist items. A left-rail "minimap" linking section headers to a vertical strip on the right. The gutter is what makes a long page navigable by eye.

The trap to avoid: writing a beautifully-styled wall of text and calling it done. If you removed all the CSS and your artifact is indistinguishable from a markdown rendering, you missed the brief. A useful gut-check before declaring an artifact finished: **count the inline `<svg>` elements**. Under two for a text-heavy artifact (PR review, status report, plan) is almost always too few; you've under-invested in the spatial structure that justified choosing HTML.

## Interactivity, kept small

These artifacts get their value from being small and obvious enough that a recipient can read the source. Match that.

- `<details>/<summary>` for collapsibles — no JS needed.
- Tabs: a row of `<button>`s and `class="on"` toggling visibility of sibling panels. Don't reach for a tab library.
- Sparklines and tiny charts: hand-write the SVG with a `<polyline>` and `viewBox`. Two lines of math beats importing a chart library.
- Live preview on input: debounce with `requestAnimationFrame`, not a debounce library.
- Sliders / numeric inputs: native `<input type="range">` or button presets that flip a CSS custom property via `root.style.setProperty('--ease', '…')`.
- Drag-and-drop: native HTML5 events. No `react-dnd`, no `Sortable.js`.

If you find yourself reaching for a dependency, stop and look at the problem again — most "I need a library" moments dissolve into 20 lines of vanilla.

## A final note on length and density

Artifacts of this kind tend to land in the 350–720 line range. If yours is creeping past ~1000 lines you're probably over-decorating or over-engineering — strip until each section earns its place. If it's under 200 lines for anything other than a single-screen report, you're probably under-investing in the spatial structure that justified choosing HTML in the first place.

Pick the pattern, write it tight, ship the file.
