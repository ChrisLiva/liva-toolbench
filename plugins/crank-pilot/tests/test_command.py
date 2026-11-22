"""The command seam: `bin/crank-pilot` run as a process."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from support import BIN, EffortCase

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


if __name__ == "__main__":
    unittest.main()
