import { start, token, getState, putDraft, postResponse } from "/page/api.js";
import { surface as questions } from "/page/questions.js";
import { surface as readback } from "/page/readback.js";
import { surface as prototype } from "/page/prototype.js";
import { BUSY, attaching } from "/page/attach.js";

const POLL_MS = 2000;
const SEND_FAILED = "Could not send. Try again.";
const DRAFT_REFUSED = "Draft not saved.";
const DRAFT_MS = 1000;
const surfaces = { questions, readback, prototype };
const $ = (id) => document.getElementById(id);

let view = null;
let teardown = null;
let sendButton = null;
let answered = null;
let latest = null;
let agendaKey = "";
let timer = null;
let draftTimer = null;
let draftRefused = false;
let connected = true;
let stopped = false;
let chain = Promise.resolve();

function words(list, current) {
  return list.map((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    if (text === current) {
      item.className = "cur";
      item.setAttribute("aria-current", "step");
    }
    return item;
  });
}

function paintStatus() {
  $("status").textContent = !connected
    ? "Reconnecting"
    : draftRefused
      ? DRAFT_REFUSED
      : "";
}

function renderAgenda(interaction) {
  $("agenda").hidden = !interaction;
  if (!interaction) return;
  const { settled, open, current } = interaction.agenda;
  const key = JSON.stringify([interaction.phase, settled, open, current]);
  if (key === agendaKey) return;
  agendaKey = key;
  $("phase").textContent = `Phase: ${interaction.phase}`;
  $("settledBtn").textContent = `Settled ${settled.length}`;
  $("settledList").replaceChildren(...words(settled));
  $("openCount").textContent = `Open ${open.length}`;
  $("openList").replaceChildren(...words(open, current));
}

function clear() {
  clearTimeout(draftTimer);
  draftRefused = false;
  paintStatus();
  teardown?.();
  teardown = null;
  sendButton = null;
  $("reading").replaceChildren();
  $("ledger").replaceChildren();
  $("ledger").hidden = true;
  $("stage").classList.add("solo");
}

function heading(text, asMessage) {
  const h1 = document.createElement("h1");
  h1.textContent = text;
  if (asMessage) h1.className = "msg";
  return h1;
}

function settle(key, build) {
  if (key === view) return;
  view = key;
  clear();
  build();
}

function message(text) {
  settle(`message:${text}`, () => $("reading").append(heading(text, true)));
}

function contextFor(n) {
  return {
    saveDraftSoon(obj) {
      clearTimeout(draftTimer);
      draftTimer = setTimeout(async () => {
        try {
          const res = await putDraft(n, obj);
          if (view !== `interaction:${n}`) return;
          draftRefused = !res.ok && res.status !== 409;
          paintStatus();
        } catch {
          // A draft that never reached the server leaves the status line to the poll, which reports a dropped connection.
        }
      }, DRAFT_MS);
    },
    // Resolves to the line the surface shows by its send button, empty when the send needs none: a 201 shows the wait
    // and a 409 the interaction that replaced this one, so neither is the surface's to report.
    async send(body, refusal) {
      if (attaching()) return BUSY;
      try {
        const res = await postResponse(n, body);
        if (res.status === 201) {
          answered = n;
          show(latest);
        } else if (res.status === 409) {
          poll();
        } else if (res.status === 400) {
          const refused = await res.json().catch(() => ({}));
          return refused.problems?.[0] ?? refusal;
        } else if (res.status === 413) {
          return "Too long to send: shorten the answer or note.";
        } else {
          return SEND_FAILED;
        }
        return "";
      } catch {
        return SEND_FAILED;
      }
    },
    setSend(button) {
      sendButton = button;
    },
  };
}

function show(state) {
  latest = state;
  const { interaction } = state;
  $("effort").textContent = state.effort;
  renderAgenda(interaction);
  if (state.ended) return stop("The session ended. This tab can be closed.");
  if (!interaction) return message("Waiting for the agent");
  const response =
    state.response ??
    (interaction.number === answered ? { via: "page" } : null);
  if (response) {
    const lead =
      { page: "Sent. ", chat: "Answered in chat. " }[response.via] ?? "";
    return message(`${lead}Waiting for the agent.`);
  }
  settle(`interaction:${interaction.number}`, () => {
    $("reading").append(heading(interaction.title));
    const surface = surfaces[interaction.kind];
    if (!surface) return;
    $("ledger").hidden = false;
    $("stage").classList.remove("solo");
    teardown = surface.mount($("stage"), state, contextFor(interaction.number));
  });
}

function stop(text) {
  stopped = true;
  clearTimeout(timer);
  message(text);
}

async function run() {
  if (stopped) return;
  try {
    const res = await getState();
    if (res.status === 403) return stop("Open this page from the session");
    if (!res.ok) throw new Error(`state ${res.status}`);
    const state = await res.json();
    connected = true;
    paintStatus();
    show(state);
  } catch {
    connected = false;
    paintStatus();
  }
  if (stopped) return;
  clearTimeout(timer);
  timer = setTimeout(poll, POLL_MS);
}

function poll() {
  clearTimeout(timer);
  chain = chain.then(run);
  return chain;
}

$("settledBtn").addEventListener("click", () => {
  const list = $("settledList");
  list.hidden = !list.hidden;
  $("settledBtn").setAttribute("aria-expanded", String(!list.hidden));
});

document.addEventListener("keydown", (event) => {
  if (
    event.key === "Enter" &&
    (event.metaKey || event.ctrlKey) &&
    sendButton?.isConnected &&
    !sendButton.disabled
  ) {
    event.preventDefault();
    sendButton.click();
  }
});

window.addEventListener(
  "pagehide",
  () => token() && navigator.sendBeacon("/api/bye"),
);

start().then((t) => (t ? poll() : stop("Open this page from the session")));
