# Property tests

What the `property tests` row says and what to do with its one finding. The row reads each
project's test files for a property-testing library and executes nothing, so it runs in the
quick profile. It is context for test quality and never a grade (per project decision:
property tests are context plus an offer, because the mutation score already rewards a suite
whose properties kill mutants, and a letter for owning a library would count it twice,
2026-11-19).

| language | counted as a property test | library the scan offers |
| --- | --- | --- |
| JS/TS | an import of `fast-check` or an `@fast-check/*` package | fast-check |
| Python | an import of `hypothesis` | Hypothesis |
| Go | an import of `pgregory.net/rapid`, gopter or `testing/quick`, or a `func Fuzz…(f *testing.F)` | rapid |
| C# | `using FsCheck`, `using CsCheck` or `using Hedgehog` | CsCheck |
| C/C++ | an include of `rapidcheck` | RapidCheck |

## Reading the row

The row's metric and the test-quality basis in `grades.md` read `hypothesis in 4 of 31 test
files`. The count is files that import the library, not properties, and only files the
inventory calls tests (`tests/`, `test_*.py`, `*_test.go`, `*.test.ts`, `*Tests.cs`,
`*_test.cpp`) are read: a suite kept elsewhere reads as zero, so check where the repo keeps
its tests before you believe a zero.

## The offer

A project whose test files use none gets one finding, `property-tests/none`, anchored on the
project's manifest, advisory and never graded. Its message names the library and the install
command. Use the repo's own package manager in place of the one printed (`pnpm add -D`,
`poetry add --group dev`), and skip the install when the manifest already declares the
library.

The finding becomes one plan task per project, placed after every graded task. The task
names the install command and up to three functions to write the first properties for. Its Grade
impact line reads `none (an offer)`. Pick
functions with a law a property can state: a parser beside its printer (round trip), an
encoder beside its decoder, a normalizer (running it twice changes nothing), a sort or merge
(the output keeps every input element), a function the complexity tool flagged that takes
plain values and returns one. Skip code whose inputs are a database, the network or the
clock. Its Verify command is `health.py rerun <run-dir> --tool "property tests"`, which
prints `0 advisory or dropped` once a test file imports the library.

Installing a test dependency is the user's call. The plan and your reply make the offer;
under `--fix`, ask before you install, and leave the task listed when the answer is no. Rule
`--dropped` with the reason when the project has nothing a property fits (a thin CLI wrapper,
generated bindings, a fixture).
