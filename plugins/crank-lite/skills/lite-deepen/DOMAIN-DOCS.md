# Domain docs

The `.crank/` artifacts are gitignored and end with the effort. Two tracked docs outlive it: the **glossary**, which holds the project's domain language, and the **ADRs**, which hold the decisions a later reader would otherwise undo. An interview sharpens both as it runs and writes to either only on the user's yes (per project decision: a glossary entry is offered like an ADR, never written unasked, 2026-11-21). They are the only files a design phase writes outside `.crank/`: leave them uncommitted, and name each one in the phase's hand-off.

## Homes

- **Glossary**: `GLOSSARY.md` at the repository root. A repo that keeps its glossary as `CONTEXT.md` keeps that file: write there and start no second glossary. A root `GLOSSARY-MAP.md` or `CONTEXT-MAP.md` means the repo has several contexts, each with its own glossary at the path the map lists: write to the one the topic belongs to, and ask when that is unclear.
- **ADRs**: `docs/adr/NNNN-<slug>.md`, numbered one past the highest there. A repo that keeps its ADRs elsewhere, such as `docs/decisions/`, keeps that home and its naming. A context the map lists may hold its own `docs/adr/` for a decision that stops at its boundary.
- **Create lazily**: the first entry written creates a missing glossary or ADR directory. Nothing creates one ahead of it.

## In the interview

Before the first round, read the glossary and each ADR that touches the area, and say nothing of either when the repo has none. An ADR's decision stands, and no round reopens it unless the user does. As the rounds run, each of these is a numbered question in its round, your pick leading:

- **Challenge a term against the glossary.** When the user's word conflicts with its entry: "The glossary defines *cancellation* as X, and you seem to mean Y. Which is it?"
- **Sharpen fuzzy language.** When a word is vague or carries two meanings, propose the canonical term: "*account*: the Customer or the User?"
- **Test a relationship with a scenario.** When two concepts meet, invent the edge case that forces the boundary between them.
- **Check a claim against the code.** When the user says how something works and the code disagrees, state both and ask which is right. What the code does is a fact you look up.

Every artifact names a domain concept by its glossary term, never by an alias the entry lists under `_Avoid_`.

## Glossary entries

An entry reaches the glossary through a question the user answered yes to. A term question from the list above carries the entry as its recommendation, so its yes is the approval. A term an answer settles with no such question, such as a concept the user coined and defined in passing, takes one in the next round: its title `Term: <name>`, its recommendation the entry as it would be written and the file it goes to. Write the entry in the turn the yes arrives, in the user's amended wording where they gave one, before composing the next round.

A new glossary takes this shape, and an existing one keeps its own:

```markdown
# <Context name>

<One or two sentences: what this context is and why it exists.>

## Language

**Order**:
A Customer's request for goods, fixed once placed.
_Avoid_: purchase, transaction
```

- **One word per concept.** Pick the best of the words in use and list the rest under `_Avoid_`.
- **One or two sentences**, saying what the term is, not what it does.
- **This project's concepts only.** A general programming concept, such as a timeout, an error type, or a utility pattern, stays out however much the project uses it.
- **A glossary and nothing else.** No implementation detail, file path, decision, or spec text.
- **Subheadings** group the entries once clusters emerge.

## ADRs

When an answer settles a decision that passes all three tests, put its ADR to the user as a question in the next round: its title `ADR: <short title>`, its recommendation the file's path and its text as it would be written.

1. **Hard to reverse**: changing it later costs real work.
2. **Surprising without context**: a later reader of the code would wonder why it is this way.
3. **A real trade-off**: a genuine alternative lost for a reason you can name.

What passes: an architectural shape, the way two contexts integrate, a technology that locks the project in, an ownership or scope boundary, a deliberate departure from the obvious path, a constraint the code does not show, and a rejection a later reader would not expect, including a load-bearing recommendation of yours the user turned down for a reason a later effort would need. A reason that expires, such as "not now", fails.

On a yes, write the file in the turn the answer arrives, in the shape of the repo's existing ADRs, or where it has none:

```markdown
# <Short title of the decision>

<One to three sentences: the context, what was decided, and why.>
```

Add `Status` frontmatter (`proposed`, `accepted`, `deprecated`, or `superseded by ADR-NNNN`), **Considered options**, or **Consequences** only when a reader needs it. The artifact's line for the decision cites the ADR's path and keeps its own one-line why.

Completion criterion: the frontier stayed open until every entry and ADR an answer earned was asked, each one is written on its yes or dropped on its no, and no round mentions a glossary or an ADR that nothing earned.
