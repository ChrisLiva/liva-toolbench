import { mock } from 'claude-code/testing'
import type { AgentInfo, CommandInfo, ModelEffort, On, PromptOrigin, RenderSurface, ToolCallInput, TurnStepToolUse } from 'claude-code'
import type { Engine } from 'claude-code/testing'

import { OFFER_DELAY_MS } from '../../hooks/resume'

export const SURFACES = ['terminal', 'desktop'] as const
export const ROOT = '/work/liva-todo'
export const LEDGER_DIR = `${ROOT}/.git/crank`
export const MINUTE = 60 * 1000
export const HOUR = 60 * MINUTE
export const NOW = 1000 * HOUR

export type Files = Record<string, { text: string; mtimeMs: number }>

const COMMANDS: CommandInfo[] = [
  { name: 'crank:crank', description: '', source: 'plugin', plugin: 'crank' },
  { name: 'crank:crank-execute', description: '', source: 'plugin', plugin: 'crank' },
  { name: 'crank:crank-deslop', description: '', source: 'plugin', plugin: 'crank' },
  { name: 'crank-lite:crank-lite', description: '', source: 'plugin', plugin: 'crank-lite' },
  { name: 'crank-lite:lite-execute', description: '', source: 'plugin', plugin: 'crank-lite' },
  { name: 'mattpocock-skills:handoff', description: '', source: 'plugin', plugin: 'mattpocock-skills' },
  ...['clear', 'compact', 'config', 'effort', 'model', 'reload-skills'].map(name => ({ name, description: '', source: 'builtin' as const })),
]

/** What the world beneath the plugin saw: the files it serves, the suggestions shown, and the store's keys read and written. */
export type World = {
  files: Files
  /** What `$.session.surfaces()` answers now; a session at startup reads [] until its terminal attaches. */
  surfaces: RenderSurface[]
  /** What `$.agent.list()` answers now. */
  agents: AgentInfo[]
  /** Whether `git rev-parse` finds a worktree; false makes it exit 128. */
  isRepo: boolean
  /** The tool calls the next step's response makes. */
  toolUses: TurnStepToolUse[]
  suggested: string[]
  store: Map<string, unknown>
  storeReads: string[]
  storeWrites: string[]
  clock: ReturnType<typeof mock.clock>
}

export type WorldOptions = {
  surfaces?: RenderSurface[]
  commands?: CommandInfo[]
  store?: Record<string, unknown>
  ledgerDir?: string
}

// A test reads no disk and nothing runs beneath it, so every op the plugin
// calls answers from memory here, the store included: a spy beside mock.store
// would register store.set twice.
export function worldOf(on: On, files: Files, options: WorldOptions = {}): World {
  const world: World = {
    files,
    surfaces: options.surfaces ?? ['terminal'],
    agents: [],
    isRepo: true,
    toolUses: [],
    suggested: [],
    store: new Map(Object.entries(options.store ?? {})),
    storeReads: [],
    storeWrites: [],
    clock: mock.clock(on, { now: NOW }),
  }
  const stdout = `${ROOT}\n${options.ledgerDir ?? LEDGER_DIR}\n`

  on('classic.SessionStart', () => ({}))
  on('classic.SubagentStop', () => ({}))
  on('session.start', (_$, e) => ({ cwd: e.cwd }))
  on('agent.spawn', (_$, e) => ({ model: 'claude-opus-5-5', agentId: e.tool_use_id.replace(/^toolu-/, '') }))
  on('agent.list', () => ({ value: world.agents }))
  on('turn.step', async function* (_$, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: world.toolUses, stopReason: 'tool_use', usage: null }
  })
  on('session.surfaces', () => ({ value: world.surfaces }))
  on('command.list', () => ({ value: options.commands ?? COMMANDS }))
  on('process.run', () => ({
    value: world.isRepo
      ? { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false }
      : { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false },
  }))
  on('fs.exists', (_$, e) => ({ value: e.path in world.files }))
  on('fs.stat', (_$, e) => {
    const file = world.files[e.path]

    return file === undefined ? { deny: `ENOENT ${e.path}` } : { value: { kind: 'file', size: file.text.length, mtimeMs: file.mtimeMs, isLink: false } }
  })
  on('fs.read', (_$, e) => {
    const file = world.files[e.path]

    return file === undefined ? { deny: `ENOENT ${e.path}` } : { value: file.text }
  })
  on('prompt.suggest', (_$, e) => {
    world.suggested.push(e.text)

    return { isShown: true }
  })
  on('store.get', (_$, e) => {
    world.storeReads.push(e.key)

    return { value: world.store.get(e.key) }
  })
  on('store.set', (_$, e) => {
    world.storeWrites.push(e.key)
    world.store.set(e.key, JSON.parse(JSON.stringify(e.value)))

    return { value: undefined }
  })
  on('store.delete', (_$, e) => {
    world.storeWrites.push(e.key)
    world.store.delete(e.key)

    return { value: undefined }
  })
  on('store.keys', () => ({ value: [...world.store.keys()] }))
  on('command.run', () => ({ text: '' }))
  on('turn.complete', (_$, e) => ({ text: e.answer }))
  on('prompt.submit', (_$, e) => ({ text: e.text }))
  on('session.end', (_$, e) => ({ sessionId: e.sessionId }))
  on('tool.call', (_$, e) => ({ result: e.tool === 'Bash' && e.run_in_background === true ? { backgroundTaskId: e.tool_use_id } : {} }))
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine band</Text>
  })

  return world
}

/** A SessionStart, then the wait after which crank-resume's suggestion lands. */
export async function startSession($: Engine, world: World, source: 'startup' | 'resume' | 'clear') {
  await $.classic.SessionStart({ source, cwd: ROOT })
  await world.clock.advance(OFFER_DELAY_MS)
}

export async function runCommand($: Engine, command: string, args = '', kind: PromptOrigin['kind'] = 'composer') {
  await $.command.run({ command, args, origin: { kind } as PromptOrigin, presentation: { isFullscreen: true, columns: 120 } })
}

export async function answer($: Engine, text: string, agentId?: string) {
  await $.turn.complete({ answer: text, durationMs: 1, isAborted: false, turnId: 't', reason: 'answer', ...(agentId === undefined ? {} : { agentId }) })
}

export async function typePrompt($: Engine, text: string, turnId?: string) {
  await $.prompt.submit({ text, wait: false, origin: { kind: 'composer' }, ...(turnId === undefined ? {} : { turnId }) })
}

/** A Bash call in the main loop, the way most progress writes land. */
export async function bash($: Engine) {
  await $.tool.call({ tool: 'Bash', command: 'true' })
}

/** The main loop's Agent call, or a subagent's with `parentAgentId`; the agent's id is `id`. */
export async function spawn(
  $: Engine,
  id: string,
  { prompt = 'Reply ok.', description = '', parentAgentId }: { prompt?: string; description?: string; parentAgentId?: string } = {},
) {
  const nested = parentAgentId === undefined ? {} : { parentAgentId }
  const provider = { plugin: 'engine', tier: 'core' } as const
  await $.agent.spawn({
    tool_use_id: `toolu-${id}`,
    prompt,
    description,
    subagentType: 'general-purpose',
    provider,
    parentModel: 'claude-opus-5-5',
    background: true,
    fork: false,
    ...nested,
  })
}

/** One request of a subagent, whose response makes `toolUses`. */
export async function step($: Engine, world: World, agentId: string, { effort, toolUses = [] }: { effort?: ModelEffort; toolUses?: TurnStepToolUse[] } = {}) {
  world.toolUses = toolUses
  const stream = $.turn.step({ turnId: 't', index: 0, model: 'claude-opus-5-5', messageCount: 1, agentId, ...(effort === undefined ? {} : { effort }) })

  for await (const _chunk of stream) {
    // drained: the step's request runs once its stream is read
  }
}

/** A subagent's Bash call; with `shellId` it runs in the background under that id. */
export async function agentBash($: Engine, agentId: string, command: string, shellId?: string) {
  // The kit's type for $.tool.call leaves out agentId, which the engine still hands every hook, as a subagent's own call carries it.
  const call = $.tool.call as (input: ToolCallInput) => Promise<unknown>
  await call({ tool: 'Bash', command, agentId, tool_use_id: shellId ?? `toolu-${agentId}`, run_in_background: shellId !== undefined })
}

/** A subagent's turn ending, while the session's background shells in `running` still run. */
export async function stop($: Engine, agentId: string, running: string[] = []) {
  const shells = running.map(id => ({ id, type: 'shell', status: 'running', description: '', command: '' }))
  await $.classic.SubagentStop({
    agent_id: agentId,
    agent_transcript_path: '',
    agent_type: 'general-purpose',
    stop_hook_active: false,
    background_tasks: shells,
  })
}

const BAND = { plugin: 'crank-mods', component: 'AbovePrompt' } as const

/** Each line the band draws, with its cells' tones: `~` before dim text, `!` before warning text, plain text bare. */
export async function bandLines($: Engine, surface: (typeof SURFACES)[number], { bodyColumns = 120, hasSurvey = false } = {}) {
  const props = { hasSurvey, isWorking: true, maxRows: 10, bodyColumns, scroll: { offset: 0, bodyRows: 10 }, view: {} }
  const ui = await $.ui.mount({ ...BAND, surface, props })
  const texts = await ui.findAll({ type: 'Text' })
  const lines = texts.filter(t => t.props.wrap === 'truncate' || t.text === 'engine band').map(t => t.text)
  const tones = texts
    .filter(t => t.props.wrap === undefined && t.text !== 'engine band')
    .map(t => `${t.props.color === 'warning' ? '!' : t.props.dimColor === true ? '~' : ''}${t.text}`)

  return { lines, tones }
}
