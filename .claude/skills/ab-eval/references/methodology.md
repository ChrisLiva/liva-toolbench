# Methodology — running A/B eval trials

The authoritative how-to for the trial mechanics. The `SKILL.md` is the spine; this file
is the detail. It is eval-agnostic: it never names a specific skill, topic, or repo.

## What an eval is

An **eval** compares two **arms** — `baseline` and `candidate` — of one *thing under
test* (a skill or a prompt). For each **topic** (a scenario), each arm runs N **trials**.
A trial executes the thing under test and leaves an artifact. Artifacts are **blind
judged** against a rubric. Scores are aggregated A/B.

The question an eval answers is not "is the candidate good?" but "did the change from
baseline to candidate measurably move the metric, beyond run-to-run noise?"

## Independence and isolation

- Each topic is scored independently, so a regression can be localised.
- A trial must not be able to grade itself leniently. For a grill-based thing under test,
  the agent running the skill (the **skill-player**) is kept in a separate context window
  from the agent simulating the user (the **user-player**), and the skill-player never
  sees the answer key. See "The two-agent runner" below.
- The **orchestrator** (the `ab-eval` skill) only spawns agents and waits. It is never in
  the data path — it cannot compose, soften, or leak an answer.

## The two-agent runner (file-mailbox relay) — grill-based evals

When the thing under test interviews a user, each trial uses two subagents in separate
context windows:

- **skill-player** (`prompts/runner.md`) — executes the thing under test, grills, writes
  the artifact. Given only the verbatim topic line; never the answer key or answer bank.
- **user-player** — answers grill questions; never sees the skill-player's reasoning or
  code exploration.

No agent in this environment can message another (`SendMessage` is unavailable to
subagents *and* to the orchestrator). The two agents communicate through a **shared
mailbox directory**, `<RUN_DIR>/relay/`:

- `relay/q-NN.md` — question text, written by the skill-player (`NN` zero-padded from
  `01`).
- `relay/q-NN.ready` — empty marker, `touch`ed *after* `q-NN.md` is fully written.
- `relay/a-NN.md` — answer text, written by the user-player.
- `relay/a-NN.ready` — empty marker, `touch`ed *after* `a-NN.md` is fully written.
- `relay/DONE.ready` — `touch`ed by the skill-player when the trial ends.

The `.ready` marker exists so a reader never reads a half-written file: poll for the
marker, then read the `.md`. The skill-player runs its whole trial in **one continuous
turn**, blocking on a Bash poll loop between questions — it never ends its turn to ask.
The trial is done when the skill-player ends with `=== TRIAL COMPLETE ===`; a user-player
ending first just means it saw `DONE.ready`. Each trial has its own `relay/` directory,
so many trials can run in parallel without collision.

A non-grill thing under test (pure input→output) uses a single runner and no mailbox.

## Record → replay (paired transcripts)

Re-simulating the user-player fresh in every trial is the dominant source of run-to-run
noise: two same-arm trials are never the same conversation, because the user paraphrases
answers differently and the skill-player asks different things. That nuisance variable
can swamp the A/B signal.

**Fix:** record the grill **once per topic**, freeze the answers into an **answer bank**,
and replay that bank to every scored trial of both arms — so the thing under test is the
only variable. Run it in two phases.

### Phase R — recording run (once per topic, unscored)

A normal two-agent trial with the **baseline** arm and the **recording user-player**
(`prompts/record-user.md`). The recording user-player sees the topic's `user-brief.md`,
answers the grill, and writes `runs/<ts>/answer-bank-<topic>.md`. The bank has three
parts:

1. **All gold answers G1–Gn**, written verbatim from the brief — *whether or not the
   recording grill asked about them*. This is load-bearing: a missing gold answer would
   send a later arm to the persona fallback and unfairly tank its gold capture.
2. **Recorded un-keyed Q&A** — every non-gold question the recording grill asked, with
   its answer, tagged by subject.
3. **The persona-priorities block**, copied verbatim — the only input the fallback uses.

The recording run's scored artifact is discarded; only the bank matters. The baseline arm
is used because the bank captures *answers* (persona/brief-derived, arm-independent) and
the baseline is the stable reference for which un-keyed questions to pre-record.

### Phase 1 — scored trials (replay)

Every scored trial of **both arms** uses the **replay user-player**
(`prompts/replay-user.md`), which reads *only* the answer bank — never the brief. It
matches each incoming question to a bank entry **by topic, not by position** (the
skill-player is stochastic and will not ask in the recorded order) and serves that answer
verbatim. On a question that matches no entry, it composes a **persona fallback** from
the bank's persona-priorities block only; it does not void the trial. It logs each
question as `SERVED` or `FALLBACK` to `relay/replay-trace.md` — an asymmetric fallback
rate between arms is a divergence signal worth reporting.

Both arms share the byte-identical bank, so equivalent questions get byte-identical
answers. What is frozen is the **answer policy**, not the literal transcript: question
order and selection still vary with the skill-player, and that residual is the
irreducible variance the eval is meant to observe. The skill-player's mailbox protocol is
unchanged — it cannot tell a live user from a bank server, which is why the swap is cheap.

## Blind judging

After all of a topic's trials finish, shuffle their artifacts into blind labels
(`A`, `B`, `C`, …) in a `judge-<topic>/` directory, copy any companion artifacts under
the matching label, and write a private `mapping.md` (label → run-dir → arm). Spawn a
judge subagent briefed verbatim with the eval's `judges/judge.md`. The judge **never**
sees `mapping.md` or run-dir names — it scores on merit only. Decode the labels via
`mapping.md` only at the aggregation step.

## Noise-floor calibration and trial counts

- Default trials: **3 per arm per topic** for a grill eval where the arms differ;
  **2** for a noise-floor check (byte-identical arms) or a non-grill eval.
- A byte-identical-arms run measures the harness's own **noise floor** — the scatter
  between trials that *should* score the same. Any A/B gap smaller than that floor is
  unresolvable; report it as "within noise / bands overlap", not as a finding.
- Replay (Phase R) removes the answer variance but not the skill-player's
  artifact-authoring variance, so n>1 still earns its keep — each retained trial just
  carries far more power than it would under an unpaired design.
- Raising n fights noise by brute force; it is the expensive lever. Prefer record→replay
  and an adversarial topic first.
