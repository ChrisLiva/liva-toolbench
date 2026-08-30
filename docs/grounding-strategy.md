# Grounding carry strategy for crank and crank-lite

Status: v1 implemented 2026-08-30 (crank 9.22.0, crank-lite 1.17.0); v2 gated on the
rollout measurements below. This doc records the recommended design for carrying
grounded facts across pipeline phases so later phases stop re-deriving what earlier phases
already established. It was produced from a full map of both skill trees plus adversarial
critique of five candidate designs; the settled choices below each note what they ruled out.

## The problem

Each phase grounds itself by dispatching research subagents and reading the codebase, then
writes an artifact that carries decisions but not the facts under them. The next phase
re-derives those facts. The four measured leaks:

1. **Brainstorm → spec.** Brainstorm's step 1 completion criterion demands a file:line
   surface inventory and pattern exemplars (crank BRAINSTORM.md:35), and its explore brief
   additionally collects canonical helpers (BRAINSTORM.md:100), but the brief's
   deliverables list has no section to hold any of it, so it dies in conversation. Spec step 1 then re-dispatches per-layer subagents unconditionally
   (SPEC.md:58) for near-identical fact categories (compare BRAINSTORM.md:98-100 with
   SPEC.md:65-68).
2. **Plan → execute.** Plan grounding collects exemplar tests with their conventions and
   any drift from the spec (PLAN.md:47-48), and proves toolchain behavior by running it
   (PLAN.md:76), but the plan template has no slot for most of it. Execute's pre-flight pays a fresh repo-sweep subagent to rebuild
   the same facts into orientation.md (crank-execute SKILL.md:144), and every implementer
   re-greps for helpers per task (IMPLEMENTER-BRIEF.md:49).
3. **Deepen's quarantine.** Deepen's explorers produce file:line evidence, dependency maps,
   and deletion-test verdicts for every candidate, but the report holding them is a temp
   file the Hard Rule forbids re-reading (crank-deepen SKILL.md:22), and the brief forwards
   only the chosen candidate's slice. Spec then re-explores covered ground.
4. **crank-lite's chat-only lookups.** Every lite phase grounds through the lookup batches
   at INTERVIEW.md:9, but findings are folded into the recommendation and lost at every
   fresh-session handoff. Gate commands get derived three times (spec reads CLAUDE.md at
   SPEC.md:13, PLAN.md re-establishes them, lite-execute SKILL.md:58 re-discovers them).

Two kinds of re-derivation exist and get opposite treatment. **Deliberate re-verification**
is load-bearing and survives this design untouched: adversarial reviewers re-read the diff
and plan from zero (crank-execute SKILL.md:20, lite-execute's reviewer, lite-review's
validator), and the plan re-runs toolchain probes rather than asserting from memory
(PLAN.md:76). **Incidental cold-start rediscovery** is the target: facts that die only
because no artifact has a slot for them.

The pipeline already endorses the carry idiom in three places, so this design generalizes
existing precedent: the Gates line inheritance ("don't re-discover the toolchain",
IMPLEMENTER-BRIEF.md:7), the evidence-line exemption from reviewer re-verification
(PLAN.md:28 feeding PLAN-REVIEW-BRIEF.md:9), and orientation.md being admissible to
per-task reviewers without counting as pre-judgment (PER-TASK-REVIEW-BRIEF.md:6).

## The design, in one paragraph

crank-lite carries grounding **inside the artifacts it already writes**: each phase's
artifact gains a short Grounding section of one-line entries, captured at the existing
lookup chokepoint. crank, whose mid-run discoveries and deepen evidence have no artifact to
live in, gets a **per-effort file** `.crank/<slug>/grounding.md` beside brainstorm.md,
spec.md, and plan.md, written only by phase coordinators and read at the top of every
grounding step. Both pipelines share one entry grammar and one trust discipline. Adversarial
reviewers never receive either form.

## Shared entry discipline (both pipelines)

**Entry grammar.** One fact per line:

```
- <claim> | <evidence> | <phase>, <date>
```

where evidence is one of: `path:line`, `` `command` exited N: <output tail> ``, or
`searched <scope>, none found`. Facts only, never decisions: artifacts and ADRs own
decisions, and an entry may cite an ADR path but never restate it. Volatile state (branch,
task checkboxes) stays out; that is ledger territory.

**Point facts vs survey facts.** A point fact is verifiable at one location: a signature at
path:line, a command's output, a file's existence. A survey fact is a claim about a
population of files: canonical helper, convention winner, analogous features, any absence.
The distinction governs what an entry may buy:

- A covered **point fact** downgrades re-derivation to one read at the cited line or one
  re-run of the recorded command.
- A covered **survey fact** never suppresses a search. It narrows the re-search to the
  recorded scope, which is why absence entries must record the scope searched.

(per project decision: every candidate design that let survey facts skip a dispatch shipped
a path where a stale absence or superseded convention winner rode uncaught into the spec;
this rule is the fix, do not relax it.)

**Verify then trust.** No phase builds on an entry it has not confirmed this session at its
cited evidence. Confirmed: use it and cite it. Drifted: rewrite the line in place with the
new evidence and the current phase and date, and carry the drift through the existing
channel (the plan's Updates since spec). Evidence gone entirely: treat the entry as absent
and do the full derivation. Re-grounding is never suppressed, only re-priced: search
becomes lookup.

**Command entries.** Only a read-only or idempotent command re-verifies by replay. A
state-mutating command (a migration, a destructive probe) re-verifies by reading the
resulting state; mark such entries `verify by state` at record time. (per project decision:
without this rule, a later phase's verify pass replays recorded migration SQL against live
data, a data-loss path the current pipeline structurally lacks.)

**Precedence and reconciliation.** The phase artifact wins any conflict with a grounding
entry. When an artifact section absorbs a fact, delete the grounding line; the file holds
only currently homeless facts, never a second copy of the spec. Adversarial reviewers edit
artifacts in place after the coordinator banks facts, so after a review's edits land, the
coordinator strikes or rewrites any entry the review contradicted before routing on.

**Enforcement rides existing criteria.** Banking is a clause added to each phase's existing
completion criterion (the facts are already enumerated there; only the landing slot is
new), and execute's printed pre-flight callout gains one row
(`Grounding: <path> | none — N entries seeded`). (per project decision: commit f8af914
exists because an unchecked prose callout got skipped until it became a checkable step;
free-floating "remember to append" sentences are dead text.)

**Reviewers stay cold.** No adversarial brief in either pipeline receives grounding
material in v1: not the spec/plan review briefs, not per-task, re-review, or final review,
not lite's execute reviewer or lite-review's validator. Reviewer re-finding from zero is
the pipeline's error correction for wrong grounding. (per project decision: every design
that handed reviewers the file softened the adversarial pass exactly where the file is
least trustworthy; the sanctioned revisit route, if eval evidence ever supports it, is the
existing evidence-line idiom of PLAN.md:28 and PLAN-REVIEW-BRIEF.md:9, not a new rule.)

**No SHA anchoring in v1.** Entries carry phase and date, not a git SHA. (per project
decision: a path-scoped `git diff` freshness check is unsound for exactly the
highest-value entries, absences and convention winners, whose truth flips when an
unrecorded file appears; verify-then-trust plus effort-scoped lifetime covers v1. Revisit
only if efforts routinely span weeks.)

**Effort-scoped lifetime.** Grounding lives and dies with the effort (`.crank/` is
gitignored). A fact worth outliving the effort goes to the durable channels the repo
already curates: an ADR, CONTEXT.md, or CLAUDE.md, with a pointer line left behind.

## crank-lite: grounding sections in existing artifacts

No new file, no slug-timing change, and the sections ride user readback for free.

- **Capture.** INTERVIEW.md's lookup rule gains one sentence: a lookup finding that carries
  a file:line or a command output lands as one grounding line in the phase's artifact, not
  only folded into the recommendation. The trigger is mechanical (has evidence), not a
  forecast of downstream reliance. This one edit (canonical in crank-lite/, synced copy in
  lite-deepen/) instruments brainstorm, spec, plan, and lite-deepen's grill at once.
- **Sections.** brainstorm.md, spec.md, and the lite-deepen brief each gain a `Grounding`
  section holding those lines; plan.md already records what runs printed (PLAN.md's
  record-the-output rule) and extends the same section shape.
- **Reads.** The two existing entry-read lists (lite SPEC.md's read list, lite-deepen's
  read step) gain one clause: read the input artifact's Grounding section; a covered
  lookup becomes a confirm at the cited evidence; an absence entry re-runs its recorded
  search.
- **lite-execute.** The fallback gate-command discovery checks the plan's Grounding section
  before re-deriving. A detour appends one grounding line beside the Progress checkbox
  flip; lite already mutates plan.md in place, so this rides existing precedent and gives
  lite the mid-execute carry that crank needs a separate file for.
- **Readback.** One clause in READBACK.md (already hand-synced across both plugins): a
  Grounding section is carried-forward material, stated in one line, never walked for veto.
- **Exclusions.** lite-review stays pipeline-detached and its validator's independent read
  is untouched.

Footprint: roughly ten one-line edits across seven files. Only INTERVIEW.md and
READBACK.md are shared copies, and both re-sync through the existing diff loop; the other
five (lite BRAINSTORM.md, SPEC.md, PLAN.md, lite-deepen SKILL.md, lite-execute SKILL.md)
are single-copy files.

## crank: a per-effort grounding file

`.crank/<slug>/grounding.md`, flat list under one heading, same entry grammar.

- **Definition.** One block (~6 lines) added to ARTIFACT-HOME.md: the path, the entry
  grammar, the point/survey rule, verify-then-trust, precedence, and the reviewer
  exclusion. No new shared basename; ARTIFACT-HOME.md is already in the AGENTS.md diff
  loop. Copies must be added to crank-execute/ and crank-refine/, which write the file but
  carry no copy today; the diff loop's glob picks new copies up without a brace-list edit.
- **Writers.** The phase coordinator only, on the main thread, at the close of its
  grounding step, after collating subagent reports. Subagents report; they never write.
  Phases run sequentially per effort, so there is one writer at a time.
- **Readers.** Each phase's grounding step reads the file before dispatching, dispatches
  only for what it leaves unanswered, and converts covered items per the point/survey rule.

Per phase:

- **Brainstorm** banks step 1's explore returns (the surface inventory and exemplars its
  completion criterion already demands, plus the canonical helpers its explore brief
  collects). Entries bank in-thread until the brief
  is written, then flush to the file, so slug derivation stays at first artifact write and
  abandoned brainstorms leave no empty directories.
- **Spec** reads first; the per-layer dispatch becomes gap-filling plus drift checks on
  covered layers (every layer still gets a dispatch; covered items are confirm-mode, which
  keeps the completion criterion's every-layer-reported rule true). Spec banks its per-layer
  findings and ADR drift, the fact SPEC.md:56 earmarks for the plan but writes nowhere.
- **Plan** reads first, extends its existing drift framing to cover grounding entries, and
  banks proven gates, the single-test invocation pattern, toolchain probe outputs, and
  convention exemplars.
- **Execute** pre-flight seeds orientation.md's unfilled slots from entries banked at plan
  phase or later, and the sweep subagent verifies each seeded line at its citation during
  the sweep instead of skipping filled slots, so the freshness gate survives and
  orientation.md carries only facts verified this run. When a detour flips a ledger line,
  the orchestrator appends the corrected fact as a grounding entry, so a resumed run or
  later dispatch stops re-hitting the same stale symbol.
- **Deepen** banks the chosen candidate's explorer evidence, dependency map, and
  surviving-tests inventory at Flow 5, before the report is sealed.
- **Refine** reads conditionally (its input may be non-pipeline); its dispatch briefs gain
  a previously-established slot ("<fact> at <evidence>: verify it still holds"), making the
  intended staleness check an explicit delta check; returns are banked.
- **Grilling** (all grilling phases at once): the lookup-batch rule in GRILLING.md gains
  one clause, check the file before dispatching a round's lookups and bank what returns.

**Contract amendments that must land in the same commit**, or a future consistency pass
will resolve the contradiction in an arbitrary direction:

1. crank-deepen's Hard Rule ("everything downstream needs travels in the brief",
   SKILL.md:22) gains "or in the effort's grounding file; the brief stays sufficient
   alone".
2. crank SKILL.md's fresh-session self-containedness contract (SKILL.md:42) gains one
   clause naming grounding.md an optional cache that artifacts never depend on.
3. The spec completion criterion's "from its grounding subagent" wording is relaxed to
   accept "confirmed against the grounding file by its grounding subagent".

## Rollout

Ship in two stages and measure between them. Headless runs bill the subscription, so eval
trials are not a cost concern.

**v1:** the whole crank-lite variant (it is six sentences), plus crank's two safest seams:
brainstorm banking feeding spec's gap-fill dispatch, and plan banking feeding execute's
verify-while-seeding orientation stock. Both fail open: an absent or ignored file reverts
that hop to today's behavior.

**Measure:** run two or three recorded efforts with and without the mechanism. Count
dispatches retired and orientation sweeps downgraded; plant one stale entry per run and
confirm the confirm-mode dispatch or the seeding verification catches it.

**v2, gated on those numbers:** deepen's Flow 5 banking, refine's previously-established
slots, the grilling clause, and execute's detour writeback. Reviewer involvement stays out
regardless; revisit only via the evidence-line idiom with eval proof.

## Deliberately out of scope

- Adversarial reviewers receive nothing (see the settled decision above).
- No cross-effort persistence; ADRs, CONTEXT.md, and CLAUDE.md remain the durable channels.
- Decisions never enter grounding entries; readback's settled-Qn ids are referenced, not
  restated.
- crank-review and crank-test-prune stay standalone; lite-review stays detached.

## Implementation checklist

- [x] ARTIFACT-HOME.md canonical block (crank/skills/crank/), re-copied to every existing
      copy plus new copies in crank-execute/ and crank-refine/; run the AGENTS.md diff loop.
- [x] READBACK.md carried-forward clause, re-copied.
- [x] INTERVIEW.md capture sentence (crank-lite/ canonical, lite-deepen/ copy).
- [x] Phase-file clauses (v1): crank BRAINSTORM/SPEC/PLAN; crank-execute SKILL, pre-flight
      row and orientation seeding; lite BRAINSTORM/SPEC/PLAN/lite-deepen/lite-execute.
- [ ] Phase-file clauses (v2): crank-execute detour writeback; GRILLING; crank-deepen
      SKILL (Flow 5 banking); crank-refine SKILL + DISPATCH-BRIEFS.
- [x] Contract amendments 1-3 above, same commit.
- [x] Completion-criterion clauses (banking) per phase touched.
- [x] Version bumps: six strings across the two plugins, one commit (crank 9.22.0,
      crank-lite 1.17.0); re-run `codex plugin add` for both after merging.

## Example entries

crank, `.crank/bulk-export-csv/grounding.md`:

```
# Grounding: bulk-export-csv

- row export goes through serializeRow() | src/lib/export/serialize.ts:31 | brainstorm, 2026-08-30
- exemplar wiring for a new export action | src/components/ExportButton.tsx:18 | brainstorm, 2026-08-30
- no retry helper in scope | searched src/lib and src/utils, none found | brainstorm, 2026-08-30
- code drifts from docs/adr/0007: the cleanup job bypasses the repository layer | src/jobs/cleanup.ts:9 | spec, 2026-08-30
- single test file | `pnpm vitest run <path>` exited 0: 1 file, 6 tests passed | plan, 2026-08-30
- getUser() renamed to fetchUser() | src/lib/session.ts:22 | execute, 2026-08-31
```

crank-lite, where each phase's section lives in its own artifact:

```
## Grounding            (in spec.md)

- settings endpoints follow defineRoute + zod body schema | src/server/routes/profile.ts:22 | spec, 2026-08-28
- no analogous bulk-edit view | searched src/app/admin, none found | spec, 2026-08-28

## Grounding            (in plan.md)

- test gate | `pnpm vitest run` exited 0: 142 passed | plan, 2026-08-29
```
