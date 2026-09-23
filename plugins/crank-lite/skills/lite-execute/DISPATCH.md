# Dispatch

How a sequential or parallel run hands each plan task to a standard-tier implementer and waits for it. Every rule here reads its terms — the task's **check**, the **detour**, the Progress block — from [SKILL.md](SKILL.md).

Dispatch one subagent per task with a brief, targeted instruction carrying five things:

1. the task text;
2. the file paths it touches, plus the absolute path to this skill's `VOCABULARY.md`, plus the path the plan's `Grounding:` header names when it carries one;
3. the task's check, which it must run and report output from;
4. the detour rule, with any detour taken reported back in its return, and the task's `Stop if:` line where the plan wrote one: an observed condition ends the task with a return naming what was observed, never a workaround;
5. the return rule — return only when every command it started has finished; a long verification runs in the foreground with a timeout, or starts in the background and waits on its completion notification, one blocking wait per command, never a polling loop, its output read in the same turn that reports it.

Done when the brief carries all five.

Sequential dispatches go out one at a time: the next task's dispatch follows the previous task's passing check and landed commit, and its brief names the commits already landed. Parallel dispatches go out in one message and block as one. Confirm each returned task yourself with a typecheck or targeted test.
