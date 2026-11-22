"""The HTTP seam: what a page sees of the server `show` started."""

import datetime
import json
import os
import socket
import stat
import time
import unittest

from support import PLUGIN, QUESTIONS, Client, EffortCase, show


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


if __name__ == "__main__":
    unittest.main()
