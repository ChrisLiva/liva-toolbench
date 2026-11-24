// Code blocks: a fence that names a language highlight.js knows is colored, and every block keeps its source text.
import assert from "node:assert/strict";
import test from "node:test";
import { pageWindow } from "./page.js";

const CODE = 'const a = "<b>"; // why';
const SOURCE = [
  "```js",
  CODE,
  "```",
  "",
  "```",
  CODE,
  "```",
  "",
  "```nosuchlanguage",
  CODE,
  "```",
].join("\n");

const tokens = (pre) =>
  [...pre.querySelectorAll("span")].map(
    (s) => `${s.className}:${s.textContent}`,
  );

test("render: a fence in a known language is highlighted, any other stays plain", async () => {
  const { document } = pageWindow();
  const { renderMarkdown } = await import("/page/render.js");
  const root = document.createElement("div");
  const blocks = await renderMarkdown(SOURCE, root);

  const [known, bare, unknown] = root.querySelectorAll("pre");
  assert.deepEqual(tokens(known), [
    "hljs-keyword:const",
    'hljs-string:"<b>"',
    "hljs-comment:// why",
  ]);
  assert.deepEqual(tokens(bare), []);
  assert.deepEqual(tokens(unknown), []);

  // Marks anchor by offsets into a block's text, so highlighting must not change it.
  assert.deepEqual(
    blocks.map((b) => `${b.first}-${b.last}:${b.text}`),
    [`1-3:${CODE}\n`, `5-7:${CODE}\n`, `9-11:${CODE}\n`],
  );
});
