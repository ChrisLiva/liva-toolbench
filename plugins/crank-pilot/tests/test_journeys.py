"""The HTTP seam: what a page sees of the server `show` started."""

import datetime
import json
import contextlib
import os
import signal
import socket
import stat
import threading
import time
import unittest

from support import PLUGIN, PROTOTYPE, QUESTIONS, READBACK, Client, EffortCase, is_dead, recording_browser, show


def non_loopback_address() -> str | None:
    """This machine's outward address, read without sending a packet, or None when it has none."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


class ServerRecordTest(EffortCase):
    def test_the_server_listens_on_loopback_only_and_keeps_its_record_private(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        path = effort.path / "pilot" / "server.json"
        record = json.loads(path.read_text())
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(len(record["token"]), 64)
        int(record["token"], 16)
        socket.create_connection(("127.0.0.1", record["port"]), timeout=2).close()
        outward = non_loopback_address()
        if outward is None:
            self.skipTest("no non-loopback address to probe")
        with self.assertRaises(ConnectionRefusedError):
            socket.create_connection((outward, record["port"]), timeout=2).close()


class StateRouteTest(EffortCase):
    def test_state_reports_the_stored_interaction_and_each_call_is_a_beat(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        client = Client(effort)
        heartbeat = effort.path / "pilot" / "heartbeat"
        heartbeat.write_bytes(b"bye")
        os.utime(heartbeat, (1, 1))
        state = client.state()
        self.assertEqual(state["interaction"]["number"], 1)
        self.assertEqual(state["interaction"]["title"], "Round 1")
        self.assertEqual({key: state[key] for key in ("ended", "effort", "response", "draft", "versions", "prior")},
                         {"ended": False, "effort": effort.path.name, "response": None, "draft": None,
                          "versions": [], "prior": None})
        self.assertEqual(heartbeat.stat().st_size, 0)
        self.assertGreater(heartbeat.stat().st_mtime, time.time() - 5)

    def test_the_root_serves_the_page_file(self):
        effort = self.effort()
        show(effort, QUESTIONS)
        status, body, _ = Client(effort).request("GET", "/", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(body, (PLUGIN / "page" / "index.html").read_bytes())


class QuestionRoundJourneyTest(EffortCase):
    def test_a_round_is_drafted_submitted_once_and_read_back(self):
        effort = self.effort()
        self.assertEqual(show(effort, QUESTIONS), 1)
        client = Client(effort)
        pilot = effort.path / "pilot"
        status, _, _ = client.request("PUT", "/api/draft/1", json.dumps({"q1": {"choice": "b"}}).encode())
        self.assertEqual(status, 204)
        self.assertEqual(client.state()["draft"], {"q1": {"choice": "b"}})
        answers = [
            {"id": "q1", "accepted": False, "option": "b", "text": "", "note": "why", "attachments": []},
            {"id": "q2", "accepted": True, "option": None, "text": "", "note": "", "attachments": []},
        ]
        status, body, _ = client.request("POST", "/api/response/1", json.dumps({"answers": answers}).encode())
        self.assertEqual((status, json.loads(body)), (201, {"path": "pilot/responses/001.json"}))
        saved = json.loads((pilot / "responses" / "001.json").read_text())
        self.assertEqual({key: saved[key] for key in ("interaction", "kind", "via", "answers")},
                         {"interaction": 1, "kind": "questions", "via": "page", "answers": answers})
        datetime.datetime.fromisoformat(saved["submitted_at"])
        state = client.state()
        self.assertEqual(state["response"], {"via": "page"})
        self.assertIsNone(state["draft"])
        self.assertFalse((pilot / "drafts" / "001.json").exists())
        done = effort.run("wait", effort.path)
        self.assertEqual((done.returncode, done.stdout, done.stderr),
                         (0, f"{effort.path.resolve()}/pilot/responses/001.json\n", ""))


SPEC = "# Spec\n\n## Criteria\n\nFollows the OS within one second.\n"
MARKS = [
    {"n": 1, "type": "comment", "text": "Why a second?", "quote": "within one second", "lines": [5, 5],
     "heading": "Criteria", "occurrence": 1, "attachments": []},
    {"n": 2, "type": "note", "text": "Add a shortcut criterion.", "attachments": []},
]


class ReadbackVersionsJourneyTest(EffortCase):
    def test_a_revision_keeps_a_second_version_and_serves_the_marks_that_asked_for_it(self):
        effort = self.effort()
        spec = effort.write("spec.md", SPEC)
        kept = effort.path / "pilot" / "versions" / "spec.md"
        stored = lambda n: json.loads((effort.path / "pilot" / "interactions" / f"{n:03d}.json").read_text())
        self.assertEqual(show(effort, READBACK), 1)
        client = Client(effort)
        self.assertEqual((kept / "001.md").read_text(), SPEC)
        self.assertEqual(stored(1)["version"], 1)
        state = client.state()
        self.assertEqual((state["versions"], state["prior"]), ([1], None))
        self.assertEqual(show(effort, READBACK), 2)
        self.assertEqual(sorted(p.name for p in kept.iterdir()), ["001.md"])
        self.assertEqual(stored(2)["version"], 1)
        body = {"verdict": "changes", "version": 1, "answers": [], "marks": MARKS}
        status, _, _ = client.request("POST", "/api/response/2", json.dumps(body).encode())
        self.assertEqual(status, 201)
        revised = SPEC.replace("within one second", "at once")
        spec.write_text(revised)
        self.assertEqual(show(effort, READBACK), 3)
        self.assertEqual((kept / "002.md").read_text(), revised)
        self.assertEqual(stored(3)["version"], 2)
        state = client.state()
        self.assertEqual(state["versions"], [1, 2])
        self.assertEqual(state["prior"], {"version": 1, "marks": MARKS})

    def test_versions_are_numbered_per_artifact_file_name(self):
        effort = self.effort()
        effort.write("spec.md", SPEC)
        effort.write("plan.md", "# Plan\n")
        self.assertEqual(show(effort, READBACK), 1)
        self.assertEqual(show(effort, {**READBACK, "artifact": "plan.md"}), 2)
        client = Client(effort)
        versions = effort.path / "pilot" / "versions"
        self.assertEqual((versions / "plan.md" / "001.md").read_text(), "# Plan\n")
        self.assertEqual(sorted(p.name for p in (versions / "spec.md").iterdir()), ["001.md"])
        state = client.state()
        self.assertEqual((state["versions"], state["prior"]), ([1], None))

    def test_prior_is_the_latest_changes_response_for_the_same_artifact(self):
        effort = self.effort()
        effort.write("spec.md", SPEC)
        effort.write("plan.md", "# Plan\n")
        plan = {**READBACK, "artifact": "plan.md"}
        self.assertEqual(show(effort, READBACK), 1)
        client = Client(effort)

        def respond(n: int, verdict: str, marks: list[dict]) -> None:
            body = {"verdict": verdict, "version": 1, "answers": [], "marks": marks}
            self.assertEqual(client.request("POST", f"/api/response/{n}", json.dumps(body).encode())[0], 201)

        respond(1, "changes", MARKS)
        self.assertIsNone(client.state()["prior"])
        self.assertEqual(show(effort, plan), 2)
        respond(2, "changes", [{**MARKS[1], "n": 1}])
        self.assertEqual(show(effort, READBACK), 3)
        self.assertEqual(client.state()["prior"], {"version": 1, "marks": MARKS})
        respond(3, "approve", [])
        self.assertEqual(show(effort, READBACK), 4)
        self.assertEqual(client.state()["prior"], {"version": 1, "marks": MARKS})


VERDICT = {
    "winner": "B", "take": "nothing", "leave_out": "nothing", "attachments": [],
    "comments": [
        {"n": 1, "variant": "A", "selector": "p", "leading_text": "A", "text": "Too small.", "attachments": []},
        {"n": 1, "variant": "B", "selector": "p", "leading_text": "B", "text": "Good.", "attachments": []},
        {"n": 2, "variant": "A", "selector": "p", "leading_text": "A", "text": "Still small.", "attachments": []},
    ],
}


class PrototypeJourneyTest(EffortCase):
    def test_a_variant_is_read_from_the_effort_and_a_verdict_is_stored(self):
        effort = self.effort()
        effort.write("prototype/variant-A.html", "<p>A</p>")
        effort.write("prototype/variant-B.html", "<p>B</p>")
        self.assertEqual(show(effort, PROTOTYPE), 1)
        client = Client(effort)
        status, body, headers = client.request("GET", "/api/file/prototype/variant-A.html")
        self.assertEqual((status, body), (200, b"<p>A</p>"))
        self.assertTrue(headers["Content-Type"].startswith("text/plain"))
        status, reply, _ = client.request("POST", "/api/response/1", json.dumps(VERDICT).encode())
        self.assertEqual((status, json.loads(reply)), (201, {"path": "pilot/responses/001.json"}))
        saved = json.loads((effort.path / "pilot" / "responses" / "001.json").read_text())
        self.assertEqual({key: saved[key] for key in ("kind", "via", *VERDICT)}, {"kind": "prototype", "via": "page", **VERDICT})


DRAFT = {"q1": {"choice": "b"}}
ANSWERS = [
    {"id": "q1", "accepted": True, "option": "a", "text": "", "note": "", "attachments": []},
    {"id": "q2", "accepted": True, "option": None, "text": "", "note": "", "attachments": []},
]


class RestartAfterKillJourneyTest(EffortCase):
    def killed_with_a_draft(self):
        """An effort whose server was killed with interaction 1 pending and a draft saved; the old client, its record."""
        effort = self.effort()
        self.assertEqual(show(effort, QUESTIONS, scale=20), 1)
        client = Client(effort)
        self.assertEqual(client.request("PUT", "/api/draft/1", json.dumps(DRAFT).encode())[0], 204)
        record = json.loads((effort.path / "pilot" / "server.json").read_text())
        os.kill(record["pid"], signal.SIGKILL)
        while not is_dead(record["pid"]):
            time.sleep(0.005)
        return effort, client, record

    def restarted(self, effort, old: dict) -> dict:
        """The record once a spawned `wait` has started a new server, within a second."""
        give_up = time.time() + 1
        while time.time() < give_up:
            with contextlib.suppress(OSError, ValueError):
                record = json.loads((effort.path / "pilot" / "server.json").read_text())
                if record["pid"] != old["pid"]:
                    Client(effort)
                    return record
            time.sleep(0.01)
        self.fail("no new server record within a second")

    def test_the_next_wait_restarts_the_server_on_the_same_port_and_token_with_the_draft_intact(self):
        effort, client, old = self.killed_with_a_draft()
        waiting = effort.spawn("wait", effort.path, scale=20)
        new = self.restarted(effort, old)
        self.assertEqual((new["port"], new["token"]), (old["port"], old["token"]))
        state = client.state()
        self.assertEqual((state["interaction"]["number"], state["draft"]), (1, DRAFT))
        self.assertEqual(client.request("POST", "/api/response/1", json.dumps({"answers": ANSWERS}).encode())[0], 201)
        out, err = waiting.communicate(timeout=5)
        self.assertEqual((waiting.returncode, err), (0, ""))

    def test_a_taken_port_gets_a_new_port_and_token_with_no_heartbeat_and_the_next_show_opens_a_tab(self):
        effort, client, old = self.killed_with_a_draft()
        pilot = effort.path / "pilot"
        with socket.socket() as squatter:
            squatter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            squatter.bind(("127.0.0.1", old["port"]))
            squatter.listen()
            waiting = effort.spawn("wait", effort.path, scale=20)
            self.addCleanup(waiting.communicate)
            self.addCleanup(waiting.terminate)
            new = self.restarted(effort, old)
            self.assertNotEqual(new["port"], old["port"])
            self.assertNotEqual(new["token"], old["token"])
            self.assertFalse((pilot / "heartbeat").exists())
            fresh = Client(effort)
            client.port = new["port"]
            self.assertEqual(client.request("GET", "/api/ping")[0], 403)
            status, body, _ = fresh.request("GET", "/api/file/pilot/drafts/001.json")
            self.assertEqual((status, json.loads(body)), (200, DRAFT))
            browser, opened = recording_browser(effort)
            env = {**browser, "CRANK_PILOT_NO_OPEN": None}
            source = effort.write("interaction.json", json.dumps(QUESTIONS))
            stop = threading.Event()

            def beat_once_opened() -> None:
                while not stop.wait(0.01):
                    if opened.exists() and opened.read_text().strip():
                        with contextlib.suppress(OSError, ValueError):
                            fresh.state()

            beater = threading.Thread(target=beat_once_opened, daemon=True)
            beater.start()
            self.addCleanup(beater.join)
            self.addCleanup(stop.set)
            shown = effort.run("show", effort.path, source, scale=20, env=env)
            self.assertEqual((shown.returncode, shown.stdout, shown.stderr), (0, "2\n", ""))
            self.assertEqual(opened.read_text().splitlines(),
                             [f"http://127.0.0.1:{new['port']}/?t={new['token']}"])


if __name__ == "__main__":
    unittest.main()
