import type { CrankArtifact, HudProgress, HudTask } from '../types'

const FAMILY = /^(?:crank|crank-lite):/
const ARTIFACT = /\.crank\/(?:([\w.-]+)\/([\w.-]+)\.md|(brainstorm|spec|plan|retro)-([\w.-]+)\.md)/
const FENCE = /^\s*(?:```|~~~)/
const SECTION_END = /^#{1,2}\s/
const PROGRESS_HEAD = /^## Progress\b/
const STAGES_HEAD = /^##\s+(?:Stages|Phases)\b/i
const TASK_BOX = /^\s*- \[([ xX~-])\]\s+(?:\*\*)?(?:Task\s+|T)([A-Z]?\d+[a-z]?(?:-T\d+)?)\b/
const TASK_HEADING = /^#{2,4}\s+(?:\*\*)?(?:Task\s+|T)(\d+[a-z]?)\b|^#{2,4}\s+(?:Task\s+)?(R\d+-T\d+)\b/
const STAGE_SPAN = /(?:Task\s*|T)?(\d+)\s*(?:(?:–|—|-|to)\s*(?:Task\s*|T)?(\d+))?/g
const TABLE_RULE = /^:?-+:?$/
const BOUND = /^Bound:\s*(.+)$/
const BOUND_TASK = /\bTask\s+(\d+)/
const STOPPED = /^Stopped:\s*(.*)$/
const RESUME_AT = /\bresume at (?:Task\s+|T)(\d+)/
const WHY_END = /\s+[—–-]+\s+resume at\b.*$/
const PLAN_HEADER = /^Plan:\s*(.+)$/
const LEDGER_HEAD_LINES = 12

export type Progress = Pick<HudProgress, 'tasks' | 'bound' | 'stopped'>

/** Whether crank or crank-lite adds the command, as `command.run` and `$.command.list()` name it (`crank-lite:lite-execute`). */
export const isFamily = (command: string) => FAMILY.test(command)

export const bare = (command: string) => command.replace(FAMILY, '')

export function artifactOf(text: string): CrankArtifact | null {
  const m = ARTIFACT.exec(text)

  if (m === null) {
    return null
  }

  return m[1] !== undefined && m[2] !== undefined
    ? { path: m[0], slug: m[1], isFlat: false }
    : { path: m[0], slug: m[4] ?? '', isFlat: true }
}

export function sibling(artifact: CrankArtifact, name: string) {
  return artifact.isFlat ? `.crank/${name}-${artifact.slug}.md` : `.crank/${artifact.slug}/${name}.md`
}

function unfenced(text: string) {
  let isFenced = false

  return text.split('\n').filter(line => {
    if (FENCE.test(line)) {
      isFenced = !isFenced
      return false
    }

    return !isFenced
  })
}

/** The lines of the first section whose heading matches, up to the next heading of level 1 or 2. */
function section(lines: string[], head: RegExp) {
  const start = lines.findIndex(line => head.test(line))

  if (start < 0) {
    return []
  }

  const rest = lines.slice(start + 1)
  const end = rest.findIndex(line => SECTION_END.test(line))

  return end < 0 ? rest : rest.slice(0, end)
}

/** The task boxes, `Bound:` line and `Stopped:` line of a ledger, or of a plan's `## Progress` block. */
export function progressOf(text: string, isPlan: boolean): Progress {
  const lines = isPlan ? section(unfenced(text), PROGRESS_HEAD) : unfenced(text)
  const tasks: HudTask[] = lines.flatMap(line => {
    const m = TASK_BOX.exec(line)

    return m === null ? [] : [{ id: m[2] ?? '', isLanded: m[1] === 'x' || m[1] === 'X' }]
  })
  const boundText = lines.map(line => BOUND.exec(line)?.[1]?.trim()).find(text => text !== undefined)
  const boundTask = boundText === undefined ? undefined : BOUND_TASK.exec(boundText)?.[1]
  const stoppedLine = lines.find(line => STOPPED.test(line))?.trim()
  const resumeAt = stoppedLine === undefined ? undefined : RESUME_AT.exec(stoppedLine)?.[1]

  return {
    tasks,
    bound: boundText === undefined || boundTask === undefined ? undefined : { task: Number(boundTask), text: boundText },
    stopped:
      stoppedLine === undefined
        ? undefined
        : {
            line: stoppedLine,
            why: stoppedLine.replace(STOPPED, '$1').replace(WHY_END, ''),
            resumeAt: resumeAt === undefined ? undefined : Number(resumeAt),
          },
  }
}

export function ledgerPlan(text: string) {
  const header = unfenced(text)
    .slice(0, LEDGER_HEAD_LINES)
    .map(line => PLAN_HEADER.exec(line)?.[1])
    .find(value => value !== undefined)

  return header === undefined ? null : artifactOf(header)
}

/** The task ids of a plan's `Task N` headings outside code fences, for the total when no box lists them. */
export function taskHeadings(text: string) {
  const ids = unfenced(text).flatMap(line => {
    const m = TASK_HEADING.exec(line)
    const id = m?.[1] ?? m?.[2]

    return id === undefined ? [] : [id]
  })

  return [...new Set(ids)]
}

export function stagesOf(text: string) {
  return section(unfenced(text), STAGES_HEAD).flatMap(line => {
    const cells = line
      .trim()
      .replace(/^\||\|$/g, '')
      .split('|')
      .map(cell => cell.trim())
    const [label = '', span] = cells

    if (!line.trim().startsWith('|') || span === undefined || TABLE_RULE.test(label.replace(/ /g, '')) || /^(?:stage|phase)$/i.test(label)) {
      return []
    }

    return [
      [...span.matchAll(STAGE_SPAN)].flatMap(m => {
        const first = Number(m[1])
        const last = m[2] === undefined ? first : Number(m[2])

        return Array.from({ length: Math.max(last - first + 1, 0) }, (_, i) => first + i)
      }),
    ]
  })
}
