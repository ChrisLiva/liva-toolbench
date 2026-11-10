"""Behaviour of crank-health's scanner, checked without the network or any analyzer.

    python3 -m unittest discover plugins/crank/skills/crank-health/scripts/tests
"""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from healthlib import cli, common, cpp, go, grade, jsts, python, report, settle  # noqa: E402
from healthlib import inventory as inv  # noqa: E402
from healthlib.runner import CATEGORIES, Failed, Finding, Metric, Row, Run, execute, sarif_results  # noqa: E402


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        check=True,
        capture_output=True,
    )


class Repo:
    """A throwaway git repo built from a {path: text} map."""

    def __init__(self, files: dict[str, str], commit: bool = True):
        self._holder = tempfile.TemporaryDirectory()
        self.path = Path(self._holder.name).resolve() / "repo"
        self.path.mkdir()
        git(self.path, "init", "-q")
        self.write(files)
        if commit:
            self.commit("init")

    def write(self, files: dict[str, str]) -> None:
        for rel, text in files.items():
            target = self.path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

    def commit(self, message: str) -> None:
        git(self.path, "add", "-A")
        git(self.path, "commit", "-qm", message)

    def cleanup(self) -> None:
        self._holder.cleanup()


class RepoCase(unittest.TestCase):
    def repo(self, files: dict[str, str], **kw) -> Repo:
        repo = Repo(files, **kw)
        self.addCleanup(repo.cleanup)
        return repo

    def run_for(self, repo: Repo, **kw) -> Run:
        inventory = inv.build(repo.path, kw.pop("projects", []))
        for project in inventory.projects:
            for language in project.files:
                project.owned.update(cli.MODULES[language].owned(repo.path, project))
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        run = Run(inventory, Path(holder.name), **kw)
        self.addCleanup(run.cleanup)
        return run


class InventoryTest(RepoCase):
    def test_scope_drops_vendored_and_hidden_directories_and_keeps_workflows(self):
        repo = self.repo(
            {
                "src/a.py": "x = 1\n",
                "vendor/lib.py": "x = 1\n",
                "build/out.py": "x = 1\n",
                ".hidden/b.py": "x = 1\n",
                ".eslintrc.json": "{}\n",
                ".github/workflows/ci.yml": "on: push\n",
                ".gitea/workflows/ci.yml": "on: push\n",
                ".gitignore": "ignored/\n",
                "ignored/c.py": "x = 1\n",
            }
        )
        inventory = inv.build(repo.path, [])
        self.assertEqual(
            inventory.files,
            [".eslintrc.json", ".gitea/workflows/ci.yml", ".github/workflows/ci.yml", ".gitignore", "src/a.py"],
        )
        self.assertEqual(inventory.workflows, [".gitea/workflows/ci.yml", ".github/workflows/ci.yml"])

    def test_untracked_unignored_files_are_in_scope(self):
        repo = self.repo({"a.py": "x = 1\n"})
        repo.write({"new.py": "y = 2\n"})
        self.assertIn("new.py", inv.build(repo.path, []).files)

    def test_files_join_the_project_with_the_longest_prefix(self):
        repo = self.repo(
            {
                "package.json": "{}",
                "tool.js": "a\nb\n",
                "apps/web/package.json": "{}",
                "apps/web/src/x.ts": "1\n2\n3\n",
                "apps/web/src/x.css": "a{}\n",
                "apps/api/go.mod": "module x\n",
                "apps/api/main.go": "package main\n",
            }
        )
        projects = {p.dir: p for p in inv.build(repo.path, []).projects}
        self.assertEqual(sorted(projects), [".", "apps/api", "apps/web"])
        self.assertEqual(projects["apps/web"].lines, {"js-ts": 3})
        self.assertEqual(projects["apps/web"].asset_lines, {"css": 1})
        self.assertEqual(projects["."].files, {"js-ts": ["tool.js"]})
        self.assertEqual(projects["apps/api"].lines, {"go": 1})

    def test_a_manifest_directory_without_source_is_a_workspace_shell(self):
        repo = self.repo({"package.json": "{}", "packages/a/package.json": "{}", "packages/a/i.ts": "1\n"})
        projects = {p.dir: p for p in inv.build(repo.path, []).projects}
        self.assertTrue(projects["."].shell)
        self.assertFalse(projects["packages/a"].shell)

    def test_cmake_lists_without_a_project_call_belong_to_the_enclosing_project(self):
        repo = self.repo(
            {
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.20)\nproject(top)\n",
                "src/CMakeLists.txt": "add_library(x x.cpp)\n",
                "src/x.cpp": "int x;\n",
                "lib/CMakeLists.txt": "  PROJECT (inner)\n",
                "lib/y.c": "int y;\n",
            }
        )
        self.assertEqual([p.dir for p in inv.build(repo.path, []).projects], [".", "lib"])

    def test_a_bare_makefile_is_a_project_only_beside_c_sources(self):
        repo = self.repo({"Makefile": "all:\n", "docs/Makefile": "all:\n", "native/Makefile": "all:\n", "native/n.c": "int n;\n", "a.py": "\n"})
        self.assertEqual([p.dir for p in inv.build(repo.path, []).projects], [".", "native"])

    def test_project_selection_narrows_projects_and_the_repo_wide_directories(self):
        repo = self.repo({"a/package.json": "{}", "a/i.ts": "1\n", "b/package.json": "{}", "b/i.ts": "1\n"})
        inventory = inv.build(repo.path, ["a/"])
        self.assertEqual([p.dir for p in inventory.projects], ["a"])
        self.assertEqual(inventory.scan_dirs(), ["a"])
        self.assertTrue(inventory.in_selection("a/i.ts"))
        self.assertFalse(inventory.in_selection("b/i.ts"))

    def test_a_language_living_only_under_fixtures_is_called_out(self):
        repo = self.repo({"package.json": "{}", "src/i.ts": "1\n", "tests/fixtures/code/sample.py": "x = 1\n"})
        project = inv.build(repo.path, []).projects[0]
        self.assertEqual(project.fixture_only, {"python": "tests/fixtures"})

    def test_snapshots_generated_files_and_lockfiles_are_listed(self):
        repo = self.repo(
            {
                "go.mod": "module x\n",
                "gen/api.pb.go": "package gen\n",
                "main.go": "// Code generated by protoc-gen-go. DO NOT EDIT.\npackage main\n",
                "hand.go": "package main\n",
                "testdata/golden/out.go": "package x\n",
                "go.sum": "",
            }
        )
        inventory = inv.build(repo.path, [])
        self.assertEqual(inventory.generated, ["gen/api.pb.go", "main.go"])
        self.assertEqual(inventory.snapshots, ["testdata/"])
        self.assertEqual(inventory.lockfiles, ["go.sum"])

    def test_footprint_names_a_file_left_beside_the_code(self):
        repo = self.repo({"a.py": "x = 1\n"})
        before = inv.footprint(repo.path)
        repo.write({"stray.cache": "x"})
        left = [line for line in inv.footprint(repo.path).splitlines() if line not in before.splitlines()]
        self.assertEqual(left, ["?? stray.cache"])


class OwnershipTest(RepoCase):
    def owned(self, files: dict[str, str], project_dir: str = ".") -> dict[str, str]:
        repo = self.repo(files)
        inventory = inv.build(repo.path, [])
        project = inventory.project(project_dir)
        found = {}
        for language in project.files:
            found.update(cli.MODULES[language].owned(repo.path, project))
        return found

    def test_a_scripts_entry_never_decides_ownership(self):
        owned = self.owned({"package.json": json.dumps({"scripts": {"lint": "eslint .", "fmt": "prettier -w ."}}), "i.js": "1\n"})
        self.assertNotIn("eslint", owned)
        self.assertNotIn("prettier", owned)

    def test_any_dependency_block_owns(self):
        manifest = {"devDependencies": {"eslint": "^9"}, "peerDependencies": {"prettier": "3"}, "optionalDependencies": {"knip": "5"}}
        owned = self.owned({"package.json": json.dumps(manifest), "i.js": "1\n"})
        self.assertEqual(owned["eslint"], "package.json devDependencies")
        self.assertEqual(owned["prettier"], "package.json peerDependencies")
        self.assertIn("knip", owned)

    def test_an_ancestor_config_owns_but_a_tsconfig_is_project_local(self):
        owned = self.owned(
            {
                "biome.json": "{}",
                "tsconfig.json": "{}",
                "package.json": "{}",
                "root.ts": "1\n",
                "pkg/package.json": json.dumps({"prettier": {"semi": False}}),
                "pkg/i.ts": "1\n",
            },
            "pkg",
        )
        self.assertEqual(owned["biome"], "biome.json")
        self.assertEqual(owned["prettier"], 'pkg/package.json "prettier"')
        self.assertNotIn("tsc", owned)

    def test_python_ownership_reads_every_place_a_dependency_is_declared(self):
        pyproject = """
[project]
dependencies = ["requests>=2"]
[project.optional-dependencies]
dev = ["mypy==1.10"]
[dependency-groups]
lint = ["ruff>=0.5", "Vulture"]
[tool.poetry.group.test.dependencies]
bandit = "^1.7"
[tool.pyright]
venv = ".venv"
"""
        owned = self.owned({"pyproject.toml": pyproject, "requirements-dev.txt": "# tools\ncomplexipy==1.0\n-r other.txt\n", "a.py": "x = 1\n"})
        self.assertEqual(owned["mypy"], "pyproject.toml project.optional-dependencies.dev")
        self.assertEqual(owned["ruff"], "pyproject.toml dependency-groups.lint")
        self.assertEqual(owned["vulture"], "pyproject.toml dependency-groups.lint")
        self.assertEqual(owned["bandit"], "pyproject.toml tool.poetry.group.test")
        self.assertEqual(owned["pyright"], "pyproject.toml [tool.pyright]")
        self.assertEqual(owned["complexipy"], "requirements-dev.txt")
        self.assertNotIn("ty", owned)

    def test_go_and_cpp_ownership_is_a_config_file(self):
        self.assertEqual(self.owned({"go.mod": "module x\n", "a.go": "package a\n", ".golangci.yml": ""}), {"golangci-lint": ".golangci.yml"})
        self.assertEqual(self.owned({"CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n", ".clang-format": ""}), {"clang-format": ".clang-format"})

    def test_jsonc_configs_parse_with_comments_and_trailing_commas(self):
        repo = self.repo({"biome.jsonc": '{\n  // note\n  "$schema": "https://x/y.json", /* c */\n  "files": {"includes": ["**", "!gen",],},\n}\n'})
        self.assertEqual(inv.read_jsonc(str(repo.path / "biome.jsonc"))["files"]["includes"], ["**", "!gen"])


class PlanTest(RepoCase):
    def rows(self, files: dict[str, str], *, present: set[str] | None = None, **kw) -> dict[str, Row]:
        run = self.run_for(self.repo(files), **kw)
        if present is None:
            run.which = lambda name: f"/usr/bin/{name}"  # every toolchain present, none executed
        else:
            run.which = lambda name: f"/usr/bin/{name}" if name in present else None
        run.version = lambda *a, **k: "99.0.0"
        return {f"{r.project}:{r.tool}": r for r in cli.plan_rows(run)}

    def test_a_missing_toolchain_names_its_install_hint(self):
        rows = self.rows({"package.json": "{}", "i.ts": "1\n", "pyproject.toml": "", "a.py": "x = 1\n", "go.mod": "module x\n", "a.go": "package a\n", "CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n", ".clang-format": "", "p/p.csproj": "<Project/>", "p/a.cs": "class A {}\n"}, present=set())
        expected = {
            "repo:gitleaks": "gitleaks not on PATH: brew install gitleaks",
            "repo:osv-scanner": "osv-scanner not on PATH: brew install osv-scanner",
            "repo:opengrep": "opengrep not on PATH: brew install opengrep",
            ".:go vet": "go not on PATH: https://go.dev/dl (1.25+)",
            "p:dotnet format whitespace": "dotnet not on PATH: https://dotnet.microsoft.com/download (SDK 10+)",
            ".:oxlint": "node not on PATH: brew install node",
            ".:ruff check": "uv not on PATH: brew install uv",
            ".:clang-format": "uv not on PATH: brew install uv",
        }
        for key, detail in expected.items():
            self.assertEqual(rows[key].detail, detail, key)

    def test_never_imposed_tools_are_skipped_and_defaults_run(self):
        rows = self.rows({"package.json": "{}", "i.ts": "1\n"})
        for tool in ("eslint", "biome lint", "biome format", "oxfmt", "fallow dead-code", "stryker"):
            self.assertEqual(rows[f".:{tool}"].detail, "not owned (never imposed)", tool)
        for tool in ("oxlint", "prettier", "knip", "fallow health", "tsc"):
            self.assertIsNotNone(rows[f".:{tool}"].job, tool)
            self.assertEqual(rows[f".:{tool}"].provenance, "default config, ephemeral", tool)
        self.assertNotIn(".:react-doctor", rows)

    def test_the_default_tool_stands_by_behind_an_owner(self):
        rows = self.rows({"package.json": json.dumps({"devDependencies": {"eslint": "9.1.0"}}), "eslint.config.js": "", "i.js": "1\n"})
        self.assertEqual(rows[".:oxlint"].standby_behind, "eslint")
        self.assertEqual(rows[".:oxlint"].provenance, "default config, ephemeral, standby behind eslint")
        self.assertEqual(rows[".:eslint"].provenance, "repo config (eslint.config.js), ephemeral")

    def test_plain_javascript_without_a_tsconfig_is_not_type_checked(self):
        rows = self.rows({"package.json": "{}", "i.js": "1\n"})
        self.assertEqual(rows[".:tsc"].state, "skipped")

    def test_python_types_follow_the_virtualenv(self):
        without = self.rows({"pyproject.toml": "", "a.py": "x = 1\n"})
        self.assertIn(".:ty", without)
        self.assertNotIn(".:pyright", without)
        self.assertEqual(without[".:mypy"].detail, "not owned (never imposed)")

    def test_quick_profile_names_what_needs_deep(self):
        rows = self.rows({"CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n", "p/p.csproj": "<Project/>", "p/a.cs": "class A {}\n"})
        self.assertTrue(rows[".:clang-tidy"].detail.startswith("needs --deep"))
        self.assertTrue(rows["p:dotnet build + NetAnalyzers"].detail.startswith("needs --deep"))
        self.assertEqual(rows[".:clang-format"].detail, "not owned (never imposed)")

    def test_owned_deep_tools_skip_until_deep(self):
        owned = [
            ({"package.json": "{}", "i.ts": "1\n", "stryker.config.json": "{}"}, ".:stryker", "jsts.md"),
            ({"go.mod": "module x\n", "a.go": "package a\n", ".gremlins.yaml": ""}, ".:gremlins", "go.md"),
            ({"pyproject.toml": "", "a.py": "x = 1\n", "cosmic-ray.toml": ""}, ".:cosmic-ray", "python.md"),
            ({"CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n", "mull.yml": ""}, ".:mull", "cpp.md"),
            (
                {"p/p.csproj": "<Project/>", "p/a.cs": "class A {}\n", "p/.config/dotnet-tools.json": json.dumps({"tools": {"dotnet-stryker": {}}})},
                "p:stryker.net",
                "csharp.md",
            ),
        ]
        for files, key, reference in owned:
            self.assertEqual(self.rows(files)[key].detail, "needs --deep", key)
            self.assertEqual(self.rows(files, deep=True)[key].detail, f"deep tool: run it from references/{reference}", key)
        never_imposed = [
            ({"pyproject.toml": "", "a.py": "x = 1\n"}, ".:cosmic-ray"),
            ({"CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n"}, ".:mull"),
            ({"p/p.csproj": "<Project/>", "p/a.cs": "class A {}\n"}, "p:stryker.net"),
        ]
        for files, key in never_imposed:
            for deep in (False, True):
                self.assertEqual(self.rows(files, deep=deep)[key].detail, "not owned (never imposed)", key)

    def test_every_standby_is_named_in_the_provenance(self):
        go_rows = self.rows({"go.mod": "module x\n", "a.go": "package a\n", ".golangci.yml": ""})
        self.assertEqual(go_rows[".:staticcheck"].standby_behind, "golangci-lint")
        self.assertEqual(go_rows[".:staticcheck"].provenance, "default config, ephemeral, standby behind golangci-lint")
        py_rows = self.rows(
            {"pyproject.toml": "[tool.mypy]\n[tool.pyright]\n", "requirements-dev.txt": "mypy\n", "a.py": "x = 1\n", ".venv/bin/python": ""}
        )
        self.assertEqual(py_rows[".:pyright"].standby_behind, "mypy")
        self.assertEqual(py_rows[".:pyright"].provenance, "repo config (pyproject.toml [tool.pyright]), system binary, standby behind mypy")

    def test_each_binary_rung_names_its_provenance(self):
        js_bare = {
            "package.json": json.dumps({"devDependencies": {"eslint": "9.1.0", "typescript": "5.4.0"}}),
            "eslint.config.js": "",
            "tsconfig.json": "{}",
            "i.ts": "1\n",
        }
        js_installed = {**js_bare, "node_modules/.bin/eslint": "", "node_modules/.bin/tsc": ""}
        py_installed = {
            "pyproject.toml": "[tool.ruff]\n[tool.mypy]\n[tool.pyright]\n",
            "requirements-dev.txt": "ruff\nmypy\n",
            "a.py": "x = 1\n",
            ".venv/bin/python": "",
            ".venv/bin/ruff": "",
            ".venv/bin/pyright": "",
            ".venv/bin/mypy": "",
        }
        py_bare = {"pyproject.toml": "[tool.mypy]\n[tool.pyright]\n", "requirements-dev.txt": "mypy\n", "a.py": "x = 1\n", ".venv/bin/python": ""}
        py_no_venv = {"pyproject.toml": "[tool.mypy]\n", "requirements-dev.txt": "mypy\n", "a.py": "x = 1\n"}
        cpp_files = {"CMakeLists.txt": "project(x)\n", "a.cpp": "int a;\n", ".clang-format": ""}
        no_node = "not available: node not on PATH: brew install node"
        no_uv = "not available: uv not on PATH: brew install uv"
        pyright = "repo config (pyproject.toml [tool.pyright])"
        cases = [
            (js_installed, set(), ".:eslint", "repo config (eslint.config.js), repo binary"),
            (js_installed, set(), ".:tsc", "repo config (tsconfig.json), repo binary"),
            (js_bare, {"node"}, ".:eslint", "repo config (eslint.config.js), ephemeral"),
            (js_bare, {"node"}, ".:tsc", "repo config (tsconfig.json), ephemeral"),
            (js_bare, set(), ".:eslint", no_node),
            (js_bare, set(), ".:tsc", no_node),
            (py_installed, set(), ".:ruff check", "repo config (pyproject.toml [tool.ruff]), repo binary"),
            (py_installed, set(), ".:mypy", "repo config (pyproject.toml [tool.mypy]), repo binary"),
            (py_bare, {"pyright", "uv"}, ".:pyright", f"{pyright}, system binary, standby behind mypy"),
            (py_bare, {"pyright", "uv"}, ".:mypy", "repo config (pyproject.toml [tool.mypy]), ephemeral"),
            (py_bare, {"uv"}, ".:pyright", f"{pyright}, ephemeral, standby behind mypy"),
            (py_bare, {"uv"}, ".:ruff check", "default config, ephemeral"),
            (py_bare, set(), ".:pyright", no_uv),
            (py_bare, set(), ".:mypy", no_uv),
            (py_bare, set(), ".:ruff check", no_uv),
            (py_no_venv, {"uv"}, ".:mypy", "not available: mypy is not installed and the project has no virtualenv"),
            (cpp_files, {"xcrun", "uv"}, ".:clang-format", "repo config (.clang-format), system binary"),
            (cpp_files, {"uv"}, ".:clang-format", "repo config (.clang-format), ephemeral"),
            (cpp_files, set(), ".:clang-format", no_uv),
        ]
        for files, present, key, provenance in cases:
            with self.subTest(key=key, present=sorted(present), files=sorted(files)):
                self.assertEqual(self.rows(files, present=present)[key].provenance, provenance)
        for files, present in ((js_installed, set()), (js_bare, {"node"})):
            eslint = self.rows(files, present=present)[".:eslint"]
            self.assertEqual(eslint.version, "")  # the argv thunk stamps the version only when the job runs
            self.assertTrue(callable(eslint.job))

    def test_only_keeps_the_rows_of_the_selected_categories(self):
        rows = self.rows({"pyproject.toml": "", "a.py": "x = 1\n"}, only=["format"])
        self.assertEqual(sorted(r.tool for r in rows.values()), ["ruff format"])

    def test_a_fixture_only_language_gets_no_scan_beside_a_real_one(self):
        rows = self.rows({"package.json": "{}", "src/i.ts": "1\n", "tests/fixtures/s.py": "x = 1\n"})
        self.assertFalse([key for key in rows if "ruff" in key])

    def test_one_duplication_pass_per_project_and_one_rollup(self):
        rows = self.rows({"a/package.json": "{}", "a/i.ts": "1\n", "b/package.json": "{}", "b/i.ts": "1\n"})
        self.assertEqual(sorted(key for key in rows if key.endswith(":jscpd")), ["a:jscpd", "b:jscpd", "repo:jscpd"])


class RunnerTest(RepoCase):
    def run_one(self, job) -> Row:
        run = self.run_for(self.repo({"a.py": "x = 1\n"}))
        row = Row(project=".", language="python", categories=("lint",), tool="probe", job=job)
        execute(run, row)
        return row

    def test_a_killed_tool_is_a_timeout_and_the_run_goes_on(self):
        def job(row):
            run = self.run_for(self.repo({"a.py": "\n"}))
            run.exec(row, [sys.executable, "-c", "import time; time.sleep(30)"], budget=1)

        row = self.run_one(job)
        self.assertEqual((row.state, row.detail), ("timeout", "killed after 1 s"))
        self.assertIsNone(row.commands[0]["exit"])

    def test_a_missing_binary_is_not_available(self):
        def job(row):
            self.run_for(self.repo({"a.py": "\n"})).exec(row, ["crank-health-no-such-binary"])

        self.assertEqual(self.run_one(job).state, "not-available")

    def test_any_exception_becomes_an_error_state_and_clears_findings(self):
        def job(row):
            row.add("a.py", 1, "lint", "r", "warning", "m")
            raise KeyError("shape changed")

        row = self.run_one(job)
        self.assertEqual(row.state, "error")
        self.assertIn("KeyError", row.detail)
        self.assertEqual(row.findings, [])

    def test_failed_carries_the_reason(self):
        def job(row):
            raise Failed("exit 2: bad flag")

        self.assertEqual(self.run_one(job).detail, "exit 2: bad flag")

    def test_a_trailing_file_list_is_recorded_as_one_runnable_line(self):
        repo = self.repo({f"f{n}.py": "x = 1\n" for n in range(6)})
        run = self.run_for(repo)
        row = Row(project=".", language="python", categories=("lint",), tool="ruff check")
        files = [str(repo.path / f"f{n}.py") for n in range(6)]
        run.exec(row, [sys.executable, "-c", "pass", *files[:3], *files[3:]], cwd=repo.path)
        run.exec(row, [sys.executable, "-c", "pass", *files], cwd=repo.path)
        self.assertEqual(len(row.commands), 1)
        self.assertEqual(row.commands[0]["runs"], 2)
        self.assertIn("xargs -0", row.commands[0]["command"])
        listing = run.run_dir / "lists" / "root--ruff-check.txt"
        self.assertEqual(listing.read_text().splitlines(), files)

    def test_overrides_reach_one_tool_and_one_project(self):
        run = self.run_for(self.repo({"a.py": "\n"}))
        (run.run_dir / "overrides.json").write_text(json.dumps({"knip": ["--config", "<run-dir>/knip.json"], "knip@web": ["--strict"]}))
        self.assertEqual(run.extra("knip", "."), ["--config", f"{run.run_dir}/knip.json"])
        self.assertEqual(run.extra("knip", "web"), ["--strict"])
        self.assertEqual(run.extra("oxlint"), [])


class SilentFailureTest(RepoCase):
    """A tool that exits as if it found something and printed nothing has crashed."""

    def context(self, files: dict[str, str]):
        run = self.run_for(self.repo(files))
        project = run.inv.projects[0]
        return run, jsts._Context(run, project, project.files["js-ts"])

    def test_prettier_exiting_1_with_nothing_listed_is_an_error_not_a_clean_tree(self):
        run, ctx = self.context({"package.json": "{}", "a.ts": "1\n"})
        probe = Row(project=".", language="js-ts", categories=("format",), tool="prettier")
        crash = [sys.executable, "-c", "import sys; sys.stderr.write('[error] Cannot find package prettier-plugin-x\\n'); sys.exit(1)"]
        listed, errors = ctx._prettier_listed(probe, crash, ["a.ts"], run.repo)
        self.assertEqual((listed, errors), ([], ["[error] Cannot find package prettier-plugin-x"]))
        differs = [sys.executable, "-c", "import sys; print(sys.argv[-1]); sys.exit(1)"]
        listed, errors = ctx._prettier_listed(probe, differs, ["a.ts"], run.repo)
        self.assertEqual((listed, errors), ([str(run.repo / "a.ts")], []))

    def test_knip_without_node_modules_grades_nothing(self):
        run, ctx = self.context({"package.json": "{}", "a.ts": "1\n"})
        knip = Row(project=".", language="js-ts", categories=("dead code",), tool="knip", state="ok")
        knip.add("a.ts", 1, "dead code", "unused-export", "warning", "unused export: f")
        ctx._knip_unmeasured(knip, "no node_modules: knip cannot load the configs that name entry points")
        self.assertEqual([f.status for f in knip.findings], ["advisory"])
        self.assertTrue(knip.notes[0].startswith("check: no node_modules"))
        got = {g.category: g for g in grade.grade([inv.ProjectRecord(dir=".", lines={"js-ts": 1}, files={"js-ts": 1}, asset_lines={})], [knip], set(CATEGORIES), False)}
        self.assertEqual(got["dead code"].letter, "")

    def test_a_recorded_mirror_command_names_the_repo(self):
        run, _ = self.context({"package.json": "{}", "a.ts": "1\n"})
        probe = Row(project="repo", language="repo-wide", categories=("security",), tool="gitleaks")
        mirror = run.temp_dir("gitleaks")
        run.exec(probe, [sys.executable, "-c", "pass", str(mirror)])
        self.assertTrue(probe.commands[0]["command"].endswith(str(run.repo)))

    def test_an_override_key_no_tool_reads_is_named(self):
        run, _ = self.context({"package.json": "{}", "a.ts": "1\n"})
        (run.run_dir / "overrides.json").write_text(json.dumps({"knip@.": [], "prettier@apps/web": ["--config", "x"]}))
        self.assertEqual(run.unread_overrides(), ["prettier@apps/web"])


class RowTest(unittest.TestCase):
    def test_categories_are_a_tuple(self):
        def categories(value):
            return Row(project=".", language="x", categories=value, tool="t").categories

        self.assertEqual(categories("lint"), ("lint",))
        self.assertEqual(categories(["lint", "security"]), ("lint", "security"))
        self.assertEqual(categories(("types",)), ("types",))


class FindingTest(unittest.TestCase):
    def test_a_row_round_trips_through_the_findings_file(self):
        row = Row(project=".", language="python", categories=("dead code",), tool="vulture")
        finding = row.add("a.py", 3, "dead code", "unused-import", "info", "unused\timport\n'os'", graded=False, reason="confidence below 90%")
        finding.data["confidence"] = 60
        finding.flags = ["test"]
        line = finding.tsv()
        self.assertEqual(line.split("\t"), ["a.py", "3", "dead code", "vulture/unused-import", "info", "advisory: confidence below 90%", "unused import 'os'", "test confidence=60"])
        back = Finding.parse(line)
        self.assertEqual((back.status, back.reason, back.flags, back.data), ("advisory", "confidence below 90%", ["test"], {"confidence": "60"}))
        self.assertEqual(back.tsv(), line)
        self.assertEqual(back.line, 3)

    def test_row_add_stores_an_int_line(self):
        row = Row(project=".", language="python", categories=("lint",), tool="t")
        got = [row.add("a.py", line, "lint", "r", "warning", "m").line for line in (12, "12", "", None, 0, "C")]
        self.assertEqual(got, [12, 12, 0, 0, 0, 0])

    def test_triage_verdicts_parse(self):
        base = "a.py\t\tlint\tx/y\twarning\t{}\tm\t"
        self.assertTrue(Finding.parse(base.format("graded")).graded)
        dropped = Finding.parse(base.format("dropped: fixture"))
        self.assertEqual((dropped.status, dropped.reason, dropped.line), ("dropped", "fixture", 0))
        self.assertEqual(dropped.tsv().split("\t")[1], "")
        self.assertEqual(Finding.parse(base.format("Advisory")).status, "advisory")
        self.assertIsNone(Finding.parse("too\tfew\tcolumns"))


def row(tool, categories, project=".", language="js-ts", state="ok", **kw) -> Row:
    made = Row(project=project, language=language, categories=tuple(categories), tool=tool, state=state)
    for key, value in kw.items():
        setattr(made, key, value)
    return made


PROJECT = inv.ProjectRecord(dir=".", lines={"js-ts": 2000}, files={"js-ts": 10}, asset_lines={"css": 500})


class GradeTest(unittest.TestCase):
    def letters(self, rows, projects=(PROJECT,), only=CATEGORIES) -> dict[str, grade.Grade]:
        return {g.category: g for g in grade.grade(list(projects), rows, set(only), False) if g.unit == projects[0].dir}

    def test_density_is_weighted_findings_over_kloc(self):
        lint = row("oxlint", ["lint"])
        for n in range(2):
            lint.add("a.ts", n + 1, "lint", "e", "error", "m")
        for n in range(3):
            lint.add("a.ts", n + 9, "lint", "w", "warning", "m")
        lint.add("a.ts", 20, "lint", "s", "warning", "m", graded=False, reason="style")
        got = self.letters([lint])["lint"]
        self.assertEqual((got.letter, got.basis), ("C", "13 weighted / 2.0 KLOC = 6.50"))

    def test_biome_reading_assets_grows_only_the_lint_denominator(self):
        biome = row("biome lint", ["lint"], reads_assets=True)
        biome.add("a.css", 1, "lint", "x", "warning", "m")
        self.assertEqual(self.letters([biome])["lint"].basis, "1 weighted / 2.5 KLOC = 0.40")

    def test_a_category_no_tool_measured_is_not_assessed_never_a(self):
        got = self.letters([row("tsc", ["types"], state="error", detail="exit 2")])
        self.assertEqual((got["types"].letter, got["types"].basis), ("", "tsc: exit 2"))
        self.assertEqual(got["lint"].letter, "")
        self.assertEqual(len(got), 8)

    def test_types_with_no_graded_finding_is_a(self):
        self.assertEqual(self.letters([row("tsc", ["types"])])["types"].letter, "A")

    def test_security_letters_follow_absolute_counts(self):
        def security(*levels, advisory=0, dropped=0):
            scanner = row("gitleaks", ["security"], project="repo", language="repo-wide")
            for n, level in enumerate(levels):
                scanner.add("a.ts", n + 1, "security", "r", level, "m")
            for n in range(advisory):
                scanner.add("a.ts", 50 + n, "security", "r", "warning", "m", graded=False, reason="dev only")
            for n in range(dropped):
                scanner.add("a.ts", 70 + n, "security", "r", "error", "m").demote("false positive", "dropped")
            return self.letters([scanner])["security"].letter

        self.assertEqual(security(), "A")
        self.assertEqual(security(advisory=1), "B")
        self.assertEqual(security(dropped=3), "A")
        self.assertEqual(security("warning", "warning", "info"), "B")
        self.assertEqual(security("warning", "warning", "warning"), "C")
        self.assertEqual(security("error"), "D")
        self.assertEqual(security("error", "critical"), "F")

    def test_a_ratio_counts_graded_rows_over_the_tools_denominator(self):
        fallow = row("fallow health", ["complexity"], metrics={"complexity": Metric(3, 200, "functions over 15")})
        for n in range(3):
            fallow.add("a.ts", n + 1, "complexity", "cognitive-complexity", "warning", "m")
        self.assertEqual(self.letters([fallow])["complexity"].basis, "3 / 200 functions over 15 = 1.50%")
        fallow.findings[0].demote("fixture", "dropped")
        self.assertEqual(self.letters([fallow])["complexity"].basis, "2 / 200 functions over 15 = 1.00%")

    def test_a_run_that_cannot_be_believed_leaves_its_category_unassessed(self):
        knip = row("knip", ["dead code"], unmeasured="no node_modules: knip cannot load the configs that name entry points")
        got = self.letters([knip])["dead code"]
        self.assertEqual((got.letter, got.basis), ("", "knip: no node_modules: knip cannot load the configs that name entry points"))

    def test_unselected_categories_read_not_selected(self):
        got = self.letters([row("tsc", ["types"])], only=["types"])
        self.assertEqual(got["lint"].basis, "not selected")
        self.assertEqual(got["types"].letter, "A")

    def test_repo_wide_findings_grade_the_project_that_holds_the_file_and_the_rollup(self):
        projects = [
            inv.ProjectRecord(dir="a", lines={"js-ts": 1000}, files={"js-ts": 1}, asset_lines={}),
            inv.ProjectRecord(dir="b", lines={"js-ts": 1000}, files={"js-ts": 1}, asset_lines={}),
        ]
        scanner = row("osv-scanner", ["security"], project="repo", language="repo-wide")
        scanner.add("b/package-lock.json", 4, "security", "vulnerable-dependency", "error", "m")
        grades = {(g.unit, g.category): g.letter for g in grade.grade(projects, [scanner], set(CATEGORIES), False)}
        self.assertEqual((grades[("a", "security")], grades[("b", "security")], grades[(grade.ROLLUP, "security")]), ("A", "D", "D"))

    def test_the_headline_is_the_rollup_when_there_is_one(self):
        def project(d):
            return inv.ProjectRecord(dir=d, lines={"js-ts": 1000}, files={"js-ts": 1}, asset_lines={})

        two = grade.grade([project("a"), project("b")], [], set(CATEGORIES), False)
        one = grade.grade([project(".")], [], set(CATEGORIES), False)
        self.assertEqual((grade.headline(two), grade.headline(one), grade.headline([])), (grade.ROLLUP, ".", ""))
        self.assertNotIn("| absent |", "\n".join(cli.delta_table(two, one, [], [])))

    def test_duplication_reads_the_project_pass_and_the_rollup_pass(self):
        projects = [
            inv.ProjectRecord(dir="a", lines={"js-ts": 1000}, files={"js-ts": 1}, asset_lines={}),
            inv.ProjectRecord(dir="b", lines={"js-ts": 1000}, files={"js-ts": 1}, asset_lines={}),
        ]
        rows = [
            row("jscpd", ["duplication"], project="a", language="repo-wide", metrics={"duplication": Metric(40, 1000, "tokens")}),
            row("jscpd", ["duplication"], project="b", language="repo-wide", metrics={"duplication": Metric(0, 0, "tokens")}),
            row("jscpd", ["duplication"], project="repo", language="repo-wide", metrics={"duplication": Metric(150, 1000, "tokens")}),
        ]
        grades = {(g.unit, g.category): g for g in grade.grade(projects, rows, set(CATEGORIES), False)}
        self.assertEqual(grades[("a", "duplication")].letter, "B")
        self.assertEqual(grades[("b", "duplication")].basis, "no file reached jscpd")
        self.assertEqual(grades[(grade.ROLLUP, "duplication")].letter, "D")


class SettleTest(RepoCase):
    def inventory(self) -> inv.Inventory:
        return inv.build(self.repo({"package.json": "{}", "src/a.ts": "1\n", "src/a.test.ts": "1\n"}).path, [])

    def test_a_standby_drops_its_findings_once_the_owner_graded(self):
        owner = row("eslint", ["lint"])
        standby = row("oxlint", ["lint"], standby_behind="eslint")
        standby.add("src/a.ts", 1, "lint", "x", "error", "m")
        settle.settle(self.inventory(), [owner, standby])
        self.assertEqual((standby.findings, standby.stood_down), ([], True))

    def test_settling_twice_writes_each_stand_down_note_once(self):
        owner = row("eslint", ["lint"])
        standby = row("oxlint", ["lint"], standby_behind="eslint")
        settle.stand_down([owner, standby])
        settle.stand_down([owner, standby])
        self.assertEqual(standby.notes, ["standby stood down: eslint graded lint"])
        owner = row("eslint", ["lint"], state="error", detail="plugin missing")
        standby = row("oxlint", ["lint"], standby_behind="eslint")
        standby.add("src/a.ts", 1, "lint", "x", "error", "m")
        settle.settle(self.inventory(), [owner, standby])
        standby.findings[0].status = "dropped"
        settle.settle(self.inventory(), [owner, standby])
        self.assertEqual(standby.notes, ["oxlint graded lint on its default config because eslint reported error (0 graded, 1 advisory)"])

    def test_a_standby_keeps_its_findings_when_the_owner_errored_and_says_so(self):
        owner = row("eslint", ["lint"], state="error", detail="plugin missing")
        standby = row("oxlint", ["lint"], standby_behind="eslint")
        standby.add("src/a.ts", 1, "lint", "x", "error", "m")
        settle.settle(self.inventory(), [owner, standby])
        self.assertEqual(len(standby.findings), 1)
        self.assertEqual(standby.notes, ["oxlint graded lint on its default config because eslint reported error (1 graded, 0 advisory)"])

    def test_an_owner_whose_config_excludes_every_file_leaves_the_category_unassessed(self):
        owner = row("biome format", ["format"], state="skipped", detail="nothing to scan (the Biome config includes none of this project's 4 files)")
        standby = row("prettier", ["format"], standby_behind="biome format", metrics={"format": Metric(4, 4, "files")})
        standby.add("src/a.ts", "", "format", "unformatted", "warning", "m")
        settle.settle(self.inventory(), [owner, standby])
        got = {g.category: g for g in grade.grade([PROJECT], [owner, standby], set(CATEGORIES), False)}
        self.assertEqual(got["format"].letter, "")

    def test_a_partial_standby_keeps_the_categories_the_owner_does_not_grade(self):
        owner = row("golangci-lint", ["lint"], language="go")
        standby = row("staticcheck", ["types", "dead code", "lint"], language="go", standby_behind="golangci-lint")
        standby.add("src/a.ts", 1, "lint", "SA1", "warning", "m")
        standby.add("src/a.ts", 2, "dead code", "U1000", "warning", "m")
        settle.settle(self.inventory(), [owner, standby])
        self.assertEqual([f.category for f in standby.findings], ["dead code"])
        self.assertFalse(standby.stood_down)

    def test_hits_outside_the_inventory_leave_with_a_count(self):
        scanner = row("aislop", ["lint"], project="repo", language="repo-wide")
        scanner.add("src/a.ts", 1, "lint", "x", "warning", "m")
        scanner.add("dist/bundle.js", 1, "lint", "x", "warning", "m")
        scanner.add("dist/other.js", 1, "lint", "x", "warning", "m")
        settle.settle(self.inventory(), [scanner])
        self.assertEqual([f.file for f in scanner.findings], ["src/a.ts"])
        self.assertEqual(scanner.notes, ["2 findings outside the inventory dropped, count only (dist 2)"])

    def test_two_tools_at_one_place_is_one_graded_finding(self):
        first = row("oxlint", ["lint"])
        first.add("src/a.ts", 7, "lint", "no-undef", "warning", "m")
        second = row("aislop", ["lint"], project="repo", language="repo-wide")
        second.add("src/a.ts", 7, "lint", "eslint/no-undef", "warning", "m")
        second.add("src/a.ts", 8, "lint", "eslint/no-undef", "warning", "m")
        settle.settle(self.inventory(), [first, second])
        self.assertEqual([f.status for f in second.findings], ["advisory", "graded"])
        self.assertEqual(second.findings[0].reason, "duplicate of oxlint/no-undef")

    def test_findings_carry_their_path_class(self):
        scanner = row("oxlint", ["lint"])
        scanner.add("src/a.test.ts", 1, "lint", "x", "warning", "m")
        scanner.add("src/a.ts", 1, "lint", "x", "warning", "m")
        settle.settle(self.inventory(), [scanner])
        self.assertEqual([f.flags for f in scanner.findings], [["test"], []])

    def test_govulncheck_decides_a_go_advisory_and_never_double_counts(self):
        osv = row("osv-scanner", ["security"], project="repo", language="repo-wide")
        called = osv.add("go.mod", 3, "security", "vulnerable-dependency", "error", "a@1")
        called.data["ids"] = "GO-1,GHSA-a"
        idle = osv.add("go.mod", 4, "security", "vulnerable-dependency", "error", "b@1")
        idle.data["ids"] = "GO-2"
        vuln = row("govulncheck", ["security"], language="go")
        vuln.add("main.go", 9, "security", "symbol-reachable", "error", "GO-1").data["ids"] = "GO-1,GHSA-a"
        vuln.add("go.mod", "", "security", "imported-no-call", "info", "GO-2", graded=False, reason="never called").data["ids"] = "GO-2"
        go.join_vulnerabilities([osv, vuln])
        self.assertEqual((called.status, idle.status), ("graded", "advisory"))
        self.assertEqual(vuln.findings[0].reason, "duplicate of osv-scanner/vulnerable-dependency")

    def test_a_reloaded_govulncheck_row_still_decides_reachability(self):
        vuln = row("govulncheck", ["security"], language="go")
        vuln.add("go.mod", "", "security", "imported-no-call", "info", "GO-2", graded=False, reason="never called").data["ids"] = "GO-2"
        with tempfile.TemporaryDirectory() as tmp:
            report.write_findings(Path(tmp), [vuln])
            reloaded = row("govulncheck", ["security"], language="go", findings=report.read_findings(Path(tmp), vuln))
        osv = row("osv-scanner", ["security"], project="repo", language="repo-wide")
        idle = osv.add("go.mod", 4, "security", "vulnerable-dependency", "error", "b@1")
        idle.data["ids"] = "GO-2"
        go.join_vulnerabilities([osv, reloaded])
        self.assertEqual((idle.status, idle.reason), ("advisory", "govulncheck: the vulnerable symbol is never called"))


class ParserTest(unittest.TestCase):
    def test_sarif_results_fall_back_to_the_rule_default_level(self):
        doc = {
            "runs": [
                {
                    "tool": {"driver": {"rules": [{"id": "r1", "defaultConfiguration": {"level": "error"}}]}},
                    "results": [
                        {"ruleId": "r1", "message": {"text": "m"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": "a.ts"}, "region": {"startLine": 4}}}]},
                        {"ruleId": "r2", "level": "note", "message": {"text": "n"}},
                    ],
                }
            ]
        }
        self.assertEqual(list(sarif_results(doc)), [("r1", "error", "m", "a.ts", 4), ("r2", "note", "n", "", 0)])

    def test_pnpm_reachability_separates_dev_only_packages(self):
        lock = """
lockfileVersion: '9.0'
importers:
  .:
    devDependencies:
      vitest:
        specifier: ^3
        version: 3.0.0
  apps/web:
    dependencies:
      '@scope/core':
        specifier: workspace:*
        version: link:../../packages/core
      react:
        specifier: ^19
        version: 19.0.0(peer@1.0.0)
  packages/core:
    dependencies:
      lodash:
        specifier: ^4
        version: 4.17.21
packages:
  react@19.0.0:
    resolution: {integrity: sha512-x}
snapshots:
  lodash@4.17.21: {}
  react@19.0.0(peer@1.0.0):
    dependencies:
      scheduler: 0.25.0
  scheduler@0.25.0: {}
  vitest@3.0.0:
    dependencies:
      esbuild: 0.18.20
  esbuild@0.18.20: {}
"""
        with tempfile.TemporaryDirectory() as holder:
            path = Path(holder) / "pnpm-lock.yaml"
            path.write_text(lock)
            reach = common._Reachability(path)
        self.assertEqual(reach.verdict("scheduler", "0.25.0"), "prod")
        self.assertEqual(reach.verdict("lodash", "4.17.21"), "prod")
        self.assertEqual(reach.verdict("esbuild", "0.18.20"), "dev")
        self.assertEqual(reach.verdict("left-pad", "1.0.0"), "unknown")

    def test_npm_reachability_reads_the_dev_flag(self):
        lock = {"packages": {"": {}, "node_modules/a": {"version": "1.0.0", "dev": True}, "node_modules/b": {"version": "2.0.0"}, "node_modules/b/node_modules/a": {"version": "1.0.0"}}}
        with tempfile.TemporaryDirectory() as holder:
            path = Path(holder) / "package-lock.json"
            path.write_text(json.dumps(lock))
            reach = common._Reachability(path)
        self.assertEqual(reach.verdict("a", "1.0.0"), "prod")
        self.assertEqual(reach.verdict("b", "2.0.0"), "prod")
        path_dev = {"packages": {"node_modules/a": {"version": "1.0.0", "dev": True}}}
        with tempfile.TemporaryDirectory() as holder:
            path = Path(holder) / "package-lock.json"
            path.write_text(json.dumps(path_dev))
            self.assertEqual(common._Reachability(path).verdict("a", "1.0.0"), "dev")

    def test_an_unreadable_lockfile_grades_rather_than_excuses(self):
        with tempfile.TemporaryDirectory() as holder:
            path = Path(holder) / "package-lock.json"
            path.write_text("{not json")
            self.assertEqual(common._Reachability(path).verdict("a", "1.0.0"), "unknown")

    def test_the_fix_is_the_smallest_fixed_version_above_the_installed_one(self):
        vuln = {
            "affected": [
                {"package": {"name": "x"}, "ranges": [{"events": [{"introduced": "0"}, {"fixed": "1.2.5"}]}, {"events": [{"introduced": "2.0.0"}, {"fixed": "2.3.1"}]}]},
                {"package": {"name": "other"}, "ranges": [{"events": [{"fixed": "9.9.9"}]}]},
            ]
        }
        self.assertEqual(common._fixed_version(vuln, "x", "2.1.0"), "2.3.1")
        self.assertEqual(common._fixed_version(vuln, "x", "1.0.0"), "1.2.5")
        self.assertEqual(common._fixed_version(vuln, "x", "3.0.0"), "")

    def test_concatenated_json_documents_split_cleanly(self):
        text = '# pkg/a\n{}\n{"pkg/b": {"printf": [{"posn": "b.go:3:2", "message": "has { brace"}]}}\ntrailing'
        self.assertEqual(go._json_documents(text), [{}, {"pkg/b": {"printf": [{"posn": "b.go:3:2", "message": "has { brace"}]}}])

    def test_tool_line_formats(self):
        m = jsts.TSC_LINE.match("src/a.ts(12,5): error TS2322: Type 'x' is not assignable.")
        self.assertEqual(m.groups(), ("src/a.ts", "12", "error", "TS2322", "Type 'x' is not assignable."))
        self.assertEqual(jsts.TSC_LINE.match("error TS2688: Cannot find type definition file for 'node'.").group(4), "TS2688")
        m = python.VULTURE_LINE.match("pkg/a.py:9: unused function 'f' (60% confidence)")
        self.assertEqual((m.group(1), m.group(2), m.group(4)), ("pkg/a.py", "9", "60"))
        m = cpp.FORMAT_LINE.match("/r/a.cpp:19:42: error: code should be clang-formatted [-Wclang-format-violations]")
        self.assertEqual(m.group(1), "/r/a.cpp")

    def test_knip_issue_lists_flatten_whatever_their_nesting(self):
        self.assertEqual(list(jsts._knip_symbols([{"name": "a", "line": 2}])), [("a", 2)])
        self.assertEqual(list(jsts._knip_symbols({"E": [{"name": "m", "line": 5}]})), [("m", 5)])
        self.assertEqual(list(jsts._knip_symbols([[{"name": "a", "line": 1}, {"name": "b", "line": 9}]])), [("a = b", 1)])
        self.assertEqual(list(jsts._knip_symbols([])), [])


class PrModeTest(RepoCase):
    def test_changed_lines_maps_renames_and_added_ranges(self):
        repo = self.repo({"a.py": "one\ntwo\nthree\n", "old.py": "".join(f"line {n}\n" for n in range(40))})
        base = subprocess.run(["git", "-C", str(repo.path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        git(repo.path, "mv", "old.py", "new.py")
        repo.write({"a.py": "one\nTWO\nthree\nfour\nfive\n"})
        repo.commit("change")
        renames, hunks = cli.changed_lines(repo.path, base)
        self.assertEqual(renames, {"old.py": "new.py"})
        self.assertEqual(hunks["a.py"], [(2, 2), (4, 5)])
        self.assertEqual(hunks["new.py"], [])

    def test_the_finding_key_ignores_line_numbers_and_follows_renames(self):
        before = Finding("old.py", 10, "lint", "ruff-check/F401", "warning", "graded", "`os` imported but unused at 10")
        after = Finding("new.py", 14, "lint", "ruff-check/F401", "warning", "graded", "`os` imported but unused at 14")
        self.assertEqual(cli.finding_key(before, {"old.py": "new.py"}), cli.finding_key(after))
        self.assertNotEqual(cli.finding_key(before), cli.finding_key(after))


class RunDirTest(RepoCase):
    """The commands that reload a run dir: verdict, grade and finish."""

    def scanned(self) -> tuple[Repo, Path]:
        repo = self.repo({"pyproject.toml": "", "src/a.py": "x = 1\n", "tests/test_a.py": "x = 1\n"})
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        run_dir = Path(holder.name)
        opts = SimpleNamespace(project=[], deep=False, only=list(CATEGORIES), budget_scale=1.0, plan=True, jobs=1)
        made = cli.scan_tree(repo.path, run_dir, opts, {}, [])
        bandit = next(r for r in made["rows"] if r.tool == "bandit")
        bandit.state = "ok"
        bandit.add("tests/test_a.py", 1, "security", "B101", "info", "assert used").flags = ["test"]
        bandit.add("src/a.py", 1, "security", "B602", "error", "shell=True").data["confidence"] = "HIGH"
        cli.write_all(run_dir, made["meta"], made["projects"], made["rows"], "test")
        return repo, run_dir

    def call(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def test_plan_writes_the_inventory_and_every_row_without_running_anything(self):
        _, run_dir = self.scanned()
        self.assertIn("python       2 files        2 lines", (run_dir / "inventory.md").read_text())
        tools = (run_dir / "tools.md").read_text()
        self.assertIn("| . | lint, security | ruff check |", tools)
        self.assertEqual((run_dir / "scope.txt").read_text().splitlines(), ["pyproject.toml", "src/a.py", "tests/test_a.py"])

    def test_a_verdict_moves_the_grade_and_survives_a_reload(self):
        _, run_dir = self.scanned()
        self.assertIn("security D", self.call("grade", str(run_dir))[1])
        code, out = self.call("verdict", str(run_dir), "--tool", "bandit", "--rule", "B602", "--dropped", "false positive: constant argv")
        self.assertEqual(code, 0)
        self.assertIn("1 findings now read `dropped: false positive: constant argv`", out)
        self.assertIn("security B", out)
        _, _, rows = report.read_results(run_dir)
        bandit = next(r for r in rows if r.tool == "bandit")
        self.assertEqual(sorted(f.status for f in bandit.findings), ["dropped", "graded"])
        self.assertIn("1 dropped", (run_dir / "summary" / "python--root.md").read_text())

    def test_scan_prints_the_grades_of_the_tree_it_ran(self):
        repo = self.repo({"pyproject.toml": "", "src/a.py": "x = 1\n"})
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)

        def run_rows(run, rows, jobs):
            bandit = next(r for r in rows if r.tool == "bandit")
            bandit.state = "ok"
            bandit.add("src/a.py", 1, "security", "B602", "error", "shell=True")

        with mock.patch.object(cli, "run_rows", run_rows):
            code, out = self.call("scan", str(repo.path), "--run-dir", holder.name)
        self.assertEqual(code, 0)
        meta, projects, rows = report.read_results(Path(holder.name))
        grades = grade.grade(projects, rows, set(meta["only"]), False)
        self.assertIn("security D", grade.line(grades, grade.headline(grades)))
        self.assertIn(f"grades (mechanical, before triage): {grade.line(grades, grade.headline(grades))}\n", out)

    def test_a_rerun_keeps_what_triage_and_settle_already_wrote(self):
        _, run_dir = self.scanned()
        meta, projects, rows = report.read_results(run_dir)
        ruff = next(r for r in rows if r.tool == "ruff check")
        ruff.state = "ok"
        ruff.add("src/a.py", 1, "security", "S602", "error", "subprocess call with shell=True")
        next(r for r in rows if r.tool == "bandit").add("tests/test_a.py", 5, "security", "B101", "info", "assert used")
        cli.write_all(run_dir, meta, projects, rows, "test")
        self.assertEqual(self.call("verdict", str(run_dir), "--tool", "bandit", "--rule", "B101", "--line", "1", "--dropped", "fixture")[0], 0)

        def run_rows(run, rows, jobs):
            for row in rows:
                row.state = "ok"

        with mock.patch.object(cli, "run_rows", run_rows):
            code, _ = self.call("rerun", str(run_dir), "--tool", "ty")
        self.assertEqual(code, 0)
        bandit_tsv = (run_dir / "findings" / "root" / "bandit.tsv").read_text().splitlines()
        self.assertTrue(next(line for line in bandit_tsv if "bandit/B602" in line).endswith("confidence=HIGH"))
        _, _, rows = report.read_results(run_dir)
        verdicts = {(f.rule, f.line): (f.status, f.reason) for r in rows for f in r.findings}
        self.assertEqual(verdicts[("bandit/B602", 1)], ("graded", ""))
        self.assertEqual(verdicts[("ruff-check/S602", 1)], ("graded", ""))
        self.assertEqual(verdicts[("bandit/B101", 1)], ("dropped", "fixture"))
        self.assertEqual(verdicts[("bandit/B101", 5)], ("graded", ""))

    def test_results_reload_as_project_records(self):
        _, run_dir = self.scanned()
        projects = report.read_results(run_dir)[1]
        self.assertTrue(all(isinstance(p, inv.ProjectRecord) for p in projects))
        first = projects[0]
        self.assertEqual((first.dir, first.files, first.lines, first.slug), (".", {"python": 2}, {"python": 2}, "root"))
        raw = json.loads((run_dir / "results.json").read_text())["projects"][0]
        self.assertEqual(list(raw), ["dir", "manifests", "files", "lines", "asset_lines", "owned", "unowned", "facts", "fixture_only"])

    def test_a_results_project_missing_a_key_fails_to_load(self):
        _, run_dir = self.scanned()
        raw = json.loads((run_dir / "results.json").read_text())["projects"][0]
        self.assertEqual(inv.ProjectRecord.from_json(raw).to_json(), raw)
        del raw["asset_lines"]
        with self.assertRaises(KeyError):
            inv.ProjectRecord.from_json(raw)

    def test_a_verdict_selects_by_line(self):
        _, run_dir = self.scanned()
        self.assertIn("2 findings now read", self.call("verdict", str(run_dir), "--tool", "bandit", "--line", "1", "--advisory", "x")[1])
        _, run_dir = self.scanned()
        path = run_dir / "findings" / "root" / "bandit.tsv"
        path.write_text(path.read_text().replace("src/a.py\t1\t", "src/a.py\t\t"))
        for line, reason, count in (("0", "y0", 0), ("", "y", 1), ("1", "y1", 1)):
            out = self.call("verdict", str(run_dir), "--tool", "bandit", "--line", line, "--advisory", reason)[1]
            self.assertIn(f"{count} findings now read", out, f"--line {line!r}")

    def test_a_verdict_needs_a_filter(self):
        _, run_dir = self.scanned()
        self.assertEqual(self.call("verdict", str(run_dir), "--dropped", "everything")[0], 2)

    def test_a_hand_edit_to_a_findings_file_is_what_grade_reads(self):
        _, run_dir = self.scanned()
        path = run_dir / "findings" / "root" / "bandit.tsv"
        path.write_text(path.read_text().replace("\terror\tgraded\t", "\terror\tadvisory: test helper\t"))
        self.assertIn("security B", self.call("grade", str(run_dir))[1])

    def test_finish_removes_scratch_and_reports_what_the_scan_left_behind(self):
        repo, run_dir = self.scanned()
        (run_dir / "scratch" / "x").write_text("x")
        self.assertEqual(self.call("finish", str(run_dir))[0], 0)
        self.assertFalse((run_dir / "scratch").exists())
        repo.write({"src/__pycache__/a.pyc": "x", "leftover.json": "{}"})
        (run_dir / "raw").mkdir(exist_ok=True)
        (run_dir / "raw" / "leak.txt").write_text("key = AKIA" + "ABCDEFGHIJKLMNOP\n")
        code, out = self.call("finish", str(run_dir))
        self.assertEqual(code, 1)
        self.assertIn("?? leftover.json", out)
        self.assertIn("src/__pycache__/a.pyc", out)
        self.assertIn("leak.txt", out)


if __name__ == "__main__":
    unittest.main()
