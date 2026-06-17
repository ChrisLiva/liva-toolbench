---
name: crank
description: Run the full Crank pipeline (spec → plan → execute) autonomously from a single prompt. Use when the user types /crank or asks to take an idea from raw thought to shipped code without back-and-forth.
argument-hint: "<idea or feature description>"
---

# Crank (autonomous)

You drive `$ARGUMENTS` end-to-end through `crank:spec` → `crank:plan` → `crank:execute` without stopping to ask the user. Each phase runs in its own subagent; phases hand off via `spec.md` / `plan.md` / `retro.md` in a shared run directory (`RUN_DIR`) you create in Phase 0. You write nothing yourself — subagents own the docs.

<subagent-tiers>
This skill delegates work to subagents at two capability tiers. Where the body says to spawn a **standard** or **heavy** subagent, resolve the tier for the harness you are running in:

- **Claude Code** — spawn via the `Agent` tool and set `model` per tier: standard → `model: sonnet`, heavy → `model: opus`. Set per spawn; nothing else to configure.
- **Codex** — spawn a subagent and set its reasoning effort per tier on `gpt-5.5`: standard → `medium`, heavy → `high`. Set per spawn; nothing else to configure.
- **Cursor** — spawn a subagent and set its `model` per tier: standard → `cursor-composer-2-5`, heavy → `gpt-5.5-high`. Set per spawn; nothing else to configure.

Tier intent (harness-independent): **standard** = bulk work — codebase grounding, exploration, per-task review. **heavy** = work that rewards the strongest reasoning — spec drafting, adversarial review, final cross-task review.
</subagent-tiers>

## Hard rules

- **Never ask the user a question** except the Phase 4 cleanup offer.
- **Always run in a fresh git worktree** created in Phase 0 — even on a clean tree, even on a feature branch.
- **One subagent per phase**, spawned via `Agent` at the tier below (see <subagent-tiers>).
- **File handoff.** You tell each subagent the exact artifact path to write inside `RUN_DIR`; its sentinel line confirms it. Pass `RUN_DIR` to the next phase.
- **Halt on blocker, don't retry.** If a subagent's final message contains a line starting with `BLOCKER:`, surface it with whatever artifacts exist and stop.
- One short status line before each phase, one after. No verbose narration.

## Headless override block

Prepend verbatim to every Phase 1–2 subagent prompt. Phase 3 (`execute`) is already non-interactive and skips this.

> **Headless mode.** You run under autonomous orchestration inside a pre-created git worktree. You have no user. Override every interactive gate in the skill you invoke:
> - At every options-and-recommendation gate, silently pick the recommended option.
> - For non-obvious picks (where the recommendation isn't clearly the best fit), write an `Assumption: <what you assumed and why>` line into the relevant doc section.
> - The orchestrator has already entered a fresh worktree on a `crank/<slug>` branch via `EnterWorktree`. Never run `git worktree`, `git checkout -b`, `EnterWorktree`, `ExitWorktree`, or any branch-switching command.
> - Skip every other interactive step the skill offers — the one-targeted-question allowance, the hand-back menu, any finish-up ask. Proceed straight to writing the output doc.
> - Write the output doc to the exact path given in your prompt — skip the skill's `mktemp` step and its hand-back menu.
> - Run the skill's adversarial review as written — it is your only review pass.
> - **Never** emit a question. On a true blocker, write what you have, append a `## Blocker` section, and end your final message with `BLOCKER: <summary>` on one line and `<ARTIFACT>_PATH=<absolute path>` on the next.
> - On success, end with **only** `<ARTIFACT>_PATH=<absolute path>` on its own line. No menu, no extra prose.

`<ARTIFACT>` is `SPEC`, `PLAN`, or `RETRO`.

## Phase 0 — Worktree setup (orchestrator)

Runs in the main thread, before any subagent. Use the **`EnterWorktree` built-in tool** — never `git worktree add` to a sibling path.

**Status:** `Setting up worktree…`

1. Resolve repo root and base branch:
   ```!
   git rev-parse --show-toplevel
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main
   ```
   Call these `REPO_ROOT` and `BASE_BRANCH` (fall back to `main`).

2. Build a worktree slug: today's date plus a short kebab-case hint from `$ARGUMENTS` (lowercase, alphanumerics + dashes, ≤30 chars): `SLUG=crank/$(date +%Y-%m-%d)-<hint>`. If `EnterWorktree` reports the name is taken, append `-2`, `-3`, etc. and retry.

3. Call `EnterWorktree` with `name: "<SLUG>"`. The tool creates the worktree at `<REPO_ROOT>/.claude/worktrees/<SLUG>` on a fresh branch (off `origin/<BASE_BRANCH>`) and switches the orchestrator session into it. Subagents you spawn afterward inherit this CWD — no need to pass `cwd:` explicitly.

4. After the call, capture state:
   ```!
   pwd
   git rev-parse --abbrev-ref HEAD
   ```
   Record these as `WORKTREE_DIR` and `WORKTREE_BRANCH`. Run orchestrator-level git commands from `WORKTREE_DIR`.

5. Create the shared run directory: `RUN_DIR=$(mktemp -d -t crank-run)`. All phase artifacts land here as `spec.md`, `plan.md`, `retro.md`.

6. If `EnterWorktree` fails, surface the error verbatim and halt. Do not fall back to manual `git worktree add`.

**Status:** `Worktree ready: <WORKTREE_DIR> on <WORKTREE_BRANCH>`

## Phases 1–3 — Subagent execution

For each phase, spawn one `Agent` (`subagent_type: general-purpose`, `description: Crank: <phase> phase`) with the tier and prompt below. Each prompt is the headless override block (skipped for Phase 3) followed by the phase body, which always opens with:

> `You are running inside this git worktree: <WORKTREE_DIR> on branch <WORKTREE_BRANCH>. Run all commands from there; do not switch branches or create new worktrees.`

After each subagent returns, extract the sentinel from its final message. If missing, halt and print the last ~20 lines of the return. If the return contains `BLOCKER:`, halt and surface it.

| # | Phase   | Tier     | Status before              | Skill arg            | Output doc            | Sentinel                | Status after            |
|---|---------|----------|----------------------------|----------------------|-----------------------|-------------------------|-------------------------|
| 1 | spec    | heavy    | `Drafting spec…`           | `$ARGUMENTS`         | `<RUN_DIR>/spec.md`   | `SPEC_PATH=<abs path>`  | `Spec ready: <path>`    |
| 2 | plan    | standard | `Planning…`                | `<RUN_DIR>/spec.md`  | `<RUN_DIR>/plan.md`   | `PLAN_PATH=<abs path>`  | `Plan ready: <path>`    |
| 3 | execute | standard | `Executing plan…`          | `<RUN_DIR>/plan.md`  | `<RUN_DIR>/retro.md`  | `RETRO_PATH=<abs path>` | `Retro written: <path>` |

**Phase body templates** (append to the worktree-context line above):

- **Phases 1–2**: `Invoke the crank:<phase> skill via the Skill tool with this argument: <skill arg>. Run it under the headless rules above. Write the output doc to <output doc>. End your final message with <SENTINEL>=<absolute path> on its own line.`
- **Phase 2 only**, additionally include: **"Default to a single-file plan unless the spec is unambiguously L/XL — bias toward fewer files."**
- **Phase 3** (no headless block):
  > `The worktree already exists — treat the current branch as the target; never create branches or worktrees, and skip the execute skill's on-main-branch confirmation. Skip the skill's Hand back section; the orchestrator owns cleanup. Invoke the crank:execute skill via the Skill tool with this argument: <RUN_DIR>/plan.md. Run the plan to completion through the skill's Verify the whole gates — including the final fresh-eyes review and any remediation it requests. Write the retro to <RUN_DIR>/retro.md — ignore the skill's mktemp instruction for the retro. The skill handles its own non-interactive triage (solo / sequential / parallel); when it would ask where to put task briefs and reports, don't ask — write them to a temp dir (the progress ledger stays in the worktree's git dir as the skill specifies). If the skill's load-and-review scan surfaces blockers or plan-mandated defects, do not ask which governs — end with BLOCKER: <summary> rather than pushing through. End your final message with RETRO_PATH=<absolute path> on its own line. On a hard blocker, end with BLOCKER: <summary> on one line then the sentinel on the next.`

After Phase 3, read `<RUN_DIR>/retro.md` and report the **Final review** verdict in your status line — the execute skill runs the whole-diff review against the spec and any remediation itself; the orchestrator does not re-review.

## Phase 4 — Cleanup offer (orchestrator)

The **one allowed user interaction**. Run it even if an earlier phase halted on a blocker, so the user can clean up the partial worktree. Ask in plain chat prose — do **not** use `AskUserQuestion`.

Detect final state from the worktree (you are still inside `WORKTREE_DIR` from Phase 0):
```!
git log --oneline "<BASE_BRANCH>..HEAD"
```

Print this block (substitute bracketed values; omit options that don't apply):

> "Crank pipeline complete on worktree `<WORKTREE_DIR>` (branch `<WORKTREE_BRANCH>`, <N> commits ahead of `<BASE_BRANCH>`). How do you want to finish up?
>
> - **Merge into `<BASE_BRANCH>` and clean up** — fast-forward `<WORKTREE_BRANCH>` into `<BASE_BRANCH>`, delete the branch, then call `ExitWorktree` with `action: "remove"`. Recommended when the change is reviewed and ready to land.
> - **Open a PR instead** — push `<WORKTREE_BRANCH>` to origin and `gh pr create` as draft. Recommended when the change needs human review before landing.
> - **Leave it as-is** — branch and worktree stay where they are; call `ExitWorktree` with `action: "keep"` to return the session to the original directory. Merge/PR/cleanup later.
> - **Throw it away** — delete the branch and call `ExitWorktree` with `action: "remove", discard_changes: true`. **Confirm twice** before doing this."

Recommend `Open a PR` if `origin` points to a code host; recommend direct merge for purely local repos. Wait for the user's pick.

For merge or PR options, do the git work first (still inside the worktree), then call `ExitWorktree` to leave and let the tool handle removal. For "leave it as-is", just `ExitWorktree` with `action: "keep"`. Report what happened in one line. Never force-push, amend, or rewrite history. Never delete a branch or worktree without explicit approval.

## Final summary

After Phase 4, print:

```
Crank complete:
  worktree    <WORKTREE_DIR> on <WORKTREE_BRANCH>
  spec        <SPEC_PATH>
  plan        <PLAN_PATH>
  retro       <RETRO_PATH>
  review      <APPROVED | CHANGES_REQUESTED — N fixes applied>  (from retro's Final review)
  cleanup     <merged and deleted | PR #123 open | left as-is | discarded>
```

If a phase halted on a blocker, list only the artifacts produced, the blocker line that ended the run, and the cleanup choice from Phase 4.
