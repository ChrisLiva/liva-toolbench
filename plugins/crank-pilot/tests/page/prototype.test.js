// The prototype surface's variant switch: the variant on show is remembered per interaction, so the next
// prototype opens on its first variant. Mounted directly with a hand-built context, as readback.test.js does.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow, routeFetch, tick } from "./page.js";

const interaction = (number) => ({
  number,
  kind: "prototype",
  title: "Toggle prototype",
  question: "Which toggle?",
  variants: [
    { key: "A", name: "Header switch", file: "prototype/variant-A.html" },
    { key: "B", name: "Menu item", file: "prototype/variant-B.html" },
  ],
});

test("prototype: the variant shown does not carry onto the next interaction", async () => {
  const window = pageWindow();
  routeFetch({
    "GET /api/file/": async () => new Response("<p>variant</p>"),
  });
  const { surface } = await import("/page/prototype.js");
  const { document } = window;
  const ctx = { saveDraftSoon() {}, send: async () => "", setSend() {} };
  const stage = document.getElementById("stage");
  const label = () => document.querySelector("#reading p.l[role=status]");
  const mount = (number) =>
    surface.mount(
      stage,
      { interaction: interaction(number), draft: null },
      ctx,
    );
  const button = (name) =>
    [...document.querySelectorAll("#reading button")].find(
      (b) => b.textContent === name,
    );

  let teardown = mount(4);
  await tick(20);
  assert.match(label().textContent, /^A/);
  button("Next").click();
  await tick(20);
  assert.match(label().textContent, /^B/);
  teardown();
  document.getElementById("reading").replaceChildren();
  document.getElementById("ledger").replaceChildren();

  teardown = mount(5);
  await tick(20);
  assert.match(label().textContent, /^A/);
  teardown();
});
