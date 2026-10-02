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
