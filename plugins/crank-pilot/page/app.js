import { token, getState, putDraft, postResponse } from "/page/api.js";
import { surface as questions } from "/page/questions.js";
import { surface as readback } from "/page/readback.js";
import { surface as prototype } from "/page/prototype.js";

const POLL_MS = 2000;
const surfaces = new Map();
const $ = (id) => document.getElementById(id);

export function registerSurface(kind, surface) {
  surfaces.set(kind, surface);
}

let view = null;
let mounted = null;
let sendButton = null;
let answered = null;
let latest = null;
let agendaKey = "";
let timer = null;
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
  if (mounted) mounted.surface.unmount();
  mounted = null;
  sendButton = null;
  $("reading").replaceChildren();
  $("ledger").replaceChildren();
  $("ledger").hidden = true;
  $("stage").classList.add("solo");
}

function heading(text, message) {
  const h1 = document.createElement("h1");
  h1.textContent = text;
  if (message) h1.className = "msg";
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
    saveDraft: (obj) => putDraft(n, obj),
    async send(body) {
      const res = await postResponse(n, body);
      if (res.status === 201) {
        answered = n;
        show(latest);
      } else if (res.status === 409) {
        poll();
      }
      return res;
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
  const response = state.response ?? (interaction.number === answered ? { via: "page" } : null);
  if (response) {
    const lead = { page: "Sent. ", chat: "Answered in chat. " }[response.via] ?? "";
    return message(`${lead}Waiting for the agent.`);
  }
  settle(`interaction:${interaction.number}`, () => {
    $("reading").append(heading(interaction.title));
    const surface = surfaces.get(interaction.kind);
    if (!surface) return;
    $("ledger").hidden = false;
    $("stage").classList.remove("solo");
    mounted = { surface };
    surface.mount($("stage"), state, contextFor(interaction.number));
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
    $("status").textContent = "";
    show(state);
  } catch {
    $("status").textContent = "Reconnecting";
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
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey) && sendButton?.isConnected && !sendButton.disabled) {
    event.preventDefault();
    sendButton.click();
  }
});

registerSurface("questions", questions);
registerSurface("readback", readback);
registerSurface("prototype", prototype);

window.addEventListener("pagehide", () => token() && navigator.sendBeacon("/api/bye"));

if (token()) poll();
else stop("Open this page from the session");
