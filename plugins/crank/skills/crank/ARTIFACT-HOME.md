# Artifact home

Where every pipeline artifact lives.

- **One directory per effort** — `.crank/<slug>/<artifact>.md` at the repository root (`git rev-parse --show-toplevel`). Create `.crank/` if missing, with a `.crank/.gitignore` containing `*`.
- **One slug per effort** — `<slug>` is two to four kebab-case words naming the effort (`dark-mode-toggle`), derived once, at the effort's first file, artifact or mock. Handed an earlier phase's artifact, or continuing in this session, write into the effort's existing directory.
- If `.crank/<slug>/` already holds a *different* effort — its `plan.md`, `spec.md`, or `brainstorm.md` describes other work — use `<slug>-2`, `<slug>-3`, …; the existing directory keeps its name and contents.
- Only outside a git repo, fall back to `${TMPDIR:-/tmp}/crank-<slug>/<artifact>.md` and say so.
- Tell the user the path once. Any mock a phase produces for the user to react to (a prototype HTML file, a sample output) goes under `.crank/<slug>/` only, and no phase deletes or moves it until the plan's execution finishes, because later phases read it at the path an artifact recorded.

## Grounding

Facts a phase proved, carried so the next phase re-verifies them at a citation. Home: in crank-lite, a `## Grounding` section in the phase's artifact; in crank, `.crank/<slug>/grounding.md` — one flat list, written only by the phase coordinator after collating subagent returns.

- **Entry grammar** — one fact per line: `- <claim> | <evidence> | <phase>, <date>`, where evidence is an **anchor** (`` `<path>` → `<symbol>` ``, per [VOCABULARY.md](VOCABULARY.md) → Verification language), `` `command` exited N: <output tail> ``, or `searched <scope>, none found`. Facts only: decisions live in artifacts and ADRs; an entry may cite an ADR path, never restate it. Volatile state (branch, task checkboxes) stays out.
- **Point vs survey.** A point fact is verifiable at one location — a signature, a command's output, a file's existence — so re-derivation shrinks to one read at the citation or one re-run. A survey fact claims a population — canonical helper, convention winner, any absence — and never suppresses a search, only narrows it to the recorded scope. (per project decision: letting survey facts skip a dispatch shipped stale absences into the spec.)
- **Verify then trust.** No phase builds on an entry unconfirmed this session at its cited evidence. Confirmed: use and cite it. Drifted: rewrite the line in place with the new evidence, phase, and date. The phase that writes the plan also carries the drift into the plan's **Updates since spec**; an earlier phase keeps the rewritten entry in its own artifact's grounding, and a later phase follows its own skill's drift rule. Evidence gone: treat the entry as absent and derive in full. A state-mutating command is marked `verify by state` at record time and re-verifies by reading the resulting state, never by replay. (per project decision: replaying recorded migration SQL against live data is a data-loss path.)
- **The artifact names the file.** Every crank artifact — brief, spec, plan, deepen brief — carries a `Grounding: <absolute path>` header line once `grounding.md` beside it holds entries, added or refreshed when the phase flushes them. A reader handed only the artifact follows it before re-deriving anything the file already proves.
- **Precedence.** The phase artifact wins any conflict. When an artifact section absorbs a fact, delete its grounding line: grounding holds only facts no artifact states. After an adversarial review's edits land, strike or rewrite any entry the review contradicted.
- **Reviewers stay cold.** No adversarial review brief receives grounding material, and a reviewer reads past the artifact's `Grounding:` line without opening the file; its re-finding from zero is how the pipeline corrects wrong grounding.
- **Effort-scoped.** Grounding lives and dies with the effort; entries carry phase and date, never a git SHA. A fact worth outliving the effort goes to an ADR, `CONTEXT.md`, or `CLAUDE.md`, with a pointer line left behind.
