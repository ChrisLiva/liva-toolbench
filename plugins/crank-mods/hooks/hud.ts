import type { CrankArtifact, CrankRun, CrankWhere, HudAgent, HudNow, HudProgress, HudRole, HudRun } from '../types'
import { bare, ledgerPlan, progressOf, sibling, stagesOf, taskHeadings } from './parse'
import type { Progress } from './parse'

const CRANK_EXECUTE = 'crank:crank-execute'
export const LITE_EXECUTE = 'crank-lite:lite-execute'
const EXECUTORS = new Set([CRANK_EXECUTE, LITE_EXECUTE])
const WIDE_COLUMNS = 140
const NARROW_COLUMNS = 100
const ROW_LIMIT = 3
const NARROW_ROW_LIMIT = 2
const MINUTE_MS = 60 * 1000
// Each role's 90th-percentile run, in minutes, over 343 implementers, 133
// per-task reviewers, 73 final reviewers, 38 plan walks and 37 re-reviewers
// in crank transcripts up to 2026-10-01.
const USUAL_MINUTES: Partial<Record<HudRole, number>> = { implementer: 40, fixer: 40, reviewer: 7, 'final reviewer': 14, 'plan walk': 14, 're-reviewer': 4 }

type Ending = 'done' | 'bound' | 'halt' | 'stopped'

type Cell = { text: string; tone: 'dim' | 'plain' | 'warning' }

/** A roster agent, with its activity once a request of its own ran. */
export type Row = { id: string; agent: HudAgent; now: HudNow | undefined }

type ProgressRead = {
  stamp: string
  plan: CrankArtifact
  planText: string
  planMtime: number
  retroMtime: number | undefined
  /** The ledgers present, in the order crank-execute picks them. */
  ledgers: { text: string; mtime: number }[]
}

export function planOf(armed: CrankRun) {
  return EXECUTORS.has(armed.command) ? armed.artifact : null
}

// crank-execute keeps its ledger in the git dir, and in the worktree when the
// harness refuses writes there.
export function progressFiles(armed: CrankRun, plan: CrankArtifact, at: CrankWhere) {
  return {
    plan: `${at.root}/${plan.path}`,
    retro: `${at.root}/${sibling(plan, 'retro')}`,
    ledgers: armed.command === CRANK_EXECUTE ? [`${at.ledgerDir}/progress-${plan.slug}.md`, `${at.root}/.crank/${plan.slug}/progress.md`] : [],
  }
}

export function progressFrom(found: ProgressRead, armedAt: number): HudProgress {
  const progress = (source: HudProgress['source'], { tasks, bound, stopped }: Progress, mtimeMs: number): HudProgress => ({
    source,
    stamp: found.stamp,
    mtimeMs,
    tasks,
    stages: stagesOf(found.planText),
    bound: mtimeMs > armedAt ? bound : undefined,
    stopped,
    hasRetro: found.retroMtime !== undefined && found.retroMtime > armedAt,
  })
  // A ledger left by another plan with the same slug is not this run's.
  const ledger = found.ledgers.find(l => ledgerPlan(l.text)?.path === found.plan.path)

  if (ledger !== undefined) {
    return progress('ledger', progressOf(ledger.text, false), ledger.mtime)
  }

  const block = progressOf(found.planText, true)

  return block.tasks.length > 0
    ? progress('progress-block', block, found.planMtime)
    : progress('plan-headings', { tasks: taskHeadings(found.planText).map(id => ({ id, isLanded: false })) }, found.planMtime)
}

export function endingOf(hud: HudRun, p: HudProgress): Ending | undefined {
  const isAllLanded = p.source !== 'plan-headings' && p.tasks.length > 0 && p.tasks.every(t => t.isLanded)

  if (p.hasRetro || isAllLanded) {
    return 'done'
  }

  const { bound, stopped } = p

  if (stopped === undefined || stopped.line === hud.stoppedAtArm) {
    return undefined
  }

  if (bound === undefined || stopped.resumeAt === undefined) {
    return 'stopped'
  }

  return stopped.resumeAt > bound.task ? 'bound' : 'halt'
}

export function isQuiet(hud: HudRun, p: HudProgress) {
  return hud.quietAt !== undefined && p.mtimeMs <= hud.quietAt
}

// The lead and each field join with ' · '; `key`, drawn in its own tone, follows the lead, and `tail` follows `key` with no separator.
function line(lead: (string | undefined)[], fields: (string | undefined)[], key?: Cell, tail = ''): Cell[] {
  const led = lead.filter(field => field !== undefined)
  const shown = fields.filter(field => field !== undefined)
  const cells: Cell[] =
    key === undefined
      ? [{ text: [...led, ...shown].join(' · '), tone: 'dim' }]
      : [{ text: `${led.join(' · ')} · `, tone: 'dim' }, key, { text: tail + shown.map(field => ` · ${field}`).join(''), tone: 'dim' }]

  return cells.filter(cell => cell.text !== '')
}

const ago = (ms: number) => (ms < MINUTE_MS ? '<1m' : `${Math.floor(ms / MINUTE_MS)}m`)

const isLive = (row: Row) => !row.agent.isDone

/** The tasks the live implementers and fixers work on, which the header names in place of the first open box. */
export function workingOf(rows: Row[]) {
  const tasks = rows
    .filter(isLive)
    .flatMap(({ agent }) => ((agent.role === 'implementer' || agent.role === 'fixer') && agent.task !== undefined ? [agent.task] : []))

  return [...new Set(tasks)].sort((a, b) => Number(a) - Number(b))
}

function rowOf({ agent, now }: Row, at: number, columns: number): Cell[] {
  const isWide = columns >= WIDE_COLUMNS
  const isNarrow = columns < NARROW_COLUMNS
  const { role, waiting } = agent
  const usual = USUAL_MINUTES[role]
  const elapsed = at - agent.startedAt
  const isLong = usual !== undefined && elapsed > usual * MINUTE_MS
  const mark = !isLong || isNarrow ? '' : isWide ? `, past the usual ${usual}m for ${/^[aeiou]/.test(role) ? 'an' : 'a'} ${role}` : `, past ${usual}m`
  const lead = [
    `  ${role === 'other' ? agent.description : role}`,
    agent.task === undefined ? undefined : `Task ${agent.task}`,
    agent.effort === undefined ? undefined : `effort ${agent.effort}`,
  ]
  const doing =
    waiting === undefined
      ? [now === undefined ? undefined : `${now.what} ${ago(at - now.since)}`]
      : [`waiting on ${isNarrow ? '' : 'its '}background ${waiting.word} ${ago(at - waiting.since)}`, isWide ? 'Claude Code lists it as finished' : undefined]

  return line(lead, doing, { text: `${ago(elapsed)}${mark}`, tone: isLong ? 'warning' : 'dim' })
}

/** One row per live agent, in spawn order, up to the width's limit, then a row counting the rest. */
export function rowsOf(rows: Row[], at: number, columns: number): Cell[][] {
  const live = rows.filter(isLive)
  const limit = columns < NARROW_COLUMNS ? NARROW_ROW_LIMIT : ROW_LIMIT
  const shown = live.slice(0, limit).map(row => rowOf(row, at, columns))

  return live.length > limit ? [...shown, [{ text: `  +${live.length - limit} more`, tone: 'dim' }]] : shown
}

export function headerOf(armed: CrankRun, hud: HudRun, p: HudProgress, working: string[], columns: number): Cell[] {
  const isWide = columns >= WIDE_COLUMNS
  const isNarrow = columns < NARROW_COLUMNS
  const slug = armed.artifact?.slug ?? ''
  const lead = isNarrow ? [slug] : [bare(armed.command), slug]
  const total = p.tasks.length
  const landed = p.tasks.filter(t => t.isLanded).length
  const { bound, stopped } = p
  const boundText = bound === undefined ? undefined : `bound ${isWide ? bound.text : `Task ${bound.task}`}`
  const resumeAt = stopped?.resumeAt === undefined ? undefined : `resume at Task ${stopped.resumeAt}`

  switch (endingOf(hud, p)) {
    case 'done':
      return line(lead, [`${landed} of ${total} landed`, p.hasRetro ? 'retro written' : undefined])
    case 'bound':
      return line(lead, [isWide && bound !== undefined ? `bound reached at ${bound.text}` : 'bound reached', `${landed} of ${total} landed`, resumeAt])
    case 'halt':
      return line(
        lead,
        isWide ? [`${landed} landed`, boundText, stopped?.why, resumeAt] : [`${landed} landed`, isNarrow ? resumeAt : stopped?.why],
        { text: 'stopped', tone: 'warning' },
        ` before Task ${stopped?.resumeAt} of ${total}`,
      )
    case 'stopped':
      return line(lead, ['stopped', `${landed} of ${total} landed`, resumeAt])
  }

  const current = p.tasks.find(t => !t.isLanded)

  if (p.source === 'plan-headings' || current === undefined) {
    return line(lead, [total > 0 ? `${total} tasks` : undefined])
  }

  const ids = working.length > 0 ? working : [current.id]
  const index = p.stages.findIndex(tasks => tasks.includes(Number(ids[0])))
  const stage = index < 0 ? undefined : { n: index + 1, of: p.stages.length }
  const position: Cell = { text: `${ids.length > 1 ? 'Tasks' : 'Task'} ${ids.join(', ')} of ${total}`, tone: 'plain' }

  if (isNarrow) {
    return line(lead, [stage && `stage ${stage.n}/${stage.of}`, `${landed} landed`, boundText], position)
  }

  return line(lead, [`${landed} landed`, boundText], position, stage ? ` (stage ${stage.n} of ${stage.of})` : '')
}
