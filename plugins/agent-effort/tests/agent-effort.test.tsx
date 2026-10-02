import { expect, test } from 'claude-code/testing'
import type { ModelEffort, On } from 'claude-code'
import type { Engine } from 'claude-code/testing'

const SURFACES = ['terminal', 'desktop'] as const
const CALL = 'toolu_probe'
const AGENT = 'a-probe'

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

// The engine beneath the plugin: spawns answer with AGENT, steps answer empty,
// and each row draws the text the plugin handed down.
function engine(on: On) {
  on('agent.spawn', () => ({ model: 'claude-opus-5-5', agentId: AGENT }))
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
  on('tool.call', { tool: 'Agent' }, () => ({
    result: { status: 'async_launched', agentId: AGENT, description: 'probe bg', prompt: 'Reply ok.', outputFile: '/tmp/probe.output' },
  }))
  on('agent.list', () => ({ value: [{ id: AGENT, description: 'probe bg', type: 'Explore', status: 'running' }] }))
  on('turn.complete', (_$, e) => ({ text: e.answer }))
}

const BAND = {
  plugin: 'agent-effort',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 80, scroll: { offset: 0, bodyRows: 10 }, view: {} },
} as const

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
