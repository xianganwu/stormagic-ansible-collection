from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.modules import svkms_key


def run_module(module_args, check_mode=False):
    set_module_args = {
        "_ansible_check_mode": check_mode,
        "_ansible_diff": False,
    }
    set_module_args.update(module_args)

    with pytest.raises(SystemExit) as exc_info:
        with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_key.main()

    return mock_module


class TestSvKMSKeyCreate:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
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

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
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
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_existing_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]
        client.destroy_key.return_value = {}

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_nonexistent_key_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSKeyRotate:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
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
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
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
