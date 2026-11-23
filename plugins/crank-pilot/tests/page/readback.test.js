// The readback surface's marking journey: draw a strike across blocks, comment on one block,
// remount from the saved draft, then remove the strike. Expected values are counted by hand from SOURCE.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow, routeFetch, tick } from "./page.js";

const SOURCE = "# Title\n\nHello *big* world\n\nSecond block here";

const STATE = {
  interaction: {
    number: 1,
    kind: "readback",
    title: "T",
    artifact: "spec.md",
    version: 1,
    lead: "",
    judgment_calls: [],
    review_landed: [],
    edits: [],
    decisions: [],
    agenda: { settled: [], open: [], current: "" },
  },
  versions: [{ n: 1, file: "kept/spec-v1.md" }],
  prior: null,
  draft: null,
};

test("readback: strike across blocks, comment, remount from the draft, remove", async () => {
  const window = pageWindow();
  routeFetch({
    "GET /api/file/": async (path) =>
      /^\/api\/file\/kept\/spec-v[12]\.md$/.test(path)
        ? new Response(SOURCE, { status: 200 })
        : new Response("", { status: 404 }),
  });
  const { surface } = await import("/page/readback.js");
  const { document } = window;

  const drafts = [];
  const ctx = {
    saveDraftSoon: (draft) => drafts.push(structuredClone(draft)),
    send: async () => "",
    setSend() {},
  };
  const stage = document.getElementById("stage");
  const mount = (draft) => surface.mount(stage, { ...STATE, draft }, ctx);
  const marked = () =>
    [...document.querySelectorAll("[data-mark]")].map(
      (m) => `${m.tagName}:${m.textContent}`,
    );
  const paragraph = (text) =>
    [...document.querySelectorAll("#reading p[data-lines]")].find(
      (p) => p.textContent === text,
    );

  let teardown = mount(null);
  await tick(20);

  // The blocks.
  const blocks = [...document.querySelectorAll("[data-lines]")].map(
    (b) => `${b.getAttribute("data-lines")}:${b.textContent}`,
  );
  assert.deepEqual(blocks, [
    "1-1:Title",
    "3-3:Hello big world",
    "5-5:Second block here",
  ]);

  // A strike across two blocks wraps each text node the selection covers.
  const hello = paragraph("Hello big world");
  const second = paragraph("Second block here");
  const select = (startNode, startOffset, endNode, endOffset) => {
    const range = document.createRange();
    range.setStart(startNode, startOffset);
    range.setEnd(endNode, endOffset);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  };
  select(hello.firstChild, 2, second.firstChild, 6);
  hello.dispatchEvent(new window.MouseEvent("mouseup", { bubbles: true }));
  await tick(10);
  document.querySelector('[data-act="strike"]').click();
  assert.deepEqual(marked(), [
    "DEL:llo ",
    "DEL:big",
    "DEL: world",
    "DEL:Second",
  ]);
  const strike = drafts.at(-1).marks[0];
  assert.equal(strike.type, "strike");
  assert.equal(strike.quote, "llo big world\nSecond");
  assert.deepEqual(strike.lines, [3, 5]);
  assert.equal(strike.start, 2);
  assert.equal(strike.end, 6);
  assert.equal(strike.heading, "Title");
  assert.equal(strike.occurrence, 1);

  // A comment inside one block carries no end offset.
  const tail = paragraph("Second block here").lastChild;
  select(tail, 1, tail, 6);
  paragraph("Second block here").dispatchEvent(
    new window.MouseEvent("mouseup", { bubbles: true }),
  );
  await tick(10);
  document.querySelector('[data-act="comment"]').click();
  document.querySelector("#pop input").value = "why";
  document.querySelector('[data-act="add"]').click();
  const comment = drafts.at(-1).marks[1];
  assert.equal(comment.type, "comment");
  assert.equal(comment.text, "why");
  assert.equal(comment.quote, "block");
  assert.deepEqual(comment.lines, [5, 5]);
  assert.equal(comment.start, 7);
  assert.equal("end" in comment, false);

  // Remounting from the draft redraws every mark on the same blocks.
  const before = marked();
  const saved = drafts.at(-1);
  teardown();
  document.getElementById("reading").replaceChildren();
  document.getElementById("ledger").replaceChildren();
  teardown = mount(saved);
  await tick(20);
  assert.deepEqual(marked(), before);

  // Every open mark in the ledger, not only the first, can be edited or removed.
  const commentId = String(saved.marks[1].id);
  const actions = (id) =>
    [...document.querySelectorAll(`#ledger [data-id="${id}"] [data-act]`)].map(
      (b) => b.textContent,
    );
  assert.deepEqual(actions(String(saved.marks[0].id)), ["Remove"]);
  assert.deepEqual(actions(commentId), ["Edit", "Remove"]);
  assert.equal(
    document.getElementById("ledger").textContent.includes("Addressed"),
    false,
  );

  // Removing the strike gives the text back as it was.
  const strikeId = String(saved.marks[0].id);
  document
    .querySelector(`#ledger [data-id="${strikeId}"] [data-act="remove"]`)
    .click();
  await tick(10);
  assert.equal(document.querySelector(`[data-mark="${strikeId}"]`), null);
  const restored = paragraph("Hello big world");
  assert.equal(restored.textContent, "Hello big world");
  assert.equal(restored.querySelector("em").textContent, "big");
  assert.deepEqual(
    drafts.at(-1).marks.map((m) => m.type),
    ["comment"],
  );
  teardown();

  // A version picked on the slider survives a reload of its interaction, and not the next interaction.
  const opensOn = async (number, pick) => {
    document.getElementById("reading").replaceChildren();
    document.getElementById("ledger").replaceChildren();
    const stop = surface.mount(
      stage,
      {
        ...STATE,
        interaction: { ...STATE.interaction, number, version: 2 },
        versions: [
          { n: 1, file: "kept/spec-v1.md" },
          { n: 2, file: "kept/spec-v2.md" },
        ],
      },
      ctx,
    );
    await tick(20);
    const slider = document.getElementById("ver");
    const shown = slider.value;
    if (pick !== undefined) {
      slider.value = String(pick);
      slider.dispatchEvent(new window.Event("input", { bubbles: true }));
    }
    stop();
    return shown;
  };
  assert.equal(await opensOn(1, 1), "2");
  assert.equal(await opensOn(1), "1");
  assert.equal(await opensOn(2), "2");
});

test("readback: Approve with Other chosen and nothing typed is refused and focuses the field", async () => {
  const window = pageWindow();
  routeFetch({
    "GET /api/file/": async () => new Response(SOURCE, { status: 200 }),
  });
  const { surface } = await import("/page/readback.js");
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
  const stop = surface.mount(
    document.getElementById("stage"),
    {
      ...STATE,
      interaction: {
        ...STATE.interaction,
        decisions: [
          {
            id: "d1",
            title: "Which?",
            options: [
              { id: "a", label: "A" },
              { id: "b", label: "B" },
            ],
            recommended: "a",
          },
        ],
      },
    },
    ctx,
  );
  await tick(20);
  const err = () => document.querySelector("#ledger .err").textContent;
  const field = document.querySelector('input[aria-label^="Your own answer"]');
  const approve = [...document.querySelectorAll("#ledger button")].find(
    (b) => b.textContent === "Approve",
  );

  document.querySelector('input[type="radio"][value="own"]').click();
  approve.click();
  assert.match(err(), /Which\?/);
  assert.equal(document.activeElement, field);
  assert.equal(sent.length, 0);

  field.value = "Neither";
  field.dispatchEvent(new window.Event("input", { bubbles: true }));
  approve.click();
  await tick(10);
  assert.equal(sent.length, 1);
  assert.equal(sent[0].verdict, "approve");
  assert.equal(err(), "");
  stop();
});
