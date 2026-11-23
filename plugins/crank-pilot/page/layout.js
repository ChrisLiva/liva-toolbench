import { el } from "/page/dom.js";

const byPosition = (a, b) => (a.ay === b.ay ? 0 : a.ay < b.ay ? -1 : 1);

// Places each note beside its marked span in the artifact and draws the
// connectors; below 720px, or with no marks anchored, notes stay in flow.
export function layoutNotes(lmarks, art, ledger) {
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
    const top = Math.max(Number.isFinite(item.ay) ? item.ay - 8 : 0, prev + 12);
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
