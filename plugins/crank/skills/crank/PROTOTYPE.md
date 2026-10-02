# Prototype

Several structurally different variants of one user-facing surface, one switcher, one command to run, and a recorded verdict. Every file lives under `.crank/<slug>/prototype/` ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). No mock code ships, and every file stays on disk until the plan's execution finishes: no phase deletes or moves one before then, because the spec, the plan, and execution read the winner at the path the `Prototype:` line records. On a reopen, skip to step 3 with the files already there. (per project decision: standalone mocks only, never mounted in a real route or held on a branch or worktree, so a native-screen mock shows layout and hierarchy, not platform feel.)

## Flow

### 1. Pick the rung

State the question the prototype answers in one line, then take the rung the surface names:

- **Browser, native app, or desktop app.** An HTML mock inside a static reproduction of the host page's chrome, using the project's design tokens and fixture data.
- **CLI output, help text, or flags.** Fenced blocks in chat, one per variant, over one shared sample input. You compose this rung yourself and write no file, since a subagent cannot print to the conversation. Skip to step 4. On the user's request, a scratch script under the prototype directory prints the same variants.
- **Interactive TUI.** A scratch program under the prototype directory that imports the project's TUI library, runs by one command, and cycles variants on one key.

Default to 3 variants and cap at 5. Give each a key (`A`, `B`, `C`), a name, and a structural direction. Variants differ in structure, meaning layout, information hierarchy, or primary affordance, never only in color or copy. (per project decision: the cap is 5 because past it variants stop differing in structure.)

Completion criterion: the question, the rung, and one distinct structural direction per variant are written down, and the token, host chrome, and fixture sources are named by path.

### 2. Build

Run `git status --porcelain` and keep the output. Dispatch one **standard** subagent per variant, resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md), all in the same turn, each with this brief filled in. The batch is a blocking call: end your turn at the dispatch and let the returns resume you.

<brief>
Build variant `<key>: <name>` of a prototype whose code never ships, to help answer `<question>`.

Write only `<absolute path to .crank/<slug>/prototype/variant-<key>.html>`: no other file, no branch, no worktree, no install.

- **Purpose of the surface:** `<what the page or screen is for, and who uses it>`
- **Data to show:** `<fixture or seed file paths>`. Copy sample values from these. Read no live database and no env file, and put no secret in the file.
- **Design tokens:** `<token file paths>`. Use these values for color, type, and spacing.
- **Host chrome:** `<paths of the page or layout this surface sits in>`. Reproduce its header, sidebar, spacing, and density as static markup around your variant, or the app's global chrome only when no host page exists.
- **Structural direction:** `<this variant's layout, information hierarchy, and primary affordance>`. Other builders hold other directions. Stay inside yours, and share no layout component with them.

The file is self-contained HTML, CSS, and JavaScript that opens by double-click, with no build and no server. It calls no backend and performs no mutation: controls change local state only.

Return the path you wrote and one sentence on the structure you built.
</brief>

The TUI program and a requested CLI script go to one builder instead, because the variants share one entry file: send the same brief with every variant's direction listed, the output path set to the prototype directory, and the file paragraph replaced by the program's contract: import the project's TUI library, run by one command, and cycle variants on one key.

When every builder has returned, rerun `git status --porcelain`. If the output differs from the first, name the differing paths to the user, revert nothing, and stop before handing over.

Then write `index.html` beside the variants:

- the question in one line at the top, plus a note when no host page exists and the mock carries only the app's global chrome;
- one iframe filling the page, its source the current variant's file;
- a floating bar fixed at bottom-center, visually distinct from the design, with previous, a label reading `B: Sidebar layout`, and next, wrapping around;
- the bar reads and sets `?variant=<key>`, so a reload keeps the variant.

Completion criterion: `.crank/<slug>/prototype/` holds `index.html` and one `variant-<key>.html` per variant, or the one scratch program, and the two `git status --porcelain` outputs match.

### 3. Hand over

Give the user the path and the run command: double-click `index.html`, `go run ./.crank/<slug>/prototype`, or the project's equivalent. Do not open the prototype yourself.

### 4. Verdict

Ask which variant wins, what to take from the others, and what in the winner to leave out. A revision request goes back to a builder as a new `variant-<key>.html` with a new key and direction, added to `index.html`, then ask again. On a hedge, ask the open look and interaction decisions in prose per [GRILLING.md](GRILLING.md) and record `no verdict`.

Completion criterion: the user has named a winner and answered what to take from the other variants and what to leave out of the winner, with `nothing` counting as an answer, or every open look and interaction decision has a prose answer.

### 5. Record

Write one `Prototype:` line: the winner, what the user took from the other variants, what the user left out of the winner, the winning variant's path (`.crank/<slug>/prototype/variant-<key>.html`, or the scratch program's path and the variant's key), and the surface the mock stood in for, or `no verdict`. A CLI rung that wrote no file reads `in chat` in place of the path, with the winning block copied beneath the line. From the spec phase the line lands in Technical decisions, and every behavior the user chose lands as a numbered acceptance criterion. From the plan phase the line and the chosen behaviors land under **Updates since spec**. From the brainstorm, the line lands in the brief's **Key decisions** beside the decision it settled.

The winning variant is the reference every later phase opens for that surface, and the verdict bounds it. The verdict's committed parts are the winner's structure, what the user took from the other variants, and the absence of each part the user left out, and the real UI keeps all three. The rest of the mock guides details the spec and the task leave open, and its fixture values and static host chrome are stand-ins the real UI replaces. Where the spec's or a task's text disagrees with the mock, the text wins.

Completion criterion: the artifact carries the line, and every chosen behavior is a numbered criterion or an **Updates since spec** entry.
