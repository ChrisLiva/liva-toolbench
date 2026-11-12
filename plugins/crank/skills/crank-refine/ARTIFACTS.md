# Artifacts

The specs and plans this skill refines, as `crank` and `crank-lite` write them. Both pipelines keep an effort's files in `.crank/<slug>/` at the repository root, the spec as `spec.md` and the plan as `plan.md`. Tell the shapes apart by content and structure, never by filename or location. `crank` fixes its headings in a template; `crank-lite` names its sections in prose, so spell each heading the way the file does.

## Roles

Every section of a spec or plan fills one of four roles:

- **Needs**: what the user asked for. Fixed for every finder.
- **Criteria**: how the artifact says the needs are proved met. Fixed for the structure and reuse finders; the scope finder judges each criterion against the needs.
- **Design**: what the artifact commits to building, and how. Every finder's material.
- **Proof**: how the built thing gets verified. Proof leaves or changes only with the behavior it proves; no row targets proof alone. A gate, check, or threshold that pins no criterion proves nothing the needs ask for: it is a requirement the artifact added, and the scope finder's.

## Shapes

| Shape | Recognize it by | Needs | Criteria | Design | Proof |
| --- | --- | --- | --- | --- | --- |
| **crank spec** | **User stories** and **Refactor scope** sections, and a `Grounding:` header line naming a separate file | **Problem**, **User stories** | **Acceptance criteria** | **Solution**, **Technical decisions** with its **Surfaces** lines, **Refactor scope** | **Testing approach** |
| **crank-lite spec** | a problem, a proposed solution, key technical decisions, and a Grounding section inside the file; no user stories | the problem | acceptance criteria | proposed solution, key technical decisions | testing/validation |
| **crank plan** | a header carrying `Goal:`, `Gates:`, and `Base:`, and `### Task N —` blocks whose `- [ ] Behavior N:` lines each name an `Oracle:` | the spec its `Spec:` line names, read in full; with no spec, `Goal:` | that spec's acceptance criteria; with no spec, the **Coverage** table's criterion column | `Architecture:`, `Tech stack:`, **Refactor scope**, **File structure**, **Tasks**, **Stages** | every `Oracle:`, `Verify:`, `Check:`, and `Stop if:` line, `Gates:`, **Coverage**, **Smoke tests for the user** |
| **crank-lite plan** | Goal, Assumptions, ordered tasks, Verification checks, Risks, and a Grounding section inside the file | the spec its `Spec:` line names, read in full; with no spec, Goal | that spec's acceptance criteria; with no spec, Coverage's criterion column | the ordered tasks, Stages | Verification checks, Coverage, every `Stop if:` line, each Risk's check |

A spec or plan in none of these shapes, such as a hand-written design doc or one a pipeline wrote off its template, still has the four roles: map its sections onto them and state the mapping.

## Outside every row

- **Verdicts.** A `Prototype:` line records the variant the user picked and what they left out of it. A `(per project decision: …)` marker and a repo ADR record a tradeoff the user settled. No row reverses one.
- **A plan's spec.** Over a plan, the spec is settled, its decisions included. A simpler design the spec ruled out is a closing line naming the spec section. The one opening is a reuse row whose replacement the spec never cites.
- **Global Constraints.** A plan copies them verbatim from its spec, and a row changes one only by changing the spec. A constraint the spec never states is the plan's own, and open to a row.
- **Out of scope.** Cuts already made. A design piece that builds something listed there is a scope row.
- **Grounding.** The file a `Grounding:` header names (`crank`) or the Grounding section in the artifact (`crank-lite`) holds facts the author proved. It is evidence, not design: a finder may take an entry as a lead and re-finds it in the code before a row rests on it.
- **A plan's repetition.** Each task goes alone to an implementer that sees no other task, so both pipelines repeat paths, contracts, and constraints from task to task on purpose. Repetition between tasks is never a row.

## Where an accepted row lands

- **A cut** (a scope row) deletes the piece from every section that names it. In a spec it also adds a line under Out of scope with the reason, so the plan phase does not build it back.
- **A substitution** (a reuse row) rewrites the decision or task to name the replacement: a code anchor, or a dependency with the version the manifest pins. Everything that existed only to build the invention goes with it. In a plan whose spec told it to build the invention, add a line under **Updates since spec** naming the replacement and its evidence.
- **A move** (a structure row) rewrites the design sections to the simpler shape. A decision the move reverses keeps its bullet in the artifact's own form, rewritten to the new choice with its reason and what it gives up.
- **In a plan**, carry every edit through the file table, each task's files and its consumed and produced interfaces, the Stages table, and Coverage. When a task goes, renumber the rest and update every reference to a task number. A behavior that goes takes its oracle, verify step, and Coverage row with it.
- **Grounding** follows the edits: strike or rewrite any grounding entry a landed edit contradicts.

## Next command

| Shape | Next |
| --- | --- |
| crank spec | `/crank plan <spec path>` |
| crank plan | `/crank-execute <plan path>` |
| crank-lite spec | `/crank-lite plan <spec path>` |
| crank-lite plan | `/lite-execute <plan path>` |

A refined spec with a `plan.md` beside it leaves that plan describing the old design: say so, and recommend the plan command over the refined spec.
