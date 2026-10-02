/** A crank artifact named by its path from the worktree root: `.crank/<slug>/<name>.md`, or V1 flat `.crank/<name>-<slug>.md`. */
export type CrankArtifact = { path: string; slug: string; isFlat: boolean }

/** The worktree a conversation works in, from one `git rev-parse`. */
export type CrankWhere = {
  /** The worktree's root, which keys crank-resume's store. */
  root: string
  /** `git rev-parse --git-path crank`, absolute: where crank-execute keeps this worktree's ledgers. */
  ledgerDir: string
}

/** The crank or crank-lite command that armed a conversation. */
export type CrankRun = {
  /** Namespaced, as `command.run` names it even for a bare typed name (`crank-lite:lite-execute`). */
  command: string
  args: string
  /** The first crank artifact the args name; null when they name none. */
  artifact: CrankArtifact | null
  armedAt: number
}

export type HudTask = { id: string; isLanded: boolean }

/** An executor run's progress, as the hud last read it. */
export type HudProgress = {
  /** A crank-execute ledger, a lite-execute plan's `## Progress` block, or the plan's task headings, which give the total alone. */
  source: 'ledger' | 'progress-block' | 'plan-headings'
  /** The mtimes of every file the read depended on; an equal stamp skips the next read. */
  stamp: string
  /** The mtime of the file the tasks came from. */
  mtimeMs: number
  tasks: HudTask[]
  /** Each stage's task numbers, from the plan's Stages or Phases table. */
  stages: number[][]
  /** The `Bound:` line, kept only once the file changed after arming, so a previous run's line never counts. */
  bound?: { task: number; text: string }
  stopped?: { line: string; why: string; resumeAt?: number }
  /** True once the effort's retro was written after arming. */
  hasRetro: boolean
}

/** The hud's hold on the armed executor run. */
export type HudRun = {
  /** The `Stopped:` line the progress source held at arming, or when the person last answered a stop; only another one ends the run. */
  stoppedAtArm?: string
  /** The progress mtime when the person answered a stop; the header hides until the file changes. */
  quietAt?: number
}

/** What a crank agent does, from its spawn prompt's literals, else its description; `other` rows show the description. */
export type HudRole = 'implementer' | 'fixer' | 'reviewer' | 're-reviewer' | 'final reviewer' | 'plan walk' | 'orientation' | 'escalation' | 'other'

/** An agent the main loop spawned during the armed run, as its events last showed it. */
export type HudAgent = {
  role: HudRole
  description: string
  /** The task number its brief's file name or its description names. */
  task?: string
  /** The effort its last request carried; absent for a model without effort. */
  effort?: string
  startedAt: number
  /** Its own background Bash calls: each backgroundTaskId, with the command's first word. */
  shells: { id: string; word: string }[]
  /** Set at a stop while one of its own shells still runs, which Claude Code reports as finished; cleared at its next request. */
  waiting?: { word: string; since: number }
  /** True once it stopped with none of its own shells running, failed, or was killed. */
  isDone: boolean
}

/** An agent's current activity: the tool its last response called, or `thinking` while a request runs. */
export type HudNow = { what: string; since: number }

declare module 'claude-code' {
  interface PluginState {
    'crank-mods': {
      /** The worktree this conversation works in, resolved at each classic.SessionStart and each arming; null outside a git worktree or headless. */
      where: CrankWhere | null
      /** The crank or crank-lite command that armed this conversation; null after /clear, the session's end, or a command that is not built in. */
      run: CrankRun | null
      /** When the box last showed crank-resume's suggestion; null after the next main-loop turn or another command. */
      offered: number | null
      /** The hud's hold on an armed crank-execute or lite-execute run; null while the hud draws nothing. */
      hudRun: HudRun | null
      hudProgress: HudProgress | null
      /** The agents the hud draws a row for, by agentId; agent-effort reads it and skips them. */
      hudRoster: string[]
      hudAgent: StateFamily<HudAgent>
      hudNow: StateFamily<HudNow>
      /** Bumped every 30 s while an agent row shows, so the band redraws its elapsed times. */
      hudTick: number
    }
  }
}
