"""Tests for claude_effort.py. Run: python3 -m unittest discover tools/claude-effort"""

import fcntl
import json
import os
import pty
import select
import signal
import struct
import sys
import tempfile
import termios
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_effort import (
    Editor,
    Layer,
    build_lines,
    build_rows,
    canonical,
    resolve,
)

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_effort.py")


def stack(user=None, project=None, local=None, managed=None):
    return [
        Layer("managed", "m", managed),
        Layer("local", "l", local),
        Layer("project", "p", project),
        Layer("user", "u", user or {}),
    ]


class ResolveTest(unittest.TestCase):
    """Cases follow the docs and headless Claude Code 2.1.287 runs that printed $CLAUDE_EFFORT."""

    def test_model_entry_beats_top_level_in_the_same_file(self):
        user = {
            "effortLevel": "high",
            "modelSettings": {"claude-opus-5": {"effortLevel": "medium"}},
        }
        res = resolve("claude-opus-5", stack(user), {})
        self.assertEqual(
            (res.level, res.winner), ("medium", ("layer", "user", "modelSettings"))
        )

    def test_user_top_level_skips_opus_and_sonnet_5_5(self):
        for model in ("claude-opus-5-5", "claude-sonnet-5-5"):
            res = resolve(model, stack({"effortLevel": "high"}), {})
            self.assertEqual((res.level, res.winner), ("medium", ("default",)), model)

    def test_user_top_level_applies_to_older_models(self):
        self.assertEqual(
            resolve("claude-opus-5", stack({"effortLevel": "low"}), {}).level, "low"
        )

    def test_project_top_level_applies_to_every_model_and_outranks_user(self):
        user = {"modelSettings": {"claude-sonnet-5-5": {"effortLevel": "xhigh"}}}
        res = resolve(
            "claude-sonnet-5-5", stack(user, project={"effortLevel": "low"}), {}
        )
        self.assertEqual(
            (res.level, res.winner), ("low", ("layer", "project", "effortLevel"))
        )

    def test_settings_env_beats_the_shell_and_saved_levels(self):
        user = {
            "env": {"CLAUDE_CODE_EFFORT_LEVEL": "low"},
            "modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}},
        }
        res = resolve(
            "claude-opus-5-5", stack(user), {"CLAUDE_CODE_EFFORT_LEVEL": "high"}
        )
        self.assertEqual((res.level, res.winner), ("low", ("env",)))

    def test_shell_env_applies_without_a_settings_env(self):
        self.assertEqual(
            resolve(
                "claude-opus-5-5", stack(), {"CLAUDE_CODE_EFFORT_LEVEL": "max"}
            ).level,
            "max",
        )

    def test_env_auto_uses_the_model_default(self):
        user = {"modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}}}
        self.assertEqual(
            resolve(
                "claude-opus-5-5", stack(user), {"CLAUDE_CODE_EFFORT_LEVEL": "auto"}
            ).level,
            "medium",
        )

    def test_lowest_cap_across_files_applies(self):
        user = {
            "maxEffortLevel": "xhigh",
            "modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}},
        }
        res = resolve(
            "claude-opus-5-5", stack(user, project={"maxEffortLevel": "high"}), {}
        )
        self.assertEqual((res.level, res.cap_source), ("high", "project"))

    def test_model_max_exempts_it_from_its_own_files_cap_only(self):
        user = {
            "maxEffortLevel": "medium",
            "modelSettings": {
                "claude-opus-5-5": {"effortLevel": "xhigh", "maxEffortLevel": "max"}
            },
        }
        self.assertEqual(resolve("claude-opus-5-5", stack(user), {}).level, "xhigh")
        self.assertEqual(
            resolve(
                "claude-opus-5-5", stack(user, local={"maxEffortLevel": "high"}), {}
            ).level,
            "high",
        )

    def test_unsupported_level_falls_back_to_the_next_lower_one(self):
        self.assertEqual(
            resolve(
                "claude-opus-4-6", stack(), {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh"}
            ).level,
            "high",
        )

    def test_explicit_level_beats_saved_levels_on_any_model(self):
        # An Opus session started with --effort xhigh, or given /effort, passed its level to a Sonnet subagent.
        user = {"modelSettings": {"claude-sonnet-5-5": {"effortLevel": "low"}}}
        res = resolve("claude-sonnet-5-5", stack(user), {}, explicit="xhigh")
        self.assertEqual((res.level, res.winner), ("xhigh", ("explicit",)))

    def test_explicit_level_obeys_support_caps_and_the_env_var(self):
        self.assertEqual(resolve("claude-opus-4-6", stack(), {}, "xhigh").level, "high")
        self.assertEqual(
            resolve(
                "claude-opus-5-5", stack({"maxEffortLevel": "medium"}), {}, "max"
            ).level,
            "medium",
        )
        self.assertEqual(
            resolve(
                "claude-opus-5-5", stack(), {"CLAUDE_CODE_EFFORT_LEVEL": "low"}, "high"
            ).level,
            "low",
        )

    def test_aliases_and_suffixes_match_the_canonical_entry(self):
        self.assertEqual(canonical("opus[1m]"), "claude-opus-5-5")
        self.assertEqual(canonical("claude-sonnet-4-6-20250929"), "claude-sonnet-4-6")
        self.assertEqual(
            resolve(
                "claude-opus-5-5",
                stack({"modelSettings": {"opus": {"effortLevel": "low"}}}),
                {},
            ).level,
            "low",
        )


class SaveTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "settings.json")
        self.original = {
            "permissions": {"allow": ["Bash(git tag:*)"]},
            "effortLevel": "high",
            "modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}},
        }
        self.write(self.original)

    def tearDown(self):
        self.dir.cleanup()

    def write(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2) + "\n")

    def read(self):
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def editor(self):
        return Editor(
            self.dir.name, self.dir.name, os.path.join(self.dir.name, "no-managed"), {}
        )

    def test_save_changes_only_the_edited_key_and_keeps_a_backup(self):
        ed = self.editor()
        ed.set(("modelSettings", "claude-sonnet-5-5", "effortLevel"), "high")
        self.assertIn("Saved 1", ed.save())
        expected = json.loads(json.dumps(self.original))
        expected["modelSettings"]["claude-sonnet-5-5"] = {"effortLevel": "high"}
        self.assertEqual(self.read(), expected)
        with open(self.path + ".bak", encoding="utf-8") as f:
            self.assertEqual(json.load(f), self.original)

    def test_save_keeps_changes_another_writer_made_after_loading(self):
        ed = self.editor()
        ed.set(("modelSettings", "claude-opus-5-5", "effortLevel"), "high")
        on_disk = json.loads(json.dumps(self.original))
        on_disk["theme"] = "dark"
        on_disk["modelSettings"]["claude-fable-5-1"] = {"effortLevel": "max"}
        self.write(on_disk)
        ed.save()
        saved = self.read()
        self.assertEqual(saved["theme"], "dark")
        self.assertEqual(
            saved["modelSettings"]["claude-fable-5-1"], {"effortLevel": "max"}
        )
        self.assertEqual(
            saved["modelSettings"]["claude-opus-5-5"], {"effortLevel": "high"}
        )

    def test_save_refuses_when_the_same_key_changed_on_disk(self):
        ed = self.editor()
        ed.set(("modelSettings", "claude-opus-5-5", "effortLevel"), "low")
        on_disk = json.loads(json.dumps(self.original))
        on_disk["modelSettings"]["claude-opus-5-5"]["effortLevel"] = "medium"
        self.write(on_disk)
        self.assertTrue(ed.save().startswith("Not saved"))
        self.assertEqual(self.read(), on_disk)

    def test_clearing_the_last_entry_removes_the_empty_objects(self):
        ed = self.editor()
        ed.set(("modelSettings", "claude-opus-5-5", "effortLevel"), None)
        ed.save()
        self.assertNotIn("modelSettings", self.read())

    def test_invalid_json_is_never_overwritten(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{not json")
        ed = self.editor()
        ed.set(("effortLevel",), "low")
        self.assertTrue(ed.save().startswith("Not saved"))
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "{not json")


class ScenarioViewTest(unittest.TestCase):
    def test_sonnet_rows_under_a_saved_opus_xhigh_setup(self):
        with tempfile.TemporaryDirectory() as config:
            with open(
                os.path.join(config, "settings.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(
                    {
                        "model": "opus",
                        "effortLevel": "high",
                        "modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}},
                    },
                    f,
                )
            os.makedirs(os.path.join(config, "agents"))
            with open(
                os.path.join(config, "agents", "reviewer.md"), "w", encoding="utf-8"
            ) as f:
                f.write(
                    "---\nname: reviewer\nmodel: sonnet\neffort: high\n---\nReview the diff.\n"
                )
            ed = Editor(config, config, os.path.join(config, "no-managed"), {})
            rows = build_rows(ed)
            cursor = next(
                i for i, row in enumerate(rows) if row.model == "claude-sonnet-5-5"
            )
            lines, _ = build_lines(ed, rows, cursor, "scenarios")
            text = ["".join(segment for segment, _ in line).strip() for line in lines]
            subagent = next(
                line for line in text if line.startswith("Subagent, no effort field")
            )
            self.assertRegex(subagent, r"\smedium\s")
            reviewer = next(line for line in text if line.startswith("reviewer"))
            self.assertRegex(reviewer, r"\shigh\s")


class TerminalTest(unittest.TestCase):
    """Drive the real curses UI through a pseudo-terminal and check the file it saves."""

    def run_tui(self, config_dir, project_dir, keys):
        env = {
            **os.environ,
            "CLAUDE_CONFIG_DIR": config_dir,
            "TERM": "xterm-256color",
            "LINES": "60",
            "COLUMNS": "140",
        }
        env.pop("CLAUDE_CODE_EFFORT_LEVEL", None)
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(project_dir)
            os.execvpe(sys.executable, [sys.executable, SCRIPT], env)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 60, 140, 0, 0))
        output, deadline, sent = b"", time.monotonic() + 15, False
        try:
            while time.monotonic() < deadline:
                if not sent and b"modelSettings" in output:
                    for key in keys:
                        os.write(fd, key)
                        time.sleep(0.05)
                    sent = True
                if select.select([fd], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(fd, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output += chunk
            done, status = os.waitpid(pid, os.WNOHANG)
            while not done and time.monotonic() < deadline:
                time.sleep(0.05)
                done, status = os.waitpid(pid, os.WNOHANG)
            if not done:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
                self.fail("the TUI did not exit after q")
            return os.waitstatus_to_exitcode(status)
        finally:
            os.close(fd)

    def test_keys_set_a_level_and_the_default_model_then_save(self):
        with (
            tempfile.TemporaryDirectory() as config,
            tempfile.TemporaryDirectory() as project,
        ):
            path = os.path.join(config, "settings.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"theme": "dark"}, f)
            down = b"\x1bOB"  # the down arrow in keypad mode, which curses turns on
            # Five global rows come first, then Opus 5.5 and Sonnet 5.5.
            keys = [down] * 5 + [b"4", down, b"d", b"w", b"q"]
            self.assertEqual(self.run_tui(config, project, keys), 0)
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(
                saved,
                {
                    "theme": "dark",
                    "modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}},
                    "model": "sonnet",
                },
            )


if __name__ == "__main__":
    unittest.main()
