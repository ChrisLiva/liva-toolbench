"""The command seam: `bin/crank-pilot` run as a process."""

import contextlib
import copy
import http.server
import json
import os
import re
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from support import (
    BIN,
    IMAGES,
    PROTOTYPE,
    Q1_B,
    Q2,
    QUESTIONS,
    READBACK,
    Client,
    EffortCase,
    is_dead,
    recording_browser,
    show,
)

NO_SUCH_DIR = "/nonexistent-xyz"


class MissingEffortDirectoryTest(EffortCase):
    def test_each_verb_exits_2_with_one_stderr_line(self):
        effort = self.effort()
        for args in (
            ("show", NO_SUCH_DIR, "x.json"),
            ("wait", NO_SUCH_DIR),
            ("resolve", NO_SUCH_DIR, "--chat"),
            ("close", NO_SUCH_DIR),
        ):
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
                [str(link), "wait", NO_SUCH_DIR],
                capture_output=True,
                text=True,
                env={**os.environ, "CRANK_PILOT_NO_OPEN": "1"},
            )
        self.assertEqual(done.returncode, 2)
        self.assertIn("no such effort directory", done.stderr)


class ShowRejectionTest(EffortCase):
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
                self.assertEqual(
                    list((effort.path / "pilot" / "interactions").glob("*")), []
                )
                if name == "cut off":
                    self.assertIn("not valid JSON", done.stderr)


def derived(base: dict, change) -> dict:
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
    (
        "duplicate question id",
        derived(QUESTIONS, lambda d: d["questions"][1].update(id="q1")),
        "duplicate",
    ),
    (
        "duplicate option id",
        derived(QUESTIONS, lambda d: d["questions"][0]["options"][1].update(id="a")),
        "duplicate",
    ),
    (
        "options, no recommended",
        derived(QUESTIONS, lambda d: d["questions"][0].pop("recommended")),
        "recommended",
    ),
    (
        "recommended, no options",
        derived(QUESTIONS, lambda d: d["questions"][1].update(recommended="a")),
        "options",
    ),
    (
        "recommended names no option",
        derived(QUESTIONS, lambda d: d["questions"][0].update(recommended="z")),
        "recommended",
    ),
    (
        "no recommendation",
        derived(QUESTIONS, lambda d: d["questions"][0].pop("recommendation")),
        "recommendation",
    ),
    (
        "absolute artifact",
        derived(READBACK, lambda d: d.update(artifact="/etc/hosts")),
        "artifact",
    ),
    (
        "artifact leaves the directory",
        derived(READBACK, lambda d: d.update(artifact="../spec.md")),
        "artifact",
    ),
    (
        "artifact names no file",
        derived(READBACK, lambda d: d.update(artifact="missing.md")),
        "artifact",
    ),
    (
        "artifact not markdown",
        derived(READBACK, lambda d: d.update(artifact="notes.txt")),
        ".md",
    ),
    (
        "artifact in a subdirectory",
        derived(READBACK, lambda d: d.update(artifact="sub/spec.md")),
        "artifact",
    ),
    (
        "artifact not UTF-8",
        derived(READBACK, lambda d: d.update(artifact="binary.md")),
        "UTF-8",
    ),
    (
        "artifact unreadable",
        derived(READBACK, lambda d: d.update(artifact="unreadable.md")),
        "cannot be read",
    ),
    (
        "bad decision",
        derived(READBACK, lambda d: d.update(decisions=[{"id": "d1"}])),
        "decisions[0]",
    ),
    ("absolute variant", variant_file("/etc/hosts"), "file"),
    ("variant leaves the directory", variant_file("../x.html"), "file"),
    ("variant through a symlink", variant_file("prototype/link.html"), "file"),
    ("variant names no file", variant_file("prototype/none.html"), "file"),
    ("one variant", derived(PROTOTYPE, lambda d: d["variants"].pop()), "variants"),
    (
        "duplicate variant key",
        derived(PROTOTYPE, lambda d: d["variants"][1].update(key="A")),
        "duplicate",
    ),
)


class ValidationCase(EffortCase):
    def effort_with_files(self):
        """An effort directory holding the files the fixtures name, a non-UTF-8
        binary.md, an unreadable.md with no read permission, and a symlink to a file
        outside it."""
        effort = self.effort()
        for rel in (
            "spec.md",
            "notes.txt",
            "sub/spec.md",
            "prototype/variant-A.html",
            "prototype/variant-B.html",
        ):
            effort.write(rel, "x")
        (effort.path / "binary.md").write_bytes(b"line\n\xff\xfe bad\n")
        effort.write("unreadable.md", "x").chmod(0)
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "outside.html"
        target.write_text("x")
        (effort.path / "prototype" / "link.html").symlink_to(target)
        return effort

    def run_show(self, effort, interaction: dict) -> subprocess.CompletedProcess:
        return effort.run(
            "show",
            effort.path,
            effort.write("interaction.json", json.dumps(interaction)),
        )

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
        interaction = derived(
            QUESTIONS, lambda d: (d.update(phase="execute"), d.pop("title"))
        )
        done = self.run_show(effort, interaction)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(
            len([line for line in done.stderr.splitlines() if line.strip()]), 2
        )
        self.assert_nothing_stored(effort)


class ShowTest(EffortCase):
    def test_show_stores_each_interaction_under_the_next_number_prints_it_reuses_server(
        self,
    ):
        effort = self.effort()
        record_path = effort.path / "pilot" / "server.json"
        self.assertEqual(show(effort, QUESTIONS), 1)
        stored = json.loads(
            (effort.path / "pilot" / "interactions" / "001.json").read_text()
        )
        self.assertEqual(stored, {**QUESTIONS, "number": 1})
        first = json.loads(record_path.read_text())
        hostile = {
            **QUESTIONS,
            "title": 'caf\u00e9 \u65e5\u672c \U0001f600 \ud800 "quoted" \\ \n',
        }
        self.assertEqual(show(effort, hostile), 2)
        stored = json.loads(
            (effort.path / "pilot" / "interactions" / "002.json").read_text()
        )
        self.assertEqual(stored, {**hostile, "number": 2})
        self.assertEqual(json.loads(record_path.read_text()), first)
        os.kill(first["pid"], 0)


class UnreadableRecordTest(EffortCase):
    def test_a_record_that_is_not_a_file_counts_as_no_server(self):
        effort = self.effort()
        record = effort.path / "pilot" / "server.json"
        record.mkdir(parents=True)
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        started = time.time()
        done = effort.run("show", effort.path, source)
        self.assertLess(time.time() - started, 4)
        self.assertEqual(
            (done.returncode, done.stdout, done.stderr.strip()),
            (1, "", "server did not start"),
        )
        done = effort.run("close", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertTrue(record.is_dir())


class ShowBrowserTest(EffortCase):
    def test_show_opens_the_page_only_when_none_is_live(self):
        effort = self.effort()
        browser, opened = recording_browser(effort)
        env = {**browser, "CRANK_PILOT_NO_OPEN": None}
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        self.assertEqual(show(effort, QUESTIONS, scale=10, env=env, opened=opened), 1)
        record = json.loads((effort.path / "pilot" / "server.json").read_text())
        url = opened.read_text()
        code = re.fullmatch(
            rf"http://127\.0\.0\.1:{record['port']}/\?c=([0-9a-f]{{32}})\n", url
        )
        self.assertIsNotNone(code, url)
        self.assertNotIn(record["token"], url)
        client = Client(effort)
        status, body, _ = client.request(
            "POST", "/api/session", json.dumps({"code": code[1]}).encode(), token=False
        )
        self.assertEqual((status, json.loads(body)), (200, {"token": record["token"]}))
        self.assertEqual(
            client.request(
                "POST",
                "/api/session",
                json.dumps({"code": code[1]}).encode(),
                token=False,
            )[0],
            403,
        )
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
                done = effort.run(
                    "show",
                    effort.path,
                    source,
                    scale=100,
                    env={**browser, "CRANK_PILOT_NO_OPEN": None},
                )
                with contextlib.suppress(FileNotFoundError, ValueError):
                    Client(effort)
                self.assertEqual(done.returncode, 4)
                self.assertEqual(done.stderr.strip(), "page did not open")
                self.assertEqual(len(opened.read_text().splitlines()), 1)


class ShowWaitTest(EffortCase):
    def test_show_exits_4_when_no_page_is_live_in_time_leaving_the_interaction_pending(
        self,
    ):
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


ANSWERS = json.dumps({"answers": [Q1_B, Q2]}).encode()


class WaitBoundTest(EffortCase):
    def test_wait_exits_3_at_the_bound_and_a_second_wait_resumes_the_same_interaction(
        self,
    ):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        with client.beating():
            started = time.time()
            done = effort.run("wait", effort.path, "--timeout", 20)
            elapsed = time.time() - started
            self.assertEqual(
                (done.returncode, done.stdout, done.stderr.strip()),
                (3, "", "still waiting"),
            )
            self.assertGreater(elapsed, 0.2)
            self.assertLess(elapsed, 1.5)
            self.assertEqual(
                len(list((effort.path / "pilot" / "interactions").glob("*.json"))), 1
            )
            self.assertEqual(client.request("POST", "/api/response/1", ANSWERS)[0], 201)
            done = effort.run("wait", effort.path)
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(
            len(list((effort.path / "pilot" / "interactions").glob("*.json"))), 1
        )

    def test_the_default_bound_is_540_seconds_and_outlasts_the_90_second_grace(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        with Client(effort).beating():
            started = time.time()
            done = effort.run("wait", effort.path, scale=2000)
            elapsed = time.time() - started
        self.assertEqual(
            (done.returncode, done.stdout, done.stderr.strip()),
            (3, "", "still waiting"),
        )
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
        self.assertEqual(
            (done.returncode, done.stdout, done.stderr.strip()), (4, "", "page closed")
        )
        self.assertGreater(elapsed, 0.85)
        self.assertLess(elapsed, 1.5)


class WaitClosingBeaconTest(EffortCase):
    def test_wait_exits_4_soon_after_a_closing_beacon_and_one_beat_after_it_clears_it(
        self,
    ):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        self.assertEqual(client.request("POST", "/api/bye", token=False)[0], 204)
        started = time.time()
        done = effort.run("wait", effort.path)
        self.assertEqual(
            (done.returncode, done.stdout, done.stderr.strip()), (4, "", "page closed")
        )
        self.assertLess(time.time() - started, 0.5)
        client.state()
        done = effort.run("wait", effort.path, "--timeout", 30)
        self.assertEqual((done.returncode, done.stderr.strip()), (3, "still waiting"))


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


RESPONSE_KEYS = ["interaction", "kind", "submitted_at", "via"]
RACE_DELAYS = [0.02 + 0.005 * step for step in range(10)]


def response_file(effort, number: int = 1) -> Path:
    return effort.path / "pilot" / "responses" / f"{number:03d}.json"


class SupersedeTest(EffortCase):
    def test_a_new_show_closes_the_pending_interaction_as_superseded_and_moves_state_on(
        self,
    ):
        effort = self.effort()
        self.assertEqual(show(effort, QUESTIONS), 1)
        client = Client(effort)
        self.assertEqual(show(effort, QUESTIONS), 2)
        saved = json.loads(response_file(effort).read_text())
        self.assertEqual(sorted(saved), RESPONSE_KEYS)
        self.assertEqual(
            (saved["via"], saved["interaction"], saved["kind"]),
            ("superseded", 1, "questions"),
        )
        state = client.state()
        self.assertEqual((state["interaction"]["number"], state["response"]), (2, None))
        self.assertEqual(client.request("POST", "/api/response/1", ANSWERS)[0], 409)


class ResolveChatTest(EffortCase):
    def test_resolve_chat_writes_a_chat_response_and_a_running_wait_exits_0_with_path(
        self,
    ):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        with client.beating():
            process = effort.spawn("wait", effort.path)
            time.sleep(0.2)
            self.assertIsNone(process.poll())
            done = effort.run("resolve", effort.path, "--chat")
            self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
            out, err = process.communicate(timeout=5)
        self.assertEqual(
            (process.returncode, out, err),
            (0, f"{effort.path.resolve()}/pilot/responses/001.json\n", ""),
        )
        saved = json.loads(response_file(effort).read_text())
        self.assertEqual(sorted(saved), RESPONSE_KEYS)
        self.assertEqual(
            (saved["via"], saved["interaction"], saved["kind"]),
            ("chat", 1, "questions"),
        )
        self.assertEqual(client.state()["response"], {"via": "chat"})

    def test_resolve_chat_never_replaces_an_existing_response(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        self.assertEqual(client.request("POST", "/api/response/1", ANSWERS)[0], 201)
        before = response_file(effort).read_bytes()
        done = effort.run("resolve", effort.path, "--chat")
        self.assertEqual(
            (done.returncode, done.stdout, done.stderr.strip()),
            (2, "", "nothing pending"),
        )
        self.assertEqual(response_file(effort).read_bytes(), before)


class ResolveRaceTest(EffortCase):
    def race(self, effort, client, *argv, delay: float):
        """Start the command, post a valid response `delay` seconds later; the post's
        status and the finished command."""
        process = effort.spawn(*argv)
        posted = []

        def post() -> None:
            time.sleep(delay)
            posted.append(client.request("POST", "/api/response/1", ANSWERS)[0])

        thread = threading.Thread(target=post)
        thread.start()
        out, err = process.communicate(timeout=10)
        thread.join()
        return posted[0], process.returncode, out, err

    def test_resolve_chat_and_a_page_submission_leave_one_response_and_one_winner(self):
        for delay in RACE_DELAYS:
            with self.subTest(delay=delay):
                effort = self.effort()
                show(effort, QUESTIONS)
                client = Client(effort)
                status, code, _, err = self.race(
                    effort, client, "resolve", effort.path, "--chat", delay=delay
                )
                self.assertIn((status, code), ((201, 2), (409, 0)), err)
                saved = json.loads(response_file(effort).read_text())
                self.assertEqual(saved["via"], "page" if status == 201 else "chat")
                self.assertEqual(
                    len(list(response_file(effort).parent.glob("*.json"))), 1
                )

    def test_show_treats_a_lost_supersede_race_as_an_answered_interaction(self):
        for delay in RACE_DELAYS:
            with self.subTest(delay=delay):
                effort = self.effort()
                show(effort, QUESTIONS)
                client = Client(effort)
                source = effort.write("second.json", json.dumps(QUESTIONS))
                status, code, out, err = self.race(
                    effort, client, "show", effort.path, source, delay=delay
                )
                self.assertEqual((code, out.strip()), (0, "2"), err)
                self.assertTrue(
                    (effort.path / "pilot" / "interactions" / "002.json").exists()
                )
                self.assertEqual(
                    len(list(response_file(effort).parent.glob("*.json"))), 1
                )
                saved = json.loads(response_file(effort).read_text())
                if saved["via"] == "page":
                    self.assertEqual(saved["answers"], json.loads(ANSWERS)["answers"])
                    self.assertEqual(status, 201)
                else:
                    self.assertEqual((saved["via"], status), ("superseded", 409))


class CloseTest(EffortCase):
    def test_close_ends_the_server_after_its_window_and_keeps_every_stored_file(self):
        effort = self.effort()
        pilot = effort.path / "pilot"
        effort.write("spec.md", "# Spec\n")
        self.assertEqual(show(effort, READBACK, scale=20), 1)
        client = Client(effort)
        self.assertEqual(
            client.request("POST", "/api/attachment/1", IMAGES["png"])[0], 201
        )
        approve = {"verdict": "approve", "version": 1, "answers": [], "marks": []}
        self.assertEqual(
            client.request("POST", "/api/response/1", json.dumps(approve).encode())[0],
            201,
        )
        self.assertEqual(show(effort, QUESTIONS, scale=20), 2)
        draft = json.dumps({"q1": {"choice": "b"}}).encode()
        self.assertEqual(client.request("PUT", "/api/draft/2", draft)[0], 204)
        pid = json.loads((pilot / "server.json").read_text())["pid"]
        done = effort.run("close", effort.path, scale=20)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertTrue(client.state()["ended"])
        with client.beating(0.001):
            time.sleep(0.6)
        self.assertTrue(is_dead(pid))
        for gone in ("server.json", "heartbeat"):
            self.assertFalse((pilot / gone).exists(), gone)
        for kept in (
            "interactions/001.json",
            "interactions/002.json",
            "responses/001.json",
            "versions/spec.md/001.md",
            "attachments/001-1.png",
            "drafts/002.json",
        ):
            self.assertTrue((pilot / kept).exists(), kept)

    def test_close_removes_the_record_of_a_server_that_was_killed(self):
        effort = self.effort()
        self.assertEqual(show(effort, QUESTIONS), 1)
        record = effort.path / "pilot" / "server.json"
        os.kill(json.loads(record.read_text())["pid"], signal.SIGKILL)
        done = effort.run("close", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertFalse(record.exists())


class CloseWindowTest(EffortCase):
    def test_a_show_during_the_window_waits_for_the_record_to_go_and_starts_a_server(
        self,
    ):
        effort = self.effort()
        show(effort, QUESTIONS, scale=20)
        Client(effort)
        record = effort.path / "pilot" / "server.json"
        old = json.loads(record.read_text())["pid"]
        stop = threading.Event()

        def beat() -> None:
            while not stop.is_set():
                with contextlib.suppress(OSError, ValueError):
                    Client(effort).state()
                stop.wait(0.02)

        beater = threading.Thread(target=beat, daemon=True)
        beater.start()
        self.addCleanup(beater.join)
        self.addCleanup(stop.set)
        self.assertEqual(effort.run("close", effort.path, scale=20).returncode, 0)
        time.sleep(0.05)
        source = effort.write("interaction.json", json.dumps(QUESTIONS))
        done = effort.spawn("show", effort.path, source, scale=20)
        out, err = done.communicate(timeout=10)
        self.assertEqual((done.returncode, out, err), (0, "2\n", ""))
        self.assertNotEqual(json.loads(record.read_text())["pid"], old)


class SecondCloseTest(EffortCase):
    def test_a_second_close_partway_through_the_window_does_not_move_the_exit_later(
        self,
    ):
        effort = self.effort()
        show(effort, QUESTIONS, scale=10)
        client = Client(effort)
        pid = json.loads((effort.path / "pilot" / "server.json").read_text())["pid"]
        self.assertEqual(effort.run("close", effort.path, scale=10).returncode, 0)
        closed = time.time()
        time.sleep(0.35)
        self.assertEqual(client.request("POST", "/api/close", b"")[0], 202)
        while not is_dead(pid) and time.time() - closed < 2:
            time.sleep(0.01)
        self.assertLessEqual(time.time() - closed, 0.75)
        self.assertTrue(is_dead(pid))


class SelfExitTest(EffortCase):
    def test_the_server_exits_when_its_record_is_gone_or_names_another_process(self):
        gone = self.effort()
        process = gone.start_server(100)
        (gone.path / "pilot" / "server.json").unlink()
        self.assertEqual(process.wait(timeout=0.5), 0)
        other = self.effort()
        process = other.start_server(100)
        record = other.path / "pilot" / "server.json"
        rewritten = json.dumps({**json.loads(record.read_text()), "pid": 1})
        record.write_text(rewritten)
        self.assertEqual(process.wait(timeout=0.5), 0)
        self.assertEqual(record.read_text(), rewritten)
        done = other.run("close", other.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertFalse(record.exists())


class ForeignPidListener:
    """A stdlib server that answers `GET /api/ping` as pid 1 and records every POST it
    receives."""

    def __init__(self) -> None:
        self.posts: list[str] = []
        posts = self.posts

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                body = json.dumps({"pid": 1}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:
                posts.append(self.path)
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args) -> None:
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()


class ForeignPidTest(EffortCase):
    def test_close_sends_nothing_to_a_recorded_pid_the_os_refuses_to_signal(self):
        try:
            os.kill(1, 0)
        except PermissionError:
            pass
        except OSError:
            self.skipTest("pid 1 is not another user's process here")
        else:
            self.skipTest("pid 1 is signalable here")
        effort = self.effort()
        listener = ForeignPidListener()
        self.addCleanup(listener.stop)
        record = effort.write(
            "pilot/server.json",
            json.dumps({"pid": 1, "port": listener.port, "token": "t"}),
        )
        done = effort.run("close", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, "", ""))
        self.assertFalse(record.exists())
        self.assertEqual(listener.posts, [])


class IdleExitTest(EffortCase):
    def test_server_stays_up_on_beats_exits_30_scaled_minutes_after_last_keeps_record(
        self,
    ):
        effort = self.effort()
        process = effort.start_server(3600)
        client = Client(effort)
        with client.beating(0.1):
            time.sleep(1.2)
            self.assertIsNone(process.poll())
        client.state()
        last = time.time()
        self.assertEqual(process.wait(timeout=1.5), 0)
        self.assertGreater(time.time() - last, 0.4)
        self.assertTrue((effort.path / "pilot" / "server.json").exists())


if __name__ == "__main__":
    unittest.main()
