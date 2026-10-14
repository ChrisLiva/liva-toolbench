import { expect, test } from 'claude-code/testing'

import { activityOf, classify, commandWord } from '../hooks/roster'

const EXEC = '/work/liva-todo/.crank/csv-export/exec'

// Prompts shaped like crank-execute's and lite-execute's dispatches, each with the literal its rule keys on.
const SPAWNS = [
  { prompt: `Review the whole run. Your rubric is ${EXEC}/final-review-rubric.md.`, description: 'Final review', role: 'final reviewer' },
  { prompt: `Re-review Task 3. Your rubric is ${EXEC}/re-review-rubric.md.`, description: 'Re-review Task 3', role: 're-reviewer', task: '3' },
  { prompt: 'You are the adversarial reviewer for a lite-execute run.', description: 'Review the run', role: 'final reviewer' },
  { prompt: `Read ${EXEC}/task-3-fix-brief.md and follow it.`, description: 'Fix round 1', role: 'fixer', task: '3' },
  { prompt: `Review one task. Your rubric is ${EXEC}/review-rubric.md.`, description: 'Review Task 3', role: 'reviewer', task: '3' },
  { prompt: `Read ${EXEC}/task-4-brief.md and follow it.`, description: 'Implement Task 4', role: 'implementer', task: '4' },
  { prompt: 'Confirm what the plan cites.', description: 'Plan walk, stage 2', role: 'plan walk' },
  { prompt: 'Reply with the thin return.', description: 'Implement Task 7: quote fields', role: 'implementer', task: '7' },
  { prompt: 'Look up how the writer streams rows.', description: 'Explore the writer', role: 'other' },
] as const

test('each crank dispatch gets the role and task its prompt or description names', () => {
  for (const { prompt, description, role, ...rest } of SPAWNS) {
    expect(classify(prompt, description, false)).toEqual({ role, task: 'task' in rest ? rest.task : undefined })
  }
})

const LITE = '/p/plugins/crank-lite/skills'
const CRANK = '/p/plugins/crank/skills/crank'
const RUN = '/w/.crank/x'

// Prompts shaped like each fan-out dispatch, the lens or shard reviewers and their merger, with an empty description so the prompt decides.
const FAN_OUT_SPAWNS = [
  {
    prompt: `Read ${LITE}/lite-execute/REVIEW-BRIEF.md and follow it.\nPlan: ${RUN}/plan.md\nLens: Tests\nFindings: ${RUN}/review-tests.md`,
    isLite: true,
    role: 'final reviewer',
  },
  {
    prompt: `Read ${LITE}/lite-execute/MERGE-BRIEF.md and follow it.\nReview brief: ${LITE}/lite-execute/REVIEW-BRIEF.md`,
    isLite: true,
    role: 'final reviewer',
  },
  {
    prompt: `Review the whole run through the quality lens. Your rubric is ${EXEC}/final-review-rubric.md. Write ${EXEC}/final-review-quality.md.`,
    isLite: false,
    role: 'final reviewer',
  },
  {
    prompt: `Merge the lens reviews. Your rubric is ${EXEC}/final-merge-rubric.md, over ${EXEC}/final-review-rubric.md.`,
    isLite: false,
    role: 'final reviewer',
  },
  {
    prompt: `Read ${LITE}/crank-lite/PLAN-REVIEW-BRIEF.md and follow it.\nShard: X\nFindings: ${RUN}/plan-review-x.md`,
    isLite: false,
    role: 'other',
  },
  {
    prompt: `Read ${LITE}/crank-lite/PLAN-MERGE-BRIEF.md and follow it.\nReview brief: ${LITE}/crank-lite/PLAN-REVIEW-BRIEF.md`,
    isLite: false,
    role: 'other',
  },
  {
    prompt:
      `You are the merger for a crank adversarial review. Three reviewers read \`${RUN}/plan.md\` in parallel, each through one lens or shard of \`${CRANK}/PLAN-REVIEW-BRIEF.md\`, and none saw another's findings. ` +
      `You validate, fold, and land them. Read the brief, the artifact, the spec at \`${RUN}/spec.md\` when one exists, and the three findings files: ` +
      `\`${RUN}/plan-review-findings-a.md\`, \`${RUN}/plan-review-findings-b.md\`, \`${RUN}/plan-review-findings-x.md\`.\n\n` +
      `Write \`plan-review-edits.py\` beside the artifact.`,
    isLite: false,
    role: 'other',
  },
] as const

test('each fan-out dispatch gets the role its brief names', () => {
  for (const { prompt, isLite, role } of FAN_OUT_SPAWNS) {
    expect(classify(prompt, '', isLite).role).toBe(role)
  }
})

test("a prompt's literal outranks the description", () => {
  expect(classify(`Your rubric is ${EXEC}/review-rubric.md.`, 'Implement Task 4', false).role).toBe('reviewer')
  expect(classify('Build the PROTOTYPE.md screens.', 'Implement Task 2', false).role).toBe('other')
})

test('final-review-rubric.md does not read as the per-task rubric', () => {
  expect(classify(`Read ${EXEC}/final-review-rubric.md`, '', false).role).toBe('final reviewer')
})

test("an adversarial review's description names the final reviewer only in a lite-execute run", () => {
  expect(classify('Reply ok.', 'Adversarial review', true).role).toBe('final reviewer')
  expect(classify('Reply ok.', 'Adversarial review', false).role).toBe('other')
})

test('a command reads as the program it runs, past cd, export and assignments', () => {
  expect(commandWord('cd build && ctest -R csv --output-on-failure')).toBe('ctest')
  expect(commandWord('CMAKE_BUILD_PARALLEL_LEVEL=8 cmake --build build')).toBe('cmake')
  expect(commandWord('(cd app && ./scripts/run-tests.sh --slow)')).toBe('run-tests.sh')
  expect(commandWord('export CI=1; npm test')).toBe('npm')
  expect(commandWord('cd build')).toBeUndefined()
})

test('a tool call reads as its name with a file basename or a command word', () => {
  expect(activityOf('Edit', { file_path: '/work/liva-todo/src/csv/writer.cpp', old_string: 'secret', new_string: 'x' })).toBe('Edit writer.cpp')
  expect(activityOf('Bash', { command: 'git commit -m "secret"' })).toBe('Bash git')
  expect(activityOf('Grep', { pattern: 'secret' })).toBe('Grep')
})
