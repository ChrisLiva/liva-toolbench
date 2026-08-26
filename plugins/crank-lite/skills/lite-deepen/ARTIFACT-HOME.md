# Artifact home

Where every pipeline artifact lives, so a later session resumes from the file, not from a pasted path.

- **One directory per effort** — `.crank/<slug>/<artifact>.md` at the repository root (`git rev-parse --show-toplevel`), not the current directory. Create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so the directory never enters version control.
- **One slug per effort** — `<slug>` is two to four kebab-case words naming the effort (`dark-mode-toggle`), derived once when its first artifact is written. Handed an artifact from an earlier phase, or continuing in this session, write into that artifact's existing directory rather than deriving a new slug.
- If `.crank/<slug>/` already holds a *different* effort — its `plan.md`, `spec.md`, or `brainstorm.md` describes work other than the effort at hand — use `<slug>-2`, `<slug>-3`, …; the existing directory keeps its name and contents.
- Only outside a git repo, fall back to `${TMPDIR:-/tmp}/crank-<slug>/<artifact>.md` and say so.
- **Adopt a legacy flat artifact on encounter.** Resolving a handed-in artifact checks the per-plan path first, then the legacy flat path (`.crank/<phase>-<slug>.md`); on a hit there, move it to its per-plan home before using it and state the new path. When both the legacy and per-plan copies exist, stop and ask which survives; overwrite neither.
- Tell the user the path once. Artifacts, and any throwaway a phase produces (a prototype HTML file, a sample output), go under `.crank/<slug>/` and nowhere else.
