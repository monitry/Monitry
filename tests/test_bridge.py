import http.client
import json
import os
import tempfile
import unittest

from core.bridge import BridgeServer, generate_code, load_or_create_token

EXT_ORIGIN = "chrome-extension://abcdefghijklmnop"


class FakeController:
    def __init__(self):
        self.started = []
        self.stopped = 0

    def status(self):
        return {"running": bool(self.started), "status": "on_task", "task": self.started[-1][0] if self.started else ""}

    def start_task(self, task, details=""):
        self.started.append((task, details))
        return {"accepted": True}

    def stop(self):
        self.stopped += 1
        return {"accepted": True}


class TestBridge(unittest.TestCase):
    def setUp(self):
        self.controller = FakeController()
        self.server = BridgeServer(self.controller, "ABCD-EFGH", port=0)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def request(self, method, path, body=None, headers=None, host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=5)
        hdrs = {"Host": host or f"127.0.0.1:{self.server.port}"}
        hdrs.update(headers or {})
        payload = json.dumps(body).encode() if body is not None else None
        if payload is not None:
            hdrs["Content-Type"] = "application/json"
        conn.request(method, path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        data = json.loads(raw) if raw else {}
        return resp.status, data, resp

    def auth(self, extra=None):
        h = {"Origin": EXT_ORIGIN, "X-Onitry-Token": "abcd-efgh"}  # case-insensitive code
        h.update(extra or {})
        return h

    def test_ping_without_token(self):
        status, data, _ = self.request("GET", "/v1/ping", headers={"Origin": EXT_ORIGIN})
        self.assertEqual(status, 200)
        self.assertEqual(data["app"], "onitry")
        self.assertFalse(data["paired"])

    def test_ping_reports_paired_with_token(self):
        _, data, _ = self.request("GET", "/v1/ping", headers=self.auth())
        self.assertTrue(data["paired"])

    def test_status_requires_token(self):
        status, _, _ = self.request("GET", "/v1/status", headers={"Origin": EXT_ORIGIN})
        self.assertEqual(status, 401)

    def test_status_with_token_and_cors_header(self):
        status, data, resp = self.request("GET", "/v1/status", headers=self.auth())
        self.assertEqual(status, 200)
        self.assertIn("running", data)
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), EXT_ORIGIN)

    def test_web_page_origin_rejected_even_with_token(self):
        status, _, _ = self.request("GET", "/v1/status", headers=self.auth({"Origin": "https://evil.example"}))
        self.assertEqual(status, 403)

    def test_preflight_only_for_extensions(self):
        status, _, resp = self.request("OPTIONS", "/v1/task", headers={"Origin": EXT_ORIGIN})
        self.assertEqual(status, 204)
        self.assertIn("X-Onitry-Token", resp.getheader("Access-Control-Allow-Headers"))
        status, _, _ = self.request("OPTIONS", "/v1/task", headers={"Origin": "https://evil.example"})
        self.assertEqual(status, 403)

    def test_dns_rebinding_host_rejected(self):
        status, _, _ = self.request("GET", "/v1/status", headers=self.auth(), host="evil.example")
        self.assertEqual(status, 403)

    def test_start_task_and_stop(self):
        status, data, _ = self.request("POST", "/v1/task", {"task": "Calc HW", "details": "due Thu"}, self.auth())
        self.assertEqual(status, 200)
        self.assertTrue(data["accepted"])
        self.assertEqual(self.controller.started, [("Calc HW", "due Thu")])
        status, _, _ = self.request("POST", "/v1/stop", {}, self.auth())
        self.assertEqual(status, 200)
        self.assertEqual(self.controller.stopped, 1)

    def test_start_task_requires_task(self):
        status, _, _ = self.request("POST", "/v1/task", {"task": "  "}, self.auth())
        self.assertEqual(status, 400)

    def test_wrong_token_rejected(self):
        status, _, _ = self.request("POST", "/v1/task", {"task": "x"}, {"Origin": EXT_ORIGIN, "X-Onitry-Token": "NOPE-NOPE"})
        self.assertEqual(status, 401)
        self.assertEqual(self.controller.started, [])


class TestPairingCode(unittest.TestCase):
    def test_code_shape(self):
        code = generate_code()
        self.assertRegex(code, r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")

    def test_load_or_create_persists(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "bridge_token")
            first = load_or_create_token(path)
            self.assertEqual(load_or_create_token(path), first)


if __name__ == "__main__":
    unittest.main()
