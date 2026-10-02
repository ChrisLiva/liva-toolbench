import { atom, read, update } from 'claude-code'
import type { AgentInfo, Register, StateDollar } from 'claude-code'

const AGENT_OF_CALL = { plugin: 'agent-effort', key: 'agentOfCall' } as const
const EFFORT_OF_AGENT = { plugin: 'agent-effort', key: 'effortOfAgent' } as const
const IS_RUNNING = { plugin: 'agent-effort', key: 'isRunning' } as const
const background = atom({ plugin: 'agent-effort', key: 'background' } as const, [])
const crankRoster = atom({ plugin: 'crank-mods', key: 'hudRoster' } as const, [])

// The engine settles a subagent's effort (its definition's `effort`, else the
// setting for its model) only when the subagent sends its first request, after
// `agent.spawn` has resolved, so the effort is read from `turn.step`.
async function effortOf($: StateDollar, agentId: string) {
  return (await $.state.get({ ...EFFORT_OF_AGENT, id: agentId })).value
}

async function effortOfCall($: StateDollar, toolUseId: string) {
  const { value: agentId } = await $.state.get({ ...AGENT_OF_CALL, id: toolUseId })

  return agentId === undefined ? undefined : effortOf($, agentId)
}

async function isRunning($: StateDollar, agentId: string) {
  return (await $.state.get({ ...IS_RUNNING, id: agentId })).value === true
}

async function bandRow($: StateDollar, agent: AgentInfo) {
  const effort = await effortOf($, agent.id)

  return [agent.description, agent.type, effort === undefined ? undefined : `effort ${effort}`].filter(Boolean).join(' · ')
}

function hasDescription(input: unknown): input is { description: string } {
  return typeof input === 'object' && input !== null && typeof (input as { description?: unknown }).description === 'string'
}

export const register: Register = on => {
  on('agent.spawn', async ($, e, next) => {
    const spawned = await next(e)

    if (spawned.agentId !== undefined) {
      await $.state.set({ ...AGENT_OF_CALL, id: e.tool_use_id }, spawned.agentId)
    }

    return spawned
  })

  // An agent's turn runs from a request until `turn.complete`; one waiting on
  // its own background work has completed a turn and resumes with a new step.
  on('turn.step', async function* ($, e, next) {
    const { agentId } = e

    if (agentId !== undefined && !(await isRunning($, agentId))) {
      await $.state.set({ ...IS_RUNNING, id: agentId }, true)
    }

    if (agentId !== undefined && e.effort !== undefined) {
      const effort = String(e.effort)

      if ((await effortOf($, agentId)) !== effort) {
        await $.state.set({ ...EFFORT_OF_AGENT, id: agentId }, effort)
      }
    }

    return yield* next(e)
  })

  on('ui.render', { component: 'ToolUse', props: { tool: 'Agent' } }, async ($, e, next) => {
    const effort = await effortOfCall($, e.requestId)

    if (effort === undefined || !hasDescription(e.props.input)) {
      return next(e)
    }

    const input = { ...e.props.input, description: `${e.props.input.description} · effort ${effort}` }

    return next({ ...e, props: { ...e.props, input } })
  })

  on('ui.render', { component: 'UserMessage', props: { origin: { kind: 'task-notification' } } }, async ($, e, next) => {
    const agentId = e.props.task?.id
    const effort = agentId === undefined ? undefined : await effortOf($, agentId)

    if (effort === undefined || e.props.isExpanded) {
      return next(e)
    }

    return next({ ...e, props: { ...e.props, text: `${e.props.text} · effort ${effort}` } })
  })

  // `async_launched` is the Agent result both for a call made with
  // run_in_background and for a foreground agent moved to the background.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const ran = await next(e)

    if (ran.deny === undefined && ran.isError !== true && 'status' in ran.result && ran.result.status === 'async_launched') {
      const { agentId } = ran.result
      await update($, background, ids => (ids.includes(agentId) ? ids : [...ids, agentId]))
    }

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      await $.state.set({ ...IS_RUNNING, id: e.agentId }, false)
    }

    return next(e)
  })

  // Claude Code's own tasks list has no render hook and draws the label fixed
  // at spawn, before the engine picks the effort, so the measured effort goes
  // in this band (per project decision: no guessed effort stamped into the
  // spawn's description). Its rows sit above the bands beneath it, and it skips
  // the agents in crank-mods' roster, whose rows crank-mods' hud draws.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    const ids = await read($, background)

    if (e.props.hasSurvey || ids.length === 0) {
      return below
    }

    const crank = await read($, crankRoster)
    const flags = await Promise.all(ids.map(id => isRunning($, id)))
    const listed = await $.agent.list()
    const running = ids.filter((id, i) => flags[i] && !crank.includes(id)).flatMap(id => listed.filter(agent => agent.id === id))

    if (running.length === 0) {
      return below
    }

    const rows = await Promise.all(running.map(agent => bandRow($, agent)))
    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        {rows.map(row => (
          <Text dimColor wrap="truncate">
            {row}
          </Text>
        ))}
        {below}
      </Box>
    )
  })
}
