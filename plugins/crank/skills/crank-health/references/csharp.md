# C# analyzers

Only `dotnet format whitespace` and the cross-language tools read C# without building it. Lint, types, complexity and dead code all need MSBuild, which runs the project's own build logic, so they are `--deep` only. In the quick profile those four categories read `not assessed (needs --deep: MSBuild executes project build logic)`.

Gate on `dotnet --version` run from the project directory (a `global.json` pins the SDK per directory). Below SDK 10 or missing: C# categories not assessed, hint https://dotnet.microsoft.com/download. A non-zero gate exit prints the installed-SDK list on stdout, so quote stderr only. Env for every command: `NUGET_PACKAGES=$HOME/.nuget/packages DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 DOTNET_CLI_UI_LANGUAGE=en`. Ephemeral tools run through `dnx -y <id> --source https://api.nuget.org/v3/index.json -v quiet -- <args>`; the `--` is load-bearing.

## Commands

**dotnet format whitespace** (format, quick). `--verify-no-changes` is the zero-footprint flag; `--folder` skips project load and restore. Exit 0 or 2; a missing `format-report.json` is an error. Exclude `bin`, `obj` and nested projects' directories.
```sh
dotnet format whitespace <project-dir> --folder --verify-no-changes --exclude bin obj <nested> --report <scratch>/dotnet-format
```
Always the repo's `.editorconfig`, so always repo provenance.

**dotnet build + NetAnalyzers** (types, lint, complexity; deep). One build per project feeds three categories. `%2C` in the ErrorLog property is mandatory: a literal comma silently emits SARIF 1.0.
```sh
dotnet build <project-dir> -p:ErrorLog=<scratch>/build.sarif%2Cversion=2.1 -p:BaseIntermediateOutputPath=<scratch>/obj/ -p:BaseOutputPath=<scratch>/bin/ -p:MSBuildProjectExtensionsPath=<scratch>/obj/ -p:CustomAfterMicrosoftCommonTargets=<scratch>/health.targets -p:RestoreSources=https://api.nuget.org/v3/index.json
```
`health.targets` adds `<PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="[<latest>]" />` (brackets pin exactly; a missing version becomes a loud NU1102), and a `BeforeTargets="CoreCompile"` target that appends a `.globalconfig` (`is_global = true`, `global_level = 0`, `dotnet_diagnostic.CA1502.severity = warning`, `dotnet_diagnostic.CA1823.severity = warning`) to `EditorConfigFiles` (the documented `GlobalAnalyzerConfigFiles` item never reaches the compiler from this hook) plus a `CodeMetricsConfig.txt` of `CA1502: 0` so every method is counted. Multi-target builds overwrite one ErrorLog: add `TreatAsLocalProperty="ErrorLog"` and rewrite to `<base>.<TargetFramework>.sarif`, then merge and dedupe by (rule, file, region, message). Route `CS…` to types with repo provenance, CA1502 to the complexity denominator and numerator (cyclomatic, not cognitive: say so), everything else to lint as default provenance. NU1102 = error, "refusing to grade on the SDK's bundled analyzers". Compile failure: types still grades, lint and complexity not available ("build failed"). Success with zero CA1502 records = "CA1502 suppressed by the repo's analyzer config", never an A.

**roslynator find-symbol --unused** (dead code; deep). cwd = scratch, one run per `.csproj`. Output is plain text with no locations: locate each symbol's declaration by searching the sources (sound: an unreferenced symbol's only occurrence is its declaration).
```sh
dnx -y roslynator.dotnet.cli --source https://api.nuget.org/v3/index.json -v quiet -- find-symbol <abs .csproj> --unused --properties BaseIntermediateOutputPath=<scratch>/obj/ BaseOutputPath=<scratch>/bin/ MSBuildProjectExtensionsPath=<scratch>/obj/
```

**Stryker.NET** (test quality; deep, owned only via `.config/dotnet-tools.json` or a `PackageReference`). cwd = project dir. Its initial build writes the project's normal `bin/` and `obj/`, which real repos gitignore. Mutants live in the project under test, so do not filter findings to this project's files. Zero mutants = error.
```sh
dotnet tool restore
dotnet stryker --output <scratch>/stryker-net --reporter json
# report: <scratch>/stryker-net/reports/mutation-report.json
```

## Gotchas

- `Directory.Packages.props` (central package management): osv-scanner skips those NuGet dependencies; say so in the security row.
- The complexity ceiling is shared with the cognitive-complexity languages, but CA1502 is cyclomatic, so a C# function just under 15 may read harder than its grade suggests.
