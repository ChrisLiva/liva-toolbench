export const mac = /Mac|iPhone|iPad/.test(
  navigator.platform || navigator.userAgent || "",
);

export const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attrs))
    node.setAttribute(name, value);
  node.append(...children);
  return node;
}

export function sendControl(label, attrs = {}) {
  const button = el(
    "button",
    {
      type: "button",
      ...attrs,
      "aria-keyshortcuts": "Control+Enter Meta+Enter",
    },
    label,
  );
  return [button, el("kbd", {}, mac ? "⌘↵" : "Ctrl+Enter")];
}

// The URL hash is one interaction's: "#n=<number>&<key>=<value>". A hash that names another interaction is not read.
export function hashParam(n, key) {
  const params = new URLSearchParams(location.hash.slice(1));
  return params.get("n") === String(n) ? params.get(key) : null;
}

export function setHashParam(n, key, value) {
  history.replaceState(
    history.state,
    "",
    `${location.pathname}${location.search}#n=${n}&${key}=${encodeURIComponent(value)}`,
  );
}
