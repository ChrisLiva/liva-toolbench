# Fix plan

`<repo>` @ `<short sha>` · crank-health · <quick|deep> profile · <date>

Grades: security <X> · types <X> · dead code <X> · complexity <X> · duplication <X> · lint <X> · format <X> · test quality <X>

| category | grade | basis | tools (version, config) |
| --- | --- | --- | --- |
| security | D | 3 high, 12 warning, 4 info (graded); 9 advisory | gitleaks 8.30.1 (default) · zizmor 1.30.0 (default) · osv-scanner 2.5.1 (default) |
| ... | | | |

Not assessed: <category> (<reason>), ...
Coverage: <assessed files> of <files in scope>; repo-wide unassessed by extension: <ext:n ...>

## Ground rules

- [advisory] rows did not count toward a grade; fix one only when the fix is obvious and behaviour-preserving. Suppressing a finding is not fixing it: if a rule is wrong for this repo, change the repo's config and say so.
- Change only what a task asks for, then run its Verify command before calling it done.
- Grade impact is the whole category: `security · F → A` is where security lands once every security task is done.

## Tasks

### T1 — <verb> <n> <things>  (project `<path>` when the repo has more than one)

Grade impact: <category> · <now> → <after every task in the category>

- `<file>:<line>` `<tool>/<rule>` — <message, one line, secret values never quoted>
- `<file>` (<n> findings): <rule> ×<k>, <rule> ×<k>
- ... at most 12 rows; above that list files with counts, and point at the raw output

Evidence: `<run-dir>/raw/<project>/<tool>.json`

Verify: `<the exact tool command that reports zero for this task>`

### T2 — ...

---

Tasks are themed (one rule across files is one task), ordered by the letters they move, most
first, then by category order. At most 20; the rest are in `<run-dir>/findings.md`.
Raw tool output: `<run-dir>/raw/`.
