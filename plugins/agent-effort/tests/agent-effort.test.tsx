import { expect, test } from 'claude-code/testing'
import type { ModelEffort, On } from 'claude-code'
import type { Engine, Mounted, Plugin } from 'claude-code/testing'

const SURFACES = ['terminal', 'desktop'] as const
const CALL = 'toolu_probe'
const AGENT = 'a-probe'
const CRANK_AGENT = 'a-crank'
const CRANK_TASK = 'Task 1 implementer'

const SPAWN = {
  tool_use_id: CALL,
  prompt: 'Reply ok.',
  description: 'probe bg',
  subagentType: 'Explore',
  provider: { plugin: 'engine', tier: 'core' },
  parentModel: 'claude-opus-5-5',
  background: true,
  fork: false,
} as const

const AGENT_ROW = {
  tool_use_id: CALL,
  tool: 'Agent',
  input: { description: 'probe bg', prompt: 'Reply ok.' },
  isRunning: true,
  isErrored: false,
  isInterrupted: false,
} as const

function agentOf(description: string) {
  return description === CRANK_TASK ? CRANK_AGENT : AGENT
}

// The engine beneath the plugin: spawns and Agent calls answer with the agent
// their description names, steps answer empty, and each row draws the text
// the plugin handed down.
function engine(on: On) {
  on('agent.spawn', (_$, e) => ({ model: 'claude-opus-5-5', agentId: agentOf(e.description) }))
  on('turn.step', async function* (_$, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
  })
  on('ui.render', { component: 'ToolUse' }, ($, e) => {
    const { Text } = $.ui.resolve(e)
    const { description } = e.props.input as { description: string }

    return <Text>{`${e.props.tool}(${description})`}</Text>
  })
  on('ui.render', { component: 'UserMessage' }, ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>{e.props.text}</Text>
  })
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine band</Text>
  })
  on('tool.call', { tool: 'Agent' }, (_$, e) => ({
    result: { status: 'async_launched', agentId: agentOf(e.description), description: e.description, prompt: 'Reply ok.', outputFile: '/tmp/probe.output' },
  }))
  on('agent.list', () => ({
    value: [
      { id: AGENT, description: 'probe bg', type: 'Explore', status: 'running' },
      { id: CRANK_AGENT, description: CRANK_TASK, type: 'general-purpose', status: 'running' },
    ],
  }))
  on('turn.complete', (_$, e) => ({ text: e.answer }))
  on('session.end', (_$, e) => ({ sessionId: e.sessionId }))
}

const BAND = {
  plugin: 'agent-effort',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 80, scroll: { offset: 0, bodyRows: 10 }, view: {} },
} as const

// Stands for crank-mods' hud, which lists each agent it sees spawn in its
// roster and empties the roster when the session ends, as at /clear.
const crankMods: Plugin = {
  name: 'crank-mods',
  register(on) {
    const roster = { plugin: 'crank-mods', key: 'hudRoster' } as const

    on('agent.spawn', async ($, e, next) => {
      const spawned = await next(e)
      const { value = [] } = await $.state.get(roster)

      if (spawned.agentId !== undefined) {
        await $.state.set(roster, [...value, spawned.agentId])
      }

      return spawned
    })
    on('session.end', async ($, e, next) => {
      await $.state.set(roster, [])

      return next(e)
    })
  },
}

// Stands for crank-mods' hud when the plugins' load order puts it beneath
// agent-effort; the append tier puts it there in the kit.
const bandBeneath: Plugin = {
  name: 'band-beneath',
  tier: 'append',
  register(on) {
    on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
      const below = await next(e)
      const { Box, Text } = $.ui.resolve(e)

      return (
        <Box flexDirection="column">
          <Text>hud row</Text>
          {below}
        </Box>
      )
    })
  },
}

async function textsOf<P extends (typeof SURFACES)[number]>(ui: Mounted<P, 'AbovePrompt'>) {
  return (await ui.findAll({ type: 'Text' })).map(found => found.text)
}

async function bandTexts($: Engine, surface: (typeof SURFACES)[number]) {
  return textsOf(await $.ui.mount({ ...BAND, surface }))
}

async function step($: Engine, agentId: string, effort: ModelEffort) {
  const stream = $.turn.step({ turnId: 't', index: 0, model: 'claude-opus-5-5', effort, messageCount: 1, agentId })
  for await (const _chunk of stream) {
    // drained: the step's request runs once its stream is read
  }
}

test("an Agent row shows the effort its agent's requests carry", async ($, on) => {
  engine(on)
  await $.agent.spawn(SPAWN)
  await step($, AGENT, 'low')

  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ plugin: 'agent-effort', surface, component: 'ToolUse', requestId: CALL, props: AGENT_ROW })
    expect((await ui.find({ type: 'Text' }))?.text).toBe('Agent(probe bg · effort low)')
  }
})

test('an Agent row whose agent has sent no request yet keeps its description', async ($, on) => {
  engine(on)
  await $.agent.spawn(SPAWN)

  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ plugin: 'agent-effort', surface, component: 'ToolUse', requestId: CALL, props: AGENT_ROW })
    expect((await ui.find({ type: 'Text' }))?.text).toBe('Agent(probe bg)')
  }
})

test('an Agent row already on screen gains the effort once the agent sends its first request', async ($, on) => {
  engine(on)
  await $.agent.spawn(SPAWN)
  const ui = await $.ui.mount({ plugin: 'agent-effort', surface: 'terminal', component: 'ToolUse', requestId: CALL, props: AGENT_ROW })
  await step($, AGENT, 'xhigh')

  expect((await ui.find({ type: 'Text' }))?.text).toBe('Agent(probe bg · effort xhigh)')
})

test('a background agent completion notice shows the effort of the agent it reports on', async ($, on) => {
  engine(on)
  await step($, AGENT, 'medium')

  for (const surface of SURFACES) {
    const ui = await $.ui.mount({
      plugin: 'agent-effort',
      surface,
      component: 'UserMessage',
      props: { text: 'Agent "probe bg" completed', origin: { kind: 'task-notification' }, isExpanded: false, task: { id: AGENT, status: 'completed' } },
    })
    expect((await ui.find({ type: 'Text' }))?.text).toBe('Agent "probe bg" completed · effort medium')
  }
})

test('the band lists a background agent with its description, type and effort', async ($, on) => {
  engine(on)
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, AGENT, 'high')

  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text' }))?.text).toBe('probe bg · Explore · effort high')
  }
})

test('the band leaves the row to the engine once the background agent finishes', async ($, on) => {
  engine(on)
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, AGENT, 'high')
  await $.turn.complete({ answer: 'ok', durationMs: 10, isAborted: false, turnId: 't', agentId: AGENT, reason: 'answer' })

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text' }))?.text).toBe('engine band')
})

test('the band shows a background agent again when it resumes after waiting on its own background work', async ($, on) => {
  engine(on)
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, AGENT, 'high')
  await $.turn.complete({ answer: '', durationMs: 10, isAborted: false, turnId: 't', agentId: AGENT, reason: 'answer' })
  await step($, AGENT, 'high')

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text' }))?.text).toBe('probe bg · Explore · effort high')
})

test('the band draws its rows above a band beneath it', { plugins: [bandBeneath] }, async ($, on) => {
  engine(on)
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, AGENT, 'high')

  for (const surface of SURFACES) {
    expect(await bandTexts($, surface)).toEqual(['probe bg · Explore · effort high', 'hud row', 'engine band'])
  }
})

test("the band skips an agent in crank-mods' roster and lists another background agent", { plugins: [crankMods] }, async ($, on) => {
  engine(on)
  await $.agent.spawn({ ...SPAWN, tool_use_id: 'toolu_crank', description: CRANK_TASK })
  await $.tool.call({ tool: 'Agent', description: CRANK_TASK, prompt: 'Reply ok.', subagent_type: 'general-purpose' })
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, CRANK_AGENT, 'high')
  await step($, AGENT, 'high')

  for (const surface of SURFACES) {
    expect(await bandTexts($, surface)).toEqual(['probe bg · Explore · effort high', 'engine band'])
  }
})

test('a band on screen drops an agent once crank-mods rosters it, and lists it again once the roster empties', { plugins: [crankMods] }, async ($, on) => {
  engine(on)
  await $.tool.call({ tool: 'Agent', description: CRANK_TASK, prompt: 'Reply ok.', subagent_type: 'general-purpose' })
  await $.tool.call({ tool: 'Agent', description: 'probe bg', prompt: 'Reply ok.', subagent_type: 'Explore' })
  await step($, CRANK_AGENT, 'high')
  await step($, AGENT, 'high')
  const both = ['Task 1 implementer · general-purpose · effort high', 'probe bg · Explore · effort high', 'engine band']
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })

  expect(await textsOf(ui)).toEqual(both)

  await $.agent.spawn({ ...SPAWN, tool_use_id: 'toolu_crank', description: CRANK_TASK })

  expect(await textsOf(ui)).toEqual(['probe bg · Explore · effort high', 'engine band'])

  await $.session.end({ reason: 'clear', sessionId: 's', resume: { id: 's' } })

  expect(await textsOf(ui)).toEqual(both)
})
