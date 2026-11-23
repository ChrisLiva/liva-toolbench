import { linesOf } from "/page/render.js";

// Anchoring: places a mark in the rendered text and reads a selection back as a mark's anchor.

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
export const plain = (range) => {
  const copy = range.cloneContents();
  for (const label of copy.querySelectorAll(".chg")) label.remove();
  return copy.textContent;
};

export function anchoring(art, getBlocks) {
  const blockOf = (node) => {
    const host = node?.nodeType === 1 ? node : node?.parentElement;
    const found = host?.closest("[data-lines]");
    return found && art.contains(found) ? found : null;
  };

  // Leaves out the blank text between blocks.
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
    getBlocks().forEach((b, i) => {
      if (b.el === block || b.el.contains(block) || b.el.compareDocumentPosition(block) & Node.DOCUMENT_POSITION_FOLLOWING) found = i;
    });
    return found;
  }
  return { blockOf, piecesIn, trimmed, anchorFor, rangeFor, wrap, draw, unwrap, blockIndex };
}
