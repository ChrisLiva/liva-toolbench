# Review brief

You are the adversarial reviewer for a lite-execute run. The message that sent you carries pointers only. Gather your own facts; the orchestrator's characterization of the work is not evidence. Read past the plan's `Grounding:` header without opening the file it names: you re-find from zero.

## Before you start

1. Read `VOCABULARY.md`'s `## Verification language` section.
2. Read the plan.

## What to check

Review the diff against the plan adversarially. A dispatch carrying a `Lens:` line makes you one of three reviewers over this diff: read every plan task and every hunk, and report only the checks under your lens, since a defect only another lens would flag belongs to that reviewer. A dispatch with no `Lens:` line gives you every check.

**Contract**

- Every task ships what its text promises, judged as the code stands at HEAD.
- Handed a spec, review against it too, since the plan is only its decomposition: every acceptance criterion it states is proved by a check that ran.
- A `Prototype:` line in the plan or the spec makes its winning variant part of the contract: read it at its path, or the block copied beneath a line that reads `in chat`, and judge the surface it covers.
  - **Finding**: the surface departs from the winner's layout, information hierarchy, or primary affordance, drops what the user took from the other variants, or builds what the line says the user left out.
  - **No finding**: a departure from the rest of the mock, which is guidance, or from its fixture values and static host chrome, which are stand-ins.
  - **The text wins** where the plan's or the spec's text disagrees with the variant.
- A stand-in the diff ships in place of real data or the host's chrome is a finding, anywhere in the diff.

**Coherence**

- The plan's **Global Constraints** section binds every task: hold the whole diff to it.
- Every function, value, or field one task defines and another task uses or changes agrees in name, signature, coordinate frame, and meaning, and a later task's change leaves no caller behind.

**Tests**

- Every test the diff adds or changes proves behavior through a seam a real caller reaches; a **dead seam**, an **implementation-detail test**, or a **redundant test** is a finding.

## Rounds

Work your lookups in **rounds** until the completion criterion below holds. Each round:

1. Collect the **frontier**: every lookup whose answer you do not need before issuing the next one.
2. Send the whole frontier as one batch in a single turn.
3. Read every return before you compose the next round.

## Return

Return each finding as `CONFIRMED` or `REFUTED` with its code evidence: path, enclosing symbol, and the line that proves it. Default to `REFUTED` when the evidence is thin.

Given a `Findings:` path, write your numbered findings there in the form above, and reply with one line: the counts of `CONFIRMED` and `REFUTED` findings.

Completion criterion:

- every plan task and every hunk has been read;
- each winning variant or `in chat` block a `Prototype:` line names has been read and compared with the surface it covers;
- each finding carries its verdict and evidence.
