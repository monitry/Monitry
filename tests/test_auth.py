import unittest
from unittest.mock import MagicMock, patch

from core import auth


def _fake_server(auth_code=None, auth_state=None, auth_error=None, raise_on_handle=None):
    server = MagicMock()
    server.server_address = ("localhost", 54321)

    def _handle_request():
        if raise_on_handle:
            raise raise_on_handle
        server.auth_code = auth_code
        server.auth_state = auth_state
        server.auth_error = auth_error

    server.handle_request.side_effect = _handle_request
    return server


class TestGoogleAuth(unittest.TestCase):
    def test_missing_client_id_raises_before_opening_browser(self):
        with self.assertRaises(auth.GoogleLoginError):
            auth.login_with_google(client_id="", client_secret="")

    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    def test_server_close_called_even_if_handle_request_raises(self, mock_http_server, mock_open):
        # Regression test: server_close() used to sit after handle_request() with
        # no try/finally, so an exception there leaked the bound localhost port
        # for the rest of this long-running desktop app's process lifetime.
        server = _fake_server(raise_on_handle=OSError("socket error"))
        mock_http_server.return_value = server

        with self.assertRaises(OSError):
            auth.login_with_google(client_id="cid", client_secret="secret")

        server.server_close.assert_called_once()

    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    def test_timeout_with_no_code_raises(self, mock_http_server, mock_open):
        mock_http_server.return_value = _fake_server(auth_code=None)
        with self.assertRaises(auth.GoogleLoginError):
            auth.login_with_google(client_id="cid", client_secret="secret")

    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    def test_callback_error_param_raises(self, mock_http_server, mock_open):
        mock_http_server.return_value = _fake_server(auth_error="access_denied")
        with self.assertRaises(auth.GoogleLoginError):
            auth.login_with_google(client_id="cid", client_secret="secret")

    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    def test_state_mismatch_raises_without_exchanging_code(self, mock_http_server, mock_open):
        # A mismatched state is a possible CSRF — the code must never be exchanged.
        mock_http_server.return_value = _fake_server(auth_code="somecode", auth_state="wrong-state")
        with patch("core.auth.httpx.post") as mock_post:
            with self.assertRaises(auth.GoogleLoginError):
                auth.login_with_google(client_id="cid", client_secret="secret")
            mock_post.assert_not_called()

    @patch("core.auth.secrets.token_urlsafe")
    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    @patch("core.auth.httpx.post")
    def test_successful_flow_returns_id_token(self, mock_post, mock_http_server, mock_open, mock_state):
        mock_state.return_value = "matching-state"
        mock_http_server.return_value = _fake_server(auth_code="realcode", auth_state="matching-state")
        mock_post.return_value.json.return_value = {"id_token": "the.jwt.token"}

        result = auth.login_with_google(client_id="cid", client_secret="secret")

        self.assertEqual(result, "the.jwt.token")
        sent = mock_post.call_args.kwargs["data"]
        self.assertEqual(sent["code"], "realcode")
        self.assertEqual(sent["client_id"], "cid")
        self.assertEqual(sent["client_secret"], "secret")
        self.assertEqual(sent["grant_type"], "authorization_code")

    @patch("core.auth.webbrowser.open")
    @patch("core.auth.http.server.HTTPServer")
    @patch("core.auth.httpx.post")
    def test_missing_id_token_in_response_raises(self, mock_post, mock_http_server, mock_open):
        mock_http_server.return_value = _fake_server(auth_code="realcode", auth_state=None)
        # Force the state check to pass by matching whatever was generated —
        # simplest is to patch token_urlsafe to a known value via the server fake's
        # auth_state directly instead.
        with patch("core.auth.secrets.token_urlsafe", return_value="s"):
            mock_http_server.return_value = _fake_server(auth_code="realcode", auth_state="s")
            mock_post.return_value.json.return_value = {}  # no id_token key
            with self.assertRaises(auth.GoogleLoginError):
                auth.login_with_google(client_id="cid", client_secret="secret")


if __name__ == "__main__":
    unittest.main()
