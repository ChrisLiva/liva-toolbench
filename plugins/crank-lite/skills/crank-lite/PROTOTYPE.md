# Prototype

Several structurally different variants of one user-facing surface, one switcher, one command to run, and a recorded verdict. Every file lives under `.crank/<slug>/prototype/`. No mock code ships, and every file stays on disk until the plan's execution finishes. No phase before then deletes or moves a prototype file, because the spec, the plan, and execution read the winner at the path the `Prototype:` line records.

Read this once the user accepts a phase's offer. On a reopen, start at step 3, Hand over, with the files already there.

## 1. Pick the rung

State the question the prototype answers in one line, then take the rung the surface names:

- **Browser, native app, or desktop app.** An HTML mock: one `variant-<key>.html` per variant inside the host page's static chrome, behind one `index.html` switcher.
- **Interactive TUI.** A scratch program under the prototype directory that cycles variants on one key.
- **CLI output, help text, or flags.** Fenced blocks in chat, one per variant, over one shared sample input. Compose them yourself and write no file, since a subagent cannot print to the conversation, then skip to step 4, Verdict. On the user's request, build a scratch script that prints the same variants in step 2, Build.

Default to 3 variants and cap at 5. Variants differ in **structure**, meaning layout, information hierarchy, or primary affordance, never only in color or copy.

Completion criterion: the question, the rung, and one distinct structure per variant are written down.

## 2. Build

For a rung that writes files:

1. Create `.crank/` with its `.gitignore` if it is missing ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)).
2. Run `git status --porcelain` and keep the output.
3. Dispatch **one** standard-tier subagent ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers) with this brief, filled in. The dispatch is a blocking call, so wait on it the way INTERVIEW.md says to wait on a lookup batch.

<brief>
Build `<N>` prototype variants, whose code never ships, to answer `<question>`.

Write only under `<absolute path to .crank/<slug>/prototype/>`: no other file, no branch, no worktree, no install.

- **Purpose of the surface:** `<what the page or screen is for, and who uses it>`
- **Data to show:** `<fixture or seed file paths>`. Copy sample values from these. Read no live database and no env file, and put no secret in any file.
- **Design tokens:** `<token file paths>`. Use these values for color, type, and spacing.
- **Host chrome:** `<paths of the page or layout this surface sits in>`. Reproduce its header, sidebar, spacing, and density as static markup around each variant, or the app's global chrome only when no host page exists.
- **Variants:** `<key: name, then its layout, information hierarchy, and primary affordance>`, one line each. They share no layout component.

For an HTML mock, write:

- one self-contained `variant-<key>.html` per variant that opens by double-click, with no build and no server;
- `index.html`: the question in one line at the top, plus a note when the mock carries only the app's global chrome; one iframe filling the page; and a floating bar fixed at bottom-center, visually distinct from the design, with previous, a label reading `B: Sidebar layout`, and next, wrapping around. The bar reads and sets `?variant=<key>`, so a reload keeps the variant.

For a TUI or a script, write one scratch program that imports the project's library, runs by `<one command>`, and cycles variants on `<key>`.

No file calls a backend or performs a mutation: controls change local state only.

Return the paths you wrote and one sentence per variant on its structure.
</brief>

4. When the builder returns, run `git status --porcelain` again. Matching outputs complete the build. When they differ, name the differing paths to the user, revert nothing, and stop before the handover.

## 3. Hand over

Give the user the path and the run command: double-click `index.html`, `go run ./.crank/<slug>/prototype`, or the project's equivalent. Do not open the prototype yourself.

## 4. Verdict

Ask which variant wins, what to take from the others, and what in the winner to leave out.

- **On a revision request**, apply the change and ask again: re-run step 2, Build, for a rung that writes files. For the CLI rung, recompose the fenced blocks, and re-run step 2 too when a scratch script exists.
- **On a hedge**, ask the open look and interaction decisions in prose and record `no verdict`.

Completion criterion: the user has named a winner and answered what to take from the others and what to leave out, where `nothing` is an answer to those two; or, after a hedge, each open look and interaction decision has a prose answer.

## 5. Record

Write one `Prototype:` line. It reads `no verdict`, or the verdict:

- the winner;
- what the user took from the other variants;
- what the user left out of the winner;
- the winning variant's path: `.crank/<slug>/prototype/variant-<key>.html`, the scratch program's path and the variant's key, or `in chat` for a CLI rung that wrote no file, with the winning block copied beneath the line;
- the surface the mock stood in for.

It lands by the phase that offered the prototype:

- **Brainstorm:** in the brief's key decisions, beside the decision it settled.
- **Spec:** among the key technical decisions, with the winner's behaviors as numbered acceptance criteria.
- **Plan:** under the plan's assumptions, with the chosen behaviors.

The winning variant is the reference every later phase opens for that surface, and the verdict bounds it:

- **Committed:** the real UI keeps the winner's structure and what the user took from the other variants, and builds nothing the user left out.
- **Guidance:** the rest of the mock, for details the spec and the task leave open.
- **Stand-ins:** the mock's fixture values and static host chrome, which the real UI replaces.
- **Conflicts:** where the spec's or a task's text disagrees with the mock, the text wins.
