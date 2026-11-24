# Product

<!-- impeccable:product-schema 1 -->

## Platform

web, served from macOS or Linux (the command refuses Windows: there os.kill(pid, 0), its liveness probe, sends a console control event or kills the process instead of testing that it exists)

## Stack

Static HTML, CSS, and plain JavaScript with no build step, served by a standard-library Python server on loopback. The markdown renderer, mermaid, and the code highlighter are vendored and pinned; the page loads nothing from a CDN.

## Users

A developer driving a crank or crank-lite design session (brainstorm, spec, plan) with a coding agent in a terminal. One person, on their own machine, for phases that run minutes to hours. The page usually sits in half a screen beside the terminal, roughly 800 to 1000 px wide.

## Product Purpose

crank-pilot puts the session's question rounds, readbacks, and prototype reviews on one local browser page. The user answers and marks up there, and the agent receives what they did as a structured result. Success is a whole phase driven from the page.

## Positioning

A session board whose only state is files under `.crank/<slug>/`, so a crashed server, a compacted session, or a fresh session resumes from disk. It is built in-house and needs no third-party app.

## Operating Context

- The agent posts one interaction at a time: a question round, a readback of an artifact, or a prototype review. The page waits between them.
- A question round is a set of questions, each with the agent's recommendation pre-selected, other options, a free-text answer, and an optional note.
- A readback shows the full rendered artifact with the agent's lead, judgment calls, and review-landed items above it. After a revision it shows what changed against the version the user marked up.
- A prototype review frames the variant files, switches between them, and takes a verdict in three fields: winner, what to take from the others, what to leave out.
- A live agenda shows the decisions settled and the ones still open.

## Capabilities and Constraints

- Three marks on a readback: a comment on selected text, a strike on selected text, and a general note. The page never edits the artifact in place.
- The user can attach images to any response by paste, drop, or file picker.
- The page renders markdown, code blocks colored by the language their fence names, mermaid, and agent-authored SVG or HTML fragments, the last in a sandboxed frame.
- One tab per effort, loopback only, usable offline.
- Every action is reachable by standard tab order and Enter. Shortcuts exist only for submit and approve.
- Claude Code only at launch. The mode is off by default.

## Brand Commitments

The name crank-pilot. Nothing else is binding.

## Evidence on Hand

- The effort's brief, with the surfaces and decisions: `.crank/crank-pilot/brainstorm.md` (gitignored, effort-scoped).
- The decisions that outlive the effort: `docs/adr/0001-own-interactive-page.md`, `docs/adr/0002-pilot-state-lives-in-files.md`, `docs/adr/0003-pilot-vendors-its-libraries.md`, `docs/adr/0004-pilot-channel-is-a-command.md`, `docs/adr/0005-pilot-page-token-by-one-time-code.md`, `docs/adr/0006-page-tests-run-on-node-and-jsdom.md`, `docs/adr/0007-pilot-dev-tools-stay-out-of-the-plugin-manifest.md`.
- No screenshots, logo, or existing interface exist. Sample content in a mock is synthetic.

## Product Principles

- The artifact's text is the subject. Chrome, motion, and density never get between the user and it.
- Every answer and mark is a durable, structured record an agent can read back.
- The page is safe to leave on: when it fails, the session continues in chat.
- It must not read as a generic dashboard of cards, stat tiles, and a sidebar that could be any admin tool.
