import os
import shutil
import tempfile
import unittest

from server import db


class TestServerDB(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmpdir, "test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self._orig_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_unknown_token_returns_none(self):
        self.assertIsNone(db.get_subscriber("nope"))

    def test_create_and_fetch_subscriber(self):
        token = db.create_subscriber("a@b.com", "cus_1", "sub_1", active=True)
        subscriber = db.get_subscriber(token)
        self.assertIsNotNone(subscriber)
        self.assertEqual(subscriber["email"], "a@b.com")
        self.assertEqual(subscriber["active"], 1)
        self.assertEqual(subscriber["total_cost"], 0.0)

    def test_created_inactive_when_requested(self):
        token = db.create_subscriber("a@b.com", "cus_1", "sub_1", active=False)
        subscriber = db.get_subscriber(token)
        self.assertEqual(subscriber["active"], 0)

    def test_set_active_by_subscription(self):
        token = db.create_subscriber("a@b.com", "cus_1", "sub_1", active=True)
        db.set_active_by_subscription("sub_1", False)
        self.assertEqual(db.get_subscriber(token)["active"], 0)
        db.set_active_by_subscription("sub_1", True)
        self.assertEqual(db.get_subscriber(token)["active"], 1)

    def test_set_active_by_token(self):
        token = db.create_subscriber("a@b.com", None, None, active=True)
        found = db.set_active_by_token(token, False)
        self.assertTrue(found)
        self.assertEqual(db.get_subscriber(token)["active"], 0)

    def test_set_active_by_token_unknown_returns_false(self):
        self.assertFalse(db.set_active_by_token("nonexistent", True))

    def test_record_usage_accumulates(self):
        token = db.create_subscriber("a@b.com", "cus_1", "sub_1", active=True)
        db.record_usage(token, 1000, 500, 0.01)
        db.record_usage(token, 2000, 1000, 0.02)
        subscriber = db.get_subscriber(token)
        self.assertEqual(subscriber["total_input_tokens"], 3000)
        self.assertEqual(subscriber["total_output_tokens"], 1500)
        self.assertAlmostEqual(subscriber["total_cost"], 0.03, places=6)

    def test_tokens_are_unique(self):
        tokens = {db.create_subscriber(f"{i}@b.com", None, None) for i in range(20)}
        self.assertEqual(len(tokens), 20)


if __name__ == "__main__":
    unittest.main()
