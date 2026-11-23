// The page's status line through app.js: a refused draft, a dropped connection that keeps its
// own line, recovery, and a new interaction. The poll timer keeps the process alive, so the
// command that runs this file passes --test-force-exit.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow, routeFetch, tick } from "./page.js";

const interaction = (number) => ({
  number,
  kind: "questions",
  title: `Round ${number}`,
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
});
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status });

test("status line: draft refused, reconnecting keeps its line, recovery, new interaction", async () => {
  const window = pageWindow();
  window.sessionStorage.setItem("pilot-token", "t");
  const { document } = window;
  const status = () => document.getElementById("status").textContent;

  let current = () => json({ effort: "e", interaction: interaction(1) });
  let answered = () => {};
  routeFetch({
    "GET /api/state": () => current(),
    "PUT /api/draft/": () => {
      answered();
      return json({}, 400);
    },
  });
  await import("/page/app.js");

  for (
    let waited = 0;
    !document.getElementById("reading").textContent.includes("Round 1");
    waited += 10
  ) {
    assert.ok(waited < 2000, "the page never showed the interaction's title");
    await tick(10);
  }
  assert.equal(status(), "");

  // A refused draft shows its line once the debounce fires.
  const pick = (value) => {
    const radio = document.querySelector(
      `input[type="radio"][value="${value}"]`,
    );
    radio.checked = true;
    radio.dispatchEvent(new window.Event("change", { bubbles: true }));
  };
  pick("b");
  await tick(1200);
  assert.equal(status(), "Draft not saved.");

  // A dropped connection shows Reconnecting, and a draft answered meanwhile does not replace it.
  current = () => {
    throw new Error("offline");
  };
  await tick(2200);
  assert.equal(status(), "Reconnecting");
  const drafted = new Promise((resolve) => {
    answered = resolve;
  });
  pick("a");
  await drafted;
  await tick(10);
  assert.equal(status(), "Reconnecting");

  // Recovery brings the refusal back.
  current = () => json({ effort: "e", interaction: interaction(1) });
  await tick(2200);
  assert.equal(status(), "Draft not saved.");

  // A new interaction clears it.
  current = () => json({ effort: "e", interaction: interaction(2) });
  await tick(2200);
  assert.ok(document.getElementById("reading").textContent.includes("Round 2"));
  assert.equal(status(), "");
});
