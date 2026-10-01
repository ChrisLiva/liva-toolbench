# Dispatch

Send each task to one standard-tier implementer, the standard model the Pre-flight lines name, with this message and every slot filled:

```
Read <absolute path to this skill's IMPLEMENTER-BRIEF.md> and follow it.
Task: <the task's full text from the plan, including its Stop if: line when it has one>
Files: <the paths the task touches, including the test file its check runs>
Check: <the task's check, per SKILL.md>
Global Constraints: <the plan's Global Constraints section, pasted, or none>
Grounding: <the plan's grounding lines that cover these files, pasted, or the file its Grounding: header names, or none>
Landed: <the commits this run has landed so far, or none>
Vocabulary: <absolute path to this skill's VOCABULARY.md>
```

Done when no `<…>` slot remains.

A sequential run sends the next task's dispatch only after the previous task's check passed and its commit landed. A parallel run sends every dispatch in one message, then ends its turn until every one has returned.
