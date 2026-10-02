import { expect, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'

import { crankPlan, LEDGER_FILE, ledger, litePlan, PLAN, PLAN_FILE, RETRO_FILE } from './fixtures/files'
import { AFTER, BEFORE, crankExecute, crankFiles, liteExecute } from './fixtures/runs'
import { bandLines, bash, HOUR, MINUTE, ROOT, runCommand, startSession, SURFACES, typePrompt, worldOf } from './fixtures/world'
import type { World } from './fixtures/world'

const ENGINE = ['engine band']
const BOUND_5 = "Bound: Task 5, the user's stop"
const HALT = "Stopped: Task 2's Stop if observed, every route sets JSON — resume at Task 2"

/** The run writes the file after arming, and a main-loop Bash call lets the hud see it. */
async function write($: Engine, world: World, path: string, text: string) {
  world.files[path] = { text, mtimeMs: AFTER }
  await bash($)
}

test('arming a crank-execute run draws the position, stage and landed count before the run writes its bound', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(['crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed', ...ENGINE])
  }
})

test("the run's own Bound: line shows once the ledger changes after arming", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 3, lines: ['Pre-flight: branch main', BOUND_5] }))

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed · bound Task 5')
  }
})

test("a previous run's Bound: line, older than the arming, is not shown", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3, lines: ["Bound: Task 3, the plan's last"] })))
  await crankExecute($, world)
  await bash($)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).not.toContain('bound')
  }
})

test('a command from the SDK draws no header', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-execute', PLAN, 'sdk')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test('a band holding a survey leaves the header out', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface, { hasSurvey: true })).lines).toEqual(ENGINE)
  }
})

test("a lite-execute run counts the Progress block's boxes, not the step boxes in task bodies", async ($, on) => {
  const world = worldOf(on, { [PLAN_FILE]: { text: litePlan({ landed: 1 }), mtimeMs: BEFORE } })
  await liteExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('lite-execute · csv-export · Task 2 of 3 · 1 landed')
  }
})

test('a box flipped through Bash moves the landed count and the position', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 4, lines: [BOUND_5] }))

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · Task 5 of 9 (stage 2 of 3) · 4 landed · bound Task 5')
  }
})

test('a reached bound shows neutral until the person types, then the header leaves', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 5, lines: [BOUND_5, 'Stopped: the user bounded this run at Task 5 — resume at Task 6'] }))

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines[0]).toBe('crank-execute · csv-export · bound reached · 5 of 9 landed · resume at Task 6')
    expect(tones.every(tone => tone.startsWith('~'))).toBe(true)
  }

  await typePrompt($, 'thanks')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test('a halt before the bound shows "stopped" in warning, hides once answered, and returns when a box flips', async ($, on) => {
  const world = worldOf(on, { [PLAN_FILE]: { text: litePlan({ landed: 1 }), mtimeMs: BEFORE } })
  await liteExecute($, world)
  await write($, world, PLAN_FILE, litePlan({ landed: 1, lines: ["Bound: Task 3, the plan's last", HALT] }))

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines[0]).toBe("lite-execute · csv-export · stopped before Task 2 of 3 · 1 landed · Task 2's Stop if observed, every route sets JSON")
    expect(tones).toContain('!stopped')
  }

  await typePrompt($, 'work around it')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }

  world.files[PLAN_FILE] = { text: litePlan({ landed: 2, lines: ["Bound: Task 3, the plan's last", HALT] }), mtimeMs: AFTER + MINUTE }
  await bash($)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('lite-execute · csv-export · Task 3 of 3 · 2 landed · bound Task 3')
  }
})

test('a stop that resumes at the bound task itself is a halt, not a reached bound', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 4, lines: [BOUND_5, 'Stopped: Task 5 failed its gate — resume at Task 5'] }))

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines[0]).toBe('crank-execute · csv-export · stopped before Task 5 of 9 · 4 landed · Task 5 failed its gate')
    expect(tones).toContain('!stopped')
  }
})

test('a stop with no fresh Bound: line shows neutral and leaves the run armed', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 5, lines: ['Stopped: the user paused the run — resume at Task 6'] }))

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines[0]).toBe('crank-execute · csv-export · stopped · 5 of 9 landed · resume at Task 6')
    expect(tones.every(tone => tone.startsWith('~'))).toBe(true)
  }

  await typePrompt($, 'go on')
  world.files[LEDGER_FILE] = { text: ledger({ landed: 6, lines: ['Stopped: the user paused the run — resume at Task 6'] }), mtimeMs: AFTER + MINUTE }
  await bash($)

  expect((await bandLines($, 'terminal')).lines[0]).toBe('crank-execute · csv-export · Task 7 of 9 (stage 3 of 3) · 6 landed')
})

test('every box checked shows the done header until the person types', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 9, lines: [BOUND_5] }))

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · 9 of 9 landed')
  }

  await typePrompt($, 'merge it')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test('/clear ends the session and the header with it', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await $.session.end({ reason: 'clear', sessionId: 's', resume: { id: 's' } })
  await world.clock.advance(HOUR)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test("a worktree ledger naming another plan is skipped, and the plan's headings give the total", async ($, on) => {
  const ledgerDir = '/work/liva-todo-wt/.git/worktrees/wt/crank'
  const files = crankFiles(ledger({ landed: 3, plan: '.crank/csv-export-old/plan.md' }))
  const world = worldOf(on, { [PLAN_FILE]: files[PLAN_FILE]!, [`${ledgerDir}/progress-csv-export.md`]: files[LEDGER_FILE]! }, { ledgerDir })
  await crankExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · 9 tasks')
  }
})

test('another crank command stands the header down', async ($, on) => {
  const world = worldOf(on, { ...crankFiles(ledger({ landed: 3 })), [`${ROOT}/.crank/other/spec.md`]: { text: '', mtimeMs: BEFORE } })
  await crankExecute($, world)
  await runCommand($, 'crank:crank', 'plan .crank/other/spec.md')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test('with the hud toggle off no header draws', { options: { hud: false } }, async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

// The design's section 3 mockups, one header per state and width.
const MOCKUPS = [
  {
    state: 'running',
    command: 'crank:crank-execute',
    before: crankFiles(ledger({ landed: 3 })),
    after: [LEDGER_FILE, ledger({ landed: 3, lines: [BOUND_5] })],
    lines: {
      80: 'csv-export · Task 4 of 9 · stage 2/3 · 3 landed · bound Task 5',
      120: 'crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed · bound Task 5',
      160: "crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed · bound Task 5, the user's stop",
    },
  },
  {
    state: 'halt',
    command: 'crank-lite:lite-execute',
    before: { [PLAN_FILE]: { text: litePlan({ landed: 1 }), mtimeMs: BEFORE } },
    after: [PLAN_FILE, litePlan({ landed: 1, lines: ['Bound: Task 3', HALT] })],
    lines: {
      80: 'csv-export · stopped before Task 2 of 3 · 1 landed · resume at Task 2',
      120: "lite-execute · csv-export · stopped before Task 2 of 3 · 1 landed · Task 2's Stop if observed, every route sets JSON",
      160: "lite-execute · csv-export · stopped before Task 2 of 3 · 1 landed · bound Task 3 · Task 2's Stop if observed, every route sets JSON · resume at Task 2",
    },
  },
  {
    state: 'bound',
    command: 'crank:crank-execute',
    before: crankFiles(ledger({ landed: 3 })),
    after: [LEDGER_FILE, ledger({ landed: 5, lines: [BOUND_5, 'Stopped: the user bounded this run at Task 5 — resume at Task 6'] })],
    lines: {
      80: 'csv-export · bound reached · 5 of 9 landed · resume at Task 6',
      120: 'crank-execute · csv-export · bound reached · 5 of 9 landed · resume at Task 6',
      160: "crank-execute · csv-export · bound reached at Task 5, the user's stop · 5 of 9 landed · resume at Task 6",
    },
  },
  {
    state: 'done',
    command: 'crank:crank-execute',
    before: crankFiles(ledger({ landed: 3 })),
    after: [LEDGER_FILE, ledger({ landed: 9, lines: [BOUND_5] })],
    lines: {
      80: 'csv-export · 9 of 9 landed · retro written',
      120: 'crank-execute · csv-export · 9 of 9 landed · retro written',
    },
  },
] as const

for (const mockup of MOCKUPS) {
  test(`the ${mockup.state} header matches the design's mockup at each width`, async ($, on) => {
    const world = worldOf(on, { ...mockup.before })
    await startSession($, world, 'startup')
    await runCommand($, mockup.command, PLAN)

    if (mockup.state === 'done') {
      world.files[RETRO_FILE] = { text: '# Retro\n', mtimeMs: AFTER }
    }

    const [path, text] = mockup.after
    await write($, world, path, text)

    for (const [columns, line] of Object.entries(mockup.lines)) {
      for (const surface of SURFACES) {
        expect((await bandLines($, surface, { bodyColumns: Number(columns) })).lines[0]).toBe(line)
      }
    }
  })
}

test("the arming header matches the design's mockup", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines[0]).toBe('crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed')
    expect(tones).toEqual(['~crank-execute · csv-export · ', 'Task 4 of 9', '~ (stage 2 of 3) · 3 landed'])
  }
})

test('a family command outside a git worktree disarms the run it replaces', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  world.isRepo = false
  await runCommand($, 'crank-lite:lite-execute', PLAN)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test('a prompt typed over a running turn leaves the ending header up, and the next prompt clears it', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await write($, world, LEDGER_FILE, ledger({ landed: 5, lines: [BOUND_5, 'Stopped: the user bounded this run at Task 5 — resume at Task 6'] }))
  await typePrompt($, 'how is it going?', 't')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · bound reached · 5 of 9 landed · resume at Task 6')
  }

  await typePrompt($, 'thanks')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(ENGINE)
  }
})

test("a retro an earlier run wrote does not end this run's header", async ($, on) => {
  const world = worldOf(on, { ...crankFiles(ledger({ landed: 3 })), [RETRO_FILE]: { text: '# Retro\n', mtimeMs: BEFORE } })
  await crankExecute($, world)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed')
  }
})

test('a command through Remote Control arms, and one from a task notification or another session does not', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await startSession($, world, 'startup')

  for (const kind of ['task-notification', 'peer'] as const) {
    await runCommand($, 'crank:crank-execute', PLAN, kind)

    for (const surface of SURFACES) {
      expect((await bandLines($, surface)).lines).toEqual(ENGINE)
    }
  }

  await runCommand($, 'crank:crank-execute', PLAN, 'bridge')

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed')
  }
})

test('a V1 flat plan keeps its header after crank-execute moves it into the per-plan layout', async ($, on) => {
  const flat = '.crank/plan-csv-export.md'
  const world = worldOf(on, { [`${ROOT}/${flat}`]: { text: crankPlan(), mtimeMs: BEFORE } })
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-execute', flat)
  delete world.files[`${ROOT}/${flat}`]
  world.files[PLAN_FILE] = { text: crankPlan(), mtimeMs: AFTER }
  await write($, world, LEDGER_FILE, ledger({ landed: 3 }))

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[0]).toBe('crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed')
  }
})
