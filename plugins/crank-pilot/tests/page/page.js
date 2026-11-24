// The page's DOM under jsdom: the globals the page modules read, a fetch a test routes, and a tick.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { runInThisContext } from "node:vm";
import { JSDOM } from "jsdom";

const PAGE_DIR = new URL("../../page/", import.meta.url);
const URL_BASE = "http://127.0.0.1:1/";
const GLOBALS = [
  "document",
  "Node",
  "NodeFilter",
  "location",
  "history",
  "sessionStorage",
];

export function pageWindow() {
  const html = readFileSync(new URL("index.html", PAGE_DIR), "utf8").replace(
    /<script\b[^>]*>\s*<\/script>/g,
    "",
  );
  const { window } = new JSDOM(html, { url: URL_BASE });
  globalThis.window = window;
  for (const name of GLOBALS) globalThis[name] = window[name];

  // The vendored UMD file sets globalThis.markdownit as a side effect; its return value is an empty namespace.
  createRequire(import.meta.url)("../../page/vendor/markdown-it.min.js");
  assert.equal(typeof globalThis.markdownit, "function");
  // The vendored highlight.js sets `hljs` through a top-level `var`, which becomes a global only when the file runs as a script.
  runInThisContext(
    readFileSync(new URL("vendor/highlight.min.js", PAGE_DIR), "utf8"),
  );
  assert.equal(typeof globalThis.hljs.highlight, "function");

  // jsdom has no layout.
  const zero = {
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    width: 0,
    height: 0,
  };
  window.Range.prototype.getBoundingClientRect = () => ({ ...zero });
  class ResizeObserver {
    observe() {}
    disconnect() {}
  }
  window.ResizeObserver = globalThis.ResizeObserver = ResizeObserver;
  window.navigator.sendBeacon = () => true;
  Object.defineProperty(globalThis, "navigator", {
    value: window.navigator,
    configurable: true,
  });
  return window;
}

// routes: { "<METHOD> <path prefix>": (path, init) => Response }, looked up on every call.
export function routeFetch(routes) {
  globalThis.fetch = async (input, init = {}) => {
    const path = new URL(String(input), URL_BASE).pathname;
    const method = (init.method || "GET").toUpperCase();
    const key = Object.keys(routes).find((k) => {
      const [m, prefix] = k.split(" ");
      return m === method && path.startsWith(prefix);
    });
    if (!key) throw new Error(`no route for ${method} ${path}`);
    return routes[key](path, init);
  };
}

export const tick = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
