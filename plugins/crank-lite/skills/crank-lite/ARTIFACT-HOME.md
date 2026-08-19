# Artifact home

Where every pipeline artifact lives, so a later session resumes from the file, not from a pasted path.

- **One directory per effort** — `.crank/<slug>/<artifact>.md` at the working root. Create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so the directory never enters version control.
- If `.crank/<slug>/` already holds a *different* effort (judge by content, not name), use `<slug>-2`, `<slug>-3`, … — never rename an existing directory.
- Only outside a git repo, fall back to `${TMPDIR:-/tmp}/crank-<slug>/<artifact>.md` and say so.
- Handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home first and state the new path.
- Tell the user the path once. Write nothing else into the working tree unless the user explicitly asks.
