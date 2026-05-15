# Scaffolding an eval folder

How to build a fresh, self-contained eval folder. Read this with `authoring.md` during
Step 2 of the skill.

## The eval folder layout

A scaffolded eval is fully self-contained — it holds everything a run needs:

```
<eval-dir>/
  README.md                  — what this eval measures: the thing under test, the
                               arms, the topics, and how to read a result
  config.md                  — the frozen, reproducible run config (see below)
  topics/
    <topic>/user-brief.md    — topic + persona + gold-answer key (authoring.md)
  prompts/
    runner.md                — skill-player / runner for the thing under test
    record-user.md           — recording user-player  (grill-based evals only)
    replay-user.md           — replay user-player      (grill-based evals only)
  judges/
    judge.md                 — blind scoring rubric
  fixtures/                  — frozen known-good inputs, if a topic needs them
  arms/                      — frozen baseline/ and candidate/ snapshots (per run)
  runs/                      — per-run artifacts and results
```

For a **non-grill** eval, omit `record-user.md` and `replay-user.md`.

## config.md — the reproducible run config

Write `config.md` so a later re-run reproduces the eval exactly. It records:

- **Thing under test** — what skill or prompt is being evaluated.
- **Arms** — how to obtain `baseline` and `candidate` (a git ref, a path, a branch).
- **Grill-based?** — yes → two-agent runner + record→replay; no → single runner.
- **Target repo** — absolute path, or "none". Always read-only.
- **Topics** — the list, and which (if any) is the adversarial topic.
- **Trial counts** and **model**.
- **Judge rubric version** in force.

## Scaffold steps

1. **Create the folder** `<eval-dir>/` and the subdirectories above.
2. **Copy the user-player templates** verbatim — `templates/record-user.md` and
   `templates/replay-user.md` → `prompts/`. They are already generic (substitution-based)
   and need no editing. Skip for a non-grill eval.
3. **Fill the runner template.** Copy `templates/runner.md` → `prompts/runner.md` and
   replace every `<<...>>` placeholder for this thing under test: its name, the artifact
   file(s) a trial must produce, and any thing-specific hard rules (e.g. "skip the
   skill's workspace-setup phase", "the target repo is read-only"). Leave the universal
   parts — the mailbox protocol, one-continuous-turn rule, write-artifacts-to-RUN_DIR —
   unchanged.
4. **Fill the judge template.** Copy `templates/judge.md` → `judges/judge.md` and replace
   the `<<...>>` placeholders: the artifact type, the scored dimensions (with gold
   capture ×3), the objective sub-metrics, and the rubric version. Follow
   `authoring.md` → "Authoring a judge rubric".
5. **Author each topic.** For every topic, write `topics/<topic>/user-brief.md` from
   `templates/user-brief.md`. Ground each gold item in the real target repo — spawn an
   `Explore` agent and verify every `path:line`. Follow `authoring.md` → "Authoring a
   topic". Author at least one adversarial topic unless the user declines.
6. **Seed fixtures** only if a topic's runner needs a frozen input artifact (e.g. a
   downstream skill that consumes an upstream skill's output). A topic with no such need
   has no fixture.
7. **Write `config.md` and `README.md`.**
8. **Show the user** the scaffolded tree and a summary, and get explicit confirmation
   before running Phase 0.

## Re-running and extending

- A scaffolded folder is re-runnable in place — point the skill at it and it re-reads
  `config.md`.
- **New topic:** add `topics/<name>/user-brief.md`; the answer bank is built
  automatically by the recording run.
- **Rubric change:** bump the version in `judges/judge.md`'s header per `authoring.md`.
