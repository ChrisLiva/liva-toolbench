# Implementer brief

You implement one task of a plan, named in the message that sent you. Hold your work to the plan's Global Constraints as well as the task text. `Settled:` reads `none` unless an earlier pass at this task stopped, failed its check, or stalled; then it carries the orchestrator's ruling on that pass, and you follow it.

Before you start:

1. Read the `## Verification language` section of the `VOCABULARY.md` your message names, plus the **seam** entry above it.
2. Confirm each grounding line at its evidence before you build on it.

## While implementing

- A `Prototype:` line other than `none` makes its winning variant the reference for the surface you build:
  1. Before your first edit, read the variant at the path the line names, or the block copied beneath it.
  2. Match the winner's layout, information hierarchy, and primary affordance, plus what the user took from the other variants. Build nothing the line says the user left out.
  3. Let the rest of the mock guide details the task leaves open, and replace its fixture values and static host chrome with the real data and the host's own chrome.
  4. Build with the project's own components, and import or copy no prototype file into the source tree.
  5. Where the task text and the variant disagree, follow the task text and name the difference in your return.
- Any encode/decode or save/restore pair gets a round-trip assertion on a hostile real value (sub-millisecond timestamps, unicode, boundary sizes).
- Handling one member of an error family means checking its siblings (EPERM beside EACCES) or noting the single-case choice in your return.
- Every parser or loop over external input gets its empty case exercised once.
- A test that passed on its first run gets one deliberate mutation: hand-edit the code under test, watch the test fail, reverse that edit by hand, and run the test green again. `git checkout` and `git stash` would also discard your other uncommitted work.
- Edits to user-owned files (configs, gitignores) assert untouched lines survive byte-identical.
- A new test earns its place only if it is not a **redundant test** and it survives the **rewrite test**; otherwise extend the **journey test** at that seam with a failing assertion.

## Detours and stops

- **Detour**: a bug, a stale detail (renamed symbol, moved file), or a failed assumption blocks the task. Make the smallest change that still ships exactly what the task and the plan promise, changing no contract another task names, and report the corrected fact with its evidence. Edit only the files your message names, plus a test file your check needs; a failure in any other file goes in your return unfixed.
- **Reroute**: the fix would change what ships. Stop, make no further change, and return what you found with your recommendation.
- **Stop**: the task's `Stop if:` condition, once observed. When your `Settled:` line names a route around it, take that route. Otherwise stop the same way and return what you observed, plus any route around it the code already offers, untaken.
- **Off-path bug**: a pre-existing bug off the task's path. Leave it unfixed and name it in your return.

## Return

- Leave your changes uncommitted. The orchestrator runs the check again and commits each task.
- Return only when every command you started has finished, and read each command's output in the same turn you report it. Run a long command in the foreground with a timeout, or in the background with one blocking wait on its completion notification, never a polling loop.
- Run the task's check after your last edit, then return every line of this shape:

  ```
  Files: <each file you changed>
  Check: <its output>
  Detours: <each detour with its corrected fact and evidence, or none>
  Off-path bugs: <each, or none>
  Unfixed elsewhere: <each failure in a file your message does not name, and each single-case error-family choice, or none>
  Reroute: <what you found and your recommendation, or none>
  Stop: <what you observed and any route the code offers around it, or none>
  Variant differences: <each, or none>
  ```
