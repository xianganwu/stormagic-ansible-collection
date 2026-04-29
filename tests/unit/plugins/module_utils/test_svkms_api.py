from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


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


class TestSvKMSClientRequest:
    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_get_request_success(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "key-1", "name": "test"}).encode()
        mock_response.getcode.return_value = 200
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com")
        result = client.request("GET", "/keys/key-1")

        assert result == {"id": "key-1", "name": "test"}
        mock_open_url.assert_called_once()

    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
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

    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
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
