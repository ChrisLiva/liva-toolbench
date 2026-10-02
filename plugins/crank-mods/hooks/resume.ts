import type { CrankArtifact, CrankRun } from '../types'
import { artifactOf, bare, sibling } from './parse'

// The box refuses a suggestion made inside SessionStart at startup, and one
// made as soon as /model, /effort or /config resolves; one made this long
// after the dispatch shows, and by then the terminal surface has attached.
export const OFFER_DELAY_MS = 100
export const MAX_ENTRIES = 5
export const MAX_KEY_LENGTH = 256
const EXPIRY_MS = 12 * 60 * 60 * 1000
const FALSE_START_MS = 15 * 60 * 1000
const CMD = /`(\/(?:crank-lite:|crank:)?([a-z][\w-]*))(?:\s+([^`]*))?`/g
const LABEL_LINE = /\*\*Next|Next step|[Rr]esume (?:with|at)|[Tt]o resume|fresh session|new session/
const EXECUTOR = /^(?:crank-execute|lite-execute)$/
const PHASE_COMMAND = /^(?:crank|crank-lite)$/
const PHASE = /^(brainstorm|spec|plan)\b/

/** One saved next-phase line, kept per worktree in the store, newest first. */
export type ResumeEntry = { slug: string; command: string; args: string; path: string; capturedAt: number; takenAt?: number }

/** The hand-off a main-loop answer prints: its labelled crank command with a .crank path, else its only one, else null. */
export function findHandoff(answer: string, names: Set<string>, armed: CrankRun) {
  const isExecutorRun = EXECUTOR.test(bare(armed.command))
  const found = answer.split('\n').flatMap(line =>
    [...line.matchAll(CMD)].flatMap(m => {
      const name = m[2] ?? ''

      if (!names.has(name)) {
        return []
      }

      const typed = (m[3] ?? '').trim()
      // A bare executor line resumes the plan an executor run was given; another run's plan is not this line's.
      const args = typed === '' && EXECUTOR.test(name) && isExecutorRun ? (armed.artifact?.path ?? '') : typed
      const artifact = artifactOf(args)

      return artifact === null ? [] : [{ command: m[1] ?? '', args, artifact, isLabelled: LABEL_LINE.test(line) }]
    }),
  )
  const labelled = found.find(c => c.isLabelled)

  if (labelled !== undefined) {
    return labelled
  }

  return new Set(found.map(c => `${c.command} ${c.args}`)).size === 1 ? (found[0] ?? null) : null
}

/** Under 12 hours since the capture, and under 15 minutes since a launch that may have been a false start. */
export function isFresh(entry: ResumeEntry, now: number) {
  return now - entry.capturedAt <= EXPIRY_MS && (entry.takenAt === undefined || now - entry.takenAt <= FALSE_START_MS)
}

/** The artifact a crank or crank-lite phase line writes, whose newer mtime means the phase ran elsewhere; none for other lines. */
export function outputOf(entry: ResumeEntry, artifact: CrankArtifact) {
  const phase = PHASE.exec(entry.args)?.[1]

  return PHASE_COMMAND.test(bare(entry.command.slice(1))) && phase !== undefined ? sibling(artifact, phase) : undefined
}
