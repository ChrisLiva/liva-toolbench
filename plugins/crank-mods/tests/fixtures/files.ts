import { LEDGER_DIR, ROOT } from './world'

export const PLAN = '.crank/csv-export/plan.md'
export const PLAN_FILE = `${ROOT}/${PLAN}`
export const LEDGER_FILE = `${LEDGER_DIR}/progress-csv-export.md`
export const RETRO_FILE = `${ROOT}/.crank/csv-export/retro.md`

const SUBJECTS = [
  'Write the CSV writer',
  'Quote fields',
  'Add the export route',
  'Stream rows',
  'Name the file',
  'Wire the button',
  'Paginate',
  'Log exports',
  'Document it',
]

const tasks = (total: number, landed: number) =>
  Array.from(
    { length: total },
    (_, i) => `- [${i < landed ? 'x' : ' '}] Task ${i + 1}: ${SUBJECTS[i] ?? 'Subject'}${i < landed ? ` — ${(0xabc1230 + i).toString(16)}` : ''}`,
  )

const headings = (total: number) => Array.from({ length: total }, (_, i) => `### Task ${i + 1} — ${SUBJECTS[i] ?? 'Subject'}\n\nBody.\n`)

const STAGES = [
  '## Stages',
  '',
  '| Stage | Tasks | Exit state |',
  '|---|---|---|',
  '| 1 | Task 1–Task 3 | rows write |',
  '| 2 | Task 4–Task 6 | the route streams |',
  '| 3 | Task 7–Task 9 | shipped |',
  '',
]

/** A crank plan of nine tasks in three stages, with no Progress block. */
export const crankPlan = () => ['# Plan: CSV export', '', ...STAGES, '## Tasks', '', ...headings(9)].join('\n')

/** A crank-execute ledger: its anchor, the lines a run writes under it, then one box per task. */
export function ledger({ landed, total = 9, lines = [], plan = PLAN }: { landed: number; total?: number; lines?: string[]; plan?: string }) {
  return ['# Crank execute — main', `Plan: ${plan}`, 'Base: 65e864f4', '', ...lines, ...(lines.length > 0 ? [''] : []), ...tasks(total, landed), ''].join('\n')
}

/** A lite plan with a Progress block, and step boxes in its task bodies that are not tasks. */
export function litePlan({ landed, total = 3, lines = [] }: { landed: number; total?: number; lines?: string[] }) {
  return [
    '# Plan: CSV export',
    '',
    '## Progress',
    '',
    ...lines,
    'Base: 65e864f4',
    '',
    ...tasks(total, landed),
    '',
    '## Tasks',
    '',
    '### Task 1 — Write the CSV writer',
    '',
    '- [x] Task 1 step: write the failing test',
    '- [x] Task 1 step: make it pass',
    '',
    '### Task 2 — Quote fields',
    '',
    '- [ ] Task 2 step: write the failing test',
    '',
  ].join('\n')
}
