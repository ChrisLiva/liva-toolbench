import { atom, read, update } from 'claude-code'
import type { CommandRunInput, EngineInterface, PromptOrigin, Register, StateDollar, Timer, TurnCompleteInput } from 'claude-code'

import type { CrankArtifact, CrankRun, CrankWhere, HudAgent, HudProgress } from '../types'
import { endingOf, headerOf, isQuiet, LITE_EXECUTE, planOf, progressFiles, progressFrom, rowsOf, workingOf } from './hud'
import type { Row } from './hud'
import { artifactOf, bare, isFamily, sibling } from './parse'
import { findHandoff, isFresh, MAX_ENTRIES, MAX_KEY_LENGTH, OFFER_DELAY_MS, outputOf } from './resume'
import type { ResumeEntry } from './resume'
import { activityOf, classify, commandWord } from './roster'

const where = atom({ plugin: 'crank-mods', key: 'where' } as const, null)
const run = atom({ plugin: 'crank-mods', key: 'run' } as const, null)
const offered = atom({ plugin: 'crank-mods', key: 'offered' } as const, null)
const hudRun = atom({ plugin: 'crank-mods', key: 'hudRun' } as const, null)
const hudProgress = atom({ plugin: 'crank-mods', key: 'hudProgress' } as const, null)
const hudRoster = atom({ plugin: 'crank-mods', key: 'hudRoster' } as const, [])
const hudTick = atom({ plugin: 'crank-mods', key: 'hudTick' } as const, 0)
const HUD_AGENT = { plugin: 'crank-mods', key: 'hudAgent' } as const
const HUD_NOW = { plugin: 'crank-mods', key: 'hudNow' } as const

const REOFFER = new Set(['model', 'effort', 'config'])
const TICK_MS = 30 * 1000
const ENDED = new Set(['failed', 'killed'])

// A hot reload drops this timer with the environment that started it, and a
// timer outlives /clear, so every disarm cancels it and session.start starts
// it again for a run still armed.
let ticker: Timer | undefined

// A -p run and the Agent SDK read origin `sdk` and never arm.
const isPerson = (origin: PromptOrigin) => origin.kind === 'composer' || origin.kind === 'bridge'

async function locate($: EngineInterface, cwd?: string): Promise<CrankWhere | null> {
  const argv = ['git', 'rev-parse', '--path-format=absolute', '--show-toplevel', '--git-path', 'crank']
  const ran = await $.process.run(argv, cwd === undefined ? undefined : { cwd }).catch(() => undefined)
  const [root, ledgerDir] = ran?.exitCode === 0 ? ran.stdout.trim().split('\n') : []

  return root && ledgerDir ? { root, ledgerDir } : null
}

async function familyNames($: EngineInterface) {
  return new Set((await $.command.list()).filter(c => isFamily(c.name)).map(c => bare(c.name)))
}

async function isBuiltin($: EngineInterface, command: string) {
  return (await $.command.list()).some(c => c.name === command && c.source === 'builtin')
}

async function arm($: EngineInterface, e: CommandRunInput) {
  const at = await locate($)

  if (at === null) {
    return null
  }

  const armed: CrankRun = { command: e.command, args: e.args, artifact: artifactOf(e.args), armedAt: await $.clock.now() }
  await update($, where, () => at)
  await update($, run, () => armed)

  return { armed, at }
}

async function disarm($: StateDollar) {
  if ((await read($, run)) !== null) {
    await update($, run, () => null)
  }

  await disarmHud($)
}

const mtimeOf = ($: EngineInterface, path: string) =>
  $.fs.stat(path).then(
    s => s.mtimeMs,
    () => undefined,
  )

// Other processes write the same store file, so each edit re-reads its key
// and writes only when the entries changed.
async function edit($: EngineInterface, at: CrankWhere, change: (entries: ResumeEntry[]) => Promise<ResumeEntry[]> | ResumeEntry[]) {
  const key = `resume/v1/${at.root}`

  if (key.length > MAX_KEY_LENGTH) {
    return []
  }

  const before = ((await $.store.get(key)) ?? []) as ResumeEntry[]
  const after = await change(before)

  if (JSON.stringify(after) !== JSON.stringify(before)) {
    await (after.length > 0 ? $.store.set(key, after) : $.store.delete(key))
  }

  return after
}

async function isStillNext($: EngineInterface, at: CrankWhere, entry: ResumeEntry, now: number) {
  const artifact = artifactOf(entry.path)

  if (!isFresh(entry, now) || artifact === null) {
    return false
  }

  const file = (path: string) => `${at.root}/${path}`

  if (!(await $.fs.exists(file(artifact.path))) || (await $.fs.exists(file(sibling(artifact, 'retro'))))) {
    return false
  }

  const output = outputOf(entry, artifact)
  const outputMtime = output === undefined ? undefined : await mtimeOf($, file(output))

  return outputMtime === undefined || outputMtime <= entry.capturedAt
}

async function offer($: EngineInterface) {
  const at = await read($, where)

  if (at === null) {
    return
  }

  const now = await $.clock.now()
  const [newest] = await edit($, at, async entries => {
    const flags = await Promise.all(entries.map(entry => isStillNext($, at, entry, now)))

    return entries.filter((_, i) => flags[i])
  })

  if (newest === undefined) {
    return
  }

  const { isShown } = await $.prompt.suggest({ text: `${newest.command} ${newest.args}` })

  if (isShown) {
    await update($, offered, () => now)
  }
}

// At startup classic.SessionStart runs before the terminal attaches, so
// surfaces() reads [] until the session is up; a headless run reads [] for
// good, and its `where` stays null so nothing offers.
async function place($: EngineInterface, cwd: string, isResume: boolean) {
  if ((await $.session.surfaces()).length === 0) {
    return
  }

  const at = await locate($, cwd)
  await update($, where, () => at)

  if (isResume) {
    await offer($)
  }
}

async function forget($: StateDollar) {
  if ((await read($, offered)) !== null) {
    await update($, offered, () => null)
  }
}

// The launched line, bound included, replaces its effort's entry's line, so a
// false start offers it again for 15 minutes.
async function take($: EngineInterface, armed: CrankRun, at: CrankWhere) {
  await forget($)
  const { artifact } = armed

  if (artifact !== null) {
    const launched = { command: `/${bare(armed.command)}`, args: armed.args, path: artifact.path, takenAt: armed.armedAt }
    await edit($, at, entries => entries.map(entry => (entry.slug === artifact.slug ? { ...entry, ...launched } : entry)))
  }
}

// A capture replaces its effort's entry whole, so the launch's takenAt never
// hides the run's own resume line.
async function capture($: EngineInterface, e: TurnCompleteInput) {
  await forget($)
  const armed = await read($, run)
  const at = await read($, where)

  if (e.reason !== 'answer' || armed === null || at === null) {
    return
  }

  const found = findHandoff(e.answer, await familyNames($), armed)

  if (found === null || !(await $.fs.exists(`${at.root}/${found.artifact.path}`))) {
    return
  }

  const { command, args, artifact } = found
  const entry: ResumeEntry = { slug: artifact.slug, command, args, path: artifact.path, capturedAt: await $.clock.now() }
  await edit($, at, entries => [entry, ...entries.filter(x => x.slug !== entry.slug)].slice(0, MAX_ENTRIES))
}

async function readProgress($: EngineInterface, armed: CrankRun, plan: CrankArtifact, at: CrankWhere, before: HudProgress | null): Promise<HudProgress | null> {
  const files = progressFiles(armed, plan, at)
  const mtimes = await Promise.all([files.plan, files.retro, ...files.ledgers].map(file => mtimeOf($, file)))
  const [planMtime, retroMtime, ...ledgerMtimes] = mtimes
  const stamp = mtimes.join(' ')

  if (before?.stamp === stamp) {
    return before
  }

  // crank-execute moves a V1 flat plan to .crank/<slug>/plan.md when it adopts it mid-run.
  if (planMtime === undefined) {
    return plan.isFlat ? readProgress($, armed, { path: `.crank/${plan.slug}/plan.md`, slug: plan.slug, isFlat: false }, at, before) : null
  }

  const ledgers = await Promise.all(
    files.ledgers.flatMap((file, i) => {
      const mtime = ledgerMtimes[i]

      return mtime === undefined ? [] : [$.fs.read(file).then(text => ({ text, mtime }))]
    }),
  )
  const found = { stamp, plan, planText: await $.fs.read(files.plan), planMtime, retroMtime, ledgers }

  return progressFrom(found, armed.armedAt)
}

async function armHud($: EngineInterface, armed: CrankRun, at: CrankWhere) {
  const plan = planOf(armed)

  if (plan === null) {
    await disarmHud($)
    return
  }

  const progress = await readProgress($, armed, plan, at, null)
  await update($, hudRun, () => ({ stoppedAtArm: progress?.stopped?.line }))
  await update($, hudProgress, () => progress)
  await update($, hudRoster, () => [])
  startTick($)
}

async function disarmHud($: StateDollar) {
  ticker?.cancel()
  ticker = undefined

  if ((await read($, hudRun)) !== null) {
    await update($, hudRun, () => null)
  }

  if ((await read($, hudRoster)).length > 0) {
    await update($, hudRoster, () => [])
  }
}

function startTick($: EngineInterface) {
  ticker?.cancel()
  ticker = $.clock.every(TICK_MS, () => void tick($))
}

async function readRows($: StateDollar): Promise<Row[]> {
  const ids = await read($, hudRoster)
  const rows = await Promise.all(ids.map(async id => ({ id, agent: await read($, { ...HUD_AGENT, id }), now: await read($, { ...HUD_NOW, id }) })))

  return rows.flatMap(({ id, agent, now }) => (agent === undefined ? [] : [{ id, agent, now }]))
}

// Claude Code lists an agent waiting on its own shell as completed, so only
// failed and killed end a row here.
async function tick($: EngineInterface) {
  const live = (await readRows($)).filter(row => !row.agent.isDone).map(row => row.id)

  if (live.length === 0) {
    return
  }

  const ended = (await $.agent.list()).filter(agent => live.includes(agent.id) && ENDED.has(agent.status))
  await Promise.all(ended.map(agent => patch($, agent.id, a => ({ ...a, isDone: true }))))
  await update($, hudTick, n => n + 1)
}

const isRostered = async ($: StateDollar, id: string) => (await read($, hudRoster)).includes(id)

async function patch($: StateDollar, id: string, change: (agent: HudAgent) => HudAgent) {
  const ref = { ...HUD_AGENT, id }
  const before = await read($, ref)

  if (before !== undefined) {
    await update($, ref, (agent = before) => change(agent))
  }
}

async function refresh($: EngineInterface) {
  const armed = await read($, run)
  const at = await read($, where)
  const plan = armed === null ? null : planOf(armed)

  if (armed === null || plan === null || at === null || (await read($, hudRun)) === null) {
    return
  }

  const before = await read($, hudProgress)
  const after = await readProgress($, armed, plan, at, before)

  if (after !== before) {
    await update($, hudProgress, () => after)
  }
}

async function settle($: StateDollar) {
  const hud = await read($, hudRun)
  const p = await read($, hudProgress)
  const ending = hud === null || p === null ? undefined : endingOf(hud, p)

  if (ending === 'done' || ending === 'bound') {
    await disarmHud($)
  } else if (ending !== undefined && p !== null) {
    await update($, hudRun, () => ({ stoppedAtArm: p.stopped?.line, quietAt: p.mtimeMs }))
  }
}

export const register: Register = (on, options) => {
  const isHud = options.hud === true
  const isResume = options.resume === true

  // A toggle change reloads the module and runs session.start alone, so a
  // hud turned off empties the roster agent-effort's band skips.
  on('session.start', async ($, e, next) => {
    const started = await next(e)

    if (!isHud) {
      await disarmHud($)
    } else if ((await read($, hudRun)) !== null) {
      startTick($)
    }

    return started
  })

  if (!isHud && !isResume) {
    return
  }

  on('classic.SessionStart', async ($, e, next) => {
    const started = await next(e)

    if (e.source === 'compact' || e.source === 'fork') {
      return started
    }

    await disarm($)

    if (isResume) {
      await forget($)
    }

    $.clock.after(OFFER_DELAY_MS, () => void place($, e.cwd, isResume))

    return started
  })

  // Arms before next(e), so the header draws before the model's first token.
  // A built-in command keeps the run armed; any other command disarms it, so
  // another skill's answer is never captured.
  on('command.run', async ($, e, next) => {
    if (!isPerson(e.origin)) {
      return next(e)
    }

    if (isFamily(e.command)) {
      const armed = await arm($, e)

      if (armed === null) {
        await disarm($)
      }

      if (armed !== null && isResume) {
        await take($, armed.armed, armed.at)
      }

      if (armed !== null && isHud) {
        await armHud($, armed.armed, armed.at)
      }

      return next(e)
    }

    const ran = await next(e)

    if (REOFFER.has(e.command)) {
      if (isResume && (await read($, offered)) !== null) {
        $.clock.after(OFFER_DELAY_MS, () => void offer($))
      }

      return ran
    }

    if (isResume) {
      await forget($)
    }

    if ((await read($, run)) !== null && !(await isBuiltin($, e.command))) {
      await disarm($)
    }

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)

    if (e.agentId === undefined && isResume) {
      await capture($, e)
    }

    if (e.agentId === undefined && isHud) {
      await refresh($)
    }

    return done
  })

  on('session.end', async ($, e, next) => {
    await disarm($)

    return next(e)
  })

  if (!isHud) {
    return
  }

  // A spawn inside a subagent carries its parentAgentId and gets no row.
  on('agent.spawn', async ($, e, next) => {
    const spawned = await next(e)
    const armed = await read($, run)

    if (e.parentAgentId !== undefined || spawned.agentId === undefined || armed === null || (await read($, hudRun)) === null) {
      return spawned
    }

    const id = spawned.agentId
    const agent: HudAgent = {
      ...classify(e.prompt, e.description, armed.command === LITE_EXECUTE),
      description: e.description,
      startedAt: await $.clock.now(),
      shells: [],
      isDone: false,
    }
    await $.state.set({ ...HUD_AGENT, id }, agent)
    await update($, hudRoster, ids => [...ids, id])

    return spawned
  })

  // A subagent's first request can start before agent.spawn resolves, so the
  // roster is read again once the step's response is in.
  on('turn.step', async function* ($, e, next) {
    const { agentId } = e

    if (agentId !== undefined && (await isRostered($, agentId))) {
      await patch($, agentId, agent => ({ ...agent, effort: e.effort === undefined ? agent.effort : String(e.effort), waiting: undefined, isDone: false }))
      await $.state.set({ ...HUD_NOW, id: agentId }, { what: 'thinking', since: await $.clock.now() })
    }

    const stepped = yield* next(e)
    const [use] = stepped.toolUses

    if (agentId !== undefined && use !== undefined && (await isRostered($, agentId))) {
      await $.state.set({ ...HUD_NOW, id: agentId }, { what: activityOf(use.name, use.input), since: await $.clock.now() })
    }

    return stepped
  })

  // Claude Code reports an agent finished while it waits on its own
  // background shell; only that shell, still running at the agent's stop,
  // tells a wait from an end.
  on('classic.SubagentStop', async ($, e, next) => {
    const stopped = await next(e)
    const id = e.agent_id

    if (await isRostered($, id)) {
      const running = new Set((e.background_tasks ?? []).filter(task => task.type === 'shell' && task.status === 'running').map(task => task.id))
      const at = await $.clock.now()
      await patch($, id, agent => {
        const shell = agent.shells.find(s => running.has(s.id))

        return shell === undefined ? { ...agent, waiting: undefined, isDone: true } : { ...agent, waiting: { word: shell.word, since: at } }
      })
    }

    return stopped
  })

  // Most progress writes go through Bash heredocs, not Edit or Write.
  on('tool.call', { tool: ['Bash', 'Edit', 'Write'] }, async ($, e, next) => {
    const ran = await next(e)
    const { agentId } = e
    const shellId = ran.deny === undefined && ran.isError !== true && 'backgroundTaskId' in ran.result ? ran.result.backgroundTaskId : undefined

    if (agentId === undefined) {
      await refresh($)
    } else if (e.tool === 'Bash' && shellId !== undefined && (await isRostered($, agentId))) {
      const shell = { id: shellId, word: commandWord(e.command) ?? 'shell' }
      await patch($, agentId, agent => ({ ...agent, shells: [...agent.shells, shell] }))
    }

    return ran
  })

  // A prompt typed over a running turn does not answer how the run ended.
  on('prompt.submit', async ($, e, next) => {
    if (isPerson(e.origin) && e.turnId === undefined) {
      await settle($)
    }

    return next(e)
  })

  // The band draws above next(e), so agent-effort's band and the engine's draw beneath it in either chain order.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    const armed = await read($, run)
    const hud = await read($, hudRun)
    const p = await read($, hudProgress)

    if (e.props.hasSurvey || armed === null || hud === null) {
      return below
    }

    // Reading hudTick subscribes the band, so its elapsed times redraw on each tick.
    await read($, hudTick)
    const rows = await readRows($)
    const columns = e.props.bodyColumns
    const header = p === null || isQuiet(hud, p) ? [] : [headerOf(armed, hud, p, workingOf(rows), columns)]
    const lines = [...header, ...rowsOf(rows, await $.clock.now(), columns)]

    if (lines.length === 0) {
      return below
    }

    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        {lines.map(cells => (
          <Text wrap="truncate">
            {cells.map(cell => (cell.tone === 'warning' ? <Text color="warning">{cell.text}</Text> : <Text dimColor={cell.tone === 'dim'}>{cell.text}</Text>))}
          </Text>
        ))}
        {below}
      </Box>
    )
  })
}
