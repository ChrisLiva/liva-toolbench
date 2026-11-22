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
