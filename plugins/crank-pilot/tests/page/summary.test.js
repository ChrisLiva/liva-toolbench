// The branches the other page tests leave out, walked through app.js as the user sees them: a question round's
// answer summary in every shape an answer takes, then a revised readback whose draft holds a general note, whose
// version control lands on a version that cannot load, and whose later version shows what changed since the prior.
// The poll timer keeps the process alive, so the command that runs this file passes --test-force-exit.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow, routeFetch, tick } from "./page.js";

const agenda = { settled: [], open: [], current: "" };
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status });
const options = [
  { id: "a", label: "A" },
  { id: "b", label: "B" },
];
const withOptions = (id, title) => ({
  id,
  title,
  options,
  recommended: "a",
});
const withoutOptions = (id, title, recommendation) => ({
  id,
  title,
  ...(recommendation ? { recommendation } : {}),
});

const ROUND = {
  number: 1,
  kind: "questions",
  title: "Round 1",
  phase: "brainstorm",
  agenda,
  questions: [
    withOptions("q1", "Accepted with a note?"),
    withOptions("q2", "Another option?"),
    withOptions("q3", "Own answer?"),
    withOptions("q4", "Own, still empty?"),
    withoutOptions("q5", "Free, recommended?", "Use X"),
    withoutOptions("q6", "Free, typed?", "Use X"),
    withoutOptions("q7", "Free, nothing?"),
  ],
};

const V1 = "# Title\n\nKept block\n\nGone block";
const V3 = "# Title\n\nKept block\n\nNew block";
const READBACK = {
  number: 2,
  kind: "readback",
  title: "Review spec",
  artifact: "spec.md",
  version: 3,
  lead: "Two versions on.",
  judgment_calls: ["Kept the title"],
  review_landed: [],
  edits: [],
  decisions: [withOptions("d1", "Ship it?")],
  phase: "spec",
  agenda,
};
const PRIOR = {
  version: 1,
  marks: [
    {
      n: 1,
      type: "comment",
      text: "tighten",
      quote: "Gone block",
      lines: [5, 5],
      heading: "Title",
      occurrence: 1,
      attachments: [],
    },
  ],
};
// A draft written by an earlier page: one whole general note, and a comment that lost its quote and lines.
const DRAFT = {
  marks: [
    { id: 1, type: "note", text: "Overall fine", attachments: [] },
    { id: 2, type: "comment", text: "broken" },
  ],
};

const until = async (condition, what, limit = 4000) => {
  for (let waited = 0; !condition(); waited += 10) {
    assert.ok(waited < limit, `the page never showed ${what}`);
    // oxlint-disable-next-line eslint/no-await-in-loop -- polls the page every 10 ms until the condition holds
    await tick(10);
  }
};

test("summary rows, a draft's general note, an unloadable version, and what changed since the prior", async () => {
  const window = pageWindow();
  window.sessionStorage.setItem("pilot-token", "t");
  const { document } = window;
  const text = (selector) => document.querySelector(selector)?.textContent;

  let state = { effort: "e", interaction: ROUND };
  routeFetch({
    "GET /api/state": () => json(state),
    "PUT /api/draft/": () => json({}),
    "GET /api/file/": (path) => {
      if (path.endsWith("/001.md")) return new Response(V1);
      if (path.endsWith("/003.md")) return new Response(V3);
      return new Response("", { status: 404 });
    },
  });
  await import("/page/app.js");
  await until(
    () => document.querySelectorAll("fieldset.q").length === 7,
    "the seven questions",
  );

  // Each row is [question number, what was said, tag].
  const rows = () =>
    [...document.querySelectorAll("#ledger ol.sum li")].map((li) => [
      li.children[0].textContent,
      li.children[1].firstChild.textContent,
      li.querySelector(".tag").textContent,
    ]);
  const fields = (n) =>
    document.querySelectorAll(
      `fieldset.q:nth-of-type(${n}) input[type="text"]`,
    );
  const type = (input, value) => {
    input.value = value;
    input.dispatchEvent(new window.Event("input", { bubbles: true }));
  };

  assert.deepEqual(rows(), [
    ["Q1", "A", "Accepted"],
    ["Q2", "A", "Accepted"],
    ["Q3", "A", "Accepted"],
    ["Q4", "A", "Accepted"],
    ["Q5", "Use X", "Accepted"],
    ["Q6", "Use X", "Accepted"],
    ["Q7", "No answer yet", "Accepted"],
  ]);
  assert.equal(text("#ledger .big"), "0");

  // An accepted option with a note, another option, an own answer, a click into Other with nothing typed,
  // and a free answer with and without text.
  type(fields(1)[1], "why");
  const second = document.querySelector(
    'input[type="radio"][name="q1"][value="b"]',
  );
  second.checked = true;
  second.dispatchEvent(new window.Event("change", { bubbles: true }));
  type(fields(3)[0], "Mine");
  fields(4)[0].dispatchEvent(new window.Event("click", { bubbles: true }));
  type(fields(6)[0], "Typed");

  assert.deepEqual(rows(), [
    ["Q1", "A", "Accepted + note"],
    ["Q2", "B", "Your choice"],
    ["Q3", "Mine", "Own answer"],
    ["Q4", "No answer yet", "Open"],
    ["Q5", "Use X", "Accepted"],
    ["Q6", "Typed", "Own answer"],
    ["Q7", "No answer yet", "Accepted"],
  ]);
  assert.equal(text("#ledger .big"), "4");

  // A revised readback whose draft holds a general note.
  state = {
    effort: "e",
    interaction: READBACK,
    versions: [1, 2, 3],
    prior: PRIOR,
    draft: DRAFT,
  };
  await until(
    () => document.querySelector("#reading .art .chg"),
    "the changed block",
    6000,
  );

  // The unfinished comment is dropped; the note stays, numbered 01.
  assert.equal(text("#ledger .big"), "1");
  assert.equal(text("#ledger .gen li .nh span"), "01 Note");
  assert.equal(text("#ledger .gen li .t"), "Overall fine");
  assert.equal(text("#ledger .lfoot .l"), "General notes 1");
  assert.equal(text("#ledger .addr .l"), "Addressed from v1 1");
  assert.equal(text("#ledger .addr .nh span"), "01 Comment · Addressed");

  // The version shown against the prior marks what changed and lists what was removed.
  const changed = () =>
    [...document.querySelectorAll("#reading .art .chg")].map(
      (tag) => tag.parentElement.firstChild.textContent,
    );
  assert.deepEqual(changed(), ["New block"]);
  assert.equal(text("#reading .removed .l"), "Removed 1");
  assert.equal(text("#reading .removed li"), "Gone block");
  assert.equal(document.querySelector("#reading .removed").hidden, false);
  assert.equal(text("#verOut"), "v3 · 3 blocks · 1 changed");

  // A version that cannot load says so and shows no change.
  const slider = document.getElementById("ver");
  const slideTo = (version) => {
    slider.value = String(version);
    slider.dispatchEvent(new window.Event("input", { bubbles: true }));
  };
  slideTo(2);
  await until(
    () => text("#reading .art") === "The artifact could not be loaded.",
    "the load failure",
  );
  assert.equal(text("#verOut"), "v2 · 0 blocks");
  assert.equal(document.querySelector("#reading .removed").hidden, true);
  assert.equal(document.querySelector("#reading .chg"), null);

  // Back on the current version, the change shows again.
  slideTo(3);
  await until(() => changed().length === 1, "the changed block again");
  assert.deepEqual(changed(), ["New block"]);
  assert.equal(text("#reading .removed li"), "Gone block");
});
