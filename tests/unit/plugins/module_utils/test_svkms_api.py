from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
    svkms_argument_spec,
    SVKMS_MUTUALLY_EXCLUSIVE,
    SVKMS_REQUIRED_ONE_OF,
    SVKMS_REQUIRED_TOGETHER,
)


class TestSvKMSArgumentSpec:
    def test_argument_spec_returns_dict(self):
        spec = svkms_argument_spec()
        assert isinstance(spec, dict)
        assert "host" in spec
        assert "port" in spec
        assert "api_key" in spec
        assert "username" in spec
        assert "password" in spec

    def test_argument_spec_no_log_on_secrets(self):
        spec = svkms_argument_spec()
        assert spec["api_key"]["no_log"] is True
        assert spec["password"]["no_log"] is True
        assert "no_log" not in spec["host"]

    def test_argument_spec_defaults(self):
        spec = svkms_argument_spec()
        assert spec["port"]["default"] == 1443
        assert spec["validate_certs"]["default"] is True
        assert spec["host"]["required"] is True

    def test_mutually_exclusive_constants(self):
        assert SVKMS_MUTUALLY_EXCLUSIVE == [["api_key", "username"]]
        assert SVKMS_REQUIRED_ONE_OF == [["api_key", "username"]]
        assert SVKMS_REQUIRED_TOGETHER == [["username", "password"]]


class TestSvKMSAPIError:
    def test_error_with_all_fields(self):
        err = SvKMSAPIError("test error", status_code=403, response_body={"detail": "forbidden"})
        assert str(err) == "test error"
        assert err.status_code == 403
        assert err.response_body == {"detail": "forbidden"}

    def test_error_defaults(self):
        err = SvKMSAPIError("simple error")
        assert err.status_code is None
        assert err.response_body is None


class TestSvKMSClientInit:
    def test_base_url_construction(self):
        client = SvKMSClient(host="kms.example.com", port=1443)
        assert client.base_url == "https://kms.example.com:1443/v0"

    def test_default_port(self):
        client = SvKMSClient(host="kms.example.com")
        assert client.base_url == "https://kms.example.com:1443/v0"

    def test_custom_port(self):
        client = SvKMSClient(host="kms.example.com", port=8443)
        assert client.base_url == "https://kms.example.com:8443/v0"

    def test_default_timeout(self):
        client = SvKMSClient(host="kms.example.com")
        assert client.timeout == 30

    def test_custom_timeout(self):
        client = SvKMSClient(host="kms.example.com", timeout=60)
        assert client.timeout == 60

    def test_stores_credentials(self):
        client = SvKMSClient(host="kms.example.com", api_key="my-key")
        assert client.api_key == "my-key"
        assert client._session_token is None


class TestSvKMSClientHeaders:
    def test_headers_with_api_key(self):
        client = SvKMSClient(host="kms.example.com", api_key="test-key")
        headers = client._get_headers()
        assert headers["X-API-Key"] == "test-key"
        assert "Authorization" not in headers

    def test_headers_with_session_token(self):
        client = SvKMSClient(host="kms.example.com")
        client._session_token = "session-abc"
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer session-abc"
        assert "X-API-Key" not in headers

    def test_headers_no_auth(self):
        client = SvKMSClient(host="kms.example.com")
        headers = client._get_headers()
        assert "X-API-Key" not in headers
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    def test_api_key_takes_precedence(self):
        client = SvKMSClient(host="kms.example.com", api_key="test-key")
        client._session_token = "should-not-use"
        headers = client._get_headers()
        assert headers["X-API-Key"] == "test-key"
        assert "Authorization" not in headers


class TestSvKMSClientLogin:
    @patch.object(SvKMSClient, "request")
    def test_login_with_credentials(self, mock_request):
        mock_request.return_value = {"token": "session-xyz"}
        client = SvKMSClient(host="kms.example.com", username="admin", password="secret")
        token = client.login()
        assert token == "session-xyz"
        assert client._session_token == "session-xyz"
        mock_request.assert_called_once_with("POST", "/auth/login", data={
            "username": "admin", "password": "secret",
        })

    @patch.object(SvKMSClient, "request")
    def test_login_clears_password(self, mock_request):
        mock_request.return_value = {"token": "session-xyz"}
        client = SvKMSClient(host="kms.example.com", username="admin", password="secret")
        client.login()
        assert client.password is None

    def test_login_with_api_key_skips(self):
        client = SvKMSClient(host="kms.example.com", api_key="test-key")
        result = client.login()
        assert result is None
        assert client._session_token is None

    def test_login_without_credentials_skips(self):
        client = SvKMSClient(host="kms.example.com")
        result = client.login()
        assert result is None


class TestSvKMSClientLogout:
    @patch.object(SvKMSClient, "request")
    def test_logout_clears_token(self, mock_request):
        mock_request.return_value = {}
        client = SvKMSClient(host="kms.example.com")
        client._session_token = "session-abc"
        client.logout()
        assert client._session_token is None
        mock_request.assert_called_once_with("POST", "/auth/logout")

    @patch.object(SvKMSClient, "request")
    def test_logout_suppresses_api_error(self, mock_request):
        mock_request.side_effect = SvKMSAPIError("logout failed")
        client = SvKMSClient(host="kms.example.com")
        client._session_token = "session-abc"
        client.logout()
        assert client._session_token is None

    def test_logout_without_token_is_noop(self):
        client = SvKMSClient(host="kms.example.com")
        client.logout()
        assert client._session_token is None


class TestSvKMSClientRequest:
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_get_request_success(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "key-1", "name": "test"}).encode()
        mock_response.getcode.return_value = 200
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com")
        result = client.request("GET", "/keys/key-1")

        assert result == {"id": "key-1", "name": "test"}
        mock_open_url.assert_called_once()

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_post_request_with_body(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "key-2"}).encode()
        mock_response.getcode.return_value = 201
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com", api_key="test-api-key")
        result = client.request("POST", "/keys", data={"name": "newkey", "algorithm": "AES"})

        assert result == {"id": "key-2"}
        call_kwargs = mock_open_url.call_args
        assert "test-api-key" in str(call_kwargs)

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_request_error_raises(self, mock_open_url):
        from urllib.error import HTTPError
        mock_open_url.side_effect = HTTPError(
            url="https://kms.example.com:1443/v0/keys/bad",
            code=404, msg="Not Found", hdrs={}, fp=MagicMock()
        )

        client = SvKMSClient(host="kms.example.com")
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.request("GET", "/keys/bad")
        assert exc_info.value.status_code == 404


class TestSvKMSClientKeyOperations:
    @patch.object(SvKMSClient, "request")
    def test_create_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        client = SvKMSClient(host="kms.example.com")
        result = client.create_key(name="mykey", algorithm="AES", length=256)
        mock_request.assert_called_once_with("POST", "/keys", data={"name": "mykey", "algorithm": "AES", "length": 256})
        assert result["id"] == "key-1"

    @patch.object(SvKMSClient, "request")
    def test_get_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "name": "mykey"}
        client = SvKMSClient(host="kms.example.com")
        result = client.get_key("key-1")
        mock_request.assert_called_once_with("GET", "/keys/key-1")
        assert result["name"] == "mykey"

    @patch.object(SvKMSClient, "request")
    def test_list_keys(self, mock_request):
        mock_request.return_value = [{"id": "key-1"}, {"id": "key-2"}]
        client = SvKMSClient(host="kms.example.com")
        result = client.list_keys()
        mock_request.assert_called_once_with("GET", "/keys")
        assert len(result) == 2

    @patch.object(SvKMSClient, "request")
    def test_rotate_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "version": 2}
        client = SvKMSClient(host="kms.example.com")
        result = client.rotate_key("key-1")
        mock_request.assert_called_once_with("POST", "/keys/key-1/rotate")
        assert result["version"] == 2

    @patch.object(SvKMSClient, "request")
    def test_destroy_key(self, mock_request):
        mock_request.return_value = {}
        client = SvKMSClient(host="kms.example.com")
        client.destroy_key("key-1")
        mock_request.assert_called_once_with("DELETE", "/keys/key-1")

    @patch.object(SvKMSClient, "request")
    def test_retire_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "state": "retired"}
        client = SvKMSClient(host="kms.example.com")
        result = client.retire_key("key-1")
        mock_request.assert_called_once_with("POST", "/keys/key-1/retire")
        assert result["state"] == "retired"


class TestSvKMSClientUserOperations:
    @patch.object(SvKMSClient, "request")
    def test_list_users(self, mock_request):
        mock_request.return_value = [{"id": "user-1", "username": "admin"}]
        client = SvKMSClient(host="kms.example.com")
        result = client.list_users()
        mock_request.assert_called_once_with("GET", "/users")
        assert len(result) == 1

    @patch.object(SvKMSClient, "request")
    def test_list_policies(self, mock_request):
        mock_request.return_value = [{"id": "pol-1", "name": "test-policy"}]
        client = SvKMSClient(host="kms.example.com")
        result = client.list_policies()
        mock_request.assert_called_once_with("GET", "/policies")
        assert len(result) == 1


class TestSvKMSClientHealthCheck:
    @patch.object(SvKMSClient, "request")
    def test_health_check_healthy(self, mock_request):
        mock_request.return_value = {"status": "healthy", "version": "4.2.0"}
        client = SvKMSClient(host="kms.example.com")
        result = client.health_check()
        mock_request.assert_called_once_with("GET", "/health")
        assert result["status"] == "healthy"


class TestSvKMSClientRetry:
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.time.sleep")
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_retries_on_5xx(self, mock_open_url, mock_sleep):
        from urllib.error import HTTPError
        error_500 = HTTPError(
            url="https://kms:1443/v0/keys", code=500,
            msg="Internal Server Error", hdrs={}, fp=MagicMock(),
        )
        success_response = MagicMock()
        success_response.read.return_value = json.dumps({"ok": True}).encode()
        mock_open_url.side_effect = [error_500, error_500, success_response]

        client = SvKMSClient(host="kms", max_retries=3, retry_delay=1)
        result = client.request("GET", "/keys")
        assert result == {"ok": True}
        assert mock_open_url.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_no_retry_on_4xx(self, mock_open_url):
        from urllib.error import HTTPError
        mock_open_url.side_effect = HTTPError(
            url="https://kms:1443/v0/keys/bad", code=404,
            msg="Not Found", hdrs={}, fp=MagicMock(),
        )

        client = SvKMSClient(host="kms", max_retries=3)
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.request("GET", "/keys/bad")
        assert exc_info.value.status_code == 404
        assert mock_open_url.call_count == 1

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.time.sleep")
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_retries_on_connection_error(self, mock_open_url, mock_sleep):
        from urllib.error import URLError
        success_response = MagicMock()
        success_response.read.return_value = json.dumps({"connected": True}).encode()
        mock_open_url.side_effect = [
            URLError("Connection refused"),
            success_response,
        ]

        client = SvKMSClient(host="kms", max_retries=3, retry_delay=1)
        result = client.request("GET", "/health")
        assert result == {"connected": True}
        assert mock_open_url.call_count == 2

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.time.sleep")
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_raises_after_exhausting_retries(self, mock_open_url, mock_sleep):
        from urllib.error import URLError
        mock_open_url.side_effect = URLError("Connection refused")

        client = SvKMSClient(host="kms", max_retries=3, retry_delay=1)
        with pytest.raises(SvKMSAPIError, match="Connection refused"):
            client.request("GET", "/keys")

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.time.sleep")
    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_retries_on_429(self, mock_open_url, mock_sleep):
        from urllib.error import HTTPError
        error_429 = HTTPError(
            url="https://kms:1443/v0/keys", code=429,
            msg="Too Many Requests", hdrs={}, fp=MagicMock(),
        )
        success_response = MagicMock()
        success_response.read.return_value = json.dumps({"ok": True}).encode()
        mock_open_url.side_effect = [error_429, success_response]

        client = SvKMSClient(host="kms", max_retries=3, retry_delay=1)
        result = client.request("GET", "/keys")
        assert result == {"ok": True}
        assert mock_open_url.call_count == 2

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_timeout_passed_to_open_url(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({}).encode()
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com", timeout=45)
        client.request("GET", "/health")
        call_kwargs = mock_open_url.call_args
        assert call_kwargs[1]["timeout"] == 45

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_empty_response_returns_empty_dict(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com")
        result = client.request("DELETE", "/keys/key-1")
        assert result == {}

    @patch("ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_4xx_error_includes_response_body(self, mock_open_url):
        from urllib.error import HTTPError
        error_fp = MagicMock()
        error_fp.read.return_value = json.dumps({"detail": "key not found"}).encode()
        mock_open_url.side_effect = HTTPError(
            url="https://kms:1443/v0/keys/bad", code=404,
            msg="Not Found", hdrs={}, fp=error_fp,
        )

        client = SvKMSClient(host="kms")
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.request("GET", "/keys/bad")
        assert exc_info.value.response_body == {"detail": "key not found"}


class TestSvKMSClientURLEncoding:
    @patch.object(SvKMSClient, "request")
    def test_get_key_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.get_key("key/with/slashes")
        mock_request.assert_called_once_with("GET", "/keys/key%2Fwith%2Fslashes")

    @patch.object(SvKMSClient, "request")
    def test_rotate_key_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.rotate_key("key with spaces")
        mock_request.assert_called_once_with("POST", "/keys/key%20with%20spaces/rotate")

    @patch.object(SvKMSClient, "request")
    def test_destroy_key_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.destroy_key("key&special=chars")
        mock_request.assert_called_once_with("DELETE", "/keys/key%26special%3Dchars")

    @patch.object(SvKMSClient, "request")
    def test_get_user_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.get_user("user/admin")
        mock_request.assert_called_once_with("GET", "/users/user%2Fadmin")

    @patch.object(SvKMSClient, "request")
    def test_get_policy_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.get_policy("pol/test")
        mock_request.assert_called_once_with("GET", "/policies/pol%2Ftest")

    @patch.object(SvKMSClient, "request")
    def test_get_certificate_encodes_id(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.get_certificate("cert/root")
        mock_request.assert_called_once_with("GET", "/certificates/cert%2Froot")

    @patch.object(SvKMSClient, "request")
    def test_list_keys_filter_encoding(self, mock_request):
        client = SvKMSClient(host="kms.example.com")
        client.list_keys(filters={"name": "key with spaces", "algo": "AES&more"})
        call_args = mock_request.call_args
        path = call_args[0][1]
        assert "name=key%20with%20spaces" in path
        assert "algo=AES%26more" in path


class TestSvKMSClientCRUDOperations:
    @patch.object(SvKMSClient, "request")
    def test_create_key_with_metadata(self, mock_request):
        mock_request.return_value = {"id": "key-1"}
        client = SvKMSClient(host="kms.example.com")
        client.create_key(name="mykey", algorithm="AES", length=256, metadata={"env": "prod"})
        call_data = mock_request.call_args[1]["data"]
        assert call_data["metadata"] == {"env": "prod"}

    @patch.object(SvKMSClient, "request")
    def test_create_user(self, mock_request):
        mock_request.return_value = {"id": "user-1", "username": "ops"}
        client = SvKMSClient(host="kms.example.com")
        result = client.create_user("ops", "operator", "password")
        mock_request.assert_called_once_with("POST", "/users", data={
            "username": "ops", "role": "operator", "auth_type": "password",
        })
        assert result["username"] == "ops"

    @patch.object(SvKMSClient, "request")
    def test_update_user(self, mock_request):
        mock_request.return_value = {"id": "user-1", "role": "admin"}
        client = SvKMSClient(host="kms.example.com")
        result = client.update_user("user-1", role="admin")
        mock_request.assert_called_once_with("PUT", "/users/user-1", data={"role": "admin"})
        assert result["role"] == "admin"

    @patch.object(SvKMSClient, "request")
    def test_delete_user(self, mock_request):
        mock_request.return_value = {}
        client = SvKMSClient(host="kms.example.com")
        client.delete_user("user-1")
        mock_request.assert_called_once_with("DELETE", "/users/user-1")

    @patch.object(SvKMSClient, "request")
    def test_create_policy(self, mock_request):
        rules = [{"principal": "user-1", "actions": ["encrypt"]}]
        mock_request.return_value = {"id": "pol-1", "rules": rules}
        client = SvKMSClient(host="kms.example.com")
        result = client.create_policy("test-policy", rules)
        mock_request.assert_called_once_with("POST", "/policies", data={"name": "test-policy", "rules": rules})
        assert result["rules"] == rules

    @patch.object(SvKMSClient, "request")
    def test_update_policy(self, mock_request):
        new_rules = [{"principal": "user-2", "actions": ["decrypt"]}]
        mock_request.return_value = {"id": "pol-1", "rules": new_rules}
        client = SvKMSClient(host="kms.example.com")
        result = client.update_policy("pol-1", new_rules)
        mock_request.assert_called_once_with("PUT", "/policies/pol-1", data={"rules": new_rules})
        assert result["rules"] == new_rules

    @patch.object(SvKMSClient, "request")
    def test_delete_policy(self, mock_request):
        mock_request.return_value = {}
        client = SvKMSClient(host="kms.example.com")
        client.delete_policy("pol-1")
        mock_request.assert_called_once_with("DELETE", "/policies/pol-1")

    @patch.object(SvKMSClient, "request")
    def test_list_certificates(self, mock_request):
        mock_request.return_value = [{"id": "cert-1", "type": "ca"}]
        client = SvKMSClient(host="kms.example.com")
        result = client.list_certificates()
        mock_request.assert_called_once_with("GET", "/certificates")
        assert len(result) == 1

    @patch.object(SvKMSClient, "request")
    def test_backup(self, mock_request):
        mock_request.return_value = {"status": "success"}
        client = SvKMSClient(host="kms.example.com")
        result = client.backup("/backup/svkms.tar.gz")
        mock_request.assert_called_once_with("POST", "/backup", data={"destination": "/backup/svkms.tar.gz"})
        assert result["status"] == "success"

    @patch.object(SvKMSClient, "request")
    def test_backup_no_destination(self, mock_request):
        mock_request.return_value = {"status": "success"}
        client = SvKMSClient(host="kms.example.com")
        client.backup()
        mock_request.assert_called_once_with("POST", "/backup", data={})

    @patch.object(SvKMSClient, "request")
    def test_restore(self, mock_request):
        mock_request.return_value = {"status": "success"}
        client = SvKMSClient(host="kms.example.com")
        result = client.restore("/backup/svkms.tar.gz")
        mock_request.assert_called_once_with("POST", "/restore", data={"source": "/backup/svkms.tar.gz"})
        assert result["status"] == "success"
