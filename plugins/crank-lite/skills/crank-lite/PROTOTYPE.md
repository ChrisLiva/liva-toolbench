# Prototype

Several structurally different variants of one user-facing surface, one switcher, one command to run, and a recorded verdict. Every file is throwaway and lives under `.crank/<slug>/prototype/`. Read this once the user accepts a phase's offer. On a reopen, skip to the handover with the files already there.

State the question the prototype answers in one line, then take the rung the surface names:

- **Browser, native app, or desktop app.** An HTML mock: `index.html` plus one `variant-<key>.html` per variant, each inside a static reproduction of the host page's chrome (header, sidebar, spacing, density), with the project's design tokens and fixture data. With no host page, the mock carries the app's global chrome only, and `index.html` says so at the top.
- **CLI output, help text, or flags.** Fenced blocks in chat, one per variant, over one shared sample input. You compose this rung yourself and write no file, since a subagent cannot print to the conversation. On the user's request, a scratch script under the prototype directory prints the same variants.
- **Interactive TUI.** A scratch program under the prototype directory that imports the project's TUI library, runs by one command, and cycles variants on one key.

Default to 3 variants and cap at 5. Variants differ in layout, information hierarchy, or primary affordance, never only in color or copy.

Run `git status --porcelain` and keep the output, then dispatch **one** standard-tier subagent ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers) with this brief, filled in. The dispatch is a blocking call: end your turn at it and let its return resume you.

<brief>
Build a throwaway prototype of `<N>` variants. The question it answers: `<question>`.

Write only under `<absolute path to .crank/<slug>/prototype/>` and nowhere else: no other file, no branch, no worktree, no install.

- **Purpose of the surface:** `<what the page or screen is for, and who uses it>`
- **Data to show:** `<fixture or seed file paths>`. Copy sample values from these. Read no live database and no env file, and put no secret in any file.
- **Design tokens:** `<token file paths>`. Use these values for color, type, and spacing.
- **Host chrome:** `<paths of the page or layout this surface sits in>`. Reproduce its header, sidebar, spacing, and density as static markup around each variant, or the app's global chrome only when no host page exists.
- **Variants:** `<key: name, then its layout, information hierarchy, and primary affordance>`, one line each. They share no layout component.

For an HTML mock, write one self-contained `variant-<key>.html` per variant that opens by double-click, with no build and no server, and `index.html`: the question in one line at the top, one iframe filling the page, and a floating bar fixed at bottom-center, visually distinct from the design, with previous, a label reading `B: Sidebar layout`, and next, wrapping around. The bar reads and sets `?variant=<key>`, so a reload keeps the variant. For a TUI or a script, write one scratch program that imports the project's library, runs by `<one command>`, and cycles variants on `<key>`.

No file calls a backend or performs a mutation: controls change local state only.

Return the paths you wrote and one sentence per variant on its structure.
</brief>

When the builder returns, run `git status --porcelain` again. When the two outputs differ, name the differing paths to the user and stop before handing over. Revert nothing yourself. Otherwise give the user the path and the run command: double-click `index.html`, `go run ./.crank/<slug>/prototype`, or the project's equivalent. Do not open the prototype yourself.

A revision request re-runs the builder with the change, and the loop ends when the user names a winner. On a hedge, ask the open look and interaction decisions in prose and record `no verdict`.

Record one `Prototype:` line. It reads the verdict, which is the winner, what the user took from the other variants, the prototype's path, and the surface the mock stood in for, or it reads `no verdict`. From the spec phase the line lands among the key technical decisions, and the winner's behaviors land as numbered acceptance criteria. From the plan phase the line and the chosen behaviors land under the plan's assumptions. From the brainstorm, the brief records the path beside the decision it settled. The plan writes the real UI from the verdict and lifts no mock code.
