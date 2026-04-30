from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_user


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

    with pytest.raises(SystemExit):
        with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_user.main()

    return mock_module


class TestSvKMSUserCreate:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_create_new_user(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = []
        client.create_user.return_value = {
            "id": "user-1", "username": "ops-user", "role": "operator",
        }

        module = run_module({
            "state": "present", "username": "ops-user", "role": "operator",
            "auth_type": "password",
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["user"]["id"] == "user-1"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_user_already_exists_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = [
            {"id": "user-1", "username": "ops-user", "role": "operator", "auth_type": "password"}
        ]

        module = run_module({
            "state": "present", "username": "ops-user", "role": "operator",
            "auth_type": "password",
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        client.create_user.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_update_existing_user_role(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = [
            {"id": "user-1", "username": "ops-user", "role": "operator", "auth_type": "password"}
        ]
        client.update_user.return_value = {
            "id": "user-1", "username": "ops-user", "role": "admin", "auth_type": "password",
        }

        module = run_module({
            "state": "present", "username": "ops-user", "role": "admin",
            "auth_type": "password",
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.update_user.assert_called_once_with("user-1", role="admin")


class TestSvKMSUserDelete:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_delete_existing_user(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = [
            {"id": "user-1", "username": "ops-user"}
        ]

        module = run_module({"state": "absent", "username": "ops-user"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.delete_user.assert_called_once_with("user-1")

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_delete_nonexistent_user_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = []

        module = run_module({"state": "absent", "username": "ops-user"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSUserCheckMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_check_mode_create_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = []

        module = run_module(
            {"state": "present", "username": "ops-user", "role": "operator",
             "auth_type": "password"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.create_user.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_user.SvKMSClient")
    def test_check_mode_delete_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_users.return_value = [
            {"id": "user-1", "username": "ops-user"}
        ]

        module = run_module(
            {"state": "absent", "username": "ops-user"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.delete_user.assert_not_called()
