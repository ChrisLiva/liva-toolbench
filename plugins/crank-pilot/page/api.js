const KEY = "pilot-token";
let held = "";

export function token() {
  if (held) return held;
  try {
    held = sessionStorage.getItem(KEY) || "";
  } catch {
    // Storage is blocked: the token then lives only until this page is closed.
  }
  return held;
}

export async function start() {
  const url = new URL(location.href);
  const code = url.searchParams.get("c");
  if (!code) return token();
  url.searchParams.delete("c");
  history.replaceState(history.state, "", url.pathname + url.search + url.hash);
  try {
    const reply = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
      cache: "no-store",
    });
    if (reply.ok) {
      held = (await reply.json()).token;
      try {
        sessionStorage.setItem(KEY, held);
      } catch {
        // Storage is blocked: the token then lives only until this page is closed.
      }
    }
  } catch {
    // The exchange failed: the page falls back to what token() holds.
  }
  return token();
}

function call(method, path, body) {
  const headers = { "X-Pilot-Token": token() };
  let payload;
  if (body instanceof Blob) {
    headers["Content-Type"] = body.type || "application/octet-stream";
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  return fetch(path, { method, headers, body: payload, cache: "no-store" });
}

export const getState = () => call("GET", "/api/state");
export const getFile = (path) => call("GET", "/api/file/" + path.split("/").map(encodeURIComponent).join("/"));
export const putDraft = (n, obj) => call("PUT", `/api/draft/${n}`, obj);
export const postResponse = (n, obj) => call("POST", `/api/response/${n}`, obj);
export const postAttachment = (n, blob) => call("POST", `/api/attachment/${n}`, blob);
export const deleteAttachment = (n, k) => call("DELETE", `/api/attachment/${n}/${k}`);
