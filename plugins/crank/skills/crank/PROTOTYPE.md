# Prototype

Several structurally different variants of one user-facing surface, one switcher, one command to run, and a recorded verdict. Every file is throwaway and lives under `.crank/<slug>/prototype/` ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). A phase reads this file once the user accepts its offer. On a reopen, skip to step 3 with the files already there. (per project decision: standalone mocks only. No variant mounts in a real route, and no branch or worktree holds one, so a native-screen mock shows layout and hierarchy, not platform feel.)

## Flow

### 1. Pick the rung

State the question the prototype answers in one line, then take the rung the surface names:

- **Browser, native app, or desktop app.** An HTML mock inside a static reproduction of the host page's chrome: header, sidebar, spacing, density. It uses the project's design tokens and fixture data. With no host page, the mock carries the app's global chrome only, and `index.html` says so at the top.
- **CLI output, help text, or flags.** Fenced blocks in chat, one per variant, over one shared sample input. You compose this rung yourself and write no file, since a subagent cannot print to the conversation. Skip to step 4. On the user's request, a scratch script under the prototype directory prints the same variants.
- **Interactive TUI.** A scratch program under the prototype directory that imports the project's TUI library, runs by one command, and cycles variants on one key.

Default to 3 variants and cap at 5. Give each a key (`A`, `B`, `C`), a name, and a structural direction. Variants differ in layout, information hierarchy, or primary affordance, never only in color or copy. (per project decision: the cap is 5 because past it variants stop differing in structure.)

Completion criterion: the question, the rung, and one distinct structural direction per variant are written down, and the token, host chrome, and fixture sources are named by path.

### 2. Build

Run `git status --porcelain` and keep the output. Dispatch one **standard** subagent per variant, resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md), every dispatch sent in the same turn, each with this brief filled in. The batch is a blocking call: end your turn at the dispatch and let the returns resume you.

<brief>
Build variant `<key>: <name>` of a throwaway prototype. The question it helps answer: `<question>`.

Write exactly one file, `<absolute path to .crank/<slug>/prototype/variant-<key>.html>`, and write nowhere else: no other file, no branch, no worktree, no install.

- **Purpose of the surface:** `<what the page or screen is for, and who uses it>`
- **Data to show:** `<fixture or seed file paths>`. Copy sample values from these. Read no live database and no env file, and put no secret in the file.
- **Design tokens:** `<token file paths>`. Use these values for color, type, and spacing.
- **Host chrome:** `<paths of the page or layout this surface sits in>`. Reproduce its header, sidebar, spacing, and density as static markup around your variant, or the app's global chrome only when no host page exists.
- **Structural direction:** `<this variant's layout, information hierarchy, and primary affordance>`. Other builders hold other directions. Stay inside yours, and share no layout component with them.

The file is self-contained HTML, CSS, and JavaScript that opens by double-click, with no build and no server. It calls no backend and performs no mutation: controls change local state only.

Return the path you wrote and one sentence on the structure you built.
</brief>

The TUI program and a requested CLI script go to one builder instead, because the variants share one entry file: send the same brief with every variant's direction listed, the output path set to the prototype directory, and the file paragraph replaced by the program's contract, which is the project's TUI library imported, one command to run it, and one key that cycles variants.

When every builder has returned, run `git status --porcelain` again. When the two outputs differ, name the differing paths to the user and stop before handing over. Revert nothing yourself.

Then write `index.html` beside the variants:

- the question in one line at the top, plus the no-host-page note where it applies;
- one iframe filling the page, its source the current variant's file;
- a floating bar fixed at bottom-center, visually distinct from the design, with previous, a label reading `B: Sidebar layout`, and next, wrapping around;
- the bar reads and sets `?variant=<key>`, so a reload keeps the variant.

Completion criterion: `.crank/<slug>/prototype/` holds `index.html` and one `variant-<key>.html` per variant, or the one scratch program, and the second `git status --porcelain` output equals the first.

### 3. Hand over

Give the user the path and the run command: double-click `index.html`, `go run ./.crank/<slug>/prototype`, or the project's equivalent. Do not open the prototype yourself.

Completion criterion: the user has the path and one command.

### 4. Verdict

Ask which variant wins and what to take from the others. A revision request goes back to a builder as a new `variant-<key>.html` with a new key and direction, added to `index.html`. Repeat until the user names a winner. On a hedge, ask the open look and interaction decisions in prose per [GRILLING.md](GRILLING.md) and record `no verdict`.

Completion criterion: the user has named a winner, or every open look and interaction decision has a prose answer.

### 5. Record

Write one `Prototype:` line. It reads the verdict, which is the winner, what the user took from the other variants, the prototype's path, and the surface the mock stood in for, or it reads `no verdict`. From the spec phase the line lands in Technical decisions, and the winner's behaviors land as numbered acceptance criteria. From the plan phase the line and the chosen behaviors land under **Updates since spec**. From the brainstorm, the brief's **Key decisions** records the path beside the decision it settled. The plan writes the real UI from the verdict and lifts no mock code.

Completion criterion: the artifact carries the line, and every behavior the user chose is a numbered criterion or an **Updates since spec** entry.
