import type { HudAgent, HudRole } from '../types'

// The first rule that matches wins: every prompt rule before any description
// rule, so a brief's literal decides. These rules classified 1630 of 1654
// crank spawns in transcripts up to 2026-10-01.
const PROMPT_HEAD = 1500
const B = '(?:^|[/`\\s])'
const PROMPT_RULES: [HudRole, RegExp][] = [
  ['final reviewer', new RegExp(`${B}final-review-rubric\\.md|fresh-eyes reviewer|final (?:cross-task |whole-diff )?review(?:er)?\\b`, 'i')],
  ['re-reviewer', new RegExp(`${B}re-review-rubric\\.md|\\bthe re-reviewer\\b|\\bre-review(?:er)? for\\b`, 'i')],
  ['final reviewer', /adversarial reviewer for a lite-execute run|lite-execute\/REVIEW-BRIEF\.md/i],
  ['fixer', /\bfix(?:er)? (?:round|brief)\b|task-\d+-fix|\bthe fixer\b|task-\d+-findings\.md/i],
  ['reviewer', new RegExp(`${B}review-rubric\\.md|per-task reviewer|code reviewer for one task|reviewer for Task \\d`, 'i')],
  [
    'implementer',
    /task-\d+-brief\.md|\bthe implementer for\b|IMPLEMENTER-BRIEF\.md|implement(?:ing|er)?(?: for)? one (?:task|slice)|You are implementing (?:Task|one)|^Implement Task \d/i,
  ],
  ['escalation', /heavy-tier escalation|\binvestigator\b|Read-only investigation/i],
  ['plan walk', /\bplan walk\b|walking an implementation plan|plan-walk(?:-\d+)?\.md/i],
  ['orientation', /orientation (?:file|\.md)|Fill in the orientation|orientation\.md\b.*template/i],
  // The planning phases' agents, which an executor run has no row name for.
  [
    'other',
    /spec-review-edits\.py|SPEC-REVIEW-BRIEF\.md|spec-review-findings\.md|plan-review-edits\.py|PLAN-REVIEW-BRIEF\.md|plan-review-findings\.md|adversarial reviewer for a crank-lite plan|PROTOTYPE\.md|\bprototype\b|(?:SLOP|STRUCTURE|PROSE)-BRIEF\.md/i,
  ],
]
const DESCRIPTION_RULES: [HudRole, RegExp][] = [
  ['final reviewer', /\bfinal\b.*review|whole[- ]diff|cross-task/i],
  ['re-reviewer', /re-review/i],
  ['fixer', /fix round|^fix\b/i],
  ['reviewer', /^(?:cold )?review (?:of )?(?:plan )?task|^cold review of task/i],
  ['implementer', /^implement|^task \d+\w?:|^finish (?:plan )?task|^T\d+\w? /i],
  ['plan walk', /plan walk|walk plan/i],
  ['orientation', /orientation/i],
]
const LITE_REVIEW = /adversarial review/i
const BRIEF_TASK = /task-(\d+)-(?:fix-)?brief\.md/
const DESCRIPTION_TASK = /\bTask (\d+)/
const SKIPPED_WORDS = new Set(['cd', 'pushd', 'export', 'source', 'env', 'time'])

/** A spawn's role and task; `isLite` admits the description rule only lite-execute's reviewer matches. */
export function classify(prompt: string, description: string, isLite: boolean): Pick<HudAgent, 'role' | 'task'> {
  const head = prompt.slice(0, PROMPT_HEAD)
  const role =
    PROMPT_RULES.find(([, rule]) => rule.test(head))?.[0] ??
    DESCRIPTION_RULES.find(([, rule]) => rule.test(description))?.[0] ??
    (isLite && LITE_REVIEW.test(description) ? 'final reviewer' : 'other')

  return { role, task: BRIEF_TASK.exec(prompt)?.[1] ?? DESCRIPTION_TASK.exec(description)?.[1] }
}

/** The program a shell command runs, past `cd`, `export` and variable assignments; its arguments never leave here. */
export function commandWord(command: string) {
  for (const part of command.split(/&&|\|\||[;|\n()]/)) {
    const word = part
      .trim()
      .split(/\s+/)
      .find(w => !/^\w+=/.test(w))

    if (word !== undefined && word !== '' && !SKIPPED_WORDS.has(word)) {
      return word.split('/').pop()
    }
  }

  return undefined
}

/** A tool call as the tool's name, plus the file's basename or the command's first word. */
export function activityOf(name: string, input: unknown) {
  const { command, file_path: path } = (input ?? {}) as { command?: unknown; file_path?: unknown }
  const detail = name === 'Bash' && typeof command === 'string' ? commandWord(command) : typeof path === 'string' ? path.split('/').pop() : undefined

  return detail === undefined ? name : `${name} ${detail}`
}
