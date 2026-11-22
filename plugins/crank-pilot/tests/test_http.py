"""The HTTP seam: what the server answers a page that drafts and submits a round."""

import json
import threading
import unittest

from support import PROTOTYPE, QUESTIONS, READBACK, Client, Effort, EffortCase, show

Q1_B = {"id": "q1", "accepted": False, "option": "b", "text": "", "note": "", "attachments": []}
Q1_A = {"id": "q1", "accepted": True, "option": "a", "text": "", "note": "", "attachments": []}
Q2 = {"id": "q2", "accepted": True, "option": None, "text": "", "note": "", "attachments": []}


def send(client: Client, method: str, path: str, payload: object) -> tuple[int, object]:
    status, body, _ = client.request(method, path, json.dumps(payload).encode())
    return status, (json.loads(body) if body else None)

SPEC = "# Spec\n\n## Criteria\n\nFollows the OS within one second.\n"
COMMENT = {"n": 1, "type": "comment", "text": "Why a second?", "quote": "within one second", "lines": [5, 5],
           "heading": "Criteria", "occurrence": 1, "attachments": []}
NOTE = {"n": 2, "type": "note", "text": "Add a shortcut criterion.", "attachments": []}
CHANGES = {"verdict": "changes", "version": 1, "answers": [], "marks": [COMMENT, NOTE]}


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


class ReadbackHttpCase(HttpCase):
    def readback(self, interaction: dict = READBACK) -> tuple[Effort, Client]:
        """An effort whose pending interaction 1 is a readback of the 5-line spec, kept as version 1."""
        effort = self.effort()
        effort.write("spec.md", SPEC)
        show(effort, interaction)
        return effort, Client(effort)


class InvalidReadbackResponseTest(ReadbackHttpCase):
    def test_a_readback_response_that_fails_validation_gets_400_and_writes_nothing(self):
        effort, client = self.readback()
        strike = {**COMMENT, "type": "strike", "text": ""}
        cases = {
            "verdict not offered": {**CHANGES, "verdict": "maybe"},
            "version not the one shown": {**CHANGES, "version": 9},
            "approve with marks": {**CHANGES, "verdict": "approve"},
            "mark type not offered": {**CHANGES, "marks": [{**COMMENT, "type": "highlight"}, NOTE]},
            "comment without text": {**CHANGES, "marks": [{**COMMENT, "text": ""}, NOTE]},
            "strike without quote": {**CHANGES, "marks": [{k: v for k, v in strike.items() if k != "quote"}, NOTE]},
            "lines start at zero": {**CHANGES, "marks": [{**COMMENT, "lines": [0, 1]}, NOTE]},
            "lines run backwards": {**CHANGES, "marks": [{**COMMENT, "lines": [5, 4]}, NOTE]},
            "lines past the version": {**CHANGES, "marks": [{**COMMENT, "lines": [5, 99]}, NOTE]},
            "occurrence below one": {**CHANGES, "marks": [{**COMMENT, "occurrence": 0}, NOTE]},
            "marks numbered with a gap": {**CHANGES, "marks": [COMMENT, {**NOTE, "n": 3}]},
            "note carrying a quote": {**CHANGES, "marks": [COMMENT, {**NOTE, "quote": "within one second"}]},
        }
        for name, body in cases.items():
            with self.subTest(name):
                status, reply = send(client, "POST", "/api/response/1", body)
                self.assertEqual(status, 400)
                self.assertTrue(reply["problems"])
                self.assertFalse(self.response_file(effort).exists())
        self.assertEqual(send(client, "POST", "/api/response/1", CHANGES)[0], 201)


class ReadbackAcceptedTest(ReadbackHttpCase):
    def test_a_strike_needs_no_text(self):
        effort, client = self.readback()
        strike = {**COMMENT, "type": "strike", "text": ""}
        self.assertEqual(send(client, "POST", "/api/response/1", {**CHANGES, "marks": [strike]})[0], 201)
        self.assertEqual(json.loads(self.response_file(effort).read_text())["marks"], [strike])

    def test_an_approve_with_empty_marks_answers_an_open_decision_as_a_question_does(self):
        effort, client = self.readback({**READBACK, "decisions": [QUESTIONS["questions"][0]]})
        q1 = {"id": "q1", "accepted": True, "option": "a", "text": "", "note": "", "attachments": []}
        approve = {"verdict": "approve", "version": 1, "answers": [q1], "marks": []}
        self.assertEqual(send(client, "POST", "/api/response/1", {**approve, "answers": []})[0], 400)
        self.assertEqual(send(client, "POST", "/api/response/1", {**approve, "answers": [{**q1, "accepted": False}]})[0], 400)
        self.assertFalse(self.response_file(effort).exists())
        self.assertEqual(send(client, "POST", "/api/response/1", approve)[0], 201)
        self.assertEqual(json.loads(self.response_file(effort).read_text())["answers"], [q1])


class InvalidVerdictTest(HttpCase):
    def test_a_prototype_verdict_that_fails_validation_gets_400_and_writes_nothing(self):
        effort = self.effort()
        effort.write("prototype/variant-A.html", "<p>A</p>")
        effort.write("prototype/variant-B.html", "<p>B</p>")
        show(effort, PROTOTYPE)
        client = Client(effort)
        a1 = {"n": 1, "variant": "A", "selector": "p", "leading_text": "A", "text": "Too small.", "attachments": []}
        b1 = {"n": 1, "variant": "B", "selector": "p", "leading_text": "B", "text": "Good.", "attachments": []}
        a2 = {**a1, "n": 2, "text": "Still small."}
        verdict = {"winner": "B", "take": "nothing", "leave_out": "nothing", "attachments": [], "comments": [a1, b1, a2]}
        cases = {
            "winner not a variant": {**verdict, "winner": "Z"},
            "winner missing": {k: v for k, v in verdict.items() if k != "winner"},
            "winner not a string": {**verdict, "winner": ["B"]},
            "comments missing": {k: v for k, v in verdict.items() if k != "comments"},
            "take empty": {**verdict, "take": ""},
            "leave_out not a string": {**verdict, "leave_out": 3},
            "comment on no variant": {**verdict, "comments": [{**a1, "variant": "Z"}, b1, a2]},
            "extra comment on no variant": {**verdict, "comments": [a1, b1, a2, {**a1, "variant": "Z"}]},
            "comment without text": {**verdict, "comments": [{**a1, "text": ""}, b1, a2]},
            "comment without selector": {**verdict, "comments": [{**a1, "selector": ""}, b1, a2]},
            "variant A numbered with a gap": {**verdict, "comments": [a1, b1, {**a2, "n": 3}]},
        }
        for name, body in cases.items():
            with self.subTest(name):
                status, reply = send(client, "POST", "/api/response/1", body)
                self.assertEqual(status, 400)
                self.assertTrue(reply["problems"])
                self.assertFalse(self.response_file(effort).exists())
        self.assertEqual(send(client, "POST", "/api/response/1", verdict)[0], 201)


class FileRoutesTest(HttpCase):
    def test_only_the_page_files_and_the_effort_directory_are_served(self):
        effort = self.effort()
        effort.write("prototype/variant-A.html", "<p>A</p>")
        effort.write("prototype/variant-B.html", "<p>B</p>")
        effort.write("notes/two words.md", "ok")
        outside = effort.path.parent / "outside.txt"
        outside.write_text("secret")
        self.addCleanup(outside.unlink, missing_ok=True)
        (effort.path / "link.txt").symlink_to(outside)
        show(effort, PROTOTYPE)
        client = Client(effort)

        def raw_get(path: str) -> int:
            request = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{client.port}\r\nX-Pilot-Token: {client.token}\r\n\r\n"
            return client.raw(request.encode())[0]

        refused = {
            "dot-dot sent raw": lambda: raw_get("/api/file/../outside.txt"),
            "encoded dot-dot": lambda: client.request("GET", "/api/file/%2e%2e/outside.txt")[0],
            "absolute path": lambda: client.request("GET", "/api/file//etc/hosts")[0],
            "symlink out of the effort": lambda: client.request("GET", "/api/file/link.txt")[0],
            "a directory": lambda: client.request("GET", "/api/file/prototype")[0],
            "a missing file": lambda: client.request("GET", "/api/file/missing.md")[0],
            "page dot-dot sent raw": lambda: raw_get("/page/../pilot/cli.py"),
            "page encoded dot-dot": lambda: client.request("GET", "/page/%2e%2e/bin/crank-pilot")[0],
            "a missing page file": lambda: client.request("GET", "/page/none.js")[0],
        }
        for name, get in refused.items():
            with self.subTest(name):
                self.assertEqual(get(), 404)
        self.assertEqual(client.request("GET", "/page/index.html", token=False)[0], 200)
        self.assertEqual(client.request("GET", "/api/file/notes/two%20words.md")[:2], (200, b"ok"))


class ContentTypeTest(HttpCase):
    def test_a_file_is_typed_by_its_extension(self):
        effort = self.effort()
        names = ["note.md", "view.html", "a.png", "a.jpg", "a.jpeg", "a.gif", "a.webp", "blob.bin"]
        for name in names:
            effort.write(f"files/{name}", "x")
        show(effort, QUESTIONS)
        client = Client(effort)
        expected = {"note.md": "text/plain; charset=utf-8", "view.html": "text/plain; charset=utf-8",
                    "a.png": "image/png", "a.jpg": "image/jpeg", "a.jpeg": "image/jpeg", "a.gif": "image/gif",
                    "a.webp": "image/webp", "blob.bin": "application/octet-stream"}
        for name in names:
            with self.subTest(name):
                status, _, headers = client.request("GET", f"/api/file/files/{name}")
                self.assertEqual((status, headers["Content-Type"]), (200, expected[name]))
        _, _, headers = client.request("GET", "/page/index.html", token=False)
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")


class DraftTest(HttpCase):
    def test_a_draft_that_is_not_a_json_object_gets_400(self):
        effort, client = self.round()
        self.assertEqual(send(client, "PUT", "/api/draft/1", [1])[0], 400)
        self.assertFalse((effort.path / "pilot" / "drafts" / "001.json").exists())


if __name__ == "__main__":
    unittest.main()
