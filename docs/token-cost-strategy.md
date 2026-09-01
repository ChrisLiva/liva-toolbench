# Token cost strategy for crank and crank-lite

Status: measured 2026-08-30 against crank 9.23.0 / crank-lite 1.17.0. **Every change below —
A through G — landed in crank 9.24.0**, E and G ahead of the re-measure they were originally
gated on. Every figure below is the pre-landing baseline the re-measurement compares against. Figures come from 7 end-to-end pipeline runs and their 42 subagent threads,
drawn from 192 sessions carrying crank activity. This doc records what a run costs, which
changes are worth making, and which text a cost pass must leave alone.

## The one insight

**Crank's own prose is 0.3% of a run.** Every `SKILL.md`, phase file, template, and shared
reference a run loads costs 0.06M of a 20.72M bill. Six prior slimming passes have already
run (`a2e4c63`, `19221b7`, `3de408e` among them); a seventh would move nothing.

The cost is **resident** context — tokens that enter a thread and are re-billed on every
later request in it. Nothing compacts in any measured run, so a token that lands at request
5 of 130 is billed 125 more times. That makes the levers, in order:

1. How many requests a thread makes while carrying a large context.
2. How large the context is when it starts being re-billed.

Adversarial review is 53.8% of the bill, and over half of that is one thread making 50-75
requests to apply one edit each. That is the whole opportunity.

## How to measure

Three properties of the transcript format each skew a naive measurement by ~3x. Cache these;
they are not discoverable from the file without hitting them.

1. **Deduplicate by `requestId`.** Claude Code writes one JSONL record per *content block*
   and repeats the same `usage` object on each. Summing per record over-counts 2.6-3.1x — in
   `cf7f9efe`, 123 assistant records carry 47 distinct `requestId`s.
2. **Read the subagent threads.** `isSidechain` is `0` in every transcript because subagent
   turns live in a sibling `<stem>/subagents/**/*.jsonl`. Those threads are **71.6%** of the
   bill; a main-transcript measurement sees a quarter of the spend.
3. **Key file reads on the full path.** Keying on `basename()` merges nine different
   `SKILL.md` files into one and invents a re-read problem. There is none: across the 7 runs,
   44 skill-file reads hit 44 distinct paths.

## What a run costs

| | requests | billed input | share |
| --- | --- | --- | --- |
| Main thread | 40.6 mean | 5.88M | 28.4% |
| Subagents | 132 mean | 14.84M | 71.6% |
| **Per phase run** | **172** | **20.72M** | |

Output is 127.5k/run — 1.35% of tokens, roughly a third of the dollars, and carries no
redundancy: every `.crank/` artifact is written exactly once, rewrite bytes are 0 in all
seven runs.

Where the 20.1M attributed tokens go:

| cause | tokens | share |
| --- | --- | --- |
| Adversarial review subagents | 11.15M | 53.8% |
| — of which, requests whose only tool call is one `Edit` | 5.98M | 28.9% |
| Grounding and verify subagents | 3.37M | 16.3% |
| Main-thread grounding sweeps | 3.11M | 15.0% |
| Readback and grilling | 1.08M | 5.2% |
| Artifact writes | 0.65M | 3.1% |
| Task bookkeeping | 0.34M | 1.6% |
| Dispatch turns | 0.31M | 1.5% |
| Skill and reference reads | 0.06M | 0.3% |

## Land now

Four prose edits, ~5.2M/run. None removes a rubric item. Only C touches a hand-synced file.
All four are in crank 9.24.0, each **Done when** below met by the shipped text — minus the
rationale each edit was drafted with, cut on review as noise inside an otherwise clear
instruction.

### A. The reviewer applies its edits in **two passes**

Worth ~5.0M/run averaged, 8-14M on an edit-heavy plan phase.

`PLAN-REVIEW-BRIEF.md:34` lists eighteen flag categories, then says to edit the plan file
"to fix every item you flagged." With no batching rule the reviewer issues one `Edit` per
finding, and each request re-bills its whole ~200-250k accumulated context. Across six runs,
**41.2% of all subagent tokens** sit in requests whose only tool call is a single `Edit`:

| reviewer | requests | billed | edit-only requests | their cost |
| --- | --- | --- | --- | --- |
| `0bf8492d` plan | 133 | 26.83M | 75 | 17.04M (63.5%) |
| `e7f8d86c` plan | 96 | 17.28M | 50 | 10.56M (61.1%) |
| `cf7f9efe` plan | 80 | 16.94M | 50 | 11.70M (69.1%) |
| `ddbe2e3f` plan, batched | 29 | 3.24M | 0 | — |

`ddbe2e3f` batched its edits unprompted and came in **8x cheaper on the same instruction**.
The shape is already reachable; the brief just never asks for it.

**Where:** `PLAN-REVIEW-BRIEF.md:34` and `:41`; mirror in `SPEC-REVIEW-BRIEF.md`.

**The edit:** two passes. The reviewer collects every finding and writes the list to its own
scratch file, then applies them at **one edit per task block** (per section, in the spec
brief). Add the bound to the `Done when` line at `:38`.

**Done when:** the brief states both passes, names the scratch file the finding list lands
in, and its `Done when` line carries the one-edit-per-block bound.

**Bound:** per-block edits, not a whole-file `Write`. `ddbe2e3f` rewrote the file wholesale,
which on a 68-80KB plan can silently drop content. Per-block still collapses 50-75 requests
to 8-14 and keeps the blast radius inside one task.

### B. Grounding returns get a per-item budget

Worth 150-280k per grounding-dispatching phase.

The four report bullets at `PLAN.md:43-56`, `SPEC.md:64-77`, and `BRAINSTORM.md:93-105` set
no length bound. Returns land at 16-47KB each and stay resident for the rest of the thread —
0.57M/run, 9.7% of the main thread. Fenced code is 26% of those bytes.

**Where:** the closing paragraph of each brief — `PLAN.md:53`, `SPEC.md:74`,
`BRAINSTORM.md:102`.

**The edit:** cite `file:line` rather than pasting; quote source only where the exact text is
the answer; aim under 150 words per item asked about; gate-command output stays verbatim and
does not count against the budget.

**Done when:** all three briefs carry the budget, and each states the verbatim carve-out.

**Bounds, all three load-bearing:**

- **Per-item, never a flat cap.** `PLAN.md:48` demands exact signatures and `:51` demands
  verbatim gate output; both are completion criteria at `:88` and `:90` (`19221b7`). A flat
  "under 400 words" breaks them — `dnd-parsers`' 30,484B return answered seven numbered
  topics, of which a flat cap drops six.
- **Keep it out of `SUBAGENT-TIERS.md`.** Six skills carry that copy, and a blanket cap
  contradicts `REVIEW-BRIEF.md:41` (unbounded per-finding format) and
  `IMPLEMENTER-BRIEF.md:115` (its own ~15-line cap on a different schema).
- **Leave `BRAINSTORM.md:109-119` alone.** The research brief returns library comparisons
  with source links, where `file:line` does not apply.

**Size it against the current state, not the measured runs.** Every measured run predates
`19221b7`'s structured `Report:` block. The one post-brief run returns 8-12KB — a 2.3x cut
already banked — so the target is ~41KB per phase, not the 128KB the old runs show.

### C. A status flip rides with adjacent work

Worth 108-225k/run.

26 requests across 9 runs contain only task-tracker calls: 2.89/run, 3.09M. Half are
structurally removable; the other half precede a text-only message, and a message carrying a
tool call cannot end the turn.

**The repo already solved this once.** `crank-execute/SKILL.md:92` caps the list at one
tracked task per plan task — `462b3de`, written after reviewing a real 8-task run. The
coordinator lacks that cap, which is why `ddbe2e3f` ran 13 tracked tasks in one phase.

**Where:** `crank/SKILL.md:37`, and its mirrors at `crank-refine/SKILL.md:46` and
`crank-deepen/SKILL.md:29`.

**The edit:** cap the tracked list at user-visible milestones, and state that a status flip
rides with the work adjacent to it.

**Done when:** all three carry the cap, phrased so a standalone status message before a
question or hand-off stays available.

**Bounds:** keep the standalone flip reachable — suppressing it regresses `62d5b74`'s stated
purpose at exactly the moments the user is about to see a question. Keep the wording
harness-agnostic: no crank skill names a harness tool today
(`grep -rnE '\b(TaskCreate|TaskUpdate|AskUserQuestion)\b' plugins/` returns zero), and
`CLAUDE.md:178` requires that.

### D. The two References reads land in one turn

Worth ~26k/run.

`PLAN.md:39` and `:60` each issue a read, as do `SPEC.md:35` and `:39`. Neither read informs
the other, and transcripts show them already landing back-to-back at identical context.

**Where:** the head of `## References` in `PLAN.md` and `SPEC.md`.

**The edit:** one line — read both together, in a single turn, before step 1.

**Done when:** both files carry the line.

**This is the only read-batching change worth making.** 4 of 7 runs never read
`VOCABULARY.md` at all, and 5 of 245 requests issue more than one `Read`.

## Landed with A–D, ahead of the re-measure

The doc gated these on landing A, re-measuring a plan phase, and confirming the reviewer's
finding count held. They shipped in 9.24.0 anyway, on the user's call, so that re-measure now
verifies six changes at once instead of gating two. Each risk note below is what it verifies.

### E. A deterministic pre-gate for the reviewer

Est. 1-3M per plan phase. Past the edit loop, reviewers spend 22-72 `Bash` calls probing,
and some of that is enumerable rather than judged — the coordinator in `cf7f9efe` already
invented the deterministic form in one call:
`tasks: 8 / coverage rows: 58 / placeholders: 0 / criteria 1..58`.

Make it a `PLAN.md` step-5 completion check, then drop the *enumeration* half of "coverage
holes" and "placeholder language" from `PLAN-REVIEW-BRIEF.md`, keeping the judgment half
("rows whose verify step doesn't exercise the behavior").

**The risk that makes this second:** review is 54% of the bill because it does real work.
`3de408e` records a prior trimming pass refusing 34 of 153 proposed cuts on a load-bearing
test.

### G. crank-execute's artifact flow

Est. 8-10M on a large execute run. Not verified to the standard of A-D.

- **Briefs quote the plan task verbatim** (`IMPLEMENTER-BRIEF.md`'s old `## Task text`). Briefs
  averaged 15.7KB; a bounded pointer keeps only the `- [ ] Behavior N:` lines the TDD rule
  at `:63` keys off. ~27k output + 2.3M cache-read.
  **Landed as:** a `## Task` block naming the plan path plus `### Task <N> — <title>`, over the
  behavior lines. The implementer reads that one section — already allowed by `orientation.md`'s
  Run boundaries line, now narrowed to "and read no other part of it."
- **Reviewer returns are uncapped** while the implementer's is capped at ~15 lines
  (`IMPLEMENTER-BRIEF.md:115`). Give the three review briefs the same shape. ~700k.
  **Landed as:** each brief writes its full review to a dispatch-named path (`task-<N>-review.md`,
  `final-review.md`) and returns the check lines, the verdict, and one line per finding. The
  read-only rule in all three gained a carve-out for that file, or the rule forbids the write.
- **The orchestrator holds the whole 109KB plan** for ~150 turns. Delegating the
  task-by-task walk is worth ~3.7M and is the riskiest item here —
  `crank-execute/SKILL.md:111-114` is a real gate.
  **Landed as:** step 1 reads the plan's frame (header, Global Constraints, Refactor scope, File
  structure, Coverage, Out of scope, task titles) and dispatches the task-by-task walk at the
  standard tier; each task body is read at step 3 as its turn comes. The gate itself is
  unchanged — both categories go to the walker verbatim, and findings still stop the run in one
  batched question. **Watch on re-measure:** whether a dispatched walker finds the
  plan-mandated defects an orchestrator holding the whole plan used to catch.

## Projection

| | main | subagents | per run | change |
| --- | --- | --- | --- | --- |
| Today | 5.88M | 14.84M | 20.72M | — |
| After A+B+C+D | ~5.5M | ~9.8M | ~15.3M | −26% |
| After E and G | ~5.3M | ~7.5M | ~12.8M | −38% |

On an edit-heavy plan phase the spread is wider: `0bf8492d` costs 34.9M today, of which
17.0M is its edit loop. A alone takes that run to ~21M.

## Preserve

Each region below was added by a commit that fixed an observed failure — it is
**load-bearing**, and a cost pass that removes it trades a regression for a saving. Verify
with `git log -S'<phrase>'` before touching anything that looks redundant.

| Region | Commit | The failure it prevents |
| --- | --- | --- |
| `crank/SKILL.md:37` live task tracking, "not in a batch" | `62d5b74` | The old fenced checklist was reproduced verbatim as plain text and never updated |
| `crank/SKILL.md:36` load one phase at a time, never at triage | `b602602` | Replaced a preload block; a preload reverses it |
| `READBACK.md` pacing and the 4-message cap | `7dd6aa1`, `60c0c9b` | From the 2026-08-07 usage retro. Post-cap runs already end at one pause via the standing exit at `:20` |
| `crank-execute/SKILL.md:155` brief *file*, not pasted task text | `d055b31` | Crank's own statement of the resident-cost model, and why measured re-reads are near zero |
| `crank-execute/SKILL.md:92` lean task list | `462b3de` | Written after reviewing a real 8-task run; the model for change C |
| `crank-deepen/SKILL.md:22` never re-read as a source of truth | `a80f52e` | |
| `crank-review/SKILL.md:105` point subagents at it, don't reproduce it | `a52e7a6` | |
| `crank-review/REVIEW-BRIEF.md:4` "Scope your reading to the diff plus targets" | `a52e7a6` | Already bounds the tree-wide read a cost pass would try to batch |
| `VOCABULARY.md` / `SUBAGENT-TIERS.md` as single sources | `02491ff` | The copies had already drifted — Depth had 3 definitions, Deletion test 2 |
| Real copies of shared references, never symlinks | `c0036a4` | The Codex installer drops symlinks when snapshotting, so the files vanished from Codex installs |
| `docs/grounding-strategy.md:170-172` single-writer rule | `d20868f` | Grounding dispatches run 4-8 in parallel |
| `PLAN.md:48` exact signature, `:51` verbatim gate output | `19221b7` | Both are completion criteria at `:88` and `:90`; any return cap exempts them |
| `PLAN.md:71` "so the executor returns `BLOCKED` instead of improvising" | `e1038b0` | Consumed at `IMPLEMENTER-BRIEF.md:48`. `PLAN-TEMPLATE.md` does not carry it, so moving the rule into the template drops it |
| Point-of-use loading of `GRILLING.md` / `READBACK.md` | `b4dee30` | Extracted so they load only at the step that needs them; inlining measures as a net loss of ~59k/run |
| Verbatim rubric copies into the brief dir before any task lands | `d308565` | Pointing reviewers at the plugin's rubric loses the freeze-before-diff property |

## Ruled out

Six proposals that measurement kills. Each is the kind a fresh cost pass proposes first.

- **A seventh "deduplicate the shared rules" slim.** Six have run, each explicitly preserving
  every rule and threshold. The remaining duplication is the deliberate real-copy shape
  `c0036a4` mandates, and skill prose is 0.3% of the bill.
- **Anything addressing re-reads.** Every skill file is read exactly once per run — 44 reads,
  44 distinct paths. An instruction against re-reading adds resident bytes to recover zero.
- **Shortening readback for tokens.** Halving *all* assistant prose saves 47.6k/run (0.8% of
  tokens), and 84% of that prose is the numbered veto lists that constitute the approval gate.
- **Splitting `crank-execute/SKILL.md` into phase files.** A `Read` result is resident exactly
  as a skill body is; moving 7,898B relocates zero bytes and adds two round trips.
- **Deduplicating the shared reference copies on disk.** No session loads two copies together
  across 16 runs, so the 25,420 tokens of on-disk duplication cost nothing at runtime.
- **A size gate on triage.** crank triages on how settled the ask is, never how big
  (`crank/SKILL.md:26-32`), while `crank-execute` makes the size call twice (`:139` solo
  shape, `:161` low-risk review skip). The asymmetry is real, but all seven measured runs are
  large efforts — plan phases against finished specs producing 8, 11, and 14 tasks — so the
  corpus holds no instance of the overpay a gate would fix. Revisit if a full crank run on a
  one-file fix appears in a transcript.

## Landing checklist

- Bump the version per `CLAUDE.md` → *Bumping a plugin version*: three files for a
  cross-harness plugin, and the marketplace-catalog copy is the easy miss.
- A, B, D, E, and G touch no hand-synced reference file. C edits `crank/SKILL.md:37` plus its
  two mirrors, which are synced by hand.
- Every change here is plain prose with relative links, so it stays harness-agnostic: no
  `${CLAUDE_*}`, no `@file`, no bang execution, no harness tool names.
