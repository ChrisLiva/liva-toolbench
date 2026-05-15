# Runner template — skill-player for an A/B eval

> SCAFFOLDING NOTE — this is a template. Replace every `<<...>>` placeholder when copying
> it to an eval's `prompts/runner.md`, then delete this note. Leave the universal parts
> (mailbox protocol, one-continuous-turn rule, write-to-RUN_DIR) unchanged. For a
> **non-grill** eval, delete the "file-mailbox protocol" section and the user-player
> references.

You run ONE trial of an A/B eval. You play the **skill-player**: you execute the thing
under test — **<<THING UNDER TEST: e.g. the `crank:spec` skill>>** — and produce an
artifact for a blind judge.

<<GRILL EVALS ONLY:>> You do **not** play the user — a separate isolated **user-player**
subagent does, and you exchange questions and answers with it through a **shared mailbox
directory** (the file-mailbox protocol below). You never see the answer key; you only see
answers as they land in the mailbox. This split stops the trial from grilling itself
softly.

## Inputs (provided by the orchestrator, used literally)

- `{{SKILL_DIR}}` — the frozen arm directory holding the thing under test. Resolve every
  relative link inside the thing to this directory.
- `{{TOPIC_LINE}}` — the verbatim line the user "typed" to start.
- `{{TARGET_REPO}}` — the codebase to work against (or "none").
- `{{RUN_DIR}}` — all artifacts you produce go here.
- `{{RELAY_DIR}}` — <<GRILL EVALS ONLY>> the shared mailbox directory
  (`{{RUN_DIR}}/relay/`). The ONLY channel between you and the user.

You are **not** given the user-brief or any answer key, and you have **no `Agent` or
`SendMessage` tool**. Read only inside `{{SKILL_DIR}}`, `{{TARGET_REPO}}`, and
`{{RUN_DIR}}` — never go looking through the eval harness (its `topics/`, other `arms/`):
that would leak the answer key and void the trial.

## Hard rules (these OVERRIDE the thing under test where they conflict)

1. `{{TARGET_REPO}}` is **strictly READ-ONLY** — Read/Grep/Glob/`git log` only. Never
   Write/Edit/branch/worktree there.
2. Every file the thing under test would write goes into `{{RUN_DIR}}`, never into the
   target repo.
3. **You do not answer your own questions** <<GRILL EVALS ONLY>> — every question goes
   out via the file-mailbox protocol; act only on the mailbox answer. Never invent the
   user's answer.
4. Never use `AskUserQuestion`. Never attempt `Agent` or `SendMessage` — you do not have
   them.
5. <<THING-SPECIFIC RULES — fill in: e.g. "Skip the skill's workspace-setup phase
   entirely", "do adversarial review inline, do not spawn a nested subagent", "force a
   single-file artifact even if the thing suggests a split". Delete if none.>>

## The file-mailbox protocol  <<GRILL EVALS ONLY — delete this whole section otherwise>>

You cannot message the user-player directly. You exchange files in `{{RELAY_DIR}}`. Run
the **whole trial in one continuous turn** — never end your turn to ask; block on a Bash
poll loop until the answer appears. Use a zero-padded counter `NN` from `01`.

- **Asking a question:**
  1. Append the full question — options, your recommendation, your reasoning, the
     invitation to disagree — to `{{RUN_DIR}}/transcript.md`.
  2. Write that same text to `{{RELAY_DIR}}/q-NN.md` with the `Write` tool.
  3. Run Bash `touch {{RELAY_DIR}}/q-NN.ready` (the marker MUST come after the `.md`).
  4. Block: run Bash (pass a `timeout` of `600000`)
     `until [ -f {{RELAY_DIR}}/a-NN.ready ]; do sleep 3; done`. If it returns early, run
     it again until the file appears.
  5. Read `{{RELAY_DIR}}/a-NN.md` — the user's verbatim answer. Append it to
     `transcript.md`, act on it, continue.

  Ask exactly **one** question at a time — never batch, never write `q-(NN+1)` before
  `a-NN` arrived.

- **Finishing:** when all artifacts are written, run Bash
  `touch {{RELAY_DIR}}/DONE.ready`, then end your turn with:

  ```
  === TRIAL COMPLETE ===
  <3-sentence report: questions asked, artifact summary, anything notable>
  ```

## Procedure

1. **Execute the thing under test.** Read it from `{{SKILL_DIR}}` and execute it
   faithfully against `{{TARGET_REPO}}`, starting from `{{TOPIC_LINE}}`. Every question
   goes out via the mailbox <<GRILL EVALS ONLY>>; record question + answer verbatim in
   `transcript.md`. Do not skip, shortcut, or soften.
2. **Write artifacts to `{{RUN_DIR}}`:**
   - `<<ARTIFACT FILE(S) — e.g. spec.md / plan.md / diff.patch>>` — the thing's output.
   - `transcript.md` — <<GRILL EVALS ONLY>> every question and every mailbox answer.
   - `meta.md` — arm label, question count, whether the mailbox reached a user-player
     (answers came back as `a-NN.md` files you did not write yourself), and anything that
     went wrong.
3. End with the `=== TRIAL COMPLETE ===` block above (or, non-grill, a 3-sentence report).
