import unittest

from core import auth


class TestGoogleAuth(unittest.TestCase):
    def test_missing_client_id_raises_before_opening_browser(self):
        with self.assertRaises(auth.GoogleLoginError):
            auth.login_with_google(client_id="", client_secret="")


if __name__ == "__main__":
    unittest.main()
