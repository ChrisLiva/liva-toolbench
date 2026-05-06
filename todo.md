# TODO

## `plan` skill — shipped at v0.1

`plugins/crank/skills/plan/` is in place, evaluated against three fixtures (small / medium / cross-cutting). Iteration-1 results: 82% pass rate with skill vs 32% baseline (+50pp).

Iteration-1 surfaced two sharpening targets that didn't make it into v0.1:

- **"Direct, not dictate" doesn't fully stick.** The skill produces full multi-line code blocks for trivial edits (e.g. a 15-line `Config` rewrite to add one field). Tighten the SKILL.md guidance with a wrong/right example pair.
- **Adversarial reviewer subagent fails when nested.** Inside a subagent context, the `Agent` tool is unavailable; the SKILL.md should explicitly describe the inline-self-review fallback rather than just failing.

Eval workspace lives at `plugins/crank/skills/plan-workspace/` — fixtures + iteration-1 outputs + benchmarks are all there. Re-run by spawning subagents per `evals/evals.json`; the skill-creator scripts at `~/.claude/plugins/cache/.../skill-creator/` aggregate and view.

## Next: pipeline-completion skill (`execute`?)

Brainstorm → spec → plan exists. The natural next piece is a skill that takes a `plan.md` (plus any phase files) and walks it task-by-task, in this session or via a fresh-context handoff. Open question: one big `execute` skill, or two small ones (`execute-task` per-task + an outer driver)?

Brainstorm the design first; carry over the crank patterns (chat-over-AskUserQuestion, headless fallback, retro append at task boundaries).
