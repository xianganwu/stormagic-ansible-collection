from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from unittest.mock import MagicMock

from ansible_collections.xianganwu.stormagic.plugins.httpapi.svkms import HttpApi


class TestSvKMSHttpApiLogin:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)

    def test_login_sends_credentials(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"token": "abc123"}).encode()
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, mock_response.read.return_value)

        # Mock get_option to return None (no api_key)
        self.httpapi.get_option = MagicMock(return_value=None)

        self.httpapi.login("admin", "password123")

        self.connection.send.assert_called_once()
        call_args = self.connection.send.call_args
        assert "/v0/auth/login" in str(call_args)
        assert self.connection._auth == {"Authorization": "Bearer abc123"}

    def test_login_with_api_key(self):
        # Mock get_option to return the API key
        self.httpapi.get_option = MagicMock(return_value="myapikey")

        self.httpapi.login(None, None)
        assert self.connection._auth == {"X-API-Key": "myapikey"}


class TestSvKMSHttpApiLogout:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)
        self.connection._auth = {"Authorization": "Bearer abc123"}

    def test_logout_clears_auth(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"{}"
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, mock_response.read.return_value)

        self.httpapi.logout()
        assert self.connection._auth is None


class TestSvKMSHttpApiSendRequest:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)

    def test_send_request_get(self):
        mock_response = MagicMock()
        response_data = json.dumps({"id": "key-1"}).encode()
        mock_response.read.return_value = response_data
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, response_data)

        code, result = self.httpapi.send_request("/keys/key-1", method="GET")

        assert code == 200
        assert result == {"id": "key-1"}

    def test_send_request_post_with_data(self):
        mock_response = MagicMock()
        response_data = json.dumps({"id": "key-2"}).encode()
        mock_response.read.return_value = response_data
        mock_response.getcode.return_value = 201
        self.connection.send.return_value = (mock_response, response_data)

        code, result = self.httpapi.send_request(
            "/keys", method="POST",
            body={"name": "test", "algorithm": "AES"}
        )

        assert code == 201
        assert result["id"] == "key-2"
