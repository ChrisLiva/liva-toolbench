# Retro: Grill-to-spec — merge `crank:brainstorm` + `crank:spec`

## Summary
Replaced the separate `crank:brainstorm` + `crank:spec` skills with a single `crank:spec` skill running a continuous Pocock-flavoured grill (one-question-at-a-time, code-first, inline `CONTEXT.md`, sparing ADRs). Added four verbatim Pocock companion files (LANGUAGE/DEEPENING/CONTEXT-FORMAT/ADR-FORMAT) pinned to mattpocock/skills@e74f0061. Stripped brainstorm references from plan/execute/orchestrator skills and the README. Renumbered orchestrator phases (1–4 → 1–3 for subagent execution; 5 → 4 review, 6 → 5 cleanup), dropped the brainstorm row from the phase table, and re-wired `RUN_DIR` from `dirname(BRAINSTORM_PATH)` to `dirname(SPEC_PATH)`. Bumped plugin and marketplace to 3.0.0; removed the `plugins/crank/skills/brainstorm/` directory entirely.

## Deviations from the plan
- **Task 3 — extra brainstorm reference.** Plan called out 4 `brainstorm.md` references in `plan/SKILL.md` (lines 21, 66, 74, 76). A fifth occurrence at line 19 ("If brainstorm/spec already created `crank/<slug>`") was not enumerated but would have caused the Task 9 `! grep -rn "/brainstorm\b"` check to fail. Fixed in the same Task 3 commit by replacing `brainstorm/spec` → `spec`, mirroring the Task 4 edit pattern in `execute/SKILL.md`.

## Validation evidence
- Task 9 sweep: `VALIDATION_PASS` (exit 0). All file-shape, manifest, companion-file diff, SHA-count, spec SKILL.md structural, orchestrator pipeline, and downstream checks passed.
- Per-task verify steps for Tasks 1–8 all printed `OK` and exited 0.
- Commit range: `6aa2aee..4125848` on branch `worktree-crank+2026-05-14-grill-to-spec` (8 commits).

## Notes for future work
- **Upstream Pocock SHA bump procedure.** When pinning to a newer commit, the diff loop in Task 9 (and the per-file diff in Task 1 verify) is the resync tool: re-run the fetch script with the new SHA, then re-run the diff to confirm bytes match.
- **Pocock opportunity flagged in spec § Open items.** The "run-slug vs. ADR-slug" overload and a possible ADR for the `docs/crank/<slug>/` path convention remain for a follow-up session.
- **Spec.md line 362 validation pattern.** Reviewer flagged a non-runnable `grep -F` pattern in `spec.md` (missing backticks). The plan's Task 9 sweep works around it; a future `crank:spec` re-run could fix the spec itself.

## Loose ends
- None. All ten plan tasks shipped; no scope was punted.
