---
name: effective-html
description: Produce a single-file HTML artifact that allows a smoother communication between the user and the coding agent when reviewing text documents.
disable-model-invocation: true
argument-hint: "<what to make as HTML>"
---

The user picked HTML for `$ARGUMENTS`. Your job is a *good* artifact, not a debate about the format.

## Constraints (load-bearing — the artifact must work offline, on a plane, when forwarded)

- One `.html` file. All CSS in a `<style>` tag. No external stylesheets, no `<script src>`, no CDN, no webfonts — use system stacks (`ui-serif…`, `system-ui…`, `ui-monospace…`).
- No JavaScript for interactivity or animation — HTML + CSS only (`<details>`, `:target`, `:checked`, transitions).
- No `fetch`, no `localStorage`, no cookies, no service workers.

## Agent ↔ user comm contract

Every artifact includes, at the top of the page, two buttons: **Export Comments Only** and **Export to Markdown**. Each logical section gets a `<textarea>` comment box; one more at the end for whole-doc comments. Both exports start with the absolute path of this HTML file as a top-line reference (e.g. `> Source: /path/to/artifact.html`) — the agent receiving the paste may not know which file the comments are about. Export Comments Only then copies each non-empty comment with its section heading. Export to Markdown copies a markdown rendering of the whole doc (comments inlined under their section). These are the only places JS is allowed — keep them tiny.

## Use visualizations where they earn their place

The whole reason the user picked HTML over markdown is to put information in space. When a section would otherwise be a wall of prose or a long list, ask whether an inline `<svg>` (a flow, a ring, a 2×2, a sparkline, a timeline tick-strip, a density bar, a margin-pin gutter, a system schematic) would let the reader pre-load the shape before reading. Hand-write the SVG; no chart libraries. There's no minimum count — use them where they teach, skip them where they'd be decoration. But "wall of styled paragraphs" almost always means you missed a chance.

## Pick a visual direction with the user first

Before writing HTML, sketch 3–4 short distinct visual directions in chat tailored to *this* artifact (palette + type + feel, one line each) and let the user pick or describe their own. Then commit to it consistently — inconsistency is what makes artifacts read as LLM-slop.

## Delegate the rendering

Once the direction is picked, invoke `Skill(name="frontend-design:frontend-design", args="<picked direction> + <one-paragraph brief of the artifact, including the constraints above and the export-button contract>")`. That skill is substantially better than you at avoiding generic-AI aesthetics, which is the whole reason the user asked for HTML.

Skip the delegation only if: (a) the artifact is a one-screen widget under ~150 lines, (b) you've already invoked frontend-design earlier in this conversation for the same direction and you're iterating a minor tweak, or (c) `frontend-design:frontend-design` isn't installed — in which case render directly, holding to the same constraints and direction.

## Visual cleanup before handoff

Open the file in a browser, screenshot the full page, and fix obvious issues — text overflowing containers, SVG strokes pointing the wrong way, misaligned grids, illegible contrast.

For every inline `<svg>` you wrote, look at the screenshot and verify the diagram says what the prose says. Specifically:
- Points that should sit on a curve/axis/ring actually sit on it (compute positions with the right polar/Cartesian formula — don't eyeball coordinates).
- Labels sit next to the thing they label without overlapping nearby elements; anchors (`text-anchor`, `dominant-baseline`) put text on the correct side.
- Scales, bar lengths, and angles are proportional to the underlying numbers — not vibes.
- The shape the reader pre-loads from the diagram matches the conclusion the prose draws.

If any of these is off, re-derive the coordinates and re-render before handing off. A visualization that contradicts the prose is worse than no visualization.
