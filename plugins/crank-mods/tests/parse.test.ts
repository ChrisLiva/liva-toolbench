import { expect, test } from 'claude-code/testing'

import { artifactOf, ledgerPlan, progressOf, sibling, stagesOf, taskHeadings } from '../hooks/parse'
import { findHandoff } from '../hooks/resume'
import type { CrankRun } from '../types'
import {
  BOUND_STAGE_GATE,
  HANDOFF_EXECUTE,
  HANDOFF_LITE_PLAN,
  HANDOFF_LITE_RESUME,
  HEALTH_LEDGER,
  REMOVAL_PLAN,
  STOPPED_PHASE_2,
  STOPPED_T25,
} from './fixtures/real'

const NAMES = new Set(['crank', 'crank-execute', 'crank-lite', 'lite-execute'])
const runOf = (command: string, args: string): CrankRun => ({ command, args, artifact: artifactOf(args), armedAt: 0 })

test('an artifact path parses in the per-slug layout and the V1 flat one, each with its sibling retro', () => {
  const perSlug = artifactOf('@.crank/csv-export/plan.md complete the next stage')
  const flat = artifactOf('/Users/chris/brew-pg/.crank/plan-class-filter.md')

  expect(perSlug).toEqual({ path: '.crank/csv-export/plan.md', slug: 'csv-export', isFlat: false })
  expect(flat).toEqual({ path: '.crank/plan-class-filter.md', slug: 'class-filter', isFlat: true })
  expect(perSlug && sibling(perSlug, 'retro')).toBe('.crank/csv-export/retro.md')
  expect(flat && sibling(flat, 'retro')).toBe('.crank/retro-class-filter.md')
  expect(artifactOf('.crank/<slug>/plan.md')).toBeNull()
  expect(artifactOf('.crank/csv-export/exec/task-4-brief.md')).toBeNull()
})

test('the counterexamples: a [~] box, an R1-T1 heading, a fenced heading, a T2–T6 stage cell, and text after the resume point', () => {
  const ledger = ['- [x] Task 1: done', '- [~] Task 2: partly', 'Stopped: the gate failed — resume at Task 8 from HEAD 7ffb8d6'].join('\n')
  const plan = ['### R1-T1: first', '```', '### Task 1 — fenced example', '```', '## Stages', '', '| Stage | Tasks |', '|---|---|', '| 1 | T2–T6 |'].join('\n')

  expect(progressOf(ledger, false)).toEqual({
    tasks: [
      { id: '1', isLanded: true },
      { id: '2', isLanded: false },
    ],
    bound: undefined,
    stopped: { line: 'Stopped: the gate failed — resume at Task 8 from HEAD 7ffb8d6', why: 'the gate failed', resumeAt: 8 },
  })
  expect(taskHeadings(plan)).toEqual(['R1-T1'])
  expect(stagesOf(plan)).toEqual([[2, 3, 4, 5, 6]])
})

test('a real ledger reads its boxes and the plan its Plan: header names', () => {
  const progress = progressOf(HEALTH_LEDGER, false)

  expect(progress.tasks.map(t => `${t.id}${t.isLanded ? 'x' : ''}`)).toEqual(['1x', '2x', '3x', '4'])
  expect(ledgerPlan(HEALTH_LEDGER)?.path).toBe('.crank/health-scan-fixes/plan.md')
})

test("a real plan's boxes count only inside its Progress block, and its Stages table spans its tasks", () => {
  expect(progressOf(REMOVAL_PLAN, true).tasks).toEqual([
    { id: '1', isLanded: true },
    { id: '2', isLanded: true },
    { id: '3', isLanded: false },
  ])
  expect(stagesOf(REMOVAL_PLAN)).toEqual([
    [1, 2, 3],
    [4, 5, 6, 7],
    [8, 9, 10, 11],
  ])
  expect(taskHeadings(REMOVAL_PLAN)).toEqual(['1', '2', '3'])
})

test('real Stopped: and Bound: lines give their resume points and bound task', () => {
  expect(progressOf(`${BOUND_STAGE_GATE}\n${STOPPED_T25}`, false)).toEqual({
    tasks: [],
    bound: { task: 4, text: 'Task 4, the stage 1 gate the user named' },
    stopped: { line: STOPPED_T25, why: 'T25 blocked on the Chrome extension disconnecting', resumeAt: 25 },
  })
  expect(progressOf(STOPPED_PHASE_2, false).stopped?.resumeAt).toBe(9)
})

test('real hand-offs give their next command, as the skill spelled it', () => {
  const execute = runOf('crank:crank-execute', '@.crank/voice-notes-pipeline/plan.md')
  const plan = runOf('crank-lite:crank-lite', 'plan Write a plan to fix all of the production bugs')
  const lite = runOf('crank-lite:lite-execute', '@.crank/miniature-removal-plan/plan.md complete the next stage')

  expect(findHandoff(HANDOFF_EXECUTE, NAMES, execute)).toMatchObject({ command: '/crank:crank-execute', args: '.crank/voice-notes-pipeline/plan.md' })
  expect(findHandoff(HANDOFF_LITE_PLAN, NAMES, plan)).toMatchObject({ command: '/lite-execute', args: '.crank/pipeline-bug-fixes/plan.md' })
  expect(findHandoff(HANDOFF_LITE_RESUME, NAMES, lite)).toMatchObject({ command: '/lite-execute', args: '.crank/miniature-removal-plan/plan.md' })
})

test('an answer naming two different crank commands with no label gives no hand-off', () => {
  const answer = 'Either `/crank plan .crank/a/spec.md` or `/crank-lite plan .crank/a/spec.md` works.'

  expect(findHandoff(answer, NAMES, runOf('crank:crank', 'spec .crank/a/brainstorm.md'))).toBeNull()
})
