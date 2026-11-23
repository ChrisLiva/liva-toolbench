import { renderMarkdown } from "/page/render.js";
import { answersFor, attachedCount, differCount, formFrom, recommendedForm, refusalMessage, unansweredOwn } from "/page/model.js";
import { el, sendControl } from "/page/dom.js";
import { mountAttach } from "/page/attach.js";

const OWN = "own";

function markdown(source, into) {
  renderMarkdown(source, into).catch(() => {
    into.textContent = source;
  });
  return into;
}

const hasOptions = (q) => Array.isArray(q.options) && q.options.length > 0;

// Draws the questions into `root` and keeps their form; `onChange(form)` runs after every change the user makes.
// `attach` names the interaction the images belong to and `others()`, how many images the response carries outside this form.
export function mountQuestions(root, questions, initial, onChange, { interaction, others = () => 0 }) {
  let state = formFrom(questions, initial);
  const parts = new Map();
  const round = el("div", { class: "round" });
  root.append(round);

  const emit = () => onChange(structuredClone(state));

  questions.forEach((q, i) => {
    const id = `q${i}`;
    const part = { radios: new Map() };
    parts.set(q.id, part);
    const set = el("fieldset", { class: "q" });
    set.append(el("legend", {}, el("span", { class: "qn" }, `Q${i + 1}`), q.title));
    if (q.body) set.append(markdown(q.body, el("div", { class: "qb" })));
    if (q.recommendation) {
      set.append(el("div", { class: "qr" }, el("p", { class: "l" }, "Recommendation"), markdown(q.recommendation, el("div", { class: "qb" }))));
    }
    if (hasOptions(q)) {
      q.options.forEach((option, j) => {
        const radio = el("input", { type: "radio", name: id, id: `${id}-${j}`, value: option.id });
        part.radios.set(option.id, radio);
        const label = el("label", { for: radio.id }, option.label);
        if (option.id === q.recommended) label.append(el("span", { class: "l rec" }, "Recommended"));
        set.append(el("div", { class: "opt" }, radio, label));
      });
      const own = el("input", { type: "radio", name: id, id: `${id}-own`, value: OWN });
      part.radios.set(OWN, own);
      part.text = el("input", { type: "text", "aria-label": `Your own answer to "${q.title}"`, placeholder: "Type your own answer" });
      set.append(el("div", { class: "opt other" }, own, el("div", { class: "row" }, el("label", { for: own.id }, "Other"), part.text)));
    } else {
      part.text = el("input", { type: "text", placeholder: "Leave empty to accept the recommendation" });
      set.append(el("label", { class: "field" }, el("span", { class: "l" }, "Your answer"), part.text));
    }
    part.note = el("input", { type: "text", placeholder: "Anything the agent should know" });
    const extras = el("div", { class: "qx" }, el("label", { class: "field" }, el("span", { class: "l" }, "Note (optional)"), part.note));
    part.attach = mountAttach(extras, {
      interaction,
      paths: state[q.id].attachments,
      count: () => attachedCount(Object.values(state)) + others(),
      onChange: (next) => {
        state[q.id].attachments = next;
        emit();
      },
      zone: set,
    });
    set.append(extras);

    part.radios.forEach((radio, choice) => {
      radio.addEventListener("change", () => {
        state[q.id].choice = choice;
        emit();
      });
    });
    part.text.addEventListener("input", () => {
      state[q.id].text = part.text.value;
      if (hasOptions(q)) choose(q.id, OWN);
      emit();
    });
    // A click (not a Tab) into the own-answer field picks Other, so passing through with the keyboard changes nothing.
    part.text.addEventListener("click", () => {
      if (hasOptions(q) && state[q.id].choice !== OWN) {
        choose(q.id, OWN);
        emit();
      }
    });
    part.note.addEventListener("input", () => {
      state[q.id].note = part.note.value;
      emit();
    });
    round.append(set);
  });

  function choose(qid, choice) {
    state[qid].choice = choice;
    parts.get(qid).radios.get(choice).checked = true;
  }

  function paint() {
    for (const q of questions) {
      const part = parts.get(q.id);
      const entry = state[q.id];
      for (const [choice, radio] of part.radios) radio.defaultChecked = radio.checked = choice === entry.choice;
      part.text.value = entry.text;
      part.note.value = entry.note;
      part.attach.set(entry.attachments);
    }
  }
  paint();

  return {
    form: () => structuredClone(state),
    setForm(next) {
      state = formFrom(questions, next);
      paint();
      emit();
    },
    focusQuestion(qid) {
      parts.get(qid)?.text.focus();
    },
  };
}

function summaryItem(q, i, answer) {
  let said;
  let tag;
  if (hasOptions(q)) {
    said = answer.option === null ? answer.text : q.options.find((o) => o.id === answer.option)?.label;
    tag = answer.accepted ? "Accepted" : answer.option === null ? "Own answer" : "Your choice";
    if (answer.option === null && !answer.text) {
      said = "";
      tag = "Open";
    }
  } else {
    said = answer.text || q.recommendation || "";
    tag = answer.accepted ? "Accepted" : "Own answer";
  }
  if (answer.note) tag += " + note";
  return el("li", {}, el("span", { class: "l" }, `Q${i + 1}`), el("span", {}, said || "No answer yet", el("span", { class: "l tag" }, tag)));
}

export const surface = {
  mount(stage, state, ctx) {
    const { questions } = state.interaction;
    const big = el("p", { class: "big", role: "img" });
    const sum = el("ol", { class: "sum", "aria-label": "Answers so far" });
    const err = el("p", { class: "err", role: "alert" });
    const accept = el("button", { type: "button" }, "Accept all recommendations");
    const [send, hint] = sendControl("Send answers", { class: "go" });
    stage.querySelector("#ledger").append(
      el("p", { class: "l" }, "Differ from recommended"),
      big,
      el("p", { class: "l lsub" }, `of ${questions.length} question${questions.length === 1 ? "" : "s"}`),
      sum,
      err,
      el("div", { class: "lact" }, accept, el("div", { class: "ar" }, send, hint)),
    );

    const refresh = (form) => {
      const count = differCount(questions, form);
      big.textContent = String(count);
      big.setAttribute("aria-label", `${count} differ from recommended`);
      const answers = answersFor(questions, form);
      sum.replaceChildren(...questions.map((q, i) => summaryItem(q, i, answers[i])));
      err.textContent = "";
    };
    const changed = (form) => {
      refresh(form);
      ctx.saveDraftSoon(form);
    };
    const ui = mountQuestions(stage.querySelector("#reading"), questions, state.draft, changed, { interaction: state.interaction.number });
    refresh(ui.form());

    accept.addEventListener("click", () => ui.setForm(recommendedForm(questions, ui.form())));
    send.addEventListener("click", async () => {
      const form = ui.form();
      const open = unansweredOwn(questions, form);
      if (open) {
        err.textContent = refusalMessage(open.title);
        ui.focusQuestion(open.id);
        return;
      }
      err.textContent = "";
      send.disabled = true;
      err.textContent = await ctx.send({ answers: answersFor(questions, form) }, "The answers were refused.");
      send.disabled = false;
    });
    ctx.setSend(send);
  },
};
