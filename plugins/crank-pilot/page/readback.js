import { getFile } from "/page/api.js";
import { renderMarkdown } from "/page/render.js";
import { anchoring, plain } from "/page/anchor.js";
import { el, mac, plural, sendControl } from "/page/dom.js";
import { mountQuestions } from "/page/questions.js";
import {
  attachedCount,
  canSendChanges,
  diffBlocks,
  headingAbove,
  marksFrom,
  numberMarks,
  occurrenceOf,
  readbackResponse,
  refusalMessage,
  unansweredOwn,
} from "/page/model.js";
import { BUSY, attaching, discardImages, holderControl } from "/page/attach.js";

const HINT =
  "Select text, or focus a block and press Enter, to comment on it or strike it.";
const OLDER_HINT = (shown, current) =>
  `Version ${shown} is read-only. Move the version control to v${current} to mark.`;
const LABEL = { comment: "Comment", strike: "Strike", note: "Note" };
const pad = (n) => String(n).padStart(2, "0");

const byPosition = (a, b) => (a.ay === b.ay ? 0 : a.ay < b.ay ? -1 : 1);

export const surface = {
  mount(stage, state, ctx) {
    const {
      number,
      title,
      artifact,
      version,
      lead,
      judgment_calls: calls,
      review_landed: landed,
      edits,
      decisions,
    } = state.interaction;
    const known =
      Array.isArray(state.versions) && state.versions.length
        ? state.versions
        : [version];
    const prior = state.prior ?? null;
    // A revision: the version on offer is not the one the user last marked up.
    const revised = prior !== null && prior.version !== version;
    const asked = revised ? prior.marks : [];
    const draft =
      state.draft && typeof state.draft === "object" ? state.draft : {};
    const reading = stage.querySelector("#reading");
    const ledger = stage.querySelector("#ledger");

    let marks = marksFrom(draft.marks);
    let nextId = marks.reduce((high, m) => Math.max(high, m.id), 0) + 1;
    let blocks = [];
    /** @type {ReturnType<typeof mountQuestions> | null} */
    let ui = null;
    /** @type {{ pieces: any[], raw: any, mode: string, returnTo: HTMLElement | null } | null} */
    let pending = null;
    /** @type {number | null} */
    let editing = null;
    let sending = false;
    let alive = true;
    let requested = 0;
    const controls = new Map();
    const hashed = Number(
      new URLSearchParams(location.hash.slice(1)).get("version"),
    );
    let shown = known.includes(hashed) ? hashed : version;
    const older = () => shown !== version;

    const art = el("div", {
      class: "art",
      role: "group",
      "aria-label": `Artifact: ${title}. ${HINT}`,
    });
    const { piecesIn, trimmed, anchorFor, wrap, draw, unwrap, blockIndex } =
      anchoring(art, () => blocks);
    const hint = el("p", { class: "l status", role: "status" }, HINT);
    const pop = el("div", {
      id: "pop",
      role: "group",
      "aria-label": "Mark the selected text",
      hidden: "",
    });

    const above = [];
    if (lead) above.push(el("p", { class: "lead" }, lead));
    for (const [label, items] of [
      ["Judgment calls", calls],
      ["Landed by review", landed],
      ["Edits since the last version", edits],
    ]) {
      if (!items?.length) continue;
      above.push(
        el(
          "div",
          { class: "calls" },
          el("p", { class: "l" }, `${label} ${items.length}`),
          el("ul", {}, ...items.map((text) => el("li", {}, text))),
        ),
      );
    }
    reading.append(...above);
    if (decisions.length) {
      const open = el(
        "div",
        { class: "decisions" },
        el("p", { class: "l" }, `Open decisions ${decisions.length}`),
      );
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

    const big = el("p", { class: "big", role: "img" });
    const lmarks = el("div", { class: "lmarks" });
    const genHead = el("p", { class: "l" });
    const gen = el("ul", { class: "gen" });
    const noteInput = el("input", {
      type: "text",
      placeholder: "A note on the whole artifact",
    });
    const noteAdd = el("button", { type: "submit" }, "Add note");
    const noteForm = el(
      "form",
      { autocomplete: "off" },
      el(
        "div",
        { class: "addrow" },
        el(
          "label",
          { class: "field" },
          el("span", { class: "l" }, "Add a general note"),
          noteInput,
        ),
        noteAdd,
      ),
    );
    const err = el("p", { class: "err", role: "alert" });
    const approve = el(
      "button",
      {
        type: "button",
        class: "go",
        "aria-keyshortcuts": "Control+Shift+A Meta+Shift+A",
      },
      "Approve",
    );
    const [send, sendHint] = sendControl("Send changes");
    const dialog = el("div", {
      role: "alertdialog",
      class: "confirm",
      "aria-labelledby": "rb-confirm",
      hidden: "",
    });
    const addressed = el("div", { class: "addr" });
    ledger.append(
      el("p", { class: "l" }, `Marks on v${version}`),
      big,
      lmarks,
      addressed,
      el("div", { class: "lfoot" }, genHead, gen, noteForm),
      err,
      el(
        "div",
        { class: "lact" },
        dialog,
        el(
          "div",
          { class: "ar" },
          approve,
          el("kbd", {}, mac ? "⌘⇧A" : "Ctrl+Shift+A"),
        ),
        el("div", { class: "ar" }, send, sendHint),
      ),
    );

    function saveSoon() {
      ctx.saveDraftSoon({ form: form(), marks });
    }

    function refreshButtons() {
      send.textContent = marks.length
        ? `Send changes (${plural(marks.length, "mark")})`
        : "Send changes";
      send.disabled =
        sending || older() || !canSendChanges(marks, decisions, form());
      approve.disabled = sending || older();
      noteInput.disabled = older();
      noteAdd.disabled = older();
    }

    function showButtons(problem) {
      pop.replaceChildren(
        el("button", { type: "button", "data-act": "comment" }, "Comment"),
        el("button", { type: "button", "data-act": "strike" }, "Strike"),
        ...(problem
          ? [el("p", { class: "perr", role: "alert" }, problem)]
          : []),
      );
      if (problem)
        for (const button of pop.querySelectorAll("button"))
          button.disabled = true;
    }

    function placePop(rect) {
      pop.hidden = false;
      const sx = window.scrollX;
      const sy = window.scrollY;
      const left = Math.min(
        Math.max(8, rect.left + sx),
        sx + document.documentElement.clientWidth - pop.offsetWidth - 8,
      );
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
      else if (pieces.some((p) => p.node.parentElement.closest(".mk")))
        problem = "That text already has a mark.";
      pending = problem ? null : { pieces, raw: plain(range), mode, returnTo };
      showButtons(problem);
      placePop(range.getBoundingClientRect());
    }

    function fromSelection() {
      setTimeout(() => {
        if (
          !alive ||
          older() ||
          (pop.contains(document.activeElement) &&
            /** @type {Element} */ (document.activeElement).tagName === "INPUT")
        )
          return;
        const selection = /** @type {Selection} */ (window.getSelection());
        if (!selection.rangeCount || selection.isCollapsed)
          return closePop(false);
        const range = selection.getRangeAt(0);
        if (!art.contains(range.commonAncestorContainer))
          return closePop(false);
        propose(range.cloneRange(), "selection", null);
      }, 0);
    }

    function fromBlock(block) {
      const range = document.createRange();
      range.selectNodeContents(block);
      propose(range, "block", block);
      pop.querySelector("button").focus();
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
        occurrence: anchor.crosses
          ? 1
          : occurrenceOf(anchor.block.textContent, anchor.quote, anchor.start),
        start: anchor.start,
        ...(anchor.crosses ? { end: anchor.end } : {}),
        attachments: [],
      };
      if (!wrap(p.pieces, mark)) return;
      nextId++;
      marks.push(mark);
      /** @type {Selection} */ (window.getSelection()).removeAllRanges();
      const markNumber = numberMarks(marks).find((m) => m.id === mark.id).n;
      closePop(true);
      hint.textContent = `Added mark ${markNumber}.`;
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
        const input = el("input", {
          type: "text",
          "aria-label": "Comment text",
          placeholder: "Your comment",
        });
        pop.replaceChildren(
          input,
          el("button", { type: "button", "data-act": "add" }, "Add"),
          el("button", { type: "button", "data-act": "cancel" }, "Cancel"),
        );
        placePop(
          pending
            ? pending.pieces[0].node.parentElement.getBoundingClientRect()
            : pop.getBoundingClientRect(),
        );
        input.focus();
      } else if (act === "add") {
        const value = pop.querySelector("input").value.trim();
        if (value) commit("comment", value);
        else pop.querySelector("input").focus();
      } else if (act === "cancel") closePop(true);
    });
    pop.addEventListener("keydown", (event) => {
      if (
        event.key === "Enter" &&
        event.target.tagName === "INPUT" &&
        !(event.metaKey || event.ctrlKey)
      ) {
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
      if (
        event.key !== "Enter" ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        event.shiftKey
      )
        return;
      if (!block.matches("[data-lines][tabindex]") || !art.contains(block))
        return;
      event.preventDefault();
      fromBlock(block);
    });
    const onSelectionChange = () => {
      if (
        pop.hidden ||
        pending?.mode !== "selection" ||
        pop.contains(document.activeElement)
      )
        return;
      if (/** @type {Selection} */ (window.getSelection()).isCollapsed)
        closePop(false);
    };
    document.addEventListener("selectionchange", onSelectionChange);

    function renderLedger() {
      const numbered = numberMarks(marks);
      big.textContent = String(numbered.length);
      big.setAttribute("aria-label", plural(numbered.length, "mark"));
      closeConfirm();
      const anchored = numbered.filter((m) => m.type !== "note");
      const notes = numbered.filter((m) => m.type === "note");
      lmarks.replaceChildren(...anchored.map(entry));
      if (!anchored.length)
        lmarks.append(
          el(
            "p",
            { class: "empty" },
            "No marks on the text yet. Select text in the artifact.",
          ),
        );
      genHead.textContent = `General notes ${notes.length}`;
      gen.replaceChildren(...notes.map(entry));
      refreshButtons();
      layout();
    }

    /** @param {boolean | number} [done] `.map(entry)` passes the index here. */
    function entry(m, done = false) {
      const acts = el("span", { class: "acts" });
      if (!done && m.type !== "strike")
        acts.append(
          el(
            "button",
            {
              type: "button",
              "data-act": "edit",
              "aria-label": `Edit mark ${m.n}`,
            },
            "Edit",
          ),
        );
      if (!done)
        acts.append(
          el(
            "button",
            {
              type: "button",
              "data-act": "remove",
              "aria-label": `Remove mark ${m.n}`,
            },
            "Remove",
          ),
        );
      const item = el(
        m.type === "note" && !done ? "li" : "div",
        { class: "note", ...(done ? {} : { "data-id": String(m.id) }) },
        el(
          "p",
          { class: "l nh" },
          el(
            "span",
            {},
            `${pad(m.n)} ${LABEL[m.type]}${done ? " · Addressed" : ""}`,
          ),
          acts,
        ),
      );
      if (m.type !== "note")
        item.append(
          el("p", { class: m.type === "strike" ? "q s" : "q" }, `“${m.quote}”`),
        );
      if (m.type !== "strike")
        item.append(
          !done && editing === m.id
            ? editor(m)
            : el("p", { class: "t" }, m.text),
        );
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
      const input = el("input", {
        type: "text",
        "aria-label": `Text of mark ${m.n}`,
        value: mark.text,
      });
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
        return {
          note,
          ay: Math.round(rect.top + rect.height / 2 - wrapBox.top),
          bx: Math.round(block.getBoundingClientRect().right - wrapBox.left),
        };
      });
      if (items.every((item) => item.ay === Infinity)) return;
      lmarks.classList.add("abs");
      let prev = -12;
      for (const item of items.toSorted(byPosition)) {
        const top = Math.max(
          Number.isFinite(item.ay) ? item.ay - 8 : 0,
          prev + 12,
        );
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
      lmarks.style.height = `${prev}px`;
    }
    window.addEventListener("resize", layout);
    const watcher = new ResizeObserver(layout);
    watcher.observe(art);

    function refused() {
      const open = unansweredOwn(decisions, form());
      if (!open) {
        err.textContent = "";
        return false;
      }
      err.textContent = refusalMessage(open.title);
      /** @type {NonNullable<typeof ui>} */ (ui).focusQuestion(open.id);
      return true;
    }

    async function submit(verdict) {
      closeConfirm();
      sending = true;
      err.textContent = "";
      refreshButtons();
      const problem = await ctx.send(
        readbackResponse(verdict, version, decisions, form(), marks),
        "The response was refused.",
      );
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
      const yes = el(
        "button",
        { type: "button", class: "go" },
        `Approve and discard ${plural(marks.length, "mark")}`,
      );
      const no = el("button", { type: "button" }, "Keep marking");
      yes.addEventListener("click", () => submit("approve"));
      no.addEventListener("click", () => {
        closeConfirm();
        approve.focus();
      });
      dialog.replaceChildren(
        el(
          "p",
          { id: "rb-confirm" },
          `Approving discards your ${plural(marks.length, "mark")}.`,
        ),
        el("div", { class: "ar" }, yes, no),
      );
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
      if (
        (event.metaKey || event.ctrlKey) &&
        event.shiftKey &&
        event.key.toLowerCase() === "a"
      ) {
        event.preventDefault();
        tryApprove();
      }
    };
    document.addEventListener("keydown", onKey);
    ctx.setSend(send);

    addressed.replaceChildren(
      ...(asked.length
        ? [
            el(
              "p",
              { class: "l" },
              `Addressed from v${prior.version} ${asked.length}`,
            ),
            ...asked.map((m) => entry(m, true)),
          ]
        : []),
    );
    const valueText = (n) =>
      n === version ? `v${n}` : `v${n}, older, read-only`;
    const readout = el("output", { class: "l", id: "verOut", for: "ver" });
    const slot = /** @type {HTMLElement} */ (
      document.getElementById("agendaTools")
    );
    if (known.length > 1) {
      const input = el("input", {
        id: "ver",
        type: "range",
        min: String(known[0]),
        max: String(known.at(-1)),
        step: "1",
        value: String(shown),
        "aria-valuetext": valueText(shown),
      });
      input.addEventListener("input", () => {
        shown = Number(input.value);
        input.setAttribute("aria-valuetext", valueText(shown));
        history.replaceState(
          history.state,
          "",
          `${location.pathname}${location.search}#version=${shown}`,
        );
        closePop(false);
        refreshButtons();
        load();
      });
      slot.replaceChildren(
        el(
          "div",
          { class: "ver" },
          el(
            "div",
            { class: "row" },
            el("label", { class: "sr", for: "ver" }, "Version"),
            el("span", { class: "l", "aria-hidden": "true" }, `v${known[0]}`),
            input,
            el(
              "span",
              { class: "l", "aria-hidden": "true" },
              `v${known.at(-1)}`,
            ),
          ),
          readout,
        ),
      );
    }

    const sources = new Map();
    async function sourceOf(n) {
      if (!sources.has(n)) {
        const res = await getFile(
          `pilot/versions/${artifact}/${String(n).padStart(3, "0")}.md`,
        );
        if (!res.ok) throw new Error(`file ${res.status}`);
        sources.set(n, await res.text());
      }
      return sources.get(n);
    }

    // The source text of each block of the version the user last marked up.
    /** @type {Promise<any[]> | null} */
    let priorBlocks = null;
    const priorSources = () =>
      (priorBlocks ??= sourceOf(prior.version)
        .then((text) => renderMarkdown(text, document.createElement("div")))
        .then((found) => found.map((b) => b.source))
        .catch((error) => {
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
      /** @type {ReturnType<typeof diffBlocks> | null} */
      let diff = null;
      if (revised && shown > prior.version && blocks.length) {
        try {
          before = await priorSources();
          diff = diffBlocks(
            before,
            blocks.map((b) => b.source),
          );
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
      removedBox.replaceChildren(
        ...(diff?.removed.length
          ? [
              el("p", { class: "l" }, `Removed ${diff.removed.length}`),
              el(
                "ul",
                { "aria-label": "Removed blocks" },
                ...diff.removed.map((index) => el("li", {}, before[index])),
              ),
            ]
          : []),
      );
      readout.textContent = `v${shown} · ${plural(blocks.length, "block")}${diff ? ` · ${diff.changed.length} changed` : ""}`;
      renderLedger();
    }

    renderLedger();
    load();

    return () => {
      alive = false;
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("selectionchange", onSelectionChange);
      window.removeEventListener("resize", layout);
      watcher.disconnect();
      slot.replaceChildren();
    };
  },
};
