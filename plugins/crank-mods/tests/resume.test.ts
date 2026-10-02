import { expect, test } from 'claude-code/testing'
import type { CommandInfo } from 'claude-code'

import { OFFER_DELAY_MS } from '../hooks/resume'
import type { ResumeEntry } from '../hooks/resume'
import { answer, HOUR, MINUTE, NOW, ROOT, runCommand, startSession, worldOf } from './fixtures/world'
import type { Files } from './fixtures/world'

const KEY = `resume/v1/${ROOT}`
const SPEC = '.crank/receipt/spec.md'
const PLAN = '.crank/receipt/plan.md'
const PLAN_HANDOFF = `- **Next:** \`/crank-execute ${PLAN}\` — in this session or a fresh one; the plan is self-contained, and one run carries it through its last task.`

const file = (mtimeMs = NOW - HOUR) => ({ text: '# artifact\n', mtimeMs })
const effort = (...names: string[]): Files => Object.fromEntries(names.map(name => [`${ROOT}/.crank/receipt/${name}.md`, file()]))
const entry = (fields: Partial<ResumeEntry> = {}): ResumeEntry => ({
  slug: 'receipt',
  command: '/crank-execute',
  args: PLAN,
  path: PLAN,
  capturedAt: NOW - HOUR,
  ...fields,
})

test('a hand-off is stored and not suggested on its own turn', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank', `plan ${SPEC}`)
  await answer($, PLAN_HANDOFF)
  await world.clock.advance(HOUR)

  expect(world.store.get(KEY)).toEqual([{ slug: 'receipt', command: '/crank-execute', args: PLAN, path: PLAN, capturedAt: NOW + 100 }])
  expect(world.suggested).toEqual([])
})

test('/clear suggests the stored hand-off', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank', `plan ${SPEC}`)
  await answer($, PLAN_HANDOFF)
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([`/crank-execute ${PLAN}`])
})

test('a new process within 12 hours suggests the entry', async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry({ capturedAt: NOW - 9 * HOUR })] } })
  await startSession($, world, 'startup')

  expect(world.suggested).toEqual([`/crank-execute ${PLAN}`])
})

test('a startup offers once the terminal attaches, though classic.SessionStart runs before it does', async ($, on) => {
  const world = worldOf(on, effort('plan'), { surfaces: [], store: { [KEY]: [entry()] } })
  await $.classic.SessionStart({ source: 'startup', cwd: ROOT })
  world.surfaces = ['terminal']
  await world.clock.advance(OFFER_DELAY_MS)

  expect(world.suggested).toEqual([`/crank-execute ${PLAN}`])
})

test('an entry older than 12 hours is pruned and its key deleted', async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry({ capturedAt: NOW - 13 * HOUR })] } })
  await startSession($, world, 'resume')

  expect(world.suggested).toEqual([])
  expect(world.store.has(KEY)).toBe(false)
})

test('an entry whose effort was deleted is not suggested', async ($, on) => {
  const world = worldOf(on, {}, { store: { [KEY]: [entry()] } })
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([])
})

test('a phase line whose output is newer than the capture is not suggested', async ($, on) => {
  const files = { ...effort('spec'), [`${ROOT}/${PLAN}`]: file(NOW - 30 * MINUTE) }
  const world = worldOf(on, files, { store: { [KEY]: [entry({ command: '/crank', args: `plan ${SPEC}`, path: SPEC })] } })
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([])
})

test('a finished run, whose sibling retro exists, is pruned', async ($, on) => {
  const world = worldOf(on, effort('plan', 'retro'), { store: { [KEY]: [entry()] } })
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([])
  expect(world.store.has(KEY)).toBe(false)
})

test('a headless session reads no store and suggests nothing', async ($, on) => {
  const world = worldOf(on, effort('plan'), { surfaces: [], store: { [KEY]: [entry()] } })
  await startSession($, world, 'startup')

  expect(world.storeReads).toEqual([])
  expect(world.suggested).toEqual([])
})

test('a command from the SDK never arms, so its hand-off is not stored', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank', `plan ${SPEC}`, 'sdk')
  await answer($, PLAN_HANDOFF)

  expect(world.storeWrites).toEqual([])
})

test("a subagent's answer is not captured", async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank', `plan ${SPEC}`)
  await answer($, PLAN_HANDOFF, 'a-implementer')

  expect(world.storeWrites).toEqual([])
})

test('a hand-off in an unarmed session is not captured', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await answer($, PLAN_HANDOFF)

  expect(world.storeWrites).toEqual([])
})

test('a hand-off that names no .crank path is not stored', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-deslop')
  await answer($, 'Fixed 4 findings.\n\n**Next:** `/crank plan` to plan the rest.')

  expect(world.storeWrites).toEqual([])
})

test("a capture after a take replaces the launch, so the run's resume line shows past the false-start window", async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry({ command: '/lite-execute', capturedAt: NOW - 10 * MINUTE })] } })
  await startSession($, world, 'startup')
  world.suggested.length = 0
  await runCommand($, 'crank-lite:lite-execute', `${PLAN} complete the next stage`)
  await world.clock.advance(HOUR)
  await answer($, `Stopped at the stage 1 gate. Run \`/lite-execute ${PLAN}\` to resume at Task 4.`)
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([`/lite-execute ${PLAN}`])
})

test('a false start offers the launched line, bound included, for 15 minutes', async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry()] } })
  await startSession($, world, 'startup')
  world.suggested.length = 0
  await runCommand($, 'crank:crank-execute', `${PLAN} Implement Phase 5.`)
  await world.clock.advance(2 * MINUTE)
  await startSession($, world, 'clear')
  await world.clock.advance(18 * MINUTE)
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([`/crank-execute ${PLAN} Implement Phase 5.`])
})

test('/model offers again while the suggestion showed since the last main-loop turn', async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry()] } })
  await startSession($, world, 'clear')
  await runCommand($, 'model', 'sonnet')
  await world.clock.advance(100)
  await answer($, 'Hello.')
  await runCommand($, 'effort', 'high')
  await world.clock.advance(100)

  expect(world.suggested).toEqual([`/crank-execute ${PLAN}`, `/crank-execute ${PLAN}`])
})

test('a built-in command keeps the run armed, and another skill disarms it', async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank-lite:lite-execute', PLAN)
  await runCommand($, 'reload-skills')
  await answer($, `Run \`/lite-execute ${PLAN}\` to resume at Task 3.`)

  expect(world.store.get(KEY)).toEqual([expect.objectContaining({ command: '/lite-execute', args: PLAN })])

  world.store.clear()
  await runCommand($, 'crank-lite:crank-lite', `plan ${SPEC}`)
  await runCommand($, 'mattpocock-skills:handoff')
  await answer($, `Next step: \`/lite-execute ${PLAN}\`.`)

  expect(world.store.has(KEY)).toBe(false)
})

test("a bare executor line takes the executor run's plan, and no other run's", async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-execute', PLAN)
  await answer($, 'Stopped before Task 6. Resume with `/crank:crank-execute`.')
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([`/crank:crank-execute ${PLAN}`])

  world.store.clear()
  await runCommand($, 'crank-lite:crank-lite', `plan ${SPEC}`)
  await answer($, 'Drafted the plan. Then run `/lite-execute`.')

  expect(world.store.has(KEY)).toBe(false)
})

test('an offer that prunes nothing writes nothing to the store', async ($, on) => {
  const world = worldOf(on, effort('plan'), { store: { [KEY]: [entry()] } })
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([`/crank-execute ${PLAN}`])
  expect(world.storeWrites).toEqual([])
})

test("a hand-off is recognised by the names $.command.list() reports, a new skill's included", async ($, on) => {
  const deepen: CommandInfo = { name: 'crank:crank-deepen', description: '', source: 'plugin', plugin: 'crank' }
  const crank: CommandInfo = { name: 'crank:crank', description: '', source: 'plugin', plugin: 'crank' }
  const world = worldOf(on, effort('deepen-brief'), { commands: [crank, deepen] })
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank-deepen', 'the csv idea')
  await answer($, 'End by recommending the next step: `/crank spec .crank/receipt/deepen-brief.md`.')

  expect(world.store.get(KEY)).toEqual([expect.objectContaining({ command: '/crank', args: 'spec .crank/receipt/deepen-brief.md' })])

  world.store.clear()
  await runCommand($, 'crank:crank-deepen', 'the csv idea')
  await answer($, 'Next step: `/lite-deepen .crank/receipt/deepen-brief.md`.')

  expect(world.store.has(KEY)).toBe(false)
})

test('the store keeps five entries per worktree, newest first', async ($, on) => {
  const slugs = ['a', 'b', 'c', 'd', 'e']
  const files: Files = Object.fromEntries(['f', ...slugs].map(slug => [`${ROOT}/.crank/${slug}/plan.md`, file()]))
  const stored = slugs.map(slug => entry({ slug, path: `.crank/${slug}/plan.md`, args: `.crank/${slug}/plan.md` }))
  const world = worldOf(on, files, { store: { [KEY]: stored } })
  await startSession($, world, 'startup')
  await runCommand($, 'crank-lite:lite-execute', '.crank/f/plan.md')
  await answer($, 'Run `/lite-execute .crank/f/plan.md` to resume at Task 2.')

  expect((world.store.get(KEY) as ResumeEntry[]).map(x => x.slug)).toEqual(['f', 'a', 'b', 'c', 'd'])
})

test('with the resume toggle off nothing is stored or suggested', { options: { resume: false } }, async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'), { store: { [KEY]: [entry()] } })
  await startSession($, world, 'startup')
  await runCommand($, 'crank:crank', `plan ${SPEC}`)
  await answer($, PLAN_HANDOFF)
  await startSession($, world, 'clear')

  expect(world.suggested).toEqual([])
  expect(world.storeWrites).toEqual([])
})

test("a compaction's SessionStart keeps the run armed and offers nothing", async ($, on) => {
  const world = worldOf(on, effort('spec', 'plan'))
  await startSession($, world, 'startup')
  await runCommand($, 'crank-lite:lite-execute', PLAN)
  await $.classic.SessionStart({ source: 'compact', cwd: ROOT })
  await world.clock.advance(OFFER_DELAY_MS)
  await answer($, `Run \`/lite-execute ${PLAN}\` to resume at Task 3.`)

  expect(world.suggested).toEqual([])
  expect(world.store.get(KEY)).toEqual([expect.objectContaining({ command: '/lite-execute', args: PLAN })])
})
