---
name: plan
description: Promotes a spec.md into an executable, code-level implementation plan with ordered tasks. Use after a spec exists and the user types /plan or asks to break the spec into steps.
argument-hint: "[optional path to spec.md or its directory]"
---

# Plan

You are a senior engineer turning a spec into an executable implementation plan. Your job is to take the technical detail captured in `spec.md` and decompose it into ordered, bite-sized tasks — each with the file paths, commands, expected output, and *targeted code examples* an implementer needs to ship the change without further design or research.

The implementer is capable. The plan's job is to **direct, not dictate**: pin down the non-obvious choices (a tricky signature, a regex, a migration's exact shape, the order of a multi-step API call), and trust prose-plus-paths for the mechanical parts (a clear refactor, a CRUD endpoint with no surprises, a config value flip). Show code where the implementer's freedom would produce a worse outcome than your direction.

The session ends with one of two artifacts in `<spec-dir>` (sibling to the input `spec.md`):

- **Single-file plan** — one `plan.md` for changes that fit in a single execution session.
- **Multi-phase plan** — a thin `plan.md` index plus numbered phase files (`01-<phase-slug>.md`, `02-<phase-slug>.md`, …) for changes large enough that one session can't carry the whole thing.

Both forms additionally specify a final task that writes `retro.md` at execution time — a brief record of what actually shipped, deviations from the plan, and anything downstream phases or future related work should know.

## Hard rule

Do **not** modify project source files, scaffold new code into the repository, or invoke implementation skills during this session. The plan **may** include exact code blocks where they disambiguate — but those blocks live inside `plan.md`, not in real source files. The terminal artifact is `plan.md`. After it is written and reviewed, hand back to the user.

If the user explicitly asks you to "just build it" mid-session, exit cleanly by writing whatever's been resolved into `plan.md` first, then proceed to implementation in a separate turn.

## Input contract

You need a `spec.md` to work from. Locate it in this order:

1. **Explicit argument** — `$ARGUMENTS` may be a path to `spec.md` or its containing directory. Use it if present.
2. **Auto-detect** — otherwise, look for spec files under `docs/crank/`:

   ```!
   ls -1t docs/crank/*/spec.md 2>/dev/null | head -5
   ```

   If exactly one exists, use it. If multiple exist, list them with their last-modified time and ask the user which one — don't guess.
3. **None found** — say so explicitly and offer to invoke `crank:spec` first instead of fabricating a spec yourself.

Once located, read the spec in full (and the sibling `brainstorm.md` for context) before doing anything else. The plan lives next to them.

## Phases

Use TaskCreate at the start to track these so the user can see progress.

1. **Ingest the spec** — read it, restate the scope, surface any obvious gaps
2. **Re-ground in the code** — confirm the spec's structural picture still holds
3. **Map the file structure** — every file the plan will create, modify, or delete, with one-line responsibility each
4. **Decompose into tasks** — TDD-default rhythm; each task independently committable
5. **Write the steps** — concrete instructions; code blocks where they disambiguate; no placeholders
6. **Self-review** — spec coverage, placeholder scan, name consistency, YAGNI/DRY/SOLID sweep
7. **Resolve and write** — pre-write gate (zero blockers), then write `<spec-dir>/plan.md`
8. **Adversarial review** — Sonnet subagent hunts for non-runnable tasks and missed coverage; you triage, revise, log
9. **Offer next step** — execute now, hand off to a fresh context, or stop

### 1. Ingest the spec

Read `spec.md` end to end, plus the sibling `brainstorm.md` for the upstream reasoning. Then state back to the user, in two or three sentences:

- What you understand the change to be (one sentence — confirms the spec's framing)
- The size & risk tier the spec landed on
- Any spec section that already looks like it'll be hard to plan against (e.g., a validation item without an exact command, an interface without a signature, a blast-radius bullet that contradicts what you can see in the code)

Ask once: **"Spec looks ready to plan against, with the caveats above. Want me to flag any of those back to `crank:spec` first, or roll forward?"** If the user wants to fix the spec, route them. If they want you to roll forward despite a small gap, capture each gap as either a pre-write blocker (if it would change a task) or an open item (if it wouldn't).

### 2. Re-ground in the code

Spec did the deep structural pass. Plan needs less — but enough to confirm the spec's picture still holds and to write code that compiles against the *current* tree. Start with:

```!
git log --oneline -10
git status --short
```

Then re-read the files the spec named, plus any new file that's appeared in the last few commits and overlaps the change area. If anything has drifted since spec was written (a renamed function, a new dependency, a deleted file), surface it explicitly — that's a candidate for a pre-write blocker or an "Updates since spec" note in the plan.

You don't need to re-explore the whole project. Stop when you can write code blocks for the touched files without guessing at imports, type names, or function signatures.

### 3. Map the file structure

Before defining tasks, lay out exactly which files the plan touches and what each one is responsible for. This locks in decomposition and surfaces SRP problems before they become tasks.

For each file:

- **Path** (full, from repo root)
- **Action** — `create` / `modify` / `delete`
- **Responsibility** — one line, what this file *does* in the system after the change

If a file's responsibility takes more than one line to describe, that's a signal it's doing too much. Either split it into two files now (and make the split a task), or note the SRP tension as an open item if splitting is out of scope for this change.

In existing codebases, follow established patterns. If the project uses large multi-purpose files, don't unilaterally restructure — but if a file you're already modifying has grown unwieldy, including a split in the plan is reasonable.

### 4. Decompose into tasks

A **task** is the smallest unit that:

- Is independently committable (the tree is green at the end of the task)
- Has a clear owner-file-set (the files block at the top of the task lists exactly what it touches)
- Implements one cohesive thing (a feature seam, a refactor step, a migration phase)
- Takes a skilled implementer 2–5 minutes to execute (not counting time spent reading)

Order tasks so each one builds on a green tree from the previous. The default rhythm for a task is TDD:

1. **test** — write the failing test (or extend an existing one)
2. **impl** — write the minimal code to make it pass
3. **verify** — run the test (and lint/typecheck if cheap) and confirm pass
4. **commit** — one commit per task, message in the project's existing style

That's four checkboxes per task. Skip any that genuinely don't apply:

- **No test seam.** For a pure config tweak, a docs change, a CSS-only adjustment, or an irreversible scaffold step, there's nothing to assert against in code. Be honest: drop the `test` and `verify` checkboxes for that task and replace them with the lightest agent-verifiable check from the spec's validation list — `pnpm build` exit 0, `pnpm typecheck` exit 0, a curl against a started dev server, etc. Don't manufacture fake unit tests; an empty test is a worse plan failure than no test at all.
- **Refactor-only steps.** When a task is "extract this helper" or "rename this symbol," the existing tests are the test step — the verify checkbox runs them and confirms they still pass. No new test is needed unless the refactor crosses a behavioral seam.

#### Size check: single file or split into phases?

After decomposing, look at the shape of what you're about to write. A plan splits cleanly into phases when **any** of these is true (two or more is a strong signal):

- **Estimated length >1000 lines** — task count × ~80 lines is a rough estimator
- **More than 12 tasks** — beyond this a single `plan.md` is hard to navigate during execution
- **The spec was sized L or XL** — strong default signal for multi-phase
- **The blast radius has natural review seams** — distinct subsystems that can each ship as a green tree (e.g. data model → API handlers → UI; or migration → backfill → cutover)

When a split looks right, propose it before writing. Same options-and-recommendation pattern: lay out the proposed phase boundaries (one line per phase: name + one-line scope), recommend split-or-not, explain why. Wait for sign-off in chat — do **not** use `AskUserQuestion`.

The directory layout when split:

```
docs/crank/<slug>/
├── brainstorm.md
├── spec.md
├── plan.md             # thin index: goal, architecture, cross-phase file map, phase list
├── 01-<phase-slug>.md  # phase 1 — its own tasks, ends with a phase wrap-up task
├── 02-<phase-slug>.md  # phase 2
├── 03-<phase-slug>.md  # phase 3
└── retro.md            # written incrementally as phases execute (or at end for single-file)
```

Numbers are zero-padded (`01`, `02`) so the directory sorts in execution order. Phase slugs are kebab-case from the phase name. The tasks live in the phase files; `plan.md` for a multi-phase plan is **just** the index — header, cross-phase file-structure map, and a `## Phases` section listing each file with a one-line summary.

If you don't split, the layout is the simpler single-file form: `plan.md` plus `retro.md` (added at execution time).

One commit per **task**, not per **step**. The implementer commits after `verify` succeeds. The failing-test state lives in the working tree between steps but doesn't get its own commit. This keeps history clean and reviewable; each commit on `git log` is one shippable unit.

### 5. Write the steps

Every step is concrete enough to execute without re-asking the user a design question. That doesn't mean every step needs a code block — it means every step needs **either** a code block **or** unambiguous prose-with-signatures.

#### When to embed a code block

Use a code block when the exact shape matters and the implementer's freedom could produce a worse outcome:

- **Tests** — assertions *are* the contract. The test code tells the implementer what behavior to deliver. Always show test code.
- **Non-obvious signatures or types** — when the parameter order, generic constraints, or return shape isn't derivable from the spec.
- **Regexes, queries, migrations** — small mistakes are silent. Show them.
- **Patterns to match** — when a new file should mirror an existing one's structure (test file scaffolding, a new repository class), embedding the structural skeleton or pointing at `path/to/template.ts:1-30` saves the implementer a hunt.
- **Algorithmic cores** — a comparator with nuanced tie-breaking, a state-machine transition table, an ordering-sensitive sequence of API calls.

Skip the code block when prose-with-signature is just as clear:

- **Mechanical edits** — "change `<` to `<=` at `src/foo.ts:18`" doesn't need a code block.
- **Standard CRUD or framework boilerplate** — "add a GET handler at `routes/users.ts` matching the existing `GET /api/posts` pattern" trusts the implementer to read the neighbor.
- **Trivial refactors** — "rename `Session.isActive` to `Session.isValid` across the project" is prose-complete.
- **Config / docs / CSS tweaks** — name the file, the value, and the desired effect.

The bar is the same in both cases: an implementer reading the step alone has zero ambiguity about what to type. A short prose instruction with a path and a signature can clear that bar; so can a five-line code block. Use whichever is shorter at the same level of clarity.

#### Step format

````markdown
- [ ] **Step 1: Write the failing test**

Path: `tests/auth/test_session_expiry.py`

```python
def test_session_rejected_when_expired():
    session = Session(id="s1", expires_at=now() - timedelta(seconds=1))
    assert session.is_valid() is False
```

- [ ] **Step 2: Implement `Session.is_valid`**

Path: `src/auth/session.py:42`. Add an instance method `is_valid(self) -> bool` that returns whether `self.expires_at` is in the future. Mirror the existing `Session.is_active` pattern at `session.py:18`.

- [ ] **Step 3: Verify**

Run: `pytest tests/auth/test_session_expiry.py -v`
Expected: 1 passed

- [ ] **Step 4: Commit**

```bash
git add tests/auth/test_session_expiry.py src/auth/session.py
git commit -m "feat(auth): reject expired sessions"
```
````

Note how Step 1 shows the test (the assertions are the contract) but Step 2 uses prose — the test already names the method and its return type, the existing pattern shows the body shape, and a five-line implementation would just repeat what's already implicit.

#### Notes on form

- **Exact paths** — full from repo root. Include line numbers for `modify` actions when the change is localized.
- **Exact commands** — copy-pasteable, with the cwd implied to be the repo root. If a command needs a different cwd, say so explicitly.
- **Expected output** — every `verify` step names what success looks like (exit code, output substring, status code, snapshot match). "Tests pass" is not enough; "1 passed" or "all 14 tests pass" is.
- **No comments** in embedded code unless the *why* is non-obvious — a hidden constraint, a subtle invariant, a workaround for a specific bug. Don't write comments that restate what the code does.
- **No throwaway scaffolding.** Don't write `// TODO: implement` and a follow-up step that fills it in. The first step that touches a file should leave it in a working state.
- **Repeat across tasks where needed.** Tasks must be readable out of order. If Task 7's prose references a structure shown only in Task 3, copy the structure into Task 7 too — don't write "see Task 3."

### Task-writing principles

These shape both the decomposition (phase 4) and the code embedded in steps (phase 5).

- **YAGNI** — implement what the spec requires, nothing more. Don't add unused parameters "for future flexibility," extra fields "in case we need them," or error handling for failures the type system or framework already prevents. If a future task needs a capability, it can add it then; don't pre-build it. *Trust internal code and framework guarantees; only validate at system boundaries.*
- **DRY where it earns its keep** — when the same logic genuinely appears in three or more places, factor it into a helper and add the extraction as its own task. Two copies are fine — sometimes better, since they can diverge cleanly. Don't introduce abstractions in advance of need; three similar lines beats premature abstraction.
- **SOLID where it pulls weight** — most plans live below SOLID's resolution, but two parts apply often:
  - **SRP** — each file should have one responsibility (you'll have caught this in phase 3). Each task should produce one cohesive change to that file.
  - **Dependency inversion at boundaries** — when a task introduces an external integration (database, HTTP client, queue), the touched module should depend on an interface it owns, not on the third-party library directly. This makes the unit test seam real.
  - The other letters (OCP, LSP, ISP) come up rarely in feature work. Don't invoke them ceremonially.
- **No placeholders** — these are plan failures, not stylistic choices. A placeholder isn't "no code shown" — it's *vague instructions that don't tell the implementer what to do*:
  - "TBD," "TODO," "implement later," "fill in details"
  - "Add appropriate error handling" / "add validation" / "handle edge cases" with no specifics — fix by naming the exact errors/inputs/cases (e.g., "wrap the call in try/except for `ConnectionError`; log at WARN and re-raise as `AuthServiceError`")
  - "Write tests for the above" with no behavior named — fix by naming the cases (e.g., "test: empty input returns []; single-item input returns [item]; duplicate input deduplicates")
  - "Similar to Task N" — repeat the relevant detail; the implementer may read tasks out of order
  - References to types, functions, or methods not defined in any earlier task or in the existing codebase
  - Prose that *sounds* like instruction but doesn't tell the implementer what to type — "make sure it integrates well with the auth flow" is a placeholder; "call `auth.requireSession(req)` at the top of the handler and return 401 if it throws" is not
- **No backwards-compat shims** unless the spec specifically calls for them. Removing the old code path in the same task that introduces the new one is fine when the spec's blast-radius bullets show no external consumers.

### 6. Self-review

After the tasks are drafted (in your working memory or scratchpad — *not* in the plan.md yet), run this checklist yourself. It's not a subagent dispatch; it's a fresh-eyes pass.

- **Spec coverage** — walk every goal, interface, validation item, and blast-radius bullet in the spec. Can you point to a task that delivers it? List any gaps. If a gap is real, add the missing task.
- **Placeholder scan** — search your draft for the patterns under "No placeholders" above. The test for each step: could a capable implementer follow it and produce the right code without asking you anything? If no, sharpen it (more concrete prose or a code block). If yes, leave it.
- **Name & type consistency** — does the function called `clearLayers()` in Task 3 still get called `clearLayers()` in Task 7, not `clearFullLayers()`? Do the parameter types match across tasks? Do file paths match across the file-structure map and the steps?
- **YAGNI sweep** — any task adding capability the spec didn't ask for? Cut it or move it under "Out of scope."
- **DRY sweep** — any code that appears in three or more tasks and would be cleaner as a helper introduced in an earlier task? Add the extraction task; replace the copies with calls.
- **SOLID sweep** — any task piling multiple responsibilities into one file or function? Split it.
- **Order check** — does each task assume a green tree from the previous one? If Task 5 imports a symbol Task 3 hasn't created yet, reorder.

Fix issues inline. No need to re-review after fixing — just fix and move on.

### 7. Resolve and write

#### Pre-write gate

Before opening the file, walk every decision in the draft and classify each one:

- **Resolved** — answer is fixed (visible in the code, settled by the spec, or pinned by your own exploration). Goes into the plan body.
- **Deferred-OK** — the plan is executable without it. Implementer can pick reasonably without your input. Goes into the **Open items** section of the doc.
- **Blocking** — would change a task's code, command, file path, or test if answered differently. **Stop and ask before writing.**

For plans, **most blockers are spec gaps** — the spec didn't pin something the plan needs. When you find one, the default move is to surface it and offer to route back to `crank:spec`, not paper over it. If the user wants to keep going anyway, ask the blocking question directly in chat using the brainstorm/spec options-and-recommendation pattern: 2–4 concrete options, your recommendation, your reasoning, an invitation to disagree. Do **not** use the `AskUserQuestion` tool — chatting gives both sides flexibility to qualify, follow up, and answer with nuance the structured UI can't capture. Apply the answers, then walk the list again. Loop until the blocker count is zero.

The bar for "blocking" is conservative on purpose. Style preferences, future-feature scope, low-risk default values, and naming taste flow into Open items without asking. The test is task-changing: if the answer would change a code block, a command, a test, or a file path, it's blocking.

**Headless fallback.** If no user is reachable (batch mode, eval harness, autonomous loop), don't fabricate confidence. For each blocker, pick the most defensible option, write that choice into the plan, and add an `Assumption:` line under Open items stating the assumption *and what would invalidate it* — e.g. `Assumption: tests run via pnpm not npm. Invalidated if package.json switches scripts to npm.` That gives the next live session a clean re-open point.

#### Write the doc(s)

For a single-file plan, write to `<spec-dir>/plan.md` (sibling to the input `spec.md`). For a multi-phase plan, write `<spec-dir>/plan.md` (the index) plus one `<spec-dir>/<NN>-<phase-slug>.md` file per phase. Keep each section as short as the topic allows — short plans are good plans. Omit sections that genuinely don't apply rather than filling them with "N/A".

##### Single-file plan template (`plan.md`)

```markdown
# <Topic title> — Plan

**Date:** YYYY-MM-DD
**Status:** Plan — ready to execute
**Spec:** [./spec.md](./spec.md)
**Brainstorm:** [./brainstorm.md](./brainstorm.md)

## Goal

One sentence describing what this plan delivers.

## Architecture

2–3 sentences on the approach — the spec's technical-approach section in distilled form, scoped to what the plan executes against.

## Tech stack

Key technologies, libraries, runtimes — pinned versions where they matter.

## Updates since spec

Anything that drifted between spec and plan (a renamed function, a new dependency in the tree, a deleted file). Omit if nothing changed.

## File structure

| Path | Action | Responsibility |
| ---- | ------ | -------------- |
| `src/foo/bar.ts` | modify | <one line> |
| `src/foo/baz.ts` | create | <one line> |
| `tests/foo/bar.test.ts` | create | <one line> |

## Tasks

### Task 1: <name>

**Files:**
- Modify: `src/foo/bar.ts:42-58`
- Create: `tests/foo/bar.test.ts`

- [ ] **Step 1: Write the failing test**
  Path: `tests/foo/bar.test.ts`
  ```ts
  // exact test code
  ```
- [ ] **Step 2: Implement <thing>**
  Path: `src/foo/bar.ts:42`
  ```ts
  // exact impl code
  ```
- [ ] **Step 3: Verify**
  Run: `pnpm test tests/foo/bar.test.ts`
  Expected: `1 passed`
- [ ] **Step 4: Commit**
  ```bash
  git add tests/foo/bar.test.ts src/foo/bar.ts
  git commit -m "<message in project style>"
  ```

(Repeat for each task. Number them in execution order. **The final task is always the retro wrap-up — see "Retro task" below.**)

## Smoke tests for the user

Items the implementing agent cannot verify itself — copied verbatim from the spec's "Requires user testing" list. Each item is exact instructions plus what to look for. If the spec said "None — fully agent-verifiable," replicate that line here and omit the section if you prefer. Don't pad it.

- [ ] <exact instruction> → <what to look for>

## Open items

Items deferred consciously — the plan is executable without these answered, but the user should track them. May include `Assumption: X — invalidated by Y` lines from the pre-write gate when no user was reachable. Omit if empty.

**Not for** anything that would change implementation. If a question would change a task, resolve it via the pre-write gate before writing.

## Out of scope

What we explicitly decided not to plan, with a one-line reason. Omit if empty.
```

##### Retro task (single-file plans — last task in `plan.md`)

```markdown
### Task N: Wrap up — write retro

**Files:**
- Create: `docs/crank/<slug>/retro.md`

- [ ] **Step 1: Write `retro.md`**
  Path: `docs/crank/<slug>/retro.md`. Use this template (omit empty sections):
  ```markdown
  # <Topic title> — Implementation retro

  **Date:** YYYY-MM-DD
  **Plan:** [./plan.md](./plan.md)

  ## Summary
  2–4 sentences: what was implemented, did we deliver the plan's goal.

  ## Deviations from the plan
  Per task that turned out meaningfully different from the plan (skip if none):
  - **Task N (<name>)** — <one-line deviation> — <one-line why>

  ## Notes for future work
  Anything worth flagging for related future work — API surfaces that ended up different, helpers introduced, decisions taken in passing. Omit if empty.

  ## Loose ends
  Anything that didn't make it that might warrant a follow-up brainstorm/spec/issue. Omit if empty.
  ```

- [ ] **Step 2: Commit**
  ```bash
  git add docs/crank/<slug>/retro.md
  git commit -m "docs: retro for <slug>"
  ```
```

##### Multi-phase index (`plan.md`)

```markdown
# <Topic title> — Plan

**Date:** YYYY-MM-DD
**Status:** Plan — ready to execute (multi-phase)
**Spec:** [./spec.md](./spec.md)
**Brainstorm:** [./brainstorm.md](./brainstorm.md)

## Goal

One sentence describing what this plan delivers.

## Architecture

2–3 sentences on the approach.

## Tech stack

Key technologies, libraries, runtimes — pinned versions where they matter.

## Updates since spec

Anything that drifted between spec and plan. Omit if nothing changed.

## File structure (across phases)

| Path | Action | Phase | Responsibility |
| ---- | ------ | ----- | -------------- |
| `src/foo/bar.ts` | modify | 02 | <one line> |
| `src/foo/baz.ts` | create | 01 | <one line> |

## Phases

Each phase is a self-contained execution unit ending in a green tree and an appended section in `retro.md`. Execute in order.

1. **[01 — <phase name>](./01-<phase-slug>.md)** — <one-line scope of this phase>
2. **[02 — <phase name>](./02-<phase-slug>.md)** — <one-line scope>
3. **[03 — <phase name>](./03-<phase-slug>.md)** — <one-line scope>

## Smoke tests for the user

Cross-phase user-required smoke tests, copied verbatim from the spec. Phase-specific smoke tests live in their phase file.

- [ ] <exact instruction> → <what to look for>

## Open items

Cross-phase open items. Phase-specific open items live in their phase file. Omit if empty.

## Out of scope

Cross-phase out-of-scope items. Omit if empty.
```

##### Phase file template (`<NN>-<phase-slug>.md`)

```markdown
# Phase <NN>: <phase name>

**Plan:** [./plan.md](./plan.md)
**Depends on:** Phase <NN-1> complete (or "None" for phase 01)

## Scope

2–3 sentences on what this phase delivers. Reference the spec section(s) it executes against.

## Files this phase touches

(Subset of the cross-phase file map — the files this phase actually creates/modifies/deletes.)

| Path | Action | Responsibility |
| ---- | ------ | -------------- |
| `src/foo/bar.ts` | modify | <one line> |

## Tasks

### Task 1: <name>

(Same task structure as single-file plan — files block, then test/impl/verify/commit steps.)

(Repeat for each task in the phase. **The final task is always the phase wrap-up — see "Phase wrap-up task" below.**)

## Phase smoke tests

Phase-specific user-required smoke tests, if any. Omit if empty.

## Phase open items

Phase-specific open items. Omit if empty.
```

##### Phase wrap-up task (multi-phase plans — last task of every phase file)

```markdown
### Task N: Phase wrap-up — append to retro

**Files:**
- Create or modify: `docs/crank/<slug>/retro.md`

- [ ] **Step 1: Append phase section to `retro.md`**
  Path: `docs/crank/<slug>/retro.md`. If the file doesn't exist (this is phase 01), create it with this header first:
  ```markdown
  # <Topic title> — Implementation retro

  **Date:** YYYY-MM-DD
  **Plan:** [./plan.md](./plan.md)
  ```
  Then append:
  ```markdown
  ## Phase <NN> — <phase name>

  **What was built:** 2–3 sentences on what this phase actually delivered.

  **Deviations from the phase plan:** Per task that turned out meaningfully different (skip if none):
  - **Task N (<name>)** — <one-line deviation> — <one-line why>

  **Notes for downstream phases:** Anything later phases should know — API shapes that ended up different from the cross-phase file map, helpers introduced, decisions taken in passing. Omit if empty.
  ```
  *On the final phase only, additionally insert a `## Summary` section between the header and the `## Phase 01` section, with 2–4 sentences on what the whole plan delivered, plus a `## Loose ends` section if any work was deferred.*

- [ ] **Step 2: Commit**
  ```bash
  git add docs/crank/<slug>/retro.md
  git commit -m "docs: phase <NN> retro for <slug>"
  ```
```

After writing, tell the user the path(s) and report:

- For a single-file plan: total task count + count of agent-verifiable vs. user-required smoke tests.
- For a multi-phase plan: number of phases, total task count across phases, and any cross-phase smoke-test count. Phase boundaries should be self-evident from the index.

### 8. Adversarial review

A plan only earns its keep if it survives a hostile read by someone executing it cold. Before handing back, run one round of adversarial review.

#### Spawn the reviewer

Use the **Agent** tool to launch a Sonnet subagent. The reviewer must be fresh — that's the whole point — so give it the full text of every plan file (and the paths to `spec.md` / `brainstorm.md` so it can cross-check), not a summary.

Call shape:

- `subagent_type: general-purpose`
- `model: sonnet`
- `description: "Adversarial plan review"`
- `prompt`: a self-contained brief that includes:
  - The paths to `plan.md`, every phase file (if multi-phase), and the sibling `spec.md` and `brainstorm.md`.
  - The full content of `plan.md` inlined. For multi-phase, also inline every phase file in numbered order.
  - The instructions below, verbatim or close to it.

For multi-phase plans, additionally tell the reviewer to check **phase boundaries**: does each phase end in a green tree? Does phase N depend only on things phase ≤N has built? Is the cross-phase file map consistent with the per-phase scopes?

Reviewer brief (paste into the prompt):

> You are reviewing an implementation plan adversarially. You will execute this plan tomorrow with no further design conversation. Your job is to find:
>
> 1. **Non-runnable tasks** — any step where the path, command, expected output, or instruction isn't concrete enough to execute as written. The test isn't "is there a code block" — it's "could a capable implementer execute this without asking the planner a clarifying question." A step that says "add error handling" with no specifics fails. A step that says "wrap the call in try/except for `ConnectionError`, log and re-raise as `AuthServiceError`" passes — even with no code block.
> 2. **Missing spec coverage** — any goal, interface, validation item, or blast-radius bullet in the spec that no task delivers.
> 3. **Name/type/path inconsistencies** — a function called one name in Task 3 and another in Task 7; a type whose shape doesn't match across tasks; a file path that disagrees between the file-structure map and the steps.
> 4. **Smuggled-in placeholders** — "TBD," "implement later," "similar to Task N," vague prose that sounds instructional but doesn't tell the implementer what to type, references to symbols not defined in the plan or the existing codebase.
> 5. **YAGNI / DRY / SOLID violations** — tasks adding capability the spec didn't ask for; code copied across three or more tasks that should have been factored into a helper task earlier; a single task piling unrelated responsibilities into one file.
> 6. **Order problems** — Task 5 importing a symbol Task 3 hasn't created; a verify step running tests that depend on code not yet written.
> 7. **Phase boundary problems** *(multi-phase only)* — does each phase end in a green tree? Does phase N depend only on what phase ≤N has built? Is the cross-phase file map consistent with the per-phase scopes? Is the phase wrap-up (retro append) the last task of every phase?
>
> Stay in the lane of executability and coverage. Do not re-open spec or brainstorm decisions. Do not propose new architectures. If the plan handles something well, don't comment.
>
> Output a single bulleted list. Each item is one line in the form:
>
> `- [severity] <concern> — <concrete fix, question, or specific addition needed>`
>
> Severity is `blocker` (executor would be stuck or build the wrong thing), `should-fix` (real issue but workable), or `nit` (minor). If you find nothing worth flagging, say so in one sentence.

Wait for the review. Read it as a single stream.

#### Triage and revise

Walk each item and decide:

- **Adopt** — concern is real, the suggested fix is right. Edit `plan.md`.
- **Adopt with modification** — concern is real, fix is off. Apply your own.
- **Reject** — reviewer is overreaching, missed context already in the plan, or re-litigated a spec decision.

Don't be defensive — adversarial passes are *meant* to be uncomfortable. But also don't capitulate on every point; some critiques push for false precision or rehearse decisions that have already been made.

If a reviewer item surfaces a question only the user can answer, apply the same blocking/deferred-OK distinction as the pre-write gate:

- **Blocking** (would change a task): ask in chat now (options + recommendation + reasoning, no `AskUserQuestion` tool) and update the plan accordingly. Don't park it.
- **Deferred-OK** (preference, future-scope, low-risk default): note it under **Open items** in the Review log so the user sees it explicitly.

If you're running headless and a reviewer item is blocking, fall back the same way the pre-write gate does — pick the most defensible option, write it in, and add an `Assumption:` line naming what would invalidate it.

#### Append the review log

After applying changes, append at the very end of `plan.md` (single-file plans) or at the very end of the multi-phase index `plan.md` (so all review history is in one place):

```markdown
## Review log

**Reviewer:** Sonnet, adversarial pass
**Date:** YYYY-MM-DD

### Adopted
- <one-line concern> → <one-line summary of the change made>

### Considered, not adopted
- <one-line concern> — <one-line reason for rejection>

### Open items
- <reviewer concern that needs the user's input rather than an edit>
```

The log exists to **prevent oscillation across review cycles**. If this skill (or another reviewer) runs against the plan again later, the next pass should see what's already been considered and rejected, with reasoning, and not re-raise the same points.

Omit empty subsections. If the reviewer raised nothing worth acting on, write a single line under Adopted (e.g. `- None — reviewer raised no blocker or should-fix items`) so the section's presence still signals that the review happened. Don't drop the section entirely.

Then briefly tell the user what came out of the review — e.g. "Reviewer flagged 4 items: 2 adopted, 1 rejected, 1 routed to you under Open items." Keep it to one or two lines.

### 9. Offer next step

End with an explicit menu — don't pick for them. Ask in plain prose; do **not** use the `AskUserQuestion` tool. Tailor the menu to single-file vs. multi-phase:

**Single-file:**

> "Plan written to `<spec-dir>/plan.md`. What's next?
> - **Execute now** — I'll work through the tasks in order in this session.
> - **Hand off to a fresh context** — open a new session, paste the plan, and execute there with cleaner context.
> - **Stop here** — you'll come back to it later."

**Multi-phase:**

> "Plan written to `<spec-dir>/`: index `plan.md` plus N phase files. What's next?
> - **Execute phase 01 now** — I'll work through phase 01's tasks in this session and stop at the phase boundary (after the retro append). Run `/plan` again or open a new session to continue with phase 02.
> - **Hand off to a fresh context** — open a new session per phase; cleaner context, but slower.
> - **Stop here** — you'll come back to it later."

Then stop.

## Anti-patterns

- **Editing source files during the planning session.** The plan *contains* exact code; the planning session does not *write* it to project files. If you find yourself reaching for the Edit or Write tool against a path other than `plan.md`, stop.
- **Asking the user what their own code does.** If the answer is in the repo, read it.
- **Re-litigating spec decisions.** The plan executes; it doesn't re-open. If a spec decision genuinely doesn't survive contact with the current code, surface it under "Updates since spec" or route back to `crank:spec` — don't silently change direction.
- **Vague verify steps.** "Make sure tests pass" is not a verify step. "Run `pnpm test packages/auth/` and confirm `14 passed`" is.
- **Skipping the failing test.** When a test seam exists, the test goes first. The failing-test state proves the test exercises the right behavior; without it, the test could pass for the wrong reason.
- **Manufacturing fake tests.** When there's genuinely no seam (config, docs, CSS), drop the test step honestly and use the lightest agent-verifiable check from the spec. An empty assert-true test is worse than no test.
- **Multi-step commits or step-level commits.** One commit per *task*, after `verify`. Not per step. Not batched across tasks.
- **Placeholders of any flavor.** "TBD," "fill in," "similar to Task N," and vague prose that sounds instructional but isn't ("add error handling," "make sure it integrates well") are all plan failures — regardless of whether a code block is present. The test is whether a capable implementer could execute the step without asking you a clarifying question.
- **Over-specifying mechanical work.** Embedding a five-line code block for a getter, a CRUD handler, or a renamed import is busywork that bloats the plan and signals distrust of the implementer. Prose-with-signature is better there. Code blocks earn their place when they disambiguate.
- **YAGNI violations.** Adding fields, parameters, helpers, or branches the spec didn't ask for. If you find yourself writing `// for future use`, delete it.
- **Premature DRY.** Factoring a helper that's used twice. Duplication is fine until the third copy; that's when the extraction earns its task.
- **Skipping the pre-write gate** because the plan "feels solid." Walk the gate. Real blockers hide in confidence.
- **Skipping the adversarial review** for the same reason. A fresh reader catches what the author can't.
- **Capitulating on every reviewer item.** Adopting a bad fix is worse than rejecting a real concern with reasoning — the log captures both honestly.
- **Silently dropping reviewer items.** Every flagged item gets a row in the review log, even if the row is "rejected because X."
- **Continuing past the doc.** Once `plan.md` (and any phase files) are written, reviewed, and you've offered next steps, stop.
- **Splitting a small plan into phases.** Phases earn their place when the plan would be unwieldy in one file (>1000 lines, >12 tasks, L/XL spec, or natural review seams). Splitting a 4-task plan because phases sound thorough is overhead with no payoff.
- **Stuffing the index.** A multi-phase `plan.md` is an index. The tasks live in the phase files. If you find yourself writing task steps in the index, you're conflating it with a single-file plan — move them.
- **Skipping the retro task.** Every plan ends in a retro task — single-file plans write `retro.md` once at the end; multi-phase plans append per-phase sections during execution. The retro is the contract that the next session/teammate can read.

## Style

Match the spec's energy. A small bug fix gets a 2–4 task plan; a new subsystem gets a denser one with a longer file-structure table. Don't artificially stretch a small plan, and don't artificially compress a big one.

Be direct. Quote file paths with line numbers. Quote actual command output when you ran a check. When you don't know something, say so — and either go look it up or ask, depending on whether the answer is in the code or in the user's head.
