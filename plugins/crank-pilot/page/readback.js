import { getFile } from "/page/api.js";
import { renderMarkdown } from "/page/render.js";
import { el, mac } from "/page/dom.js";
import { mountQuestions } from "/page/questions.js";
import { attachedCount, canSendChanges, diffBlocks, headingAbove, numberMarks, occurrenceOf, readbackResponse, refusalMessage, roundRefusal, unansweredOwn } from "/page/model.js";
import { BUSY, attaching, discardImages, holderControl } from "/page/attach.js";

const HINT = "Select text, or focus a block and press Enter, to comment on it or strike it.";
const OLDER_HINT = (shown, current) => `Version ${shown} is read-only. Move the version control to v${current} to mark.`;
const LABEL = { comment: "Comment", strike: "Strike", note: "Note" };
const pad = (n) => String(n).padStart(2, "0");
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const linesOf = (node) => node.getAttribute("data-lines").split("-").map(Number);

// A draft is whatever an earlier page wrote: keep the marks that are whole and fill what a mark may lack.
function restore(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  for (const m of raw) {
    if (!m || typeof m !== "object" || !Number.isInteger(m.id) || typeof m.text !== "string") continue;
    const attachments = Array.isArray(m.attachments) ? m.attachments.filter((a) => typeof a === "string") : [];
    if (m.type === "note") {
      out.push({ id: m.id, type: "note", text: m.text, attachments });
      continue;
    }
    const whole =
      (m.type === "comment" || m.type === "strike") &&
      typeof m.quote === "string" &&
      Array.isArray(m.lines) && m.lines.length === 2 && m.lines.every(Number.isInteger) &&
      Number.isInteger(m.start);
    if (!whole) continue;
    out.push({
      id: m.id, type: m.type, text: m.text, quote: m.quote, lines: m.lines,
      heading: typeof m.heading === "string" ? m.heading : "",
      occurrence: Number.isInteger(m.occurrence) && m.occurrence >= 1 ? m.occurrence : 1,
      start: m.start,
      ...(Number.isInteger(m.end) ? { end: m.end } : {}),
      attachments,
    });
  }
  return out;
}

// The text node and offset that sit `offset` characters into `block`'s rendered text.
function locate(block, offset, atEnd) {
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  let seen = 0;
  let last = null;
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (atEnd ? offset <= seen + node.length : offset < seen + node.length) return [node, offset - seen];
    seen += node.length;
    last = node;
  }
  return last ? [last, last.length] : [block, 0];
}

const offsetIn = (block, node, at) => {
  const range = document.createRange();
  range.selectNodeContents(block);
  range.setEnd(node, at);
  return range.toString().length;
};

// The text a range covers, leaving out the CHANGED labels that sit inside blocks.
const plain = (range) => {
  const copy = range.cloneContents();
  for (const label of copy.querySelectorAll(".chg")) label.remove();
  return copy.textContent;
};

const byPosition = (a, b) => (a.ay === b.ay ? 0 : a.ay < b.ay ? -1 : 1);

let live = null;

export const surface = {
  mount(stage, state, ctx) {
    const { number, title, artifact, version, lead, judgment_calls: calls, review_landed: landed, edits, decisions } = state.interaction;
    const known = Array.isArray(state.versions) && state.versions.length ? state.versions : [version];
    const prior = state.prior && typeof state.prior === "object" ? state.prior : null;
    // A revision: the version on offer is not the one the user last marked up.
    const revised = prior !== null && prior.version !== version;
    const asked = revised && Array.isArray(prior.marks) ? prior.marks : [];
    const draft = state.draft && typeof state.draft === "object" ? state.draft : {};
    const reading = stage.querySelector("#reading");
    const ledger = stage.querySelector("#ledger");

    let marks = restore(draft.marks);
    let nextId = marks.reduce((high, m) => Math.max(high, m.id), 0) + 1;
    let blocks = [];
    let ui = null;
    let pending = null;
    let editing = null;
    let sending = false;
    let alive = true;
    let requested = 0;
    // One attach control per mark, kept across the ledger's redraws (see `holderControl`).
    const controls = new Map();
    const hashed = Number(new URLSearchParams(location.hash.slice(1)).get("version"));
    let shown = known.includes(hashed) ? hashed : version;
    const older = () => shown !== version;

    const art = el("div", { class: "art", role: "group", "aria-label": `Artifact: ${title}. ${HINT}` });
    const hint = el("p", { class: "l status", role: "status" }, HINT);
    const pop = el("div", { id: "pop", role: "group", "aria-label": "Mark the selected text", hidden: "" });

    const above = [];
    if (lead) above.push(el("p", { class: "lead" }, lead));
    for (const [label, items] of [["Judgment calls", calls], ["Landed by review", landed], ["Edits since the last version", edits]]) {
      if (!items?.length) continue;
      above.push(el("div", { class: "calls" }, el("p", { class: "l" }, `${label} ${items.length}`), el("ul", {}, ...items.map((text) => el("li", {}, text)))));
    }
    reading.append(...above);
    if (decisions.length) {
      const open = el("div", { class: "decisions" }, el("p", { class: "l" }, `Open decisions ${decisions.length}`));
      reading.append(open);
      ui = mountQuestions(
        open,
        decisions,
        draft.form,
        () => {
          refreshButtons();
          err.textContent = "";
          saveSoon();
        },
        { interaction: number, others: () => attachedCount(marks) },
      );
    }
    const removedBox = el("div", { class: "removed", hidden: "" });
    reading.append(hint, removedBox, art, pop);

    const form = () => (ui ? ui.form() : {});

    // The ledger.
    const big = el("p", { class: "big", role: "img" });
    const lmarks = el("div", { class: "lmarks" });
    const genHead = el("p", { class: "l" });
    const gen = el("ul", { class: "gen" });
    const noteInput = el("input", { type: "text", placeholder: "A note on the whole artifact" });
    const noteAdd = el("button", { type: "submit" }, "Add note");
    const noteForm = el("form", { autocomplete: "off" }, el("div", { class: "addrow" }, el("label", { class: "field" }, el("span", { class: "l" }, "Add a general note"), noteInput), noteAdd));
    const err = el("p", { class: "err", role: "alert" });
    const approve = el("button", { type: "button", class: "go", "aria-keyshortcuts": "Control+Shift+A Meta+Shift+A" }, "Approve");
    const send = el("button", { type: "button", "aria-keyshortcuts": "Control+Enter Meta+Enter" }, "Send changes");
    const dialog = el("div", { role: "alertdialog", class: "confirm", "aria-labelledby": "rb-confirm", hidden: "" });
    const addressed = el("div", { class: "addr" });
    ledger.append(
      el("p", { class: "l" }, `Marks on v${version}`),
      big,
      lmarks,
      addressed,
      el("div", { class: "lfoot" }, genHead, gen, noteForm),
      err,
      el("div", { class: "lact" },
        dialog,
        el("div", { class: "ar" }, approve, el("kbd", {}, mac ? "⌘⇧A" : "Ctrl+Shift+A")),
        el("div", { class: "ar" }, send, el("kbd", {}, mac ? "⌘↵" : "Ctrl+Enter")),
      ),
    );

    function saveSoon() {
      ctx.saveDraftSoon({ form: form(), marks });
    }

    function refreshButtons() {
      send.textContent = marks.length ? `Send changes (${plural(marks.length, "mark")})` : "Send changes";
      send.disabled = sending || older() || !canSendChanges(marks, decisions, form());
      approve.disabled = sending || older();
      noteInput.disabled = older();
      noteAdd.disabled = older();
    }

    // Anchoring: a mark knows its first and last source line, its offset in the first block's rendered text, and, when it crosses blocks, its end offset in the last.
    const blockOf = (node) => {
      const host = node?.nodeType === 1 ? node : node?.parentElement;
      const found = host?.closest("[data-lines]");
      return found && art.contains(found) ? found : null;
    };

    // Each text node a selection covers, clipped to the selection, leaving out the blank text between blocks.
    function piecesIn(range) {
      const root = range.commonAncestorContainer;
      const out = [];
      const consider = (node) => {
        if (!range.intersectsNode(node)) return;
        const s = node === range.startContainer ? range.startOffset : 0;
        const e = node === range.endContainer ? range.endOffset : node.length;
        const parent = node.parentElement;
        if (e <= s || !parent || !blockOf(parent) || parent.closest("svg, .chg")) return;
        if (node.data.trim() === "" && parent.querySelector(":scope > [data-lines]")) return;
        out.push({ node, s, e });
      };
      if (root.nodeType === Node.TEXT_NODE) consider(root);
      else {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) consider(node);
      }
      return out;
    }

    function trimmed(pieces) {
      const out = pieces.map((p) => ({ ...p }));
      while (out.length) {
        const p = out[0];
        const text = p.node.data.slice(p.s, p.e);
        const lead = text.length - text.trimStart().length;
        if (lead === text.length) out.shift();
        else {
          p.s += lead;
          break;
        }
      }
      while (out.length) {
        const p = out.at(-1);
        const text = p.node.data.slice(p.s, p.e);
        const tail = text.length - text.trimEnd().length;
        if (tail === text.length) out.pop();
        else {
          p.e -= tail;
          break;
        }
      }
      return out;
    }

    function anchorFor(pieces, raw) {
      const first = pieces[0];
      const last = pieces.at(-1);
      const a = blockOf(first.node);
      const b = blockOf(last.node);
      const start = offsetIn(a, first.node, first.s);
      const end = offsetIn(b, last.node, last.e);
      if (a === b) return { block: a, lines: linesOf(a), start, quote: a.textContent.slice(start, end), crosses: false };
      return { block: a, lines: [linesOf(a)[0], linesOf(b)[1]], start, end, quote: raw.trim(), crosses: true };
    }

    // The innermost element with these source lines; `null` leaves a bound open.
    function blockFor(first, last) {
      const found = [...art.querySelectorAll("[data-lines]")].filter((node) => {
        const [f, l] = linesOf(node);
        return (first === null || f === first) && (last === null || l === last);
      });
      return found.at(-1) ?? null;
    }

    function rangeFor(mark) {
      const single = !Number.isInteger(mark.end);
      const a = blockFor(mark.lines[0], single ? mark.lines[1] : null);
      const b = single ? a : blockFor(null, mark.lines[1]);
      if (!a || !b) return null;
      const range = document.createRange();
      range.setStart(...locate(a, mark.start, false));
      range.setEnd(...locate(b, single ? mark.start + mark.quote.length : mark.end, true));
      return range;
    }

    // Each selected text node gets its own wrapper, so a mark can cross inline elements without nesting them.
    function wrap(pieces, mark) {
      for (const { node, s, e } of pieces) {
        let target = node;
        if (e < node.length) node.splitText(e);
        if (s > 0) target = node.splitText(s);
        const span = document.createElement(mark.type === "strike" ? "del" : "span");
        span.setAttribute("class", `mk ${mark.type}`);
        span.setAttribute("data-mark", String(mark.id));
        target.replaceWith(span);
        span.append(target);
      }
      return pieces.length;
    }

    function draw(mark) {
      const range = rangeFor(mark);
      return range ? wrap(piecesIn(range), mark) : 0;
    }

    function unwrap(id) {
      for (const span of art.querySelectorAll(`[data-mark="${id}"]`)) span.replaceWith(...span.childNodes);
      art.normalize();
    }

    function blockIndex(block) {
      let found = -1;
      blocks.forEach((b, i) => {
        if (b.el === block || b.el.contains(block) || b.el.compareDocumentPosition(block) & Node.DOCUMENT_POSITION_FOLLOWING) found = i;
      });
      return found;
    }

    // The popover.
    function showButtons(problem) {
      pop.replaceChildren(
        el("button", { type: "button", "data-act": "comment" }, "Comment"),
        el("button", { type: "button", "data-act": "strike" }, "Strike"),
        ...(problem ? [el("p", { class: "perr", role: "alert" }, problem)] : []),
      );
      if (problem) for (const button of pop.querySelectorAll("button")) button.disabled = true;
    }

    function placePop(rect) {
      pop.hidden = false;
      const sx = window.scrollX;
      const sy = window.scrollY;
      const left = Math.min(Math.max(8, rect.left + sx), sx + document.documentElement.clientWidth - pop.offsetWidth - 8);
      let top = rect.top + sy - pop.offsetHeight - 8;
      if (top < sy + 4) top = rect.bottom + sy + 8;
      pop.style.left = `${left}px`;
      pop.style.top = `${top}px`;
    }

    function closePop(refocus) {
      pop.hidden = true;
      pop.replaceChildren();
      const back = pending?.returnTo;
      pending = null;
      if (refocus && back?.isConnected) back.focus({ preventScroll: true });
    }

    function propose(range, mode, returnTo) {
      const pieces = trimmed(piecesIn(range));
      let problem = "";
      if (!pieces.length) problem = "Select some text in the artifact.";
      else if (pieces.some((p) => p.node.parentElement.closest(".mk"))) problem = "That text already has a mark.";
      pending = problem ? null : { pieces, raw: plain(range), mode, returnTo };
      showButtons(problem);
      placePop(range.getBoundingClientRect());
    }

    function fromSelection() {
      setTimeout(() => {
        if (!alive || older() || (pop.contains(document.activeElement) && document.activeElement.tagName === "INPUT")) return;
        const selection = window.getSelection();
        if (!selection.rangeCount || selection.isCollapsed) return closePop(false);
        const range = selection.getRangeAt(0);
        if (!art.contains(range.commonAncestorContainer)) return closePop(false);
        propose(range.cloneRange(), "selection", null);
      }, 0);
    }

    function fromBlock(block) {
      const range = document.createRange();
      range.selectNodeContents(block);
      propose(range, "block", block);
      pop.querySelector("button")?.focus();
    }

    function commit(type, text) {
      const p = pending;
      if (!p) return;
      const anchor = anchorFor(p.pieces, p.raw);
      const mark = {
        id: nextId,
        type,
        text,
        quote: anchor.quote,
        lines: anchor.lines,
        heading: headingAbove(blocks, blockIndex(anchor.block)),
        occurrence: anchor.crosses ? 1 : occurrenceOf(anchor.block.textContent, anchor.quote, anchor.start),
        start: anchor.start,
        ...(anchor.crosses ? { end: anchor.end } : {}),
        attachments: [],
      };
      if (!wrap(p.pieces, mark)) return;
      nextId++;
      marks.push(mark);
      window.getSelection().removeAllRanges();
      const number = numberMarks(marks).find((m) => m.id === mark.id).n;
      closePop(true);
      hint.textContent = `Added mark ${number}.`;
      renderLedger();
      saveSoon();
    }

    pop.addEventListener("mousedown", (event) => {
      if (!event.target.closest("input")) event.preventDefault();
    });
    pop.addEventListener("click", (event) => {
      const act = event.target.closest("button")?.dataset.act;
      if (act === "strike") commit("strike", "");
      else if (act === "comment") {
        const input = el("input", { type: "text", "aria-label": "Comment text", placeholder: "Your comment" });
        pop.replaceChildren(input, el("button", { type: "button", "data-act": "add" }, "Add"), el("button", { type: "button", "data-act": "cancel" }, "Cancel"));
        placePop(pending ? pending.pieces[0].node.parentElement.getBoundingClientRect() : pop.getBoundingClientRect());
        input.focus();
      } else if (act === "add") {
        const value = pop.querySelector("input").value.trim();
        if (value) commit("comment", value);
        else pop.querySelector("input").focus();
      } else if (act === "cancel") closePop(true);
    });
    pop.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && event.target.tagName === "INPUT" && !(event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        const value = event.target.value.trim();
        if (value) commit("comment", value);
      } else if (event.key === "Escape") {
        event.preventDefault();
        closePop(true);
      }
    });
    art.addEventListener("mouseup", fromSelection);
    art.addEventListener("keyup", (event) => {
      if (event.shiftKey || /Arrow|Home|End/.test(event.key)) fromSelection();
    });
    art.addEventListener("keydown", (event) => {
      const block = event.target;
      // 'Enter' on a focused block marks the whole block; Ctrl or Cmd with it stays the send shortcut.
      if (event.key !== "Enter" || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
      if (!block.matches?.("[data-lines][tabindex]") || !art.contains(block)) return;
      event.preventDefault();
      fromBlock(block);
    });
    const onSelectionChange = () => {
      if (pop.hidden || pending?.mode !== "selection" || pop.contains(document.activeElement)) return;
      if (window.getSelection().isCollapsed) closePop(false);
    };
    document.addEventListener("selectionchange", onSelectionChange);

    // The ledger's list: each anchored mark sits beside the text it marks.
    function renderLedger() {
      const numbered = numberMarks(marks);
      big.textContent = String(numbered.length);
      big.setAttribute("aria-label", plural(numbered.length, "mark"));
      closeConfirm();
      const anchored = numbered.filter((m) => m.type !== "note");
      const notes = numbered.filter((m) => m.type === "note");
      lmarks.replaceChildren(...anchored.map(entry));
      if (!anchored.length) lmarks.append(el("p", { class: "empty" }, "No marks on the text yet. Select text in the artifact."));
      genHead.textContent = `General notes ${notes.length}`;
      gen.replaceChildren(...notes.map(entry));
      refreshButtons();
      layout();
    }

    function entry(m, done = false) {
      const acts = el("span", { class: "acts" });
      if (!done && m.type !== "strike") acts.append(el("button", { type: "button", "data-act": "edit", "aria-label": `Edit mark ${m.n}` }, "Edit"));
      if (!done) acts.append(el("button", { type: "button", "data-act": "remove", "aria-label": `Remove mark ${m.n}` }, "Remove"));
      const item = el(m.type === "note" && !done ? "li" : "div", { class: "note", ...(done ? {} : { "data-id": String(m.id) }) }, el("p", { class: "l nh" }, el("span", {}, `${pad(m.n)} ${LABEL[m.type]}${done ? " · Addressed" : ""}`), acts));
      if (m.type !== "note") item.append(el("p", { class: m.type === "strike" ? "q s" : "q" }, `“${m.quote}”`));
      if (m.type !== "strike") item.append(!done && editing === m.id ? editor(m) : el("p", { class: "t" }, m.text));
      if (!done) holderControl(controls, m.id, item, attachOptions(m.id));
      return item;
    }

    const markOf = (id) => marks.find((m) => m.id === id);
    const attachOptions = (id) => ({
      interaction: number,
      paths: markOf(id).attachments,
      count: () => attachedCount(marks) + attachedCount(Object.values(form())),
      onChange(next) {
        markOf(id).attachments = next;
        saveSoon();
        layout();
      },
    });

    function editor(m) {
      const mark = marks.find((x) => x.id === m.id);
      const original = mark.text;
      const input = el("input", { type: "text", "aria-label": `Text of mark ${m.n}`, value: mark.text });
      let done = false;
      const finish = (keep) => {
        if (done) return;
        done = true;
        mark.text = keep ? input.value.trim() || original : original;
        editing = null;
        renderLedger();
        saveSoon();
        ledger.querySelector(`[data-id="${m.id}"] [data-act="edit"]`)?.focus();
      };
      input.addEventListener("input", () => {
        mark.text = input.value;
        saveSoon();
      });
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !(event.metaKey || event.ctrlKey)) {
          event.preventDefault();
          finish(true);
        } else if (event.key === "Escape") {
          event.preventDefault();
          finish(false);
        }
      });
      input.addEventListener("blur", () => finish(true));
      return input;
    }

    async function removeMark(id) {
      if (!markOf(id)) return;
      if (attaching()) {
        err.textContent = BUSY;
        return;
      }
      // A mark leaves with its images, so the page and the server keep the same count.
      if (!(await discardImages(number, markOf(id).attachments))) {
        err.textContent = "Could not remove that mark's images. Try again.";
        return;
      }
      const index = marks.findIndex((m) => m.id === id);
      if (index < 0) return;
      controls.delete(id);
      closePop(false);
      unwrap(id);
      marks.splice(index, 1);
      if (editing === id) editing = null;
      renderLedger();
      saveSoon();
      (ledger.querySelector('[data-act="remove"]') ?? noteInput).focus();
    }

    function onLedgerClick(event) {
      const button = event.target.closest("button[data-act]");
      const id = Number(button?.closest("[data-id]")?.dataset.id);
      if (!button || !Number.isInteger(id)) return;
      if (button.dataset.act === "remove") removeMark(id);
      else if (button.dataset.act === "edit") {
        editing = id;
        renderLedger();
        ledger.querySelector(`[data-id="${id}"] input`)?.focus();
      }
    }
    lmarks.addEventListener("click", onLedgerClick);
    gen.addEventListener("click", onLedgerClick);
    noteForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = noteInput.value.trim();
      if (!text) return;
      marks.push({ id: nextId++, type: "note", text, attachments: [] });
      noteInput.value = "";
      renderLedger();
      saveSoon();
      noteInput.focus();
    });

    function layout() {
      lmarks.classList.remove("abs");
      lmarks.style.height = "";
      for (const stale of lmarks.querySelectorAll(".cn")) stale.remove();
      const notes = [...lmarks.querySelectorAll(".note")];
      for (const note of notes) note.style.top = "";
      if (!notes.length || window.innerWidth < 720 || ledger.hidden) return;
      const wrapBox = lmarks.getBoundingClientRect();
      const items = notes.map((note) => {
        const span = art.querySelector(`[data-mark="${note.dataset.id}"]`);
        const rect = span?.getClientRects()[0];
        const block = span?.closest("[data-lines]");
        if (!rect || !block) return { note, ay: Infinity, bx: 0 };
        return { note, ay: Math.round(rect.top + rect.height / 2 - wrapBox.top), bx: Math.round(block.getBoundingClientRect().right - wrapBox.left) };
      });
      if (items.every((item) => item.ay === Infinity)) return;
      lmarks.classList.add("abs");
      let prev = -12;
      for (const item of items.sort(byPosition)) {
        const top = Math.max(Number.isFinite(item.ay) ? item.ay - 8 : 0, prev + 12, 0);
        item.note.style.top = `${top}px`;
        prev = top + item.note.offsetHeight;
        if (!Number.isFinite(item.ay)) continue;
        const across = el("div", { class: "cn" });
        across.style.cssText = `left:${Math.min(item.bx, 0)}px;width:${Math.max(0, -item.bx)}px;top:${item.ay}px`;
        lmarks.append(across);
        if (top > item.ay) {
          const down = el("div", { class: "cn v" });
          down.style.cssText = `left:0;top:${item.ay}px;height:${top - item.ay}px`;
          lmarks.append(down);
        }
      }
      lmarks.style.height = `${Math.max(prev, 0)}px`;
    }
    window.addEventListener("resize", layout);
    const watcher = new ResizeObserver(layout);
    watcher.observe(art);

    // Sending.
    function refused() {
      const current = form();
      const name = roundRefusal(decisions, current);
      if (name === null) {
        err.textContent = "";
        return false;
      }
      err.textContent = refusalMessage(name);
      ui.focusQuestion(unansweredOwn(decisions, current).id);
      return true;
    }

    async function submit(verdict) {
      closeConfirm();
      sending = true;
      err.textContent = "";
      refreshButtons();
      const problem = await ctx.send(readbackResponse(verdict, version, decisions, form(), marks), "The response was refused.");
      if (alive) err.textContent = problem;
      sending = false;
      if (alive) refreshButtons();
    }

    function closeConfirm() {
      dialog.hidden = true;
      dialog.replaceChildren();
    }

    function tryApprove() {
      if (sending || older() || refused()) return;
      if (!marks.length) return submit("approve");
      const yes = el("button", { type: "button", class: "go" }, `Approve and discard ${plural(marks.length, "mark")}`);
      const no = el("button", { type: "button" }, "Keep marking");
      yes.addEventListener("click", () => submit("approve"));
      no.addEventListener("click", () => {
        closeConfirm();
        approve.focus();
      });
      dialog.replaceChildren(el("p", { id: "rb-confirm" }, `Approving discards your ${plural(marks.length, "mark")}.`), el("div", { class: "ar" }, yes, no));
      dialog.hidden = false;
      yes.focus();
    }

    approve.addEventListener("click", tryApprove);
    send.addEventListener("click", () => {
      if (sending || send.disabled || refused()) return;
      submit("changes");
    });
    dialog.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      closeConfirm();
      approve.focus();
    });
    const onKey = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key.toLowerCase() === "a") {
        event.preventDefault();
        tryApprove();
      }
    };
    document.addEventListener("keydown", onKey);
    ctx.setSend(send);

    addressed.replaceChildren(...(asked.length ? [el("p", { class: "l" }, `Addressed from v${prior.version} ${asked.length}`), ...asked.map((m) => entry(m, true))] : []));
    const valueText = (n) => (n === version ? `v${n}` : `v${n}, older, read-only`);
    const readout = el("output", { class: "l", id: "verOut", for: "ver" });
    const slot = document.getElementById("agendaTools");
    if (known.length > 1) {
      const input = el("input", { id: "ver", type: "range", min: String(known[0]), max: String(known.at(-1)), step: "1", value: String(shown), "aria-valuetext": valueText(shown) });
      input.addEventListener("input", () => {
        shown = Number(input.value);
        input.setAttribute("aria-valuetext", valueText(shown));
        history.replaceState(history.state, "", `${location.pathname}${location.search}#version=${shown}`);
        closePop(false);
        refreshButtons();
        load();
      });
      slot.replaceChildren(el("div", { class: "ver" }, el("div", { class: "row" }, el("label", { class: "sr", for: "ver" }, "Version"), el("span", { class: "l", "aria-hidden": "true" }, `v${known[0]}`), input, el("span", { class: "l", "aria-hidden": "true" }, `v${known.at(-1)}`)), readout));
    }

    const sources = new Map();
    async function sourceOf(n) {
      if (!sources.has(n)) {
        const res = await getFile(`pilot/versions/${artifact}/${String(n).padStart(3, "0")}.md`);
        if (!res.ok) throw new Error(`file ${res.status}`);
        sources.set(n, await res.text());
      }
      return sources.get(n);
    }

    // The source text of each block of the version the user last marked up.
    let priorBlocks = null;
    const priorSources = () => (priorBlocks ??= sourceOf(prior.version).then((text) => renderMarkdown(text, document.createElement("div"))).then((found) => found.map((b) => b.source)).catch((error) => {
      priorBlocks = null;
      throw error;
    }));

    async function load() {
      const mine = ++requested;
      const stale = () => !alive || mine !== requested;
      const guide = older() ? OLDER_HINT(shown, version) : HINT;
      hint.textContent = guide;
      art.setAttribute("aria-label", `Artifact: ${title}. ${guide}`);
      try {
        const next = await renderMarkdown(await sourceOf(shown), art);
        if (stale()) return;
        blocks = next;
      } catch {
        if (stale()) return;
        art.textContent = "The artifact could not be loaded.";
        blocks = [];
      }
      let before = [];
      let diff = null;
      if (revised && shown > prior.version && blocks.length) {
        try {
          before = await priorSources();
          diff = diffBlocks(before, blocks.map((b) => b.source));
        } catch {
          // Without the earlier version nothing can be shown as changed.
        }
        if (stale()) return;
      }
      if (!older()) {
        for (const block of blocks) block.el.setAttribute("tabindex", "0");
        for (const mark of marks) if (mark.type !== "note") draw(mark);
      }
      for (const index of diff?.changed ?? []) {
        blocks[index].el.classList.add("changed");
        blocks[index].el.append(el("span", { class: "chg" }, "CHANGED"));
      }
      removedBox.hidden = !diff?.removed.length;
      removedBox.replaceChildren(...(diff?.removed.length ? [el("p", { class: "l" }, `Removed ${diff.removed.length}`), el("ul", { "aria-label": "Removed blocks" }, ...diff.removed.map((index) => el("li", {}, before[index])))] : []));
      readout.textContent = `v${shown} · ${plural(blocks.length, "block")}${diff ? ` · ${diff.changed.length} changed` : ""}`;
      renderLedger();
    }

    renderLedger();
    load();

    live = {
      stop() {
        alive = false;
        document.removeEventListener("keydown", onKey);
        document.removeEventListener("selectionchange", onSelectionChange);
        window.removeEventListener("resize", layout);
        watcher.disconnect();
        slot.replaceChildren();
      },
    };
  },
  unmount() {
    live?.stop();
    live = null;
  },
};
