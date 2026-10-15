import { atom, read, update } from 'claude-code'
import type { AgentInfo, Register, StateDollar } from 'claude-code'

const AGENT_OF_CALL = { plugin: 'agent-effort', key: 'agentOfCall' } as const
const EFFORT_OF_AGENT = { plugin: 'agent-effort', key: 'effortOfAgent' } as const
const MODEL_OF_AGENT = { plugin: 'agent-effort', key: 'modelOfAgent' } as const
const IS_RUNNING = { plugin: 'agent-effort', key: 'isRunning' } as const
const MODEL_ID = /^claude-([a-z]+)-(\d+)-(\d{1,2})(?:-\d{8})?$/
const background = atom({ plugin: 'agent-effort', key: 'background' } as const, [])

// The engine settles a subagent's effort (the Agent call's `effort`, else its
// definition's `effort`, else the setting for its model) only when the subagent
// sends its first request, after `agent.spawn` has resolved, so the effort is
// read from `turn.step`.
async function effortOf($: StateDollar, agentId: string) {
  return (await $.state.get({ ...EFFORT_OF_AGENT, id: agentId })).value
}

// Ids outside the claude-<family>-<major>-<minor> form show as written (per
// project decision: no model table to keep in sync with the Python one in
// tools/claude-effort/claude_effort.py).
function modelName(model: string) {
  const [, family, major, minor] = MODEL_ID.exec(model) ?? []

  return family === undefined ? model : `${family.charAt(0).toUpperCase()}${family.slice(1)} ${major}.${minor}`
}

async function labelOf($: StateDollar, agentId: string) {
  const { value: model } = await $.state.get({ ...MODEL_OF_AGENT, id: agentId })

  if (model === undefined) {
    return undefined
  }

  const effort = await effortOf($, agentId)

  return effort === undefined ? modelName(model) : `${modelName(model)} · effort ${effort}`
}

async function labelOfCall($: StateDollar, toolUseId: string) {
  const { value: agentId } = await $.state.get({ ...AGENT_OF_CALL, id: toolUseId })

  return agentId === undefined ? undefined : labelOf($, agentId)
}

async function isRunning($: StateDollar, agentId: string) {
  return (await $.state.get({ ...IS_RUNNING, id: agentId })).value === true
}

async function bandRow($: StateDollar, agent: AgentInfo) {
  return [agent.description, agent.type, await labelOf($, agent.id)].filter(Boolean).join(' · ')
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

    if (agentId !== undefined && (await $.state.get({ ...MODEL_OF_AGENT, id: agentId })).value !== e.model) {
      await $.state.set({ ...MODEL_OF_AGENT, id: agentId }, e.model)
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
    const label = await labelOfCall($, e.requestId)

    if (label === undefined || !hasDescription(e.props.input)) {
      return next(e)
    }

    const input = { ...e.props.input, description: `${e.props.input.description} · ${label}` }

    return next({ ...e, props: { ...e.props, input } })
  })

  on('ui.render', { component: 'UserMessage', props: { origin: { kind: 'task-notification' } } }, async ($, e, next) => {
    const agentId = e.props.task?.id
    const label = agentId === undefined ? undefined : await labelOf($, agentId)

    if (label === undefined || e.props.isExpanded) {
      return next(e)
    }

    return next({ ...e, props: { ...e.props, text: `${e.props.text} · ${label}` } })
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
  // spawn's description). Its rows sit above the bands beneath it.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    const ids = await read($, background)

    if (e.props.hasSurvey || ids.length === 0) {
      return below
    }

    const flags = await Promise.all(ids.map(id => isRunning($, id)))
    const listed = await $.agent.list()
    const running = ids.filter((id, i) => flags[i]).flatMap(id => listed.filter(agent => agent.id === id))

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
