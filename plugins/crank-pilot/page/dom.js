export const mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
  node.append(...children);
  return node;
}

export function sendControl(label, attrs = {}) {
  const button = el("button", { type: "button", ...attrs, "aria-keyshortcuts": "Control+Enter Meta+Enter" }, label);
  return [button, el("kbd", {}, mac ? "⌘↵" : "Ctrl+Enter")];
}
