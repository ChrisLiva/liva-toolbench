import { getFile } from "/page/api.js";
import { sandboxFrame } from "/page/render.js";
import { el, mac } from "/page/questions.js";
import { attachedCount, numberPins, prototypeFrom, prototypeResponse, verdictRefusal } from "/page/model.js";
import { BUSY, attaching, holderControl, mountAttach } from "/page/attach.js";

const DRAFT_MS = 1000;
const LEADING = 80;

// Runs inside the variant's frame. With comment mode on it swallows the click and reports the element it landed on;
// the frame's origin is opaque, so its postMessage must target every origin and the page checks event.source.
const PICKER =
  "(()=>{let on=false;" +
  "const css=document.createElement('style');css.textContent='html.pilot-pick,html.pilot-pick *{cursor:crosshair!important}';document.head.append(css);" +
  "const path=(node)=>{const parts=[];for(;node&&node.nodeType===1&&node!==document.documentElement;node=node.parentElement){" +
  "if(node.id){parts.unshift('#'+CSS.escape(node.id));break}let n=1;" +
  "for(let s=node.previousElementSibling;s;s=s.previousElementSibling)if(s.localName===node.localName)n++;" +
  "parts.unshift(node.localName+':nth-of-type('+n+')')}return parts.join(' > ')};" +
  "addEventListener('message',(e)=>{if(e.source!==parent||!e.data||typeof e.data.pilotPick!=='boolean')return;" +
  "on=e.data.pilotPick;document.documentElement.classList.toggle('pilot-pick',on)});" +
  "addEventListener('click',(e)=>{if(!on)return;e.preventDefault();e.stopImmediatePropagation();" +
  `const text=(e.target.textContent||'').replace(/\\s+/g,' ').trim().slice(0,${LEADING});` +
  "parent.postMessage({pilotPick:{selector:path(e.target),leading_text:text}},'*')},true)})();";

const hashKey = () => new URLSearchParams(location.hash.slice(1)).get("variant");

let live = null;

export const surface = {
  mount(stage, state, ctx) {
    const { number, question, variants } = state.interaction;
    let { verdict, pins } = prototypeFrom(variants, state.draft);
    let index = Math.max(0, variants.findIndex((v) => v.key === hashKey()));
    let picking = false;
    let frame = null;
    let shown = 0;
    let alive = true;
    let timer = null;
    const texts = new Map();
    // One attach control per pin, kept across the list's redraws (see `holderControl`).
    const controls = new Map();
    const count = () => attachedCount(verdict, pins);

    const prev = el("button", { type: "button" }, "Previous");
    const next = el("button", { type: "button" }, "Next");
    const label = el("p", { class: "l", role: "status" });
    const mode = el("button", { type: "button", "aria-pressed": "false" }, "Comment mode");
    const hint = el("p", { class: "l", role: "status" });
    const box = el("div", { class: "vstage" });
    const ask = el("div", { class: "pinask" });
    stage.querySelector("#reading").append(
      el("h2", { class: "pq" }, question),
      box,
      el("div", { class: "vsw" }, prev, label, next),
      el("div", { class: "vmode" }, mode, hint),
      ask,
    );

    const big = el("p", { class: "big", role: "img" });
    const sub = el("p", { class: "l lsub" });
    const list = el("ol", { class: "pins", "aria-label": "Pinned comments" });
    const err = el("p", { class: "err", role: "alert" });
    const win = el("fieldset", { class: "win" }, el("legend", { class: "l" }, "Winner"));
    for (const v of variants) {
      const radio = el("input", { type: "radio", name: "winner", id: `win-${v.key}`, value: v.key });
      radio.defaultChecked = radio.checked = verdict.winner === v.key;
      radio.addEventListener("change", () => {
        verdict.winner = v.key;
        changed();
      });
      win.append(el("label", { for: radio.id }, radio, `${v.key} · ${v.name}`));
    }
    const area = (field, title) => {
      const input = el("textarea", { rows: "3" });
      input.value = verdict[field];
      input.addEventListener("input", () => {
        verdict[field] = input.value;
        changed();
      });
      return el("label", { class: "field" }, el("span", { class: "l" }, title), input);
    };
    const send = el("button", { type: "button", class: "go", "aria-keyshortcuts": "Control+Enter Meta+Enter" }, "Send verdict");
    const foot = el("div", { class: "lfoot vfoot" }, win, area("take", "What to take from the others"), area("leave_out", "What to leave out"));
    mountAttach(foot, {
      interaction: number,
      paths: verdict.attachments,
      count,
      onChange(next) {
        verdict.attachments = next;
        changed();
      },
    });
    stage.querySelector("#ledger").append(
      el("p", { class: "l" }, "Variant"),
      big,
      sub,
      list,
      foot,
      err,
      el("div", { class: "lact" }, el("div", { class: "ar" }, send, el("kbd", {}, mac ? "⌘↵" : "Ctrl+Enter"))),
    );

    const saveNow = () => {
      timer = null;
      Promise.resolve(ctx.saveDraft({ verdict, pins })).catch(() => {});
    };
    const changed = () => {
      err.textContent = "";
      paintPins();
      clearTimeout(timer);
      timer = setTimeout(saveNow, DRAFT_MS);
    };

    function paintPins() {
      sub.textContent = `of ${variants.length} variants · ${pins.length} pinned comment${pins.length === 1 ? "" : "s"}`;
      list.replaceChildren(
        ...numberPins(pins).map((pin, i) => {
          const item = el("li", {}, el("span", { class: "l" }, `Variant ${pin.variant} · Pin ${pin.n}`), el("span", { class: "pt" }, pin.text), el("span", { class: "sel" }, pin.selector));
          holderControl(controls, i, item, {
            interaction: number,
            paths: pins[i].attachments,
            count,
            onChange(next) {
              pins[i].attachments = next;
              changed();
            },
          });
          return item;
        }),
      );
    }

    function closeAsk(refocus) {
      ask.replaceChildren();
      if (refocus) mode.focus();
    }

    function openAsk(pick) {
      const v = variants[index];
      const input = el("input", { type: "text", required: "", placeholder: "What should change here?" });
      const form = el(
        "form",
        { class: "pinform" },
        el("label", { class: "field" }, el("span", { class: "l" }, `Comment on ${pick.selector}`), input),
        el("div", { class: "ar" }, el("button", { type: "submit" }, "Pin comment"), el("button", { type: "button" }, "Cancel")),
      );
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!input.value.trim()) {
          input.value = "";
          input.reportValidity();
          return;
        }
        pins.push({ variant: v.key, selector: pick.selector, leading_text: pick.leading_text, text: input.value.trim(), attachments: [] });
        closeAsk(true);
        changed();
      });
      form.querySelector("button[type=button]").addEventListener("click", () => closeAsk(true));
      input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeAsk(true);
      });
      ask.replaceChildren(form);
      input.focus();
    }

    async function variantText(v) {
      if (!texts.has(v.key)) {
        const res = await getFile(v.file);
        if (!res.ok) throw new Error(`file ${res.status}`);
        texts.set(v.key, await res.text());
      }
      return texts.get(v.key);
    }

    async function show(to) {
      index = (to + variants.length) % variants.length;
      const v = variants[index];
      const mine = ++shown;
      label.textContent = `${v.key} · ${v.name}`;
      big.textContent = v.key;
      big.setAttribute("aria-label", `Variant ${v.key}`);
      history.replaceState(history.state, "", `#variant=${encodeURIComponent(v.key)}`);
      closeAsk(false);
      frame = null;
      box.replaceChildren(el("p", { class: "l vmsg" }, "Loading the variant"));
      try {
        const html = await variantText(v);
        if (!alive || mine !== shown) return;
        frame = sandboxFrame(html, { script: PICKER });
        frame.className = "pframe";
        frame.title = `Variant ${v.key}: ${v.name}`;
        const pushed = frame;
        frame.addEventListener("load", () => pushed.contentWindow.postMessage({ pilotPick: picking }, "*"));
        box.replaceChildren(frame);
      } catch {
        if (alive && mine === shown) box.replaceChildren(el("p", { class: "l vmsg" }, `Could not load variant ${v.key}.`));
      }
    }

    const onMessage = (event) => {
      const pick = event.data?.pilotPick;
      if (!frame || event.source !== frame.contentWindow || !picking) return;
      if (typeof pick?.selector !== "string" || typeof pick.leading_text !== "string") return;
      openAsk({ selector: pick.selector, leading_text: pick.leading_text.slice(0, LEADING) });
    };
    window.addEventListener("message", onMessage);

    prev.addEventListener("click", () => show(index - 1));
    next.addEventListener("click", () => show(index + 1));
    mode.addEventListener("click", () => {
      picking = !picking;
      mode.setAttribute("aria-pressed", String(picking));
      box.classList.toggle("picking", picking);
      hint.textContent = picking ? "Click an element of the variant to pin a comment" : "";
      if (!picking) closeAsk(false);
      frame?.contentWindow?.postMessage({ pilotPick: picking }, "*");
    });

    send.addEventListener("click", async () => {
      const refusal = verdictRefusal(verdict);
      if (refusal) {
        err.textContent = refusal;
        win.querySelector("input").focus();
        return;
      }
      if (attaching()) {
        err.textContent = BUSY;
        return;
      }
      err.textContent = "";
      send.disabled = true;
      try {
        const res = await ctx.send(prototypeResponse(verdict, pins));
        // 201 and 409 are app.js's: it shows the wait, or the interaction that replaced this one.
        if (res.status === 400 && alive) {
          const body = await res.json().catch(() => ({}));
          err.textContent = body.problems?.[0] ?? "The verdict was refused.";
        }
      } catch {
        if (alive) err.textContent = "Could not send. Try again.";
      }
      send.disabled = false;
    });
    ctx.setSend(send);

    paintPins();
    show(index);
    live = {
      stop() {
        alive = false;
        clearTimeout(timer);
        window.removeEventListener("message", onMessage);
      },
    };
  },
  unmount() {
    live?.stop();
    live = null;
  },
};
