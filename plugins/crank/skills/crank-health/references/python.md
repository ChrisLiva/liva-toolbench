# Python analyzers

`<files>` is the project's tracked `.py`/`.pyi` files, passed as a shell array. Ephemeral form is `uvx --quiet <dist> …` (`--quiet` stops uv narrating cold installs onto stderr; leave `UV_CACHE_DIR` unset, an empty value is an error); a repo-owned tool runs as `<venv>/bin/<tool>` when it is installed there (`.venv`, `venv`, `env`, then `$VIRTUAL_ENV`). Ownership = a `[tool.<name>]` table in `pyproject.toml`, a dedicated config file, or the package in PEP 621 / optional / dependency-group / poetry / pdm dependencies or `requirements*.txt`, ancestors included. Record the version each tool prints.

| category | default | notes |
| --- | --- | --- |
| lint | `ruff check` | `S` rules land in security |
| format | `ruff format --check` | |
| types | ty when the project has no virtualenv, pyright when it has one | mypy only when owned, never imposed |
| dead code | vulture | ≥ 90% confidence graded, 60 to 89% advisory |
| complexity | complexipy | |
| security | bandit (complementary to the repo-wide scanners) | |
| test quality (deep) | cosmic-ray, owned and installed only; coverage.py as context | |

## Commands

**ruff check** (lint). `--exit-zero` so exit code carries nothing.
```sh
ruff check --output-format json --no-cache --exit-zero <files>
# no repo config: add
--config <scratch>/ruff.toml     # containing: [lint]\nselect = ["E4", "E7", "E9", "F"]
```
On the default config `F`, `E9` and `invalid-syntax` grade; everything else advisory. Route `S\d+` rules to the security category.

**ruff format** (format). Exit 1 = would reformat, 2 = unparseable file with diagnostics still printed; only empty stdout is fatal. One finding per file; a row with `"code": "io"` is a missing file, not a format finding.
```sh
ruff format --check --no-cache --output-format json <files>
```

**ty** (types, default without a venv). gitlab is the only machine format carrying rule, severity and range.
```sh
ty check --output-format gitlab --exit-zero --no-progress --color never <files>
```
Advisory on the default config: `unresolved-import`, `missing-typeshed-stub`.

**pyright** (types, default with a venv). Ranges are 0-based on both axes.
```sh
pyright --outputjson --pythonpath <venv>/bin/python <files>
```
Advisory on the default config: `reportMissingImports`, `reportMissingModuleSource`, `reportMissingTypeStubs`, `reportAttributeAccessIssue`.

**mypy** (types, owned only). One invocation over all files (it builds one dependency graph). `--config-file=` with an empty value stops mypy discovering `setup.cfg` or `~/.mypy.ini`. Never pass `--txt-report`, `--html-report`, `--xml-report`, `--cobertura-xml-report`: they abort without lxml. Output is JSON lines; drop `note` rows. Not installed and no venv: not available.
```sh
mypy --output=json --cache-dir <scratch>/mypy-cache --config-file <owned config or empty> --python-executable <venv>/bin/python <files>
```

**vulture** (dead code). One invocation over all files (splitting invents dead code at the seams). Exit 0 or 3.
```sh
vulture --min-confidence 60 <files>
```

**complexipy** (complexity). cwd = `<scratch>/complexipy`, because `.complexipy_cache/` lands beside the cwd and cannot be disabled. Trailing `/` on `--output` is required. JSON gives the denominator (every function), SARIF gives the locations over the ceiling.
```sh
complexipy --quiet --max-complexity-allowed 15 --output <scratch>/complexipy/out/ --output-format json,sarif <absolute files>
```

**bandit** (security). cwd = scratch. Exit 0 or 1. `B105`, `B106`, `B107` quote the literal in their message: replace the quoted value with `<redacted>` before writing anything, and strip the `code` window from the saved JSON.
```sh
bandit --format json -q <absolute files>
```
On the default config a finding grades at HIGH severity or HIGH confidence; HIGH and HIGH is `error`, the rest medium-confidence heuristics are advisory. A repo that owns a bandit config grades every tier it selected.

**coverage.py** (deep, context only). Suite failure is not the verdict. Never graded; a line can be executed by a test that asserts nothing.
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
- `__pycache__` and `.pytest_cache`: `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` on anything that imports the code.
- The ruff default select is deliberately the old `E4,E7,E9,F` set, not ruff's modern default, so the grade reflects correctness rules only.
