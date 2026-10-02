import { expect, test } from 'claude-code/testing'
import type { Plugin } from 'claude-code/testing'

import { ledger } from './fixtures/files'
import { crankExecute, crankFiles } from './fixtures/runs'
import { agentBash, bandLines, MINUTE, ROOT, spawn, step, stop, SURFACES, worldOf } from './fixtures/world'

const ENGINE = ['engine band']
const HEADER = 'crank-execute · csv-export · Task 4 of 9 (stage 2 of 3) · 3 landed'
const IMPLEMENTER = 'a-implementer'
const BRIEF_4 = {
  prompt: `You are the implementer for one task. Read ${ROOT}/.crank/csv-export/exec/task-4-brief.md and follow it.`,
  description: 'Implement Task 4',
}
const CTEST = { name: 'Bash', input: { command: 'cd build && ctest -R csv --output-on-failure', description: 'Run the CSV tests' } }
const PROPS = { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 120, scroll: { offset: 0, bodyRows: 10 }, view: {} }

// Stands for a hot reload, which drops the plugin's timers: it refuses the
// first clock.every period asked for 10 minutes after the test's NOW, which
// ends that interval.
const reload: Plugin = {
  name: 'reload',
  tier: 'append',
  register(on) {
    const reloadAt = 1000 * 60 * 60 * 1000 + 10 * 60 * 1000
    let isReloaded = false

    on('clock.every', async ($, e, next) => {
      if (!isReloaded && (await $.clock.now()) >= reloadAt) {
        isReloaded = true
        return { deny: 'reloaded' }
      }

      return next(e)
    })
  },
}

// Stands for agent-effort sitting outer, as load order can place it: it draws
// its rows above next(e) and skips the agents in the hud's roster.
const effortBand: Plugin = {
  name: 'effort-band',
  tier: 'prepend',
  register(on) {
    const efforts = new Map<string, string>()

    on('turn.step', async function* ($, e, next) {
      if (e.agentId !== undefined && e.effort !== undefined) {
        efforts.set(e.agentId, String(e.effort))
      }

      return yield* next(e)
    })

    on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
      const below = await next(e)
      const { value: crank = [] } = await $.state.get({ plugin: 'crank-mods', key: 'hudRoster' })
      const rows = [...efforts].filter(([id]) => !crank.includes(id))
      const { Box, Text } = $.ui.resolve(e)

      return (
        <Box flexDirection="column">
          {rows.map(([id, effort]) => (
            <Text dimColor wrap="truncate">{`${id} · effort ${effort}`}</Text>
          ))}
          {below}
        </Box>
      )
    })
  },
}

// Counts the clock.every periods asked beneath the hud and draws the count,
// so a test sees whether the hud's tick still runs.
const periods: Plugin = {
  name: 'periods',
  tier: 'append',
  register(on) {
    let count = 0

    on('clock.every', (_$, e, next) => {
      count += 1
      return next(e)
    })

    on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
      const below = await next(e)
      const { Box, Text } = $.ui.resolve(e)

      return (
        <Box flexDirection="column">
          <Text wrap="truncate">{`periods ${count}`}</Text>
          {below}
        </Box>
      )
    })
  },
}

const implementer = (task: number) => ({
  prompt: `You are the implementer for one task. Read ${ROOT}/.crank/csv-export/exec/task-${task}-brief.md and follow it.`,
  description: `Implement Task ${task}`,
})

test('a spawn inside a subagent draws no row', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, 'a-nested', { ...BRIEF_4, parentAgentId: IMPLEMENTER })
  await step($, world, 'a-nested', { effort: 'high' })

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual([HEADER, ...ENGINE])
  }
})

test("an implementer past its role's 90th percentile shows its task, effort and elapsed time in warning", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await world.clock.advance(39 * MINUTE)
  await step($, world, IMPLEMENTER, { effort: 'high', toolUses: [CTEST] })
  await world.clock.advance(2 * MINUTE)

  for (const surface of SURFACES) {
    const { lines, tones } = await bandLines($, surface)
    expect(lines).toEqual([HEADER, '  implementer · Task 4 · effort high · 41m, past 40m · Bash ctest 2m', ...ENGINE])
    expect(tones).toContain('!41m, past 40m')
  }
})

test('an agent under its 90th percentile shows its elapsed time dim', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await world.clock.advance(39 * MINUTE)

  const { lines, tones } = await bandLines($, 'terminal')
  expect(lines[1]).toBe('  implementer · Task 4 · 39m')
  expect(tones).toContain('~39m')
})

test('the activity names the program a command runs or the file a tool touches, never their arguments', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await step($, world, IMPLEMENTER, { toolUses: [CTEST] })

  expect((await bandLines($, 'terminal')).lines[1]).toBe('  implementer · Task 4 · <1m · Bash ctest <1m')

  const edit = { name: 'Edit', input: { file_path: `${ROOT}/src/csv/writer.cpp`, old_string: 'a', new_string: 'b' } }
  await step($, world, IMPLEMENTER, { toolUses: [edit] })

  expect((await bandLines($, 'terminal')).lines[1]).toBe('  implementer · Task 4 · <1m · Edit writer.cpp <1m')
})

test('an agent shows "thinking" while its request runs', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await world.clock.advance(3 * MINUTE)
  await step($, world, IMPLEMENTER, { effort: 'high' })

  expect((await bandLines($, 'terminal')).lines[1]).toBe('  implementer · Task 4 · effort high · 3m · thinking <1m')
})

test('an agent waiting on its own background shell keeps a waiting row until it stops with none of its own running', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await step($, world, IMPLEMENTER, { toolUses: [CTEST] })
  await agentBash($, IMPLEMENTER, 'cd build && ctest --output-on-failure', 'b1')
  await world.clock.advance(17 * MINUTE)
  await stop($, IMPLEMENTER, ['b1'])
  await world.clock.advance(6 * MINUTE)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines[1]).toBe('  implementer · Task 4 · 23m · waiting on its background ctest 6m')
  }

  await step($, world, IMPLEMENTER, { toolUses: [{ name: 'Read', input: { file_path: `${ROOT}/build/Testing/LastTest.log` } }] })

  expect((await bandLines($, 'terminal')).lines[1]).toBe('  implementer · Task 4 · 23m · Read LastTest.log <1m')

  // b9 is another agent's shell, so this stop ends the row.
  await stop($, IMPLEMENTER, ['b9'])

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual([HEADER, ...ENGINE])
  }
})

test('an agent Claude Code lists as completed keeps its row; a failed or killed one leaves at the next tick', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, 'a-4', implementer(4))
  await spawn($, 'a-5', implementer(5))
  await spawn($, 'a-6', implementer(6))
  world.agents = [
    { id: 'a-4', description: 'Implement Task 4', type: 'general-purpose', status: 'completed' },
    { id: 'a-5', description: 'Implement Task 5', type: 'general-purpose', status: 'failed' },
    { id: 'a-6', description: 'Implement Task 6', type: 'general-purpose', status: 'killed' },
  ]
  await world.clock.advance(MINUTE)

  expect((await bandLines($, 'terminal')).lines).toEqual([HEADER, '  implementer · Task 4 · 1m', ...ENGINE])
})

test('parallel implementers put their tasks in the header and draw a row each', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, 'a-4', implementer(4))
  await spawn($, 'a-5', implementer(5))

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual([
      'crank-execute · csv-export · Tasks 4, 5 of 9 (stage 2 of 3) · 3 landed',
      '  implementer · Task 4 · <1m',
      '  implementer · Task 5 · <1m',
      ...ENGINE,
    ])
  }
})

test('the band draws three agent rows, two under 100 columns, then counts the rest', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)

  for (const task of [4, 5, 6, 7]) {
    await spawn($, `a-${task}`, implementer(task))
  }

  const rows = ['  implementer · Task 4 · <1m', '  implementer · Task 5 · <1m', '  implementer · Task 6 · <1m']
  expect((await bandLines($, 'terminal', { bodyColumns: 120 })).lines.slice(1)).toEqual([...rows, '  +1 more', ...ENGINE])
  expect((await bandLines($, 'terminal', { bodyColumns: 80 })).lines.slice(1)).toEqual([...rows.slice(0, 2), '  +2 more', ...ENGINE])
})

test('a row on screen redraws its elapsed time on each 30 s tick', async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  const ui = await $.ui.mount({ plugin: 'crank-mods', surface: 'terminal', component: 'AbovePrompt', props: PROPS })
  await world.clock.advance(5 * MINUTE)

  expect((await ui.findAll({ type: 'Text', text: 'implementer' })).map(t => t.text)).toContain('  implementer · Task 4 · 5m')
})

test("/clear stops the tick and hands the crank agents to agent-effort's band", { plugins: [effortBand, periods] }, async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await step($, world, IMPLEMENTER, { effort: 'high' })
  await world.clock.advance(MINUTE)
  await $.session.end({ reason: 'clear', sessionId: 's', resume: { id: 's' } })
  const [, ticked] = (await bandLines($, 'terminal')).lines
  await world.clock.advance(10 * MINUTE)

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(['a-implementer · effort high', ticked, ...ENGINE])
  }
})

test('session.start restarts the tick a hot reload dropped', { plugins: [reload] }, async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  const ui = await $.ui.mount({ plugin: 'crank-mods', surface: 'terminal', component: 'AbovePrompt', props: PROPS })
  const row = async () => (await ui.findAll({ type: 'Text', text: 'implementer' })).map(t => t.text).find(text => text.startsWith('  implementer'))
  await world.clock.advance(15 * MINUTE)

  expect(await row()).toBe('  implementer · Task 4 · 10m')

  await $.session.start({ cwd: ROOT, surface: 'terminal', isInteractive: true })
  await world.clock.advance(MINUTE)

  expect(await row()).toBe('  implementer · Task 4 · 16m')
})

test(
  "agent-effort's band, sitting outer, keeps its row for another agent above the hud's row for the crank agent",
  { plugins: [effortBand] },
  async ($, on) => {
    const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
    await crankExecute($, world)
    await spawn($, IMPLEMENTER, BRIEF_4)
    await spawn($, 'a-probe', { description: 'probe the build', parentAgentId: IMPLEMENTER })
    await step($, world, IMPLEMENTER, { effort: 'high' })
    await step($, world, 'a-probe', { effort: 'low' })

    for (const surface of SURFACES) {
      expect((await bandLines($, surface)).lines).toEqual([
        'a-probe · effort low',
        HEADER,
        '  implementer · Task 4 · effort high · <1m · thinking <1m',
        ...ENGINE,
      ])
    }
  },
)

test("with the hud toggle off a crank agent stays in agent-effort's band", { options: { hud: false }, plugins: [effortBand] }, async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await step($, world, IMPLEMENTER, { effort: 'high' })

  for (const surface of SURFACES) {
    expect((await bandLines($, surface)).lines).toEqual(['a-implementer · effort high', ...ENGINE])
  }
})

// One agent-row mockup per state and width. Effort shows at every width,
// because agent-effort's band skips the agents these rows draw.
const ROW_MOCKUPS = {
  running: {
    80: '  implementer · Task 4 · effort high · 41m · Bash ctest 2m',
    120: '  implementer · Task 4 · effort high · 41m, past 40m · Bash ctest 2m',
    160: '  implementer · Task 4 · effort high · 41m, past the usual 40m for an implementer · Bash ctest 2m',
  },
  waiting: {
    80: '  implementer · Task 4 · effort high · 23m · waiting on background ctest 6m',
    120: '  implementer · Task 4 · effort high · 23m · waiting on its background ctest 6m',
    160: '  implementer · Task 4 · effort high · 23m · waiting on its background ctest 6m · Claude Code lists it as finished',
  },
}

test("the running agent row matches the design's mockup at each width", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await world.clock.advance(39 * MINUTE)
  await step($, world, IMPLEMENTER, { effort: 'high', toolUses: [CTEST] })
  await world.clock.advance(2 * MINUTE)

  for (const [columns, line] of Object.entries(ROW_MOCKUPS.running)) {
    for (const surface of SURFACES) {
      const { lines, tones } = await bandLines($, surface, { bodyColumns: Number(columns) })
      expect(lines[1]).toBe(line)
      expect(tones.some(tone => tone.startsWith('!41m'))).toBe(true)
    }
  }
})

test("the waiting agent row matches the design's mockup at each width", async ($, on) => {
  const world = worldOf(on, crankFiles(ledger({ landed: 3 })))
  await crankExecute($, world)
  await spawn($, IMPLEMENTER, BRIEF_4)
  await step($, world, IMPLEMENTER, { effort: 'high', toolUses: [CTEST] })
  await agentBash($, IMPLEMENTER, 'cd build && ctest --output-on-failure', 'b1')
  await world.clock.advance(17 * MINUTE)
  await stop($, IMPLEMENTER, ['b1'])
  await world.clock.advance(6 * MINUTE)

  for (const [columns, line] of Object.entries(ROW_MOCKUPS.waiting)) {
    for (const surface of SURFACES) {
      expect((await bandLines($, surface, { bodyColumns: Number(columns) })).lines[1]).toBe(line)
    }
  }
})
