// The questions surface's refusal to send an own answer left empty: it names the question, moves focus to
// that question's text field, and sends nothing; typing the answer lets the send through. Mounted directly
// with a hand-built context, as readback.test.js does.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow } from "./page.js";

test("questions: Other chosen with nothing typed refuses the send and focuses the field", async () => {
  const window = pageWindow();
  const { surface } = await import("/page/questions.js");
  const { document } = window;
  const sent = [];
  const ctx = {
    saveDraftSoon() {},
    send: async (body) => {
      sent.push(body);
      return "";
    },
    setSend() {},
  };
  surface.mount(
    document.getElementById("stage"),
    {
      interaction: {
        number: 3,
        kind: "questions",
        title: "Round",
        phase: "brainstorm",
        agenda: { settled: [], open: [], current: "" },
        questions: [
          {
            id: "q1",
            title: "Which?",
            options: [
              { id: "a", label: "A" },
              { id: "b", label: "B" },
            ],
            recommended: "a",
          },
        ],
      },
      draft: null,
    },
    ctx,
  );
  const err = () => document.querySelector("#ledger .err").textContent;
  const field = document.querySelector('input[aria-label^="Your own answer"]');
  const sendButton = [...document.querySelectorAll("#ledger button")].find(
    (b) => b.textContent === "Send answers",
  );

  document.querySelector('input[type="radio"][value="own"]').click();
  sendButton.click();
  assert.equal(err(), 'Type your answer to "Which?" or pick an option.');
  assert.equal(document.activeElement, field);
  assert.equal(sent.length, 0);

  field.value = "Neither";
  field.dispatchEvent(new window.Event("input", { bubbles: true }));
  sendButton.click();
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(sent.length, 1);
  assert.equal(sent[0].answers[0].text, "Neither");
  assert.equal(err(), "");
});
