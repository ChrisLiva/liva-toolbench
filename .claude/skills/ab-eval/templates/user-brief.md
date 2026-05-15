# User brief — simulated user persona & answer key

> SCAFFOLDING NOTE — this is a template. Fill every `<<...>>` placeholder when copying it
> to `topics/<topic>/user-brief.md`, then delete this note. Ground every gold item in the
> real target repo (`references/authoring.md`); never invent a path or symbol.

This file is the **ground truth** for the user-player — the isolated subagent that
answers grill questions in the user role. The user-player answers **only** from this
brief; the skill-player never sees it.

---

<<ADVERSARIAL TOPICS ONLY — delete this block for an ordinary topic:>>
## What this topic is for

This is the eval's **adversarial topic**. It is deliberately shaped so the *tempting*
decision is the *wrong* one — it baits the failure mode **<<name the failure mode>>**. It
measures whether the thing under test **resists that failure when the failure is
tempting**, not "is the candidate good in general". Read a result here only as evidence
about that failure mode.

---

## Who the user is

<<Who the user is: role, expertise, what they care about, how they communicate. This
drives every un-keyed answer.>>

## The topic (verbatim, what the user types to start the grill)

> <<The exact opening line the user "types". One short paragraph. Ends naturally — e.g.
> "Let's grill it." for a grill-based skill.>>

## Persona priorities — use these for ANY question not in the answer key below

1. <<A stable preference the user-player applies to un-keyed questions.>>
2. <<…>>
3. <<…>>

## Answer key — non-obvious decisions (THE GOLD)

The user-player answers these as written. The judge scores each artifact on how many it
captured **correctly**. Each must be real and grounded in the target repo.

- **G1 — <<short label>>.** <<The decision, a one-line why, and its grounding — a real
  `path:line`, symbol, table, or documented decision. If the naive/tempting answer is
  wrong, call it out: that is the adversarial signal.>>

- **G2 — <<short label>>.** <<…>>

  <<… one bullet per gold item; aim for 6–8 genuinely non-obvious decisions …>>

## How to answer un-keyed questions

If the skill asks something not covered by the gold key, answer in character using the
persona priorities. Keep answers short and decisive. Do NOT invent new scope. If the
skill proposes a refactor, accept it only if it improves consistency with existing
patterns; otherwise decline as out of scope.

## "Just build it" — do NOT trigger it

The user is patient and wants the full grill. Never short-circuit with "just build it".
Answer every question the skill poses.
