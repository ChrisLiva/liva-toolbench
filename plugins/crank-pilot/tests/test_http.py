"""The HTTP seam: what the server answers a page that drafts and submits a round."""

import json
import threading
import unittest

from support import QUESTIONS, Client, Effort, EffortCase, show

Q1_B = {"id": "q1", "accepted": False, "option": "b", "text": "", "note": "", "attachments": []}
Q1_A = {"id": "q1", "accepted": True, "option": "a", "text": "", "note": "", "attachments": []}
Q2 = {"id": "q2", "accepted": True, "option": None, "text": "", "note": "", "attachments": []}


def send(client: Client, method: str, path: str, payload: object) -> tuple[int, object]:
    status, body, _ = client.request(method, path, json.dumps(payload).encode())
    return status, (json.loads(body) if body else None)


class HttpCase(EffortCase):
    def round(self) -> tuple[Effort, Client]:
        """An effort with interaction 1 pending and a client for its server."""
        effort = self.effort()
        show(effort, QUESTIONS)
        return effort, Client(effort)

    def response_file(self, effort: Effort, number: int = 1):
        return effort.path / "pilot" / "responses" / f"{number:03d}.json"


class NotPendingTest(HttpCase):
    def test_a_draft_or_response_for_an_interaction_that_is_not_pending_gets_409_and_writes_nothing(self):
        effort, client = self.round()
        self.assertEqual(send(client, "POST", "/api/response/1", {"answers": [Q1_A, Q2]})[0], 201)
        self.assertEqual(show(effort, QUESTIONS), 2)
        pilot = effort.path / "pilot"
        before = sorted(str(p.relative_to(pilot)) for p in pilot.rglob("*") if p.name not in ("heartbeat",))
        for method, path in (("POST", "/api/response/1"), ("POST", "/api/response/7"), ("PUT", "/api/draft/1")):
            with self.subTest(path=path):
                self.assertEqual(send(client, method, path, {"answers": [Q1_B, Q2]})[0], 409)
        after = sorted(str(p.relative_to(pilot)) for p in pilot.rglob("*") if p.name not in ("heartbeat",))
        self.assertEqual(after, before)
        self.assertEqual(json.loads(self.response_file(effort).read_text())["answers"], [Q1_A, Q2])


class SubmitOnceTest(HttpCase):
    def test_two_submissions_at_once_produce_one_response_file(self):
        effort, client = self.round()
        bodies = [{"answers": [Q1_A, Q2]}, {"answers": [Q1_B, Q2]}]
        barrier = threading.Barrier(2)
        results: list[tuple[int, dict]] = []

        def post(body: dict) -> None:
            barrier.wait()
            results.append((send(client, "POST", "/api/response/1", body)[0], body))

        threads = [threading.Thread(target=post, args=(body,)) for body in bodies]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(status for status, _ in results), [201, 409])
        winner = next(body for status, body in results if status == 201)
        self.assertEqual(json.loads(self.response_file(effort).read_text())["answers"], winner["answers"])
        self.assertEqual(send(client, "POST", "/api/response/1", bodies[0])[0], 409)
        self.assertEqual([p.name for p in self.response_file(effort).parent.iterdir()], ["001.json"])


class InvalidResponseTest(HttpCase):
    def test_a_response_that_fails_validation_gets_400_with_problems_and_writes_nothing(self):
        effort, client = self.round()
        (effort.path / "pilot" / "attachments").mkdir(parents=True, exist_ok=True)
        cases = {
            "not an object": [1],
            "answers missing": {},
            "unknown id": {"answers": [Q1_A, Q2, {**Q2, "id": "q9"}]},
            "no answer for q2": {"answers": [Q1_A]},
            "option not offered": {"answers": [{**Q1_A, "option": "z"}, Q2]},
            "option on a question with none": {"answers": [Q1_A, {**Q2, "option": "a"}]},
            "accepted with another option": {"answers": [{**Q1_B, "accepted": True}, Q2]},
            "own answer with empty text": {"answers": [{**Q1_A, "accepted": False, "option": None, "text": ""}, Q2]},
            "note not a string": {"answers": [{**Q1_A, "note": 3}, Q2]},
            "attachment absent": {"answers": [{**Q1_A, "attachments": ["pilot/attachments/001-1.png"]}, Q2]},
            "attachment is not an image of this interaction":
                {"answers": [{**Q1_A, "attachments": ["pilot/attachments/../server.json"]}, Q2]},
            "accepted contradicts the rule": {"answers": [Q1_A, {**Q2, "accepted": True, "text": "x"}]},
        }
        for name, body in cases.items():
            with self.subTest(name):
                status, reply = send(client, "POST", "/api/response/1", body)
                self.assertEqual(status, 400)
                self.assertTrue(reply["problems"])
                self.assertFalse(self.response_file(effort).exists())

    def test_accepted_follows_the_rule_so_an_own_text_on_a_question_with_no_options_is_not_accepted(self):
        effort, client = self.round()
        own_text = {**Q2, "accepted": False, "text": "x"}
        for name, answers in {"empty text not accepted": [Q1_A, {**Q2, "accepted": False}],
                              "recommended option not accepted": [{**Q1_A, "accepted": False}, Q2]}.items():
            with self.subTest(name):
                self.assertEqual(send(client, "POST", "/api/response/1", {"answers": answers})[0], 400)
        self.assertEqual(send(client, "POST", "/api/response/1", {"answers": [Q1_A, {**own_text, "accepted": True}]})[0], 400)
        self.assertEqual(send(client, "POST", "/api/response/1", {"answers": [Q1_A, own_text]})[0], 201)
        self.assertEqual(json.loads(self.response_file(effort).read_text())["answers"][1], own_text)


class DraftTest(HttpCase):
    def test_a_draft_that_is_not_a_json_object_gets_400(self):
        effort, client = self.round()
        self.assertEqual(send(client, "PUT", "/api/draft/1", [1])[0], 400)
        self.assertFalse((effort.path / "pilot" / "drafts" / "001.json").exists())


if __name__ == "__main__":
    unittest.main()
