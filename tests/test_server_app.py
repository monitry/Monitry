import json
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from server import app as server_app
from server import db


def _fake_message(input_tokens, output_tokens, payload):
    return SimpleNamespace(
        content=[SimpleNamespace(text=json.dumps(payload))],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class TestServerApp(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmpdir, "test.db")
        db.init_db()
        self.client = TestClient(server_app.app)

    def tearDown(self):
        db.DB_PATH = self._orig_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_whoami_unknown_token(self):
        resp = self.client.get("/v1/whoami", params={"token": "nope"})
        self.assertEqual(resp.status_code, 401)

    def test_whoami_inactive_token(self):
        token = db.create_subscriber("a@b.com", None, None, active=False)
        resp = self.client.get("/v1/whoami", params={"token": token})
        self.assertEqual(resp.status_code, 402)

    def test_whoami_active_token(self):
        token = db.create_subscriber("a@b.com", None, None, active=True)
        resp = self.client.get("/v1/whoami", params={"token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"email": "a@b.com", "active": True})

    def test_analyze_rejects_unknown_token(self):
        resp = self.client.post("/v1/analyze", json={
            "token": "nope", "task": "work", "screenshot_b64": "abc",
        })
        self.assertEqual(resp.status_code, 401)

    def test_analyze_rejects_inactive_subscriber(self):
        token = db.create_subscriber("a@b.com", None, None, active=False)
        resp = self.client.post("/v1/analyze", json={
            "token": token, "task": "work", "screenshot_b64": "abc",
        })
        self.assertEqual(resp.status_code, 402)

    @patch("server.app._get_client")
    def test_analyze_returns_parsed_result_and_records_usage(self, mock_get_client):
        token = db.create_subscriber("a@b.com", None, None, active=True)
        payload = {"onTask": True, "interrupt": False, "activity": "coding", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(
            1_000_000, 1_000_000, payload
        )

        resp = self.client.post("/v1/analyze", json={
            "token": token, "task": "write code", "screenshot_b64": "abc",
            "model": "claude-haiku-4-5-20251001",
        })

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["onTask"], True)
        self.assertEqual(body["activity"], "coding")
        # 1M input @ $1.00/M + 1M output @ $5.00/M = $6.00
        self.assertAlmostEqual(body["cost"], 6.00, places=6)

        subscriber = db.get_subscriber(token)
        self.assertEqual(subscriber["total_input_tokens"], 1_000_000)
        self.assertEqual(subscriber["total_output_tokens"], 1_000_000)
        self.assertAlmostEqual(subscriber["total_cost"], 6.00, places=6)

    @patch("server.app._get_client")
    def test_analyze_falls_back_to_default_model_if_unknown(self, mock_get_client):
        token = db.create_subscriber("a@b.com", None, None, active=True)
        payload = {"onTask": True, "activity": "x", "reminder": "", "notes": ""}
        mock_get_client.return_value.messages.create.return_value = _fake_message(0, 0, payload)

        resp = self.client.post("/v1/analyze", json={
            "token": token, "task": "work", "screenshot_b64": "abc",
            "model": "not-a-real-model",
        })
        self.assertEqual(resp.status_code, 200)
        called_model = mock_get_client.return_value.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, server_app.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
