import unittest
from unittest.mock import patch

from server import admin, db


class TestAdminCLI(unittest.TestCase):
    """This CLI is the only support tool for subscribers until email delivery is
    wired up (see server/README.md's "What's NOT done yet"), so a wiring bug here
    (wrong db function called for a subcommand) directly blocks support requests."""

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.get_subscriber")
    def test_lookup_found(self, mock_get, mock_init):
        mock_get.return_value = {"token": "onitry_abc", "plan": "byok"}
        with patch("sys.argv", ["admin.py", "lookup", "onitry_abc"]):
            admin.main()
        mock_get.assert_called_once_with("onitry_abc")

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.get_subscriber")
    def test_lookup_not_found_does_not_raise(self, mock_get, mock_init):
        mock_get.return_value = None
        with patch("sys.argv", ["admin.py", "lookup", "nope"]):
            admin.main()  # should print a message, not crash

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.create_manual")
    def test_issue_defaults_to_byok_and_active(self, mock_create, mock_init):
        mock_create.return_value = "onitry_newtoken"
        with patch("sys.argv", ["admin.py", "issue", "user@example.com"]):
            admin.main()
        mock_create.assert_called_once_with(email="user@example.com", plan=db.PLAN_BYOK, active=True)

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.create_manual")
    def test_issue_inactive_flag(self, mock_create, mock_init):
        mock_create.return_value = "onitry_newtoken"
        with patch("sys.argv", ["admin.py", "issue", "user@example.com", "--plan", "managed_paid", "--inactive"]):
            admin.main()
        mock_create.assert_called_once_with(email="user@example.com", plan=db.PLAN_PAID, active=False)

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.set_active_by_token")
    def test_deactivate_calls_set_active_false(self, mock_set, mock_init):
        mock_set.return_value = True
        with patch("sys.argv", ["admin.py", "deactivate", "onitry_abc"]):
            admin.main()
        mock_set.assert_called_once_with("onitry_abc", False)

    @patch("server.admin.db.init_db")
    @patch("server.admin.db.set_active_by_token")
    def test_activate_calls_set_active_true(self, mock_set, mock_init):
        mock_set.return_value = True
        with patch("sys.argv", ["admin.py", "activate", "onitry_abc"]):
            admin.main()
        mock_set.assert_called_once_with("onitry_abc", True)

    @patch("server.admin.db.init_db")
    def test_missing_subcommand_exits_with_error(self, mock_init):
        with patch("sys.argv", ["admin.py"]):
            with self.assertRaises(SystemExit):
                admin.main()


if __name__ == "__main__":
    unittest.main()
