export const FRAME_POLICY = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:";

const MERMAID_SRC = "/page/vendor/mermaid.min.js";
const FRAGMENTS = new Set(["html", "svg"]);
// A sandboxed frame has an opaque origin, so its postMessage must target every origin; the page checks event.source.
const SIZER = "const send=()=>parent.postMessage({pilotHeight:Math.ceil(document.documentElement.getBoundingClientRect().height)},'*');" +
  "addEventListener('load',send);new ResizeObserver(send).observe(document.documentElement);";

const md = globalThis.markdownit({ html: false });

md.core.ruler.push("lines", (state) => {
  const lines = state.src.split("\n");
  for (const token of state.tokens) {
    if (!token.map || token.nesting === -1 || !token.block) continue;
    let last = token.map[1];
    while (last > token.map[0] + 1 && lines[last - 1].trim() === "") last--;
    token.attrSet("data-lines", `${token.map[0] + 1}-${last}`);
  }
});

md.renderer.rules.fence = (tokens, i, options, env, self) => {
  const token = tokens[i];
  const kind = token.info.trim().split(/\s+/)[0];
  const fence = kind ? ` data-fence="${md.utils.escapeHtml(kind)}"` : "";
  return `<pre${self.renderAttrs(token)}${fence}><code>${md.utils.escapeHtml(token.content)}</code></pre>\n`;
};

export function sandboxFrame(html, options = {}) {
  const frame = document.createElement("iframe");
  frame.setAttribute("sandbox", "allow-scripts");
  const script = options.script ? `<script>${options.script}</script>` : "";
  frame.setAttribute(
    "srcdoc",
    `<meta http-equiv="Content-Security-Policy" content="${FRAME_POLICY}"><script>${SIZER}</script>${script}${html}`,
  );
  frame.className = "frag";
  frame.title = "Fragment from the artifact";
  return frame;
}

window.addEventListener("message", (event) => {
  const height = event.data?.pilotHeight;
  if (!Number.isFinite(height) || height < 0) return;
  for (const frame of document.querySelectorAll("iframe.frag")) {
    if (event.source === frame.contentWindow) frame.style.height = `${height}px`;
  }
});

function figure(pre) {
  const el = document.createElement("div");
  el.className = "fig";
  el.setAttribute("data-lines", pre.getAttribute("data-lines"));
  pre.replaceWith(el);
  return el;
}

let mermaidReady = null;
function loadMermaid() {
  mermaidReady ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = MERMAID_SRC;
    script.onload = () => {
      globalThis.mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
      resolve(globalThis.mermaid);
    };
    script.onerror = () => {
      mermaidReady = null;
      reject(new Error("mermaid did not load"));
    };
    document.head.append(script);
  });
  return mermaidReady;
}

let diagrams = 0;
async function drawDiagram(pre) {
  const id = `pilot-mermaid-${diagrams++}`;
  try {
    const mermaid = await loadMermaid();
    const { svg } = await mermaid.render(id, pre.textContent);
    figure(pre).innerHTML = svg;
  } catch {
    // A diagram that cannot be drawn stays on the page as its source.
    document.getElementById(`d${id}`)?.remove();
  }
}

export async function renderMarkdown(source, root) {
  root.innerHTML = md.render(source);
  for (const pre of root.querySelectorAll("pre[data-fence]")) {
    if (!FRAGMENTS.has(pre.dataset.fence)) continue;
    figure(pre).append(sandboxFrame(pre.textContent));
  }
  for (const pre of root.querySelectorAll('pre[data-fence="mermaid"]')) await drawDiagram(pre);
  const lines = source.split("\n");
  return [...root.querySelectorAll("[data-lines]")]
    .filter((el) => !el.querySelector("[data-lines]"))
    .map((el) => {
      const [first, last] = el.getAttribute("data-lines").split("-").map(Number);
      return { el, first, last, tag: el.tagName.toLowerCase(), text: el.textContent, source: lines.slice(first - 1, last).join("\n") };
    });
}
