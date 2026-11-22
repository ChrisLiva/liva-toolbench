// The question round's data rules. No DOM here: every function takes questions and a form and returns data.
// A form is {[questionId]: {choice: <option id> | "own" | null, text, note, attachments}}.

// Attachments. The server stores only the four types sniffImage names and at most ten images per response.
export const MAX_IMAGES = 10;
export const MAX_BYTES = 10 * 1024 * 1024;
export const ATTACH_MESSAGES = {
  type: "Only PNG, JPEG, GIF, WebP images can be attached.",
  size: "That image is over 10 MiB.",
  count: `A response can carry at most ${MAX_IMAGES} images.`,
};

const startsWith = (bytes, signature, at = 0) => signature.every((byte, i) => bytes[at + i] === byte);
const ascii = (text) => [...text].map((c) => c.charCodeAt(0));

// The image type a file's leading bytes name, or null: a name, a MIME type, and an SVG's markup are not evidence.
export function sniffImage(bytes) {
  if (startsWith(bytes, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) return "png";
  if (startsWith(bytes, [0xff, 0xd8, 0xff])) return "jpg";
  if (startsWith(bytes, ascii("GIF87a")) || startsWith(bytes, ascii("GIF89a"))) return "gif";
  if (startsWith(bytes, ascii("RIFF")) && startsWith(bytes, ascii("WEBP"), 8)) return "webp";
  return null;
}

export function attachRefusal({ kind, size, count }) {
  if (kind === null) return ATTACH_MESSAGES.type;
  if (size > MAX_BYTES) return ATTACH_MESSAGES.size;
  if (count >= MAX_IMAGES) return ATTACH_MESSAGES.count;
  return null;
}

// The images attached to every holder (a form's entries, marks, a verdict and its pins) on one response.
export const attachedCount = (...holders) => holders.flat().reduce((total, holder) => total + holder.attachments.length, 0);

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

export const refusalMessage = (title) => `Type your answer to "${title}" or pick an option.`;

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

// Blocks compared by source text with a longest common subsequence: the indexes into `newSources` that are added or
// changed, and the indexes into `oldSources` that are removed.
export function diffBlocks(oldSources, newSources) {
  const rows = oldSources.length;
  const cols = newSources.length;
  // tail[i][j] is the length of the longest common subsequence of oldSources.slice(i) and newSources.slice(j).
  const tail = Array.from({ length: rows + 1 }, () => new Array(cols + 1).fill(0));
  for (let i = rows - 1; i >= 0; i--) {
    for (let j = cols - 1; j >= 0; j--) {
      tail[i][j] = oldSources[i] === newSources[j] ? tail[i + 1][j + 1] + 1 : Math.max(tail[i + 1][j], tail[i][j + 1]);
    }
  }
  const changed = [];
  const removed = [];
  let i = 0;
  let j = 0;
  while (i < rows && j < cols) {
    if (oldSources[i] === newSources[j]) {
      i++;
      j++;
    } else if (tail[i + 1][j] >= tail[i][j + 1]) removed.push(i++);
    else changed.push(j++);
  }
  while (i < rows) removed.push(i++);
  while (j < cols) changed.push(j++);
  return { changed, removed };
}

// The prototype review. A pin is {variant, selector, leading_text, text, attachments}; a verdict is
// {winner: key | null, take, leave_out, attachments}. `n` is a pin's number within its variant, in the order pins were made.

export function numberPins(pins) {
  const counts = new Map();
  return pins.map((pin) => {
    const n = (counts.get(pin.variant) ?? 0) + 1;
    counts.set(pin.variant, n);
    return { ...pin, n };
  });
}

export const verdictRefusal = (verdict) => (verdict.winner ? null : "Choose a winner.");

const orNothing = (text) => text.trim() || "nothing";

export function prototypeResponse(verdict, pins) {
  return {
    winner: verdict.winner,
    take: orNothing(verdict.take),
    leave_out: orNothing(verdict.leave_out),
    attachments: verdict.attachments,
    comments: numberPins(pins).map(({ n, variant, selector, leading_text, text, attachments }) => ({ n, variant, selector, leading_text, text, attachments })),
  };
}

// The verdict and pins a saved draft holds, read defensively: a draft is whatever an earlier page wrote.
export function prototypeFrom(variants, draft) {
  const given = draft?.verdict && typeof draft.verdict === "object" ? draft.verdict : {};
  const text = (value) => (typeof value === "string" ? value : "");
  const keys = new Set(variants.map((v) => v.key));
  const pins = Array.isArray(draft?.pins) ? draft.pins : [];
  return {
    verdict: {
      winner: keys.has(given.winner) ? given.winner : null,
      take: text(given.take),
      leave_out: text(given.leave_out),
      attachments: strings(given.attachments),
    },
    pins: pins
      .filter((pin) => pin && typeof pin === "object" && keys.has(pin.variant))
      .map((pin) => ({ variant: pin.variant, selector: text(pin.selector), leading_text: text(pin.leading_text), text: text(pin.text), attachments: strings(pin.attachments) })),
  };
}
