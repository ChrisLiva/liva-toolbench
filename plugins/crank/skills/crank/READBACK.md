# Readback protocol

The readback shows the user the written artifact in one message, after any adversarial review has landed its edits, then folds the user's feedback into the file until the user approves it.

## Opens after the review

Open the readback once the artifact is written and, where the phase runs an adversarial review, the review's edits are in the file. The interview settled every decision, so the user reads finished items and strikes or amends them.

## The readback message

Send the whole artifact as one message, compressed:

- **Open with what the artifact commits to and what it cuts**, in two or three lines.
- **Walk every section in the artifact's order**, each as its items: the decisions, criteria, cuts, tasks, and rows themselves, one line each. A section copied unchanged from the previous phase's artifact, and the Grounding section, each get one line naming the section and its item count.
- **Show each judgment call beside the option it beat**, so a veto is a real choice.
- **Mark the review's work.** Where a review ran, tag each item the review added or rewrote `(review)`, and after the last section state how many findings the review landed and how many it refuted.
- **Draw what reads better as a picture.** Show an interface, flow, or logic as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- **Close on one line:** reply with changes, or say **done** to finish.

The test for the message: could the user strike or amend a specific item from it? If the only reply it invites is "sounds good", it describes the artifact; rewrite it as items.

## Fold in feedback

Sort each reply:

- **Approval**, such as "done" or "looks good", ends the readback.
- **A question** about an item gets an answer in chat, then the same closing line.
- **A change the user states outright**, such as strike this, reword that, or add this criterion, goes to one standard-tier subagent, resolved the way this skill resolves its other standard-tier dispatches, with the brief below.
- **A change with more than one defensible landing** is a decision: ask it as one interview round, then dispatch the answer.

<brief>
Apply the user's feedback below to the artifact at `<artifact-path>`. The feedback is settled; land exactly what it asks.

Read the artifact in full first. Land each change everywhere the artifact states the item it touches, so no two sections disagree: a struck acceptance criterion also takes the rows and lines that prove only it, and a renamed interface changes in every section that names it. A change that forces a decision the feedback does not make stays unlanded and comes back as a question.

Feedback, verbatim: <the user's reply>

Return one line per edit, `<section>: <old> → <new>`, then any question.
</brief>

When the subagent returns, send one message listing its edits and any question it raised, closed on the readback message's closing line.

The readback is done when the user approves the artifact as it stands in the file. An unanswered objection is not approval.
