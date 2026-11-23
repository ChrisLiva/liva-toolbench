// Maps the page's root-relative imports ("/page/render.js") onto the page folder,
// the way the page server serves them, so a test imports a page module as the browser does.
import { registerHooks } from "node:module";

const PAGE_DIR = new URL("../../page/", import.meta.url);

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith("/page/")) {
      const file = new URL(specifier.slice("/page/".length), PAGE_DIR);
      return nextResolve(file.href, context);
    }
    return nextResolve(specifier, context);
  },
});
