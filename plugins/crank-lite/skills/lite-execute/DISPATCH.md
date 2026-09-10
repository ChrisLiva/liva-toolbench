# Dispatch

How an orchestrate run hands each plan task to a standard-tier implementer and waits for it. Every rule here reads its terms — the task's **check**, the **detour**, the Progress block — from [SKILL.md](SKILL.md).

Dispatch one subagent per task with a brief, targeted instruction carrying five things:

1. the task text;
2. the file paths it touches, plus the absolute path to this skill's `VOCABULARY.md`, plus the path the plan's `Grounding:` header names when it carries one;
3. the task's check, which it must run and report output from;
4. the detour rule, with any detour taken reported back in its return;
5. the return rule — return only when every command it started has finished; long verifications run synchronously, their output read in the same turn that reports them.

Done when the brief carries all five.

Parallel dispatches go out in one message and block as one. Confirm each returned task yourself with a typecheck or targeted test.
