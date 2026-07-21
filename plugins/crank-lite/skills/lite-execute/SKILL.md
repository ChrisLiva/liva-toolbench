---
name: lite-execute
description: "Execute a PRD, spec, or implementation plan: implement, verify, review, and commit the work."
disable-model-invocation: true
---

Implement the work described in the plan (or PRD/spec) the user provides.

**Before touching any file, pick the execution shape and state it** — count the plan's tasks and the areas of code it touches, then tell the user which shape you chose and why:

- **Solo** — ~3 tasks or fewer, one area of code, or tightly coupled edits that share in-flight state. Implement inline on this thread.
- **Orchestrate** — the default above that: you are the orchestrator; Sonnet/GPT-5.6-Terra-High subagents implement. Dispatch one subagent per task (parallel only when tasks touch disjoint files), each with a brief, targeted instruction: the task text, the relevant file paths, and the verification command it must run and report output from. Verify each returned task yourself with a cheap check (typecheck, targeted test) instead of re-reading the whole diff — keep this thread's context for coordination, not implementation.

A stated shape binds the run: if you said orchestrate, the first action on each task is a dispatch, not an inline edit. Drop back to solo only by saying so and why.

Track the run with your harness's task tracker (todo/plan tool): create one entry per plan task before starting work, mark it in progress when you begin it, and completed the moment it lands. Every run gets this, solo included — it is how the user sees progress mid-run and how an interrupted session knows where to resume.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done implementing the entire plan, spawn an Opus/GPT-5.6-Terra-High subagent to adversarially review your work against the original plan. Address confirmed findings before committing.

Before committing, inspect the worktree and stage only the files changed for this task. If unrelated user changes are present, leave them untouched and ask before committing only when you cannot separate your changes safely.

Before the retro, close the loop — you ship finished work: settle every loose end (reviewer findings, plan risks, your own "worth noting" observations) with a command, read, or test this session; a loose end survives only as a decision the user must make or an action only a human can perform, written with your recommendation.

Once you've finished implementation and review, record a concise retro to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-retro-<slug>.md`) and stop. Keep the artifact light: include what changed, verification run, review outcome, deviations from the plan, and any surviving decisions when those sections earn their place. Tell the user the commit SHA and temp file path; when nothing survived the loop-close, say the work is complete.
