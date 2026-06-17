# HTML review artifact — shared by `crank:crank-spec` and `crank:crank-plan`

Render the finished spec / plan as a **single self-contained HTML page**, open it in the user's browser, and let them comment inline and ship those comments back with one click. The markdown temp file stays the source of truth — this HTML is a review *lens*, not a re-typeset of the doc.

This runs only in the **Hand back** step of a standalone run. Under `/crank` (headless) the hand-back is skipped entirely, so this never fires — no browser pop-up mid-pipeline.

## What the page is for — read this before you render anything

The full markdown is embedded verbatim in the page (the export reads it for "Copy … + comments"), and the temp `.md` is the truth. So the **visible** page never has to *contain* the doc — it has to make a potentially large doc **graspable, walkable, and easy to react to**. It has exactly three jobs, in order:

1. **Orient** — in ~5 seconds the reader sees the *shape*: how big, how the pieces connect, what's covered, what's risky. Numbers and one diagram, not paragraphs.
2. **Walk** — the reader moves through the doc **one bite at a time** (a focus stepper), never faced with a wall of every task at once.
3. **React** — they comment on any piece, flag scope cuts back in, and export — all without touching the markdown.

### The anti-wordiness rules (hard constraints)

The #1 failure mode is transcribing the doc onto the page. Don't. Obey these:

- **No prose paragraph from the doc appears on the page.** Every section becomes a *number, badge, table row, diagram node, or one-line essence*. If the doc has a paragraph, distill it to its claim; the full text is already in the embedded markdown.
- **Each card shows only what a reviewer must judge** — for a **plan** task: its one outcome + the verify/seam line; for a **spec**: the single falsifiable criterion. Supporting detail goes behind a `<details>` "full text" toggle or stays only in the embedded markdown.
- **If a thing can be a number, badge, row, or node, it is one** — never a sentence.
- **Lead every region with the visual** (a diagram, the stat strip, a table). Prose is the last resort, never the default.
- **Word budgets:** task/criterion title ≤ ~10 words · step line ≤ ~14 words on **one** line, imperative · any card essence ≤ 2 lines · decision/why cell ≤ ~6 words. Over budget → cut or move it to the embedded markdown.
- **Scale by collapsing, not by growing.** A 25-task plan is still one card on screen (the stepper) plus one map — never 25 stacked cards. If the page gets long, you transcribed; delete.

A good page can be skimmed in under a minute and still lets the reader leave a precise comment on task 17. If yours reads like the markdown with fonts, start over.

## Render & open

1. The doc lives at a markdown temp path (call it `$MD`). Write the HTML beside it: `HTML="${MD%.md}.html"`.
2. Render the page (below) and write it to `$HTML`.
3. Open it: `open "$HTML"` (macOS) · `xdg-open "$HTML"` (Linux) · `start "" "$HTML"` (Windows).
4. Set `<body data-source="...">` to the **absolute path of `$MD`** — exports reference the markdown you edit, not the HTML.
5. Tell the user the HTML path, that they step through with the rail / arrow keys, can comment on any card + tick out-of-scope items, hit **Export comments →**, and paste the block back — you'll apply it to `$MD` and re-render.

## Applying a pasted review

When the user pastes a block that begins `> Source: <path>`:

- Edit that markdown file per each `## <heading>` comment.
- For each `## Out of scope → requested IN scope` line (`- [x] <item> — <reason>`): pull the item into the doc body as real scope (a new acceptance criterion / task / decision), **or** push back in chat with why it should stay cut. Never silently drop it.
- Then re-render `$HTML` from the updated markdown and reopen it. Quote one line on what changed.

## Stack

Tailwind + Mermaid, both via CDN (per project decision). The diagram is **load-bearing here**, not optional decoration — it's how the reader grasps a large plan's shape. Use it where the relationship is genuinely graph-shaped (a plan's task/dependency flow always is; a spec's story→criteria or before/after often is). Skip it only when the doc truly has no structure to draw — then lead with the stat strip instead. A diagram that has to be explained in a paragraph should be redrawn or cut.

## Assemble the page in this order

`<head>` → sticky bar → orientation hero (stat strip) → **the map** (Mermaid) → **walkthrough** (rail + focused step cards) → coverage table *(plan)* / decisions table *(spec)* → out-of-scope → overall comment → footnote → toast → embedded markdown → script.

The **`<head>`, sticky bar, embedded-markdown block, and script are load-bearing constants — reproduce them verbatim.** Everything between is filled from the doc, distilled per the rules above.

### Constant — `<head>` (verbatim)

```html
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{Spec|Plan}} review — {{doc title}}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = { theme: { extend: {
    fontFamily: {
      sans: ['system-ui','-apple-system','Segoe UI','Roboto','sans-serif'],
      serif: ['ui-serif','Georgia','Iowan Old Style','Times New Roman','serif'],
      mono: ['ui-monospace','SFMono-Regular','SF Mono','Menlo','Consolas','monospace'],
    },
    colors: { ink:'#1b1b1f', accent:'#4f46e5' },
  }}};
</script>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose",
    flowchart: { curve: "basis" } });
</script>
<style>
  html{scroll-behavior:smooth}
  .code{background:#1c1b22;color:#e6e6ea;border-radius:9px;padding:13px 15px;overflow-x:auto;
    font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;line-height:1.5}
  .code .c{color:#8b8a96}.code .k{color:#c4b5fd}.code .s{color:#a7e8b0}
  .ta{width:100%;min-height:48px;resize:vertical;font:inherit;font-size:14px;line-height:1.5;
    background:#eef0ff;border:1px solid #d9dcfb;border-radius:9px;padding:9px 12px;color:#1b1b1f}
  .ta:focus{outline:none;border-color:#4f46e5;background:#fff}
  .ta::placeholder{color:#a8a6c4}
  details>summary{list-style:none}details>summary::-webkit-details-marker{display:none}
  details[open] .chev{transform:rotate(90deg)}
  .chev{transition:transform .18s ease}
  .mermaid{display:flex;justify-content:center}
  /* walkthrough stepper */
  .walk[data-mode="focus"] .step:not(.current){display:none}
  .step{animation:fade .22s ease}
  @keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
  .dot{width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:9px;
    font:600 12px ui-monospace,Menlo,monospace;color:#78768a;background:#fff;border:1px solid #e3e1ea;
    cursor:pointer;transition:all .14s;position:relative;flex:none}
  .dot:hover{border-color:#b9b6ff;color:#4f46e5}
  .dot.cur{background:#1b1b1f;color:#fff;border-color:#1b1b1f}
  .dot.note::after{content:"";position:absolute;top:-3px;right:-3px;width:8px;height:8px;border-radius:50%;
    background:#4f46e5;border:1.5px solid #fff}
  .dot.gap{border-color:#f0b4ad}.dot.gap.cur{background:#b3261e;border-color:#b3261e}
  .toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(20px);
    opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:100}
  .toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
</style>
</head>
```

Open the body with `<body class="bg-stone-50 text-ink font-sans antialiased" data-source="{{absolute path to $MD}}">`.

### Constant — sticky bar (verbatim, swap the kicker label)

```html
<div class="sticky top-0 z-50 bg-stone-50/85 backdrop-blur border-b border-stone-200">
  <div class="max-w-4xl mx-auto px-7 py-2.5 flex items-center gap-3.5">
    <span class="text-xs tracking-[.14em] uppercase font-semibold text-stone-400">Crank · {{Spec|Plan}} review</span>
    <span class="flex-1"></span>
    <span id="counter" class="text-xs font-semibold text-stone-500 bg-white border border-stone-200 rounded-full px-2.5 py-1">0 comments</span>
    <button onclick="copyMarkdown()" class="text-[13px] font-semibold rounded-lg px-3 py-1.5 border border-stone-300 bg-white hover:border-accent transition">Copy {{plan|spec}} + comments</button>
    <button onclick="copyComments()" class="text-[13px] font-semibold rounded-lg px-3 py-1.5 bg-accent text-white border border-accent hover:bg-indigo-700 transition">Export comments →</button>
  </div>
</div>
<main class="max-w-4xl mx-auto px-7 pt-8 pb-32">
```

### Filled — orientation hero (lead with numbers, one line of context)

Title in `font-serif text-[32px]`, then **one** line of context (the goal / the problem — a single sentence, hard cap). Then the **stat strip**: a row of `flex-1` stat cards (`<div class="font-serif text-[26px] font-bold">` over a `text-xs uppercase tracking-wider text-stone-400` label).

- **plan:** Tasks · Files touched · Criteria covered (`N / M`, with a green progress bar `style="width:<pct>%"` under it — this is the headline number, keep it).
- **spec:** User stories · Acceptance criteria · In-scope modules.

Put the goal/spec-path/stack facts the reader may want but won't read first into a single collapsed `<details class="text-[13px] text-stone-500 mt-2"><summary class="cursor-pointer">details</summary>…</details>` — a `<dl>` of Goal / Spec path / Architecture / Tech stack (plan) or Problem / Solution (spec). Paths in `font-mono text-[13px] text-stone-500`. Collapsed by default: orientation is the numbers, not the metadata.

### Filled — the map (Mermaid — the centerpiece)

A single diagram that shows the **whole** doc's shape so the reader pre-loads it before walking. This is the most important visual on the page.

- **plan:** the task flow — one node per task in dependency order (`T1 --> T2`), branch where tasks are independent. Flag any coverage-gap task `class:bad`. Keep node labels to the task's short title.
- **spec:** the story→criteria or problem→solution flow, only when it's genuinely graph-shaped; otherwise skip and let the stat strip + walkthrough orient.

```html
<div class="bg-white border border-stone-200 rounded-xl p-4 mb-7">
  <div class="text-xs tracking-wider uppercase font-semibold text-stone-400 mb-2">{{caption — e.g. "Task flow"}}</div>
  <pre class="mermaid">
flowchart LR
  T1([T1 · scaffold]) --> T2([T2 · render map]) --> T3([T3 · export])
  T2 --> T4([T4 · coverage])
  classDef bad fill:#fbe7e6,stroke:#b3261e,stroke-width:2px;
  classDef hi fill:#eef0ff,stroke:#4f46e5,stroke-width:2px;
  </pre>
</div>
```

Keep it readable — if the flow has 25 nodes, group by phase (`subgraph`) rather than drawing one unreadable chain. A diagram that contradicts the prose or needs a paragraph to explain is worse than none.

### Constant — walkthrough frame (verbatim; fill the `.step` cards)

The walkthrough is the page's spine: a **rail** of numbered dots, the **focused card**, and **Prev / Next / Show all**. In markup every `.step` is present and visible; the script enters focus mode on load and shows one at a time. So if scripts ever fail, the reader still sees every card (graceful degradation).

```html
<h2 class="text-[13px] tracking-[.16em] uppercase font-bold text-stone-400 mt-9 mb-3 pb-2 border-b border-stone-200">{{Tasks | Acceptance criteria}}</h2>
<div id="walk" class="walk" data-mode="focus">
  <div id="rail" class="flex flex-wrap gap-1.5 mb-4"></div>
  <div id="cards">
    <!-- one .step per task/criterion — see card templates below -->
  </div>
  <div class="flex items-center gap-3 mt-4">
    <button id="prev" class="text-[13px] font-semibold rounded-lg px-3 py-1.5 border border-stone-300 bg-white hover:border-accent transition">‹ Prev</button>
    <button id="next" class="text-[13px] font-semibold rounded-lg px-3 py-1.5 border border-stone-300 bg-white hover:border-accent transition">Next ›</button>
    <span id="pos" class="text-xs font-semibold text-stone-500"></span>
    <span class="flex-1"></span>
    <button id="mode" class="text-[13px] font-semibold rounded-lg px-3 py-1.5 text-stone-500 hover:text-accent transition">Show all</button>
  </div>
</div>
```

### Filled — step card (plan task) — repeat per task

Distilled: title, files, the steps as terse one-liners, the verify line (the thing to judge), commit. No reproduced prose; anything longer goes in the `full text` toggle or stays in the embedded markdown.

```html
<details class="step task bg-white border border-stone-200 rounded-xl mb-3 overflow-hidden">
  <summary class="cursor-pointer flex items-center gap-3 select-none" style="padding:.9rem 1.1rem">
    <span class="font-mono text-xs font-bold text-white bg-ink rounded-md px-2 py-1">{{T#}}</span>
    <span class="font-semibold text-[15.5px] flex-1">{{task title — ≤10 words}}</span>
    <span class="has-note w-2 h-2 rounded-full bg-accent opacity-0 transition-opacity"></span>
    <svg class="chev text-stone-400" width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </summary>
  <div class="px-[1.1rem] pb-4 border-t border-stone-100">
    <div class="font-mono text-[12.5px] text-stone-500 my-3"><b class="text-ink">Files:</b> {{paths only}}</div>
    <!-- per step: a checkbox marker + ≤14-word line; code only if it IS the deliverable, in <pre class="code"> -->
    <div class="flex gap-2.5 mb-2"><div class="w-[15px] h-[15px] border-[1.5px] border-stone-300 rounded mt-0.5 shrink-0"></div><div class="flex-1 text-[14px]">{{Step N — one line}}</div></div>
    <!-- verify line — the reviewer's anchor: -->
    <div class="flex gap-2.5 items-baseline bg-green-50 border-l-[3px] border-green-700 rounded-r-md px-3 py-2 mt-2 text-[13.5px]"><span class="text-[11px] font-bold uppercase tracking-wide text-green-700 shrink-0">verify</span><span>✓ {{exact success}} &nbsp;<span class="font-mono text-[12px] text-stone-500">seam: {{named seam}}</span></span></div>
    <div class="text-[12.5px] text-stone-500 italic mt-2">↳ commit: <code class="font-mono text-[.86em] not-italic">{{commit}}</code></div>
    {{COMMENT BOX, data-section "T# — {{task title}}"}}
  </div>
</details>
```

### Filled — step card (spec acceptance criterion) — repeat per criterion

Each acceptance criterion is its own `.step` with its **own** comment box — they are the contract every downstream check keys off (locked). The card title **is** the falsifiable statement; keep it to one line, no surrounding prose.

```html
<details class="step bg-white border border-stone-200 rounded-xl mb-3 overflow-hidden">
  <summary class="cursor-pointer flex items-center gap-3 select-none" style="padding:.9rem 1.1rem">
    <span class="font-mono text-xs font-bold text-white bg-ink rounded-md px-2 py-1">{{AC#}}</span>
    <span class="font-medium text-[15px] flex-1">{{the falsifiable criterion — one line}}</span>
    <span class="has-note w-2 h-2 rounded-full bg-accent opacity-0 transition-opacity"></span>
    <svg class="chev text-stone-400" width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </summary>
  <div class="px-[1.1rem] pb-4 border-t border-stone-100">
    <div class="text-[13px] text-stone-500 my-3">{{how it's checked — agent test or named human smoke check, ≤2 lines}}</div>
    {{COMMENT BOX, data-section "AC# — {{short label}}"}}
  </div>
</details>
```

The spec's other sections (Problem, Solution, Technical decisions, Testing approach) are **not** walkthrough cards — render Technical decisions as the decisions table below, and fold Problem/Solution into the orientation `<details>`. Don't re-stack them as prose.

### Filled — coverage table (plan) / decisions table (spec)

A table earns its place by replacing prose with a scannable grid.

**plan — coverage:** one row per acceptance criterion: `criterion` · `task` (`font-mono text-xs text-stone-500`) · verify cell in one of three states:
- covered → `font-mono text-xs text-green-700`, prefix `✓`
- human smoke check → `font-mono text-xs text-amber-700`, prefix `⚠`
- **gap** → row gets `class="bg-red-50"`, cell `font-mono text-xs text-red-700 font-bold`, prefix `✗ no task — coverage gap`

The red gap row is the point — it makes a missing criterion impossible to miss. Mark the matching rail dot `gap` too.

**spec — decisions:** one row per technical decision: `decision` · `choice` (`font-mono`) · `why` (≤6 words). Prose decisions become rows; never a paragraph.

Precede either with the section-heading constant.

### Filled — global constraints (plan only)

If the plan has a **Global Constraints** section, render it right after the table: the section-heading constant labelled `Global Constraints`, a tight `<ul>` with one `<li>` per rule (pinned values in `font-mono`), then a single comment box (`data-section="Global Constraints"`). These bind every task, so they read as a standing reference — not another task card.

### Constant — section heading

```html
<h2 class="text-[13px] tracking-[.16em] uppercase font-bold text-stone-400 mt-9 mb-3 pb-2 border-b border-stone-200">{{Section}}</h2>
```

### Filled — out-of-scope (interactive) — same for spec and plan

Intro line, then one `.oos-item` per cut. Ticking the box reveals its reason textarea and flags it for export.

```html
<p class="text-[13px] text-stone-500 mb-3.5">Tick anything that should actually be <b>in</b> scope and say why — the agent will pull it back in.</p>
<div id="oos" class="space-y-2">
  <!-- repeat per cut -->
  <div class="oos-item bg-white border border-stone-200 rounded-xl px-4 py-3" data-oos="{{item, plain text}}">
    <label class="flex items-start gap-3 cursor-pointer">
      <input type="checkbox" class="oos-check mt-1 w-4 h-4 accent-indigo-600 shrink-0">
      <span class="flex-1">{{item}}</span>
      <span class="oos-tag text-[11px] font-bold uppercase tracking-wide text-indigo-600 opacity-0 transition-opacity">move in-scope</span>
    </label>
    <textarea class="ta oos-reason mt-2.5 hidden" placeholder="why should this be in scope?"></textarea>
  </div>
</div>
<div class="mt-3 comment" data-section="Out of scope (overall)">
  <label class="flex items-center gap-1.5 text-[11px] tracking-wider uppercase text-accent font-bold mb-1.5">💬 group note on the scope cuts (applies to all you ticked)</label>
  <textarea class="ta" placeholder="e.g. ship A + B in v1; defer C…"></textarea>
</div>
```

### Constant — comment box (every commentable region)

```html
<div class="mt-4 comment" data-section="{{unique heading — matched in the export}}">
  <label class="flex items-center gap-1.5 text-[11px] tracking-wider uppercase text-accent font-bold mb-1.5">💬 comment on {{thing}}</label>
  <textarea class="ta" placeholder="leave a comment…"></textarea>
</div>
```

### Filled — global comment + footnote

```html
<div class="bg-indigo-50 border border-indigo-200 rounded-xl px-5 py-4 mt-10 comment" data-section="Overall">
  <label class="text-xs tracking-wider uppercase text-accent font-bold">💬 overall comment on the {{plan|spec}}</label>
  <textarea class="ta mt-1.5" placeholder="anything about the {{plan|spec}} as a whole…"></textarea>
</div>
<p class="mt-8 text-[12.5px] text-stone-400 text-center">Generated by <b>crank · {{plan|spec}}</b> — comments here never touch the source markdown until you export and the agent applies them.</p>
</main>
<div id="toast" class="toast bg-ink text-white px-4 py-2.5 rounded-xl text-[13px] font-semibold">Copied to clipboard</div>
```

### Constant — embedded markdown (so "Copy … + comments" is faithful)

Paste the **doc's actual markdown** between the tags. The export reads it verbatim — this is why the visible page never needs to transcribe it:

```html
<script type="text/markdown" id="source-md">
{{the full spec/plan markdown}}
</script>
```

### Constant — script (verbatim)

Drives the stepper (rail, focus mode, Prev/Next, arrow keys), the comment counter, the out-of-scope reveal, and both exports. The `> Source:` line and per-section format match the project's `effective-html` paste contract, so any agent can apply the result.

```html
<script>
  const SRC = document.body.dataset.source;
  const sections = () => [...document.querySelectorAll('.comment[data-section]')];
  const toastEl = document.getElementById('toast');
  let toastT;
  function toast(msg){ toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toastT); toastT = setTimeout(()=>toastEl.classList.remove('show'), 1600); }

  /* ---- walkthrough stepper ---- */
  const walk = document.getElementById('walk');
  const steps = walk ? [...walk.querySelectorAll('.step')] : [];
  const rail = document.getElementById('rail');
  const posEl = document.getElementById('pos');
  let cur = 0;
  const hasNote = s => !!s.querySelector('.comment textarea')?.value.trim();

  function buildRail(){
    if(!rail) return;
    rail.innerHTML = '';
    steps.forEach((s,i)=>{
      const b = document.createElement('button');
      b.className = 'dot' + (s.dataset.gap ? ' gap' : '');
      b.textContent = i + 1;
      b.title = s.querySelector('summary span:nth-child(2)')?.textContent || ('Step ' + (i+1));
      b.onclick = () => go(i);
      rail.appendChild(b);
    });
  }
  function paintRail(){
    if(!rail) return;
    [...rail.children].forEach((b,i)=>{
      b.classList.toggle('cur', i === cur && walk.dataset.mode === 'focus');
      b.classList.toggle('note', hasNote(steps[i]));
    });
  }
  function go(i){
    if(!steps.length) return;
    cur = Math.max(0, Math.min(steps.length - 1, i));
    if(walk.dataset.mode === 'focus'){
      steps.forEach((s,k)=>{ s.classList.toggle('current', k === cur); s.open = (k === cur); });
      if(posEl) posEl.textContent = `${cur + 1} / ${steps.length}`;
    }
    paintRail();
  }
  function setMode(m){
    walk.dataset.mode = m;
    const btn = document.getElementById('mode');
    if(m === 'all'){
      steps.forEach(s=>{ s.classList.remove('current'); s.open = false; });
      if(posEl) posEl.textContent = `all ${steps.length}`;
      if(btn) btn.textContent = 'Focus mode';
    } else {
      if(btn) btn.textContent = 'Show all';
      go(cur);
    }
    paintRail();
  }
  if(walk){
    document.getElementById('prev').onclick = () => go(cur - 1);
    document.getElementById('next').onclick = () => go(cur + 1);
    document.getElementById('mode').onclick = () => setMode(walk.dataset.mode === 'focus' ? 'all' : 'focus');
    document.addEventListener('keydown', e=>{
      if(walk.dataset.mode !== 'focus' || e.target.tagName === 'TEXTAREA') return;
      if(e.key === 'ArrowRight'){ go(cur + 1); e.preventDefault(); }
      if(e.key === 'ArrowLeft'){ go(cur - 1); e.preventDefault(); }
    });
    buildRail();
    go(0);
  }

  /* ---- out-of-scope ---- */
  document.querySelectorAll('.oos-item').forEach(item=>{
    const cb = item.querySelector('.oos-check');
    const reason = item.querySelector('.oos-reason');
    const tag = item.querySelector('.oos-tag');
    cb.addEventListener('change', ()=>{
      reason.classList.toggle('hidden', !cb.checked);
      tag.style.opacity = cb.checked ? '1' : '0';
      item.classList.toggle('border-indigo-300', cb.checked);
      item.classList.toggle('bg-indigo-50/40', cb.checked);
      refresh();
    });
  });

  function oosRequests(){
    return [...document.querySelectorAll('.oos-item')]
      .filter(i=>i.querySelector('.oos-check').checked)
      .map(i=>({ item:i.dataset.oos, reason:i.querySelector('.oos-reason').value.trim() }));
  }

  function refresh(){
    let n = 0;
    sections().forEach(s=>{
      const v = s.querySelector('textarea').value.trim();
      if(v) n++;
      const card = s.closest('.step');
      if(card) card.querySelector('.has-note').style.opacity = v ? '1' : '0';
    });
    paintRail();
    const oos = oosRequests().length;
    const parts = [];
    if(n) parts.push(n + (n===1?' comment':' comments'));
    if(oos) parts.push(oos + ' scope flag' + (oos===1?'':'s'));
    document.getElementById('counter').textContent = parts.length ? parts.join(' · ') : '0 comments';
  }
  document.addEventListener('input', e=>{ if(e.target.tagName==='TEXTAREA') refresh(); });

  function collected(){
    return sections().map(s=>({ heading:s.dataset.section, body:s.querySelector('textarea').value.trim() }))
      .filter(c=>c.body);
  }

  function oosBlock(){
    const reqs = oosRequests();
    if(!reqs.length) return '';
    const lines = reqs.map(r=>`- [x] ${r.item}${r.reason ? ' — '+r.reason : ' — (no reason given)'}`);
    return '\n## Out of scope → requested IN scope\n' + lines.join('\n');
  }

  async function clip(text, label){
    try{ await navigator.clipboard.writeText(text); toast(label); }
    catch(_){ const ta=document.createElement('textarea'); ta.value=text; document.body.appendChild(ta);
      ta.select(); document.execCommand('copy'); ta.remove(); toast(label); }
  }

  function copyComments(){
    const c = collected();
    const oos = oosRequests();
    if(!c.length && !oos.length){ toast('Nothing to export yet'); return; }
    const head = `> Source: ${SRC}\n> ${c.length} comment(s)` +
      (oos.length ? `, ${oos.length} scope flag(s)` : '') + ` from review — apply to the markdown above.\n`;
    const body = c.map(x=>`## ${x.heading}\n${x.body}`).join('\n\n');
    const out = [head, body].filter(Boolean).join('\n') + oosBlock();
    clip(out, 'Copied review');
  }

  function copyMarkdown(){
    const md = document.getElementById('source-md').textContent.trim();
    const c = collected();
    let out = `> Source: ${SRC}\n\n` + md;
    if(c.length){
      out += '\n\n---\n## Review comments\n\n' +
        c.map(x=>`**${x.heading}**\n> ${x.body.replace(/\n/g,'\n> ')}`).join('\n\n');
    }
    out += oosBlock();
    clip(out, 'Copied + comments');
  }

  refresh();
</script>
```

## Before you hand off

`open` the file and glance at it:

- **It's a lens, not a transcript.** No section is a reproduced paragraph; the page skims in under a minute. If it reads like the markdown, cut.
- **Focus mode works:** one card shows at a time, the rail highlights it, Prev/Next + ← → move between cards, the dot lights when a card has a comment, "Show all" reveals every card. (If JS were stripped, every card is still visible — confirm none are hidden in the markup.)
- **The map rendered** (an unrendered `.mermaid` shows raw text — fix the syntax) and matches the doc; coverage gaps show red in both the table and the rail.
- No text overflowing cards; code blocks scroll rather than break layout.
- Each commentable region has exactly one `data-section` with a **unique** label (duplicate labels collide in the export).

## Tone

Plain, concise, schematic. Module labels in diagrams read as labels (`text-xs uppercase tracking-wider`), not UI. Colour sparingly: indigo accent, green for covered/create, amber for smoke/modify, red for gap/delete. **The diagram, the stat strip, and the one-card-at-a-time pacing carry the weight — prose is the fallback you reach for only when nothing visual fits.** If a region is a wall of text, you haven't distilled it yet.
