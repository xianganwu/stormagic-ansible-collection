from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_key


def run_module(module_args, check_mode=False):
    set_module_args = {
        "_ansible_check_mode": check_mode,
        "_ansible_diff": False,
        "host": "kms.example.com",
        "port": 1443,
        "api_key": "test-api-key",
        "validate_certs": True,
        "ca_path": None,
    }
    set_module_args.update(module_args)

    with pytest.raises(SystemExit) as exc_info:
        with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_key.main()

    return mock_module


class TestSvKMSKeyCreate:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_create_new_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []
        client.create_key.return_value = {
            "id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256,
        }

        module = run_module({
            "state": "present", "name": "mykey", "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["key"]["id"] == "key-1"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_key_already_exists_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        ]

        module = run_module({
            "state": "present", "name": "mykey", "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSKeyDelete:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_existing_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]
        client.destroy_key.return_value = {}

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_nonexistent_key_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSKeyRotate:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_rotate_existing_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]
        client.rotate_key.return_value = {"id": "key-1", "name": "mykey", "version": 2}

        module = run_module({"state": "rotated", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["key"]["version"] == 2


class TestSvKMSKeyCheckMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_create_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module(
            {"state": "present", "name": "mykey", "algorithm": "AES", "length": 256},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.create_key.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_create_no_change_when_exists(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        ]

        module = run_module(
            {"state": "present", "name": "mykey", "algorithm": "AES", "length": 256},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_delete_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]

        module = run_module(
            {"state": "absent", "name": "mykey"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.destroy_key.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_rotate_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]

        module = run_module(
            {"state": "rotated", "name": "mykey"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.rotate_key.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_retire_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]

        module = run_module(
            {"state": "retired", "name": "mykey"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.retire_key.assert_not_called()


class TestSvKMSKeyErrors:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_rotate_nonexistent_key_fails(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module({"state": "rotated", "name": "missing"})

        module.fail_json.assert_called_once()
        assert "not found" in module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_retire_nonexistent_key_fails(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module({"state": "retired", "name": "missing"})

        module.fail_json.assert_called_once()
        assert "not found" in module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_api_error_with_detail(self, MockClient):
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client = MockClient.return_value
        client.login.side_effect = SvKMSAPIError(
            "HTTP 403: Forbidden", status_code=403,
            response_body={"detail": "invalid api key"},
        )

        module = run_module({"state": "present", "name": "mykey", "algorithm": "AES", "length": 256})

        module.fail_json.assert_called_once()
        msg = module.fail_json.call_args[1]["msg"]
        assert "invalid api key" in msg
        assert module.fail_json.call_args[1]["status_code"] == 403

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_api_error_without_detail(self, MockClient):
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client = MockClient.return_value
        client.login.side_effect = SvKMSAPIError("HTTP 500: Server Error", status_code=500)

        module = run_module({"state": "present", "name": "mykey", "algorithm": "AES", "length": 256})

        module.fail_json.assert_called_once()
        assert "500" in module.fail_json.call_args[1]["msg"]


class TestSvKMSKeyDiffMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_create_produces_diff(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []
        new_key = {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        client.create_key.return_value = new_key

        module = run_module({"state": "present", "name": "mykey", "algorithm": "AES", "length": 256})

        call_kwargs = module.exit_json.call_args[1]
        assert "diff" in call_kwargs
        assert call_kwargs["diff"]["before"] == {}
        assert call_kwargs["diff"]["after"] == new_key

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_produces_diff(self, MockClient):
        existing = {"id": "key-1", "name": "mykey"}
        client = MockClient.return_value
        client.list_keys.return_value = [existing]
        client.destroy_key.return_value = {}

        module = run_module({"state": "absent", "name": "mykey"})

        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["diff"]["before"] == existing
        assert call_kwargs["diff"]["after"] == {}


class TestSvKMSKeyLookupByID:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_lookup_by_key_id(self, MockClient):
        client = MockClient.return_value
        client.get_key.return_value = {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}

        module = run_module({
            "state": "present", "name": "mykey", "key_id": "key-1",
            "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        assert module.exit_json.call_args[1]["changed"] is False
        client.get_key.assert_called_once_with("key-1")
        client.list_keys.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_lookup_by_key_id_not_found_creates(self, MockClient):
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client = MockClient.return_value
        client.get_key.side_effect = SvKMSAPIError("not found", status_code=404)
        client.create_key.return_value = {"id": "key-2", "name": "newkey"}

        module = run_module({
            "state": "present", "name": "newkey", "key_id": "key-notfound",
            "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        assert module.exit_json.call_args[1]["changed"] is True


class TestSvKMSKeyMetadata:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_create_with_metadata(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []
        client.create_key.return_value = {"id": "key-1", "name": "mykey", "metadata": {"env": "prod"}}

        module = run_module({
            "state": "present", "name": "mykey", "algorithm": "AES",
            "length": 256, "metadata": {"env": "prod"},
        })

        client.create_key.assert_called_once_with(
            name="mykey", algorithm="AES", length=256, metadata={"env": "prod"},
        )
        assert module.exit_json.call_args[1]["changed"] is True
