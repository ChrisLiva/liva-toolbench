import type { Engine } from 'claude-code/testing'

import { crankPlan, LEDGER_FILE, PLAN, PLAN_FILE } from './files'
import { HOUR, MINUTE, NOW, runCommand, startSession } from './world'
import type { Files, World } from './world'

export const BEFORE = NOW - HOUR
export const AFTER = NOW + MINUTE

export const crankFiles = (ledgerText: string, mtimeMs = BEFORE): Files => ({
  [PLAN_FILE]: { text: crankPlan(), mtimeMs: BEFORE },
  [LEDGER_FILE]: { text: ledgerText, mtimeMs },
})

export async function crankExecute($: Engine, world: World) {
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-execute', `${PLAN} Complete Tasks 4-5, then stop.`)
}

export async function liteExecute($: Engine, world: World) {
  await startSession($, world, 'startup')
  await runCommand($, 'crank-lite:lite-execute', `@${PLAN} complete the next stage`)
}
