# C and C++ analyzers

One `c-cpp` language: every tool here reads C as readily as C++, a `.h` belongs to neither by name, and one cppcheck run over files that share headers needs one KLOC denominator. `<files>` is the project's tracked `.c .cpp .cc .cxx .c++` sources as a shell array; headers (`.h .hpp .hh .hxx .h++`) are reached through `-I`, never passed, or cppcheck analyzes each twice. cwd = the project directory. Ephemeral form is `uvx --quiet <dist> …`, so `uv` is the gate as it is for Python: missing, every C/C++ category is not assessed, hint `brew install uv`. Record the version each tool prints.

Ownership = a `.clang-format` or `_clang-format` (format), a `.clang-tidy` (deep lint), or a `mull.yml` (mutation) in the project or an ancestor. cppcheck and lizard are never owned: cppcheck discovers no config file on its own, so a suppressions list the repo passes in CI is not applied here, and both always run on the skill's flags at default provenance.

C++ has no build-free type check, so quick reads types `not assessed (needs --deep: a compile database comes from the repo's build configure)`. Deep configures the build into scratch and runs clang-tidy over the database, which feeds types, lint and complexity from one run the way one `dotnet build` feeds three C# categories.

| category | quick | deep |
| --- | --- | --- |
| security | cppcheck `error` and `warning` | same |
| lint | cppcheck `style`, `performance`, `portability` | clang-tidy; cppcheck stands down |
| dead code | cppcheck `unusedFunction` | same |
| complexity | lizard (cyclomatic, say so) | clang-tidy cognitive numerator over lizard's denominator |
| format | clang-format (owned only) | same |
| types | not assessed | clang-tidy `clang-diagnostic-error` rows |
| test quality | | Mull (owned only) |

## Commands

**cppcheck** (security, lint, dead code from one run; 300 s). XML, not SARIF: the SARIF export collapses `style`, `performance` and `portability` into `warning`, and the routing below needs all six severities. `-q` keeps stdout empty. `--cppcheck-build-dir` under scratch is what lets `unusedFunction` (whole-program) run under `-j`. `-I` takes every directory in the project's inventory that holds a header. Exit 0 with findings; 1 = could not run, and stderr's first line says why. Route by the `severity` attribute: `unusedFunction` to dead code first, then `error` and `warning` to security, `style`, `performance` and `portability` to lint. `information` rows are never graded: their count, minus `checkersReport`, is what cppcheck could not resolve (`missingInclude`, `toomanyconfigs`, `normalCheckLevelMaxBranches`), and it prints as `n unresolved` in the row's metric column and beside the security and lint letters in the plan. `missingIncludeSystem` is suppressed because system headers are never on cppcheck's path.
```sh
uvx --quiet --from cppcheck-py cppcheck -q --enable=all --xml --output-file=<raw>/cppcheck.xml --cppcheck-build-dir=<scratch>/cppcheck -j 4 --suppress=missingIncludeSystem -I <header dirs…> <files>
```
`unusedFunction` over-reports a library's public API, so the knip and fallow carve-out in [grading.md](grading.md) applies: an unused function a library exports for callers outside the repo is advisory.

**lizard** (complexity). CSV columns are `NLOC,CCN,token,PARAM,length,location,file,function,long_name,start,end`, one row per function whatever the threshold, so the row count is the denominator. Metric = rows with CCN over 15 / rows. CCN is cyclomatic, not cognitive: say so, as the C# footnote does. Exit 0; only empty stdout is failure.
```sh
uvx --quiet lizard --csv -l cpp <files> <header files>
```

**clang-format** (format, owned only). `--fallback-style=none` is load-bearing: the default fallback is LLVM, which grades an F on a repo that never adopted clang-format. `--ferror-limit=1` gives one `-Wclang-format-violations` diagnostic per failing file; metric = distinct files named / files passed. Exit 1 = some file would change, 0 = clean. `xcrun clang-format` on macOS (Xcode Command Line Tools), `uvx --quiet clang-format` elsewhere; the two print different versions, and a repo formatted with an older release lands in the advisory case in [grading.md](grading.md). No `.clang-format`: the row is `skipped: not owned (never imposed)` and format reads `not assessed (no .clang-format)`.
```sh
xcrun clang-format --style=file --fallback-style=none --dry-run -Werror --ferror-limit=1 <files> <header files>
```

**configure** (deep, 300 s). `--deep` already means "may execute the repo's build logic" for C#, and a CMake configure runs `CMakeLists.txt`, which can write into the source tree even with an external build dir; the footprint comparison catches strays. Configure into scratch, one per project; the database lands at `<scratch>/build/compile_commands.json`. A configure that fails: types reads `error` with stderr's first line, and lint and complexity keep the quick tools' grades, with the plan saying so (the standby rule in `assets/tools.md`). Another build system: a `compile_commands.json` in the project's inventory is used as-is; none, and types stays not assessed (Bazel and plain-Makefile projects get no deep upgrade).
```sh
cmake -S <project-dir> -B <scratch>/build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
meson setup <scratch>/build <project-dir>
```

**clang-tidy** (types, lint, complexity numerator; deep, 300 s). `-p` names the database's directory. On macOS the wheel's clang finds no system headers without the SDK: add `--extra-arg=-isysroot --extra-arg="$(xcrun --show-sdk-path)"`, or every `<cstdio>` include is a `clang-diagnostic-error`. `-ferror-limit=0` lifts clang's cap of 19 errors per file. Unowned, `--config` sets the check set; owned (`.clang-tidy`), `InheritParentConfig: true` keeps the repo's set and appends the complexity check. No JSON: a finding is one stdout line `<abs file>:<line>:<col>: <warning|error>: <message> [<check>]`; drop `note:` lines and the source echo under each, and dedupe on (file, line, column, check), because a header's diagnostic repeats once per translation unit that includes it. Exit 1 = at least one compile error, which is a types finding, not a failure; no finding line and an `Error:` on stderr is a failure. Route `clang-diagnostic-error` to types as error and other `clang-diagnostic-*` to types as info; `readability-function-cognitive-complexity` to the complexity numerator over lizard's function count; `clang-analyzer-security.*` to security, advisory as a duplicate when cppcheck named the place; the rest to lint. On the skill's set `bugprone-*` and `clang-analyzer-*` grade and `performance-*` is advisory; a repo's `.clang-tidy` grades everything it selected. A file carrying an error row still yields its warnings; name those files in Notes.
```sh
uvx --quiet clang-tidy -p <scratch>/build --quiet --extra-arg=-ferror-limit=0 --config='{Checks: "-*,bugprone-*,clang-analyzer-*,performance-*,readability-function-cognitive-complexity", CheckOptions: {readability-function-cognitive-complexity.Threshold: 15}}' <files>
# owned .clang-tidy: replace --config with
--config='{InheritParentConfig: true, Checks: "readability-function-cognitive-complexity", CheckOptions: {readability-function-cognitive-complexity.Threshold: 15}}'
```

**Mull** (test quality; deep, owned only via `mull.yml`, 15 min). The repo's own build compiles its test binary with Mull's pass plugin (`-fpass-plugin=<mull-ir-frontend>`), so build the test target from the deep configure, `cmake --build <scratch>/build --target <tests>`, then run the runner from `mull.yml`'s directory (it searches upward from cwd). The runner is versioned per LLVM major (`mull-runner-18`); missing from PATH: not available, hint https://mull.readthedocs.io. Zero mutants = error. Score = the `Mutation score: N%` line, killed / total.
```sh
mull-runner-<llvm major> --reporters Sarif --report-dir <scratch>/mull --report-name mull <test-binary>
```

## Gotchas

- Timeouts: 300 s for cppcheck, the configure and clang-tidy; cppcheck tries up to 12 preprocessor configurations per file (`--max-configs`), and a large tree spends its budget there.
- Dependencies: osv-scanner reads `conan.lock` and git submodule commits only. A `vcpkg.json`, a `conanfile` without a lock, or CMake `FetchContent` is invisible to it; say so in the security row.
- opengrep ships no C or C++ ruleset, so the "no local ruleset, skip" rule in [common.md](common.md) is the whole story unless the repo carries its own rules.
- A `.h` under a Python package (a C extension) or a Go module (cgo) joins that project by the longest-prefix rule in [inventory.md](inventory.md) and is scanned as its `c-cpp` language.
