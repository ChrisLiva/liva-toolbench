// The URL hash belongs to one interaction: a version picked on one readback must not carry onto the next.
// The poll timer keeps the process alive, so the command that runs this file passes --test-force-exit.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow, routeFetch, tick } from "./page.js";

const json = (body) => new Response(JSON.stringify(body), { status: 200 });
const readback = (number, version) => ({
  number,
  kind: "readback",
  title: `Review ${number}`,
  artifact: "spec.md",
  version,
  lead: "",
  judgment_calls: [],
  review_landed: [],
  edits: [],
  decisions: [],
  phase: "spec",
  agenda: { settled: [], open: [], current: "" },
});

const versions = (...ns) =>
  ns.map((n) => ({ n, file: `kept/spec-v${n}.md` }));

const until = async (condition, what, limit = 6000) => {
  for (let waited = 0; !condition(); waited += 10) {
    assert.ok(waited < limit, `the page never showed ${what}`);
    // oxlint-disable-next-line eslint/no-await-in-loop -- polls the page every 10 ms until the condition holds
    await tick(10);
  }
};

test("a version picked on one readback does not carry onto the next interaction", async () => {
  const window = pageWindow();
  window.sessionStorage.setItem("pilot-token", "t");
  const { document } = window;

  let state = {
    effort: "e",
    interaction: readback(2, 2),
    versions: versions(1, 2),
    prior: null,
    draft: null,
  };
  routeFetch({
    "GET /api/state": () => json(state),
    "GET /api/file/": (path) =>
      /^\/api\/file\/kept\/spec-v[1-3]\.md$/.test(path)
        ? new Response("# Title\n\nBody")
        : new Response("", { status: 404 }),
  });
  await import("/page/app.js");
  await until(() => document.getElementById("ver"), "the version control");

  const slideTo = (version) => {
    const slider = document.getElementById("ver");
    slider.value = String(version);
    slider.dispatchEvent(new window.Event("input", { bubbles: true }));
  };
  slideTo(1);
  slideTo(2);

  state = {
    ...state,
    interaction: readback(3, 3),
    versions: versions(1, 2, 3),
  };
  await until(
    () => document.getElementById("ver")?.max === "3",
    "the next readback",
  );

  assert.equal(document.getElementById("ver").value, "3");
  assert.doesNotMatch(
    document.querySelector("#reading p.status").textContent,
    /read-only/,
  );
});
