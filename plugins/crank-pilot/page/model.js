// The question round's data rules. No DOM here: every function takes questions and a form and returns data.
// A form is {[questionId]: {choice: <option id> | "own" | null, text, note, attachments}}.

const hasOptions = (question) => Array.isArray(question.options) && question.options.length > 0;
const strings = (value) => (Array.isArray(value) ? value.filter((item) => typeof item === "string") : []);

// One question's entry, read defensively: a draft is whatever an earlier page wrote.
function entry(question, raw) {
  const given = raw && typeof raw === "object" ? raw : {};
  let choice = null;
  if (hasOptions(question)) {
    const known = given.choice === "own" || question.options.some((option) => option.id === given.choice);
    choice = known ? given.choice : question.recommended;
  }
  return {
    choice,
    text: typeof given.text === "string" ? given.text : "",
    note: typeof given.note === "string" ? given.note : "",
    attachments: strings(given.attachments),
  };
}

export function formFrom(questions, draft) {
  return Object.fromEntries(questions.map((q) => [q.id, entry(q, draft?.[q.id])]));
}

export function answersFor(questions, form) {
  return questions.map((q) => {
    const { choice, text, note, attachments } = entry(q, form[q.id]);
    const own = hasOptions(q) ? choice === "own" : true;
    const typed = own ? text.trim() : "";
    const option = hasOptions(q) && !own ? choice : null;
    const accepted = hasOptions(q) ? option === q.recommended : typed === "";
    return { id: q.id, accepted, option, text: typed, note: note.trim(), attachments };
  });
}

// The first question whose own-answer choice is selected with no text.
export function unansweredOwn(questions, form) {
  return questions.find((q) => {
    const { choice, text } = entry(q, form[q.id]);
    return hasOptions(q) && choice === "own" && text.trim() === "";
  });
}

export const roundRefusal = (questions, form) => unansweredOwn(questions, form)?.title ?? null;

export const differCount = (questions, form) => answersFor(questions, form).filter((a) => !a.accepted).length;

export function recommendedForm(questions, form) {
  return Object.fromEntries(
    questions.map((q) => {
      const { note, attachments } = entry(q, form[q.id]);
      return [q.id, { choice: hasOptions(q) ? q.recommended : null, text: "", note, attachments }];
    }),
  );
}

// The readback's marks. A page-side mark is {id, type, text, quote, lines, heading, occurrence, start, attachments}:
// `id` is the creation counter and `start` the selection's offset in its first block's text; neither is sent.

// Anchored marks in document order (first line, then offset, then creation), general notes last in creation order.
export function numberMarks(marks) {
  const anchored = marks.filter((m) => m.type !== "note").sort((a, b) => a.lines[0] - b.lines[0] || a.start - b.start || a.id - b.id);
  const notes = marks.filter((m) => m.type === "note").sort((a, b) => a.id - b.id);
  return [...anchored, ...notes].map((m, i) => ({ ...m, n: i + 1 }));
}

// Which occurrence of `quote` in the block's rendered `text` the one at offset `start` is, counting overlapping matches.
export function occurrenceOf(text, quote, start) {
  let count = 0;
  for (let at = text.indexOf(quote); at !== -1 && at <= start; at = text.indexOf(quote, at + 1)) count++;
  return Math.max(count, 1);
}

// The nearest heading at or above block `index`: a heading block is under itself.
export function headingAbove(blocks, index) {
  for (let i = Math.min(index, blocks.length - 1); i >= 0; i--) {
    if (/^h[1-6]$/.test(blocks[i].tag)) return blocks[i].text ?? "";
  }
  return "";
}

export function markRecord(mark) {
  const { n, type, text, attachments } = mark;
  if (type === "note") return { n, type, text, attachments };
  const { quote, lines, heading, occurrence } = mark;
  return { n, type, text, quote, lines, heading, occurrence, attachments };
}

export const canSendChanges = (marks, questions, form) => marks.length > 0 || differCount(questions, form) > 0;

// An approve sends no marks, whatever marks exist.
export function readbackResponse(verdict, version, questions, form, marks) {
  const sent = verdict === "approve" ? [] : numberMarks(marks).map(markRecord);
  return { verdict, version, answers: answersFor(questions, form), marks: sent };
}
