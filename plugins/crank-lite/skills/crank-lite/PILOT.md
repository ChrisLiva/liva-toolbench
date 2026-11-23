# Interactive mode

A phase in interactive mode puts its question rounds, its readback, and its prototype review on a local page and reads the user's answers back from files. The `crank-pilot` command, on PATH, is the only channel. Everything else in the phase runs as written.

## Show, wait, read

Every interaction follows one sequence. `<effort-dir>` is the effort's `.crank/<slug>/` directory.

1. Write the interaction as a JSON file inside the effort directory, such as `<effort-dir>/interaction.json`, replacing the last one.
2. Run `crank-pilot show <effort-dir> <interaction-file>`. It validates the file, puts it on the page, opens the page when none is open, and exits 0 once the page is up. On exit 2, `show` printed each problem in the file; fix them and run `show` once more. Any other non-zero exit, or a second exit 2, is a fallback (see Fallback).
3. On exit 0, end the turn with the one line `On the page: <title>. Answer there, or reply here.` and run `crank-pilot wait <effort-dir>` so the session is told when it exits: as a background command where the harness reports a background command's exit, otherwise in the foreground.
4. On `wait`'s exit 0, read the response file whose path it printed. On exit 3, run `wait` again without showing the interaction again. Exits 1, 2, and 4 are a fallback.
5. After reading a response, write one short recap in chat of what was answered or marked and what happens next, and print no `❓` or `➡️` line for an interaction the page carried.

Every interaction carries four common fields:

- `kind`: `questions`, `readback`, or `prototype`;
- `phase`: `brainstorm`, `spec`, or `plan`;
- `title`: the page's heading and the `<title>` in step 3's `On the page: <title>.` line;
- `agenda`: the same agenda the phase's chat flow opens with, as `{"settled": [...], "open": [...], "current": "..."}`, each entry a decision in one short line, `current` the one this interaction asks.

Every question also carries a `body`, the markdown the page shows under its title.

Every response carries `interaction` (its number), `kind`, `via`, and `submitted_at`. `via` is `page`, `chat`, or `superseded`; a `chat` or `superseded` response holds nothing else.

## Question round

Each round goes up as a `questions` interaction carrying the agenda's settled and open decisions; the opening agenda rides on the first round's interaction. A round holds every question the phase's chat flow would ask in that round.

```json
{
  "kind": "questions",
  "phase": "spec",
  "title": "Technical decisions, round 1",
  "agenda": {
    "settled": ["Python standard library only"],
    "open": ["Where the store lives", "How a response is validated"],
    "current": "Where the store lives"
  },
  "questions": [
    {
      "id": "q1",
      "title": "Where does the store live?",
      "body": "Markdown: the decision and what it touches.",
      "recommendation": "Markdown: the pick and the trade-off it accepts.",
      "options": [
        {"id": "a", "label": "Files under the effort directory"},
        {"id": "b", "label": "A database file"}
      ],
      "recommended": "a"
    }
  ]
}
```

`options` and `recommended` come together or not at all; a question with neither is open text. Every question carries a `recommendation`, because every question leads with a pick. A glossary or ADR question takes the same shape. Single confirmations, such as a destination confirmation, an approach pick, or a prototype offer, stay in chat.

Read the response's `answers`, one per question, each `{"id", "accepted", "option", "text", "note", "attachments"}`:

- `accepted` is true when the user took the recommendation as it stood;
- `option` is the option id the user chose, or null for an answer of their own, which is then in `text`;
- `note` is an added remark on the question, whatever else was answered;
- `attachments` lists image paths relative to the effort directory; read each as part of the answer.

Land each answer exactly as the phase's chat flow lands an answer given in chat.

## Readback

The readback goes up as a `readback` interaction, the same content the readback message carries, split into fields. `artifact` is a `.md` file name directly in the effort directory. `lead` is the open-on-what-it-commits-to-and-cuts paragraph. `judgment_calls` lists each judgment call beside the option it beat, `review_landed` lists what the review landed and refuted, `decisions` holds the review's open decisions as questions of the shape above, and `edits` holds the lines the feedback subagent returned, empty on the first showing.

```json
{
  "kind": "readback",
  "phase": "spec",
  "title": "Read back the spec",
  "agenda": {"settled": ["Every decision"], "open": [], "current": "Approve the spec"},
  "artifact": "spec.md",
  "lead": "Markdown: what the spec commits to and what it cuts.",
  "judgment_calls": ["Polling over streaming: streaming needs connection state"],
  "review_landed": ["3 findings landed, 1 refuted"],
  "decisions": [],
  "edits": []
}
```

The response carries `verdict`, `version` (the version of the artifact the user read), `answers` (one per decision), and `marks`. Each mark has `n`, `type` (`comment`, `strike`, or `note`), `text`, and, except for a general `note`, `quote`, `lines`, `heading`, and `occurrence`. Each mark also carries `attachments`, image paths relative to the effort directory; read each as part of that mark.

- On `verdict` `approve`, the readback is done, and each decision's answer lands as a stated change.
- On `changes`, dispatch the feedback subagent of the readback protocol's Fold in feedback step (READBACK.md → Fold in feedback) with the response file's path in place of the verbatim feedback line, and add the sentence `Land each mark at the source lines it names in the version the response names, using its quote to find the text if the file has moved.` Each decision's answer lands as a stated change. Then write the returned edits into a new `readback` interaction for the same artifact and show it again.

## Prototype review

A prototype built as HTML variant files is handed over as a `prototype` interaction in place of the path and run command. `question` is what the variants answer, and each of `variants` has a `key`, a `name`, and a `file` relative to the effort directory.

```json
{
  "kind": "prototype",
  "phase": "spec",
  "title": "Which layout wins?",
  "agenda": {"settled": ["Scope"], "open": ["Layout"], "current": "Layout"},
  "question": "Which layout reads best for the result list?",
  "variants": [
    {"key": "A", "name": "Table", "file": "prototype/variant-A.html"},
    {"key": "B", "name": "Cards", "file": "prototype/variant-B.html"}
  ]
}
```

Read the verdict from the response: `winner` (a variant key), `take` and `leave_out` (what to take from the others and what to leave out of the winner, `nothing` counting as an answer), and `comments`, each pinned to an element of a variant with `variant`, `selector`, `leading_text`, and `text`. The verdict and each comment carry `attachments` the same way; read each as part of what it is attached to. The phase records them as its verdict step records an answer given in chat. The CLI and TUI rungs stay in chat. A user who will not choose replies in chat, and the phase records `no verdict`.

## Chat replies

A chat reply that arrives while an interaction is pending is the answer. Run `crank-pilot resolve <effort-dir> --chat` and carry on from the reply as the phase's chat flow would.

## Fallback

When `crank-pilot` is not found, `show` exits 1 or 4 or exits 2 twice, or `wait` exits 1, 2, or 4, run the phase's chat flow for that interaction in the same turn. The first fallback in a phase prints the one line `The page is unavailable; continuing in chat.` and later ones in that phase print nothing about it. The next interaction tries the page again.

## Hand-off

At a brainstorm or spec phase's hand-off, the fresh-session command in the next-step line ends with ` --pilot`, so the next session starts in the same mode. A plan phase's next-step line stays as it is.

Run `crank-pilot close <effort-dir>` once, at the plan phase's hand-off and at no earlier one.
