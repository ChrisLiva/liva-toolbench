---
name: crank-wizard
description: Generate a cross-platform TUI wizard — a committed Go program (Bubble Tea) that walks a human through the steps only they can perform, with automated checks gating the flow.
argument-hint: "[the procedure the wizard walks through]"
disable-model-invocation: true
---

# Crank Wizard

A **wizard** is a small Go program that walks a human, step by step, through a procedure that's tedious to do by hand and tedious to re-explain every time: provisioning infrastructure, capturing credentials, walking a third-party dashboard, running a one-off cutover. The human does the steps only they can do; the wizard opens the pages, captures the values, verifies results with real commands, and saves progress so a quit at step 4 resumes at step 4.

A wizard is committed and repeatable: it lives at `wizards/<name>/` in the target repo and runs on macOS and Windows with `go run ./wizards/<name>`. Every wizard is two halves: [runtime.go](template/runtime.go), the immutable library, byte-identical in every wizard, and `steps.go`, the only file you author. [template/steps.go](template/steps.go) is the exemplar: a complete demo wizard that exercises every helper.

## Process

### 1. Grill briefly

The task description says what the wizard walks through; your questions exist only to catch edge cases and pin the full behavior. The blind spots, asked only when the description leaves them open:

- **Audience**: who runs this, on which OSes? Both macOS and Windows must work; a non-portable shell command branches on `runtime.GOOS`.
- **Lifecycle**: repeatable and committed (the default), or genuinely one-run?
- **Abort and resume**: a step re-runs from its start after a quit — flag any step where that repeat is unsafe.
- **Partial completion**: when a push or check fails midway, what must the human finish by hand?
- **Secrets**: which captured values are secret (hidden entry, kept out of saved progress), and where does each land — the env file, a CI secret, both, or nowhere?

Put the open ones to the user as one numbered round; ask one follow-up round only when an answer opens a real fork.

**Done when:** every blind spot above is settled by the task description or an answer, and every captured value has a known source, destination, and secrecy.

### 2. Scope the steps

Map the procedure into steps, one focused task per step — the runtime shows one step per screen, so a step is what the human should see at once. For each step, decide what the human does, what the wizard captures, and what the wizard checks itself: a `Check` runs a real command behind a spinner and gates the step, which beats asking the human to paste output. Where you don't actually know the current UI or the exact command, say so and ask the user or check the docs; a wizard earns trust by only naming dashboard pages that exist.

**Done when:** every step is named in order and, for each, you know the human's action, the captured values, and the automated checks.

### 3. Author the wizard

Create `wizards/<name>/` in the target repo:

1. Copy [runtime.go](template/runtime.go) from this skill's template, unchanged — its header says never hand-edit it, and that includes you.
2. Write `steps.go`: a `wizardDef() *Wizard` returning name, title, intro, and the steps. Model it on [template/steps.go](template/steps.go); the helper API and each helper's contract are the doc comments in `runtime.go`.
3. Run `go mod init <name>` and `go mod tidy` in the wizard dir; commit `go.mod` and `go.sum` beside the source.
4. Add `.wizard-state.*.json` to the repo's gitignore: saved progress is per-machine.

Hold the bar the demo sets: open the URL before asking for its value, `AskSecret` for anything secret, `WriteEnv` every persisted value, `SetSecret` only what CI actually consumes, `Confirm` before any irreversible action, and branch on `runtime.GOOS` wherever a shell command isn't portable (the demo's `grep`/`findstr` branch is the pattern).

**Done when:** `runtime.go` is byte-identical to the template's, `steps.go` compiles, and every captured value from step 1's map is routed through a helper.

### 4. Verify and hand off

Verify statically — the wizard opens browsers and blocks on human input, so trace it instead of running it end-to-end:

- `go vet ./...` and `go build` pass, and so does the other OS's build: `GOOS=windows go build` (or `GOOS=darwin` when authoring on Windows).
- `go run . --list` prints every step in order.
- Trace each captured value to its destination, and match every `SetSecret` name to the `secrets.*` reference in CI that consumes it.

Hand off with the run command (`go run ./wizards/<name>`) and, for teammates without Go installed, offer cross-compiled binaries: `GOOS=windows go build -o <name>.exe .` and `GOOS=darwin go build -o <name> .`.

**Done when:** both OS builds pass, `--list` matches step 2's map, every value traces to its destination, and the handoff message names the run command.
