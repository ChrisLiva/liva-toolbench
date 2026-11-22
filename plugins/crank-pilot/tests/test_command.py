"""The command seam: `bin/crank-pilot` run as a process."""

import contextlib
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from support import BIN, QUESTIONS, Client, EffortCase, show

NO_SUCH_DIR = "/nonexistent-xyz"


class MissingEffortDirectoryTest(EffortCase):
    def test_each_verb_exits_2_with_one_stderr_line(self):
        effort = self.effort()
        for args in (("wait", NO_SUCH_DIR), ("resolve", NO_SUCH_DIR, "--chat"), ("close", NO_SUCH_DIR)):
            with self.subTest(verb=args[0]):
                done = effort.run(*args)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertEqual(len(done.stderr.strip().splitlines()), 1)
                self.assertIn("no such effort directory", done.stderr)


class EmptyStoreTest(EffortCase):
    def test_wait_with_nothing_pending_exits_2(self):
        effort = self.effort()
        done = effort.run("wait", effort.path)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stderr.strip(), "nothing pending")
        self.assertEqual(done.stdout, "")

    def test_resolve_chat_with_nothing_pending_exits_2(self):
        effort = self.effort()
        done = effort.run("resolve", effort.path, "--chat")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stderr.strip(), "nothing pending")
        self.assertEqual(done.stdout, "")

    def test_close_with_no_server_record_exits_0_silently(self):
        effort = self.effort()
        done = effort.run("close", effort.path)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout, "")
        self.assertEqual(done.stderr, "")


class EntryTest(EffortCase):
    def test_the_entry_runs_through_a_symlink_with_no_interpreter_prefix(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            link = Path(elsewhere) / "crank-pilot"
            link.symlink_to(BIN)
            done = subprocess.run(
                [str(link), "wait", NO_SUCH_DIR], capture_output=True, text=True,
                env={**os.environ, "CRANK_PILOT_NO_OPEN": "1"},
            )
        self.assertEqual(done.returncode, 2)
        self.assertIn("no such effort directory", done.stderr)


def recording_browser(effort) -> tuple[dict[str, str | None], Path]:
    """An environment whose BROWSER appends its arguments to a file, and that file; it also writes to stdout."""
    script = effort.write("browser.sh", '#!/bin/sh\necho "$@" >> "$(dirname "$0")/opened.txt"\necho noise\n')
    script.chmod(0o755)
    return {"BROWSER": str(script)}, effort.path / "opened.txt"


class ShowRejectionTest(EffortCase):
    def test_show_on_a_missing_effort_directory_exits_2(self):
        effort = self.effort()
        done = effort.run("show", NO_SUCH_DIR, "x.json")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout, "")
        self.assertEqual(len(done.stderr.strip().splitlines()), 1)
        self.assertIn("no such effort directory", done.stderr)

    def test_show_on_an_unreadable_interaction_file_exits_2_and_stores_nothing(self):
        effort = self.effort()
        cases = {
            "cut off": '{"kind":',
            "empty": "",
            "not text": b"\xff\xfe{",
            "missing": None,
        }
        for name, content in cases.items():
            with self.subTest(file=name):
                source = effort.path / "interaction.json"
                source.unlink(missing_ok=True)
                if isinstance(content, str):
                    source.write_text(content)
                elif content is not None:
                    source.write_bytes(content)
                done = effort.run("show", effort.path, source)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertEqual(len(done.stderr.strip().splitlines()), 1)
                self.assertEqual(list((effort.path / "pilot" / "interactions").glob("*")), [])
                if name == "cut off":
                    self.assertIn("not valid JSON", done.stderr)


class ShowTest(EffortCase):
    def test_show_stores_each_interaction_under_the_next_number_and_prints_it(self):
        effort = self.effort()
        self.assertEqual(show(effort, QUESTIONS), 1)
        stored = json.loads((effort.path / "pilot" / "interactions" / "001.json").read_text())
        self.assertEqual(stored, {**QUESTIONS, "number": 1})
        hostile = {**QUESTIONS, "title": "caf\u00e9 \u65e5\u672c \U0001f600 \ud800 \"quoted\" \\ \n"}
        self.assertEqual(show(effort, hostile), 2)
        stored = json.loads((effort.path / "pilot" / "interactions" / "002.json").read_text())
        self.assertEqual(stored, {**hostile, "number": 2})


class ShowServerTest(EffortCase):
    def test_show_starts_the_server_once_and_reuses_it(self):
        effort = self.effort()
        record_path = effort.path / "pilot" / "server.json"
        show(effort, QUESTIONS)
        first = json.loads(record_path.read_text())
        os.kill(first["pid"], 0)
        show(effort, QUESTIONS)
        self.assertEqual(json.loads(record_path.read_text()), first)


class UnreadableRecordTest(EffortCase):
    def test_a_record_that_is_not_a_file_counts_as_no_server(self):
        effort = self.effort()
        record = effort.path / "pilot" / "server.json"
        record.mkdir(parents=True)
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        started = time.time()
        done = effort.run("show", effort.path, source)
        self.assertLess(time.time() - started, 4)
        self.assertEqual((done.returncode, done.stdout, done.stderr.strip()), (1, "", "server did not start"))
        done = effort.run("close", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertTrue(record.is_dir())


class ShowBrowserTest(EffortCase):
    def test_show_opens_the_page_only_when_none_is_live(self):
        effort = self.effort()
        browser, opened = recording_browser(effort)
        env = {**browser, "CRANK_PILOT_NO_OPEN": None}
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        self.assertEqual(show(effort, QUESTIONS, scale=10, env=env), 1)
        self.assertRegex(opened.read_text(), r"\Ahttp://127\.0\.0\.1:\d+/\?t=[0-9a-f]{64}\n\Z")
        done = effort.run("show", effort.path, source, scale=10, env=env)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "2\n", ""))
        self.assertEqual(len(opened.read_text().splitlines()), 1)

    def test_a_stale_or_closing_heartbeat_does_not_count_as_a_live_page(self):
        for name, content, age in (("stale", b"", 2), ("bye", b"bye", 0)):
            with self.subTest(heartbeat=name):
                effort = self.effort()
                browser, opened = recording_browser(effort)
                heartbeat = effort.write("pilot/heartbeat", "")
                heartbeat.write_bytes(content)
                os.utime(heartbeat, (time.time() - age, time.time() - age))
                source = effort.write("interaction.json", json.dumps(QUESTIONS))
                done = effort.run("show", effort.path, source, scale=100, env={**browser, "CRANK_PILOT_NO_OPEN": None})
                with contextlib.suppress(FileNotFoundError, ValueError):
                    Client(effort)
                self.assertEqual(done.returncode, 4)
                self.assertEqual(done.stderr.strip(), "page did not open")
                self.assertEqual(len(opened.read_text().splitlines()), 1)


class ShowWaitTest(EffortCase):
    def test_show_exits_4_when_no_page_is_live_in_time_and_leaves_the_interaction_pending(self):
        effort = self.effort()
        browser, opened = recording_browser(effort)
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        started = time.time()
        done = effort.run("show", effort.path, source, scale=100, env=browser)
        elapsed = time.time() - started
        with contextlib.suppress(FileNotFoundError, ValueError):
            Client(effort)
        self.assertEqual(done.returncode, 4)
        self.assertEqual(done.stderr.strip(), "page did not open")
        self.assertEqual(done.stdout, "")
        self.assertLess(elapsed, 3)
        self.assertTrue((effort.path / "pilot" / "interactions" / "001.json").exists())
        self.assertEqual(list((effort.path / "pilot" / "responses").glob("*")), [])
        self.assertFalse(opened.exists())


if __name__ == "__main__":
    unittest.main()
