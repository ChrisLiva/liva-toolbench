"""The command seam: `bin/crank-pilot` run as a process."""

import contextlib
import copy
import json
import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from support import BIN, PROTOTYPE, QUESTIONS, READBACK, Client, EffortCase, show

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


def derived(base: dict, change) -> dict:
    """A copy of a fixture with `change` applied to it."""
    copy_ = copy.deepcopy(base)
    change(copy_)
    return copy_


def variant_file(name: str) -> dict:
    return derived(PROTOTYPE, lambda d: d["variants"][0].update(file=name))


REJECTED = (
    ("unknown kind", derived(QUESTIONS, lambda d: d.update(kind="poll")), "kind"),
    ("bad phase", derived(QUESTIONS, lambda d: d.update(phase="execute")), "phase"),
    ("missing field", derived(QUESTIONS, lambda d: d.pop("title")), "title"),
    ("wrong type", derived(QUESTIONS, lambda d: d.update(questions="q1")), "questions"),
    ("wrong agenda type", derived(QUESTIONS, lambda d: d.update(agenda=[])), "agenda"),
    ("duplicate question id", derived(QUESTIONS, lambda d: d["questions"][1].update(id="q1")), "duplicate"),
    ("duplicate option id", derived(QUESTIONS, lambda d: d["questions"][0]["options"][1].update(id="a")), "duplicate"),
    ("options, no recommended", derived(QUESTIONS, lambda d: d["questions"][0].pop("recommended")), "recommended"),
    ("recommended, no options", derived(QUESTIONS, lambda d: d["questions"][1].update(recommended="a")), "options"),
    ("recommended names no option", derived(QUESTIONS, lambda d: d["questions"][0].update(recommended="z")), "recommended"),
    ("no recommendation", derived(QUESTIONS, lambda d: d["questions"][0].pop("recommendation")), "recommendation"),
    ("absolute artifact", derived(READBACK, lambda d: d.update(artifact="/etc/hosts")), "artifact"),
    ("artifact leaves the directory", derived(READBACK, lambda d: d.update(artifact="../spec.md")), "artifact"),
    ("artifact names no file", derived(READBACK, lambda d: d.update(artifact="missing.md")), "artifact"),
    ("artifact not markdown", derived(READBACK, lambda d: d.update(artifact="notes.txt")), ".md"),
    ("artifact in a subdirectory", derived(READBACK, lambda d: d.update(artifact="sub/spec.md")), "artifact"),
    ("bad decision", derived(READBACK, lambda d: d.update(decisions=[{"id": "d1"}])), "decisions[0]"),
    ("absolute variant", variant_file("/etc/hosts"), "file"),
    ("variant leaves the directory", variant_file("../x.html"), "file"),
    ("variant through a symlink", variant_file("prototype/link.html"), "file"),
    ("variant names no file", variant_file("prototype/none.html"), "file"),
    ("one variant", derived(PROTOTYPE, lambda d: d["variants"].pop()), "variants"),
    ("duplicate variant key", derived(PROTOTYPE, lambda d: d["variants"][1].update(key="A")), "duplicate"),
)


class ValidationCase(EffortCase):
    def effort_with_files(self):
        """An effort directory holding the files the fixtures name, plus a symlink to a file outside it."""
        effort = self.effort()
        for rel in ("spec.md", "notes.txt", "sub/spec.md", "prototype/variant-A.html", "prototype/variant-B.html"):
            effort.write(rel, "x")
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "outside.html"
        target.write_text("x")
        (effort.path / "prototype" / "link.html").symlink_to(target)
        return effort

    def run_show(self, effort, interaction: dict) -> subprocess.CompletedProcess:
        return effort.run("show", effort.path, effort.write("interaction.json", json.dumps(interaction)))

    def assert_nothing_stored(self, effort) -> None:
        self.assertEqual(list((effort.path / "pilot" / "interactions").glob("*")), [])
        self.assertFalse((effort.path / "pilot" / "server.json").exists())


class ShowValidationTest(ValidationCase):
    def test_show_rejects_each_invalid_interaction_with_exit_2_and_stores_nothing(self):
        effort = self.effort_with_files()
        for name, interaction, keyword in REJECTED:
            with self.subTest(case=name):
                done = self.run_show(effort, interaction)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, "")
                self.assertIn(keyword, done.stderr)
                self.assert_nothing_stored(effort)

    def test_a_file_with_two_problems_prints_two_lines(self):
        effort = self.effort_with_files()
        interaction = derived(QUESTIONS, lambda d: (d.update(phase="execute"), d.pop("title")))
        done = self.run_show(effort, interaction)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(len([line for line in done.stderr.splitlines() if line.strip()]), 2)
        self.assert_nothing_stored(effort)

    def test_each_fixture_is_accepted_as_written(self):
        effort = self.effort_with_files()
        self.assertEqual([show(effort, item) for item in (QUESTIONS, READBACK, PROTOTYPE)], [1, 2, 3])


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


ANSWERS = json.dumps({"answers": [
    {"id": "q1", "accepted": False, "option": "b", "text": "", "note": "", "attachments": []},
    {"id": "q2", "accepted": True, "option": None, "text": "", "note": "", "attachments": []},
]}).encode()


class WaitResponseTest(EffortCase):
    def test_wait_prints_the_response_path_when_it_arrives_while_waiting(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        with client.beating():
            process = effort.spawn("wait", effort.path)
            time.sleep(0.2)
            self.assertIsNone(process.poll())
            self.assertEqual(client.request("POST", "/api/response/1", ANSWERS)[0], 201)
            out, err = process.communicate(timeout=5)
        self.assertEqual((process.returncode, out, err), (0, f"{effort.path.resolve()}/pilot/responses/001.json\n", ""))


class WaitBoundTest(EffortCase):
    def test_wait_exits_3_at_the_bound_and_a_second_wait_resumes_the_same_interaction(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        with client.beating():
            started = time.time()
            done = effort.run("wait", effort.path, "--timeout", 20)
            elapsed = time.time() - started
            self.assertEqual((done.returncode, done.stdout, done.stderr.strip()), (3, "", "still waiting"))
            self.assertGreater(elapsed, 0.2)
            self.assertLess(elapsed, 1.5)
            self.assertEqual(len(list((effort.path / "pilot" / "interactions").glob("*.json"))), 1)
            self.assertEqual(client.request("POST", "/api/response/1", ANSWERS)[0], 201)
            done = effort.run("wait", effort.path)
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(len(list((effort.path / "pilot" / "interactions").glob("*.json"))), 1)

    def test_the_default_bound_is_540_seconds_and_outlasts_the_90_second_grace(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        with Client(effort).beating():
            started = time.time()
            done = effort.run("wait", effort.path, scale=2000)
            elapsed = time.time() - started
        self.assertEqual((done.returncode, done.stdout, done.stderr.strip()), (3, "", "still waiting"))
        self.assertGreater(elapsed, 0.27)
        self.assertLess(elapsed, 1.5)


class WaitClosedPageTest(EffortCase):
    def test_wait_exits_4_when_90_scaled_seconds_pass_with_no_heartbeat(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        Client(effort)
        heartbeat = effort.path / "pilot" / "heartbeat"
        os.utime(heartbeat, (time.time() - 2, time.time() - 2))
        started = time.time()
        done = effort.run("wait", effort.path)
        elapsed = time.time() - started
        self.assertEqual((done.returncode, done.stdout, done.stderr.strip()), (4, "", "page closed"))
        self.assertGreater(elapsed, 0.85)
        self.assertLess(elapsed, 1.5)


class WaitClosingBeaconTest(EffortCase):
    def test_wait_exits_4_after_a_closing_beacon_with_no_beat_following_it(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        self.assertEqual(client.request("POST", "/api/bye", token=False)[0], 204)
        self.assertEqual((effort.path / "pilot" / "heartbeat").read_bytes(), b"bye")
        started = time.time()
        done = effort.run("wait", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr.strip()), (4, "", "page closed"))
        self.assertLess(time.time() - started, 0.5)

    def test_a_beat_after_the_closing_beacon_clears_it(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        self.assertEqual(client.request("POST", "/api/bye", token=False)[0], 204)
        client.state()
        self.assertEqual((effort.path / "pilot" / "heartbeat").stat().st_size, 0)
        with client.beating():
            done = effort.run("wait", effort.path, "--timeout", 30)
        self.assertEqual((done.returncode, done.stderr.strip()), (3, "still waiting"))


class WaitContactTest(EffortCase):
    def test_wait_polls_touch_the_contact_file(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        contact = effort.path / "pilot" / "contact"
        contact.unlink(missing_ok=True)
        with Client(effort).beating():
            done = effort.run("wait", effort.path, "--timeout", 20)
        self.assertEqual((done.returncode, done.stderr.strip()), (3, "still waiting"))
        self.assertTrue(contact.exists())


class WaitSuspendTest(EffortCase):
    def test_a_suspend_restarts_the_90_second_count(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        Client(effort)
        contact = effort.path / "pilot" / "contact"
        contact.unlink(missing_ok=True)
        process = effort.spawn("wait", effort.path)
        give_up = time.time() + 5
        while not contact.exists() and time.time() < give_up:
            time.sleep(0.01)
        os.kill(process.pid, signal.SIGSTOP)
        time.sleep(1.2)
        os.kill(process.pid, signal.SIGCONT)
        resumed = time.time()
        out, err = process.communicate(timeout=5)
        self.assertEqual((process.returncode, out, err.strip()), (4, "", "page closed"))
        self.assertGreater(time.time() - resumed, 0.85)


if __name__ == "__main__":
    unittest.main()
