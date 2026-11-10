# Python analyzers

What the scan runs for a Python project and how to read each tool's rows. The commands themselves,
with their pinned versions and cwd, are in `<run-dir>/tools.md` → Commands.

Ownership = a `[tool.<name>]` table in `pyproject.toml`, a dedicated config file, or the package
in PEP 621 / optional / dependency-group / poetry / pdm dependencies or `requirements*.txt`,
ancestors included. A repo-owned tool runs as `<venv>/bin/<tool>` when it is installed there
(`.venv`, `venv`, `env`, then `$VIRTUAL_ENV`); everything else runs ephemerally through `uvx`.

| category | default | notes |
| --- | --- | --- |
| lint | `ruff check` | `S` rules land in security |
| format | `ruff format --check` | |
| types | ty when the project has no virtualenv, pyright when it has one | mypy only when owned, never imposed |
| dead code | vulture | ≥ 90% confidence graded, 60 to 89% advisory |
| complexity | complexipy | |
| security | bandit (complementary to the repo-wide scanners) | |
| test quality (deep) | cosmic-ray, owned and installed only; coverage.py as context | |

## Reading the rows

**ruff check** (lint). Without a repo config the scan selects `E4`, `E7`, `E9`, `F`: deliberately
the old set rather than ruff's modern default, so the grade reflects correctness rules only. On
that default `F`, `E9` and `invalid-syntax` grade and everything else is advisory. A repo config
grades every rule it selected, and its `S` rules route to security.

**ruff format** (format). One finding per file that would be reformatted.

**ty** (types, default without a virtualenv). Advisory on the default config: import-resolution
rules (`unresolved-import`, `import-not-found`) and `missing-typeshed-stub`, since nothing is
installed to resolve against. Untyped Python reads F here; that is the honest reading
([grading.md](grading.md)).

**pyright** (types, default with a virtualenv). It runs from the virtualenv, else from PATH, else ephemerally. Advisory on the default config:
`reportMissingImports`, `reportMissingModuleSource`, `reportMissingTypeStubs`,
`reportAttributeAccessIssue`. One library pattern can account for hundreds of rows (a pydantic
`Field` default read as the declared type): group by rule and message before you judge the
count.

**mypy** (types, owned only). Its `note` rows are dropped. With mypy owned, ty or pyright runs as
the standby. Not installed and no virtualenv: not available.

**vulture** (dead code). The `confidence` flag carries the number; below 90 is advisory. An
unused import ruff also reports (`F401`) is one dead-code finding: ruff's row reads
`advisory: duplicate of vulture/unused-import`.

**complexipy** (complexity). The metric is functions over 15 / every function it counted, and the
`score` flag carries each function's number.

**bandit** (security). On the default config a finding grades at HIGH severity or HIGH
confidence; the medium-confidence heuristics are advisory. A repo that owns a bandit config
grades every tier it selected. `B105`, `B106` and `B107` are secrets: critical at high
confidence, their quoted literal replaced with `<redacted>`. `B101` grades every `assert` in a
pytest suite, at info: rows flagged `test` are yours to drop in one ruling.

## Deep

**coverage.py** (deep, context only). Suite failure is not the verdict. Never graded; a line can be executed by a test that asserts nothing. When coverage is not installed in the virtualenv, `uv run --no-sync --with coverage python -m coverage …` supplies it without touching the lockfile.
```sh
COVERAGE_FILE=<scratch>/.coverage PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python -m coverage run -m pytest -q -p no:cacheprovider
COVERAGE_FILE=<scratch>/.coverage <venv>/bin/python -m coverage json -o <scratch>/coverage.json --quiet
```

**cosmic-ray** (deep, owned and installed only). It mutates files **in place** and restores them; a run killed midway leaves mutated source on disk, so only a repo that chose it gets it, and never with uncommitted changes in the tree. Write `<scratch>/cr.toml` with `module-path`, `timeout = 30.0`, `excluded-modules`, and `test-command = "<absolute venv python> -m pytest -x -q -p no:cacheprovider"` (a bare `python` makes every mutant incompetent). Run baseline first: a broken test command reads as "mutant killed" and scores 100%.
```sh
cosmic-ray baseline --session-file <scratch>/baseline.sqlite <scratch>/cr.toml
cosmic-ray init <scratch>/cr.toml <scratch>/session.sqlite
cosmic-ray exec <scratch>/cr.toml <scratch>/session.sqlite
cosmic-ray dump <scratch>/session.sqlite
```

## Gotchas

- `uv` missing from PATH: every Python category is not assessed, hint `brew install uv`.
- `__pycache__` and `.pytest_cache`: `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` on anything you run that imports the code.
- A suite with a slow marker can outlast the deep budget: read the repo's test configuration for the marker its own CI excludes before you run coverage.
