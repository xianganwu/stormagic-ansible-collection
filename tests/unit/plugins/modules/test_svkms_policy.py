from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_policy


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
        with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_policy.main()

    return mock_module


class TestSvKMSPolicyCreate:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_create_new_policy(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = []
        client.create_policy.return_value = {
            "id": "pol-1", "name": "app-policy",
            "rules": [{"principal": "app-user", "actions": ["encrypt"]}],
        }

        module = run_module({
            "state": "present", "name": "app-policy",
            "rules": [{"principal": "app-user", "actions": ["encrypt"]}],
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["policy"]["id"] == "pol-1"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_policy_already_exists_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = [
            {"id": "pol-1", "name": "app-policy", "rules": []}
        ]

        module = run_module({
            "state": "present", "name": "app-policy", "rules": [],
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        client.create_policy.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_update_existing_policy_rules(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = [
            {"id": "pol-1", "name": "app-policy", "rules": []}
        ]
        new_rules = [{"principal": "app-user", "actions": ["encrypt"]}]
        client.update_policy.return_value = {
            "id": "pol-1", "name": "app-policy", "rules": new_rules,
        }

        module = run_module({
            "state": "present", "name": "app-policy", "rules": new_rules,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.update_policy.assert_called_once_with("pol-1", new_rules)


class TestSvKMSPolicyDelete:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_delete_existing_policy(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = [
            {"id": "pol-1", "name": "app-policy"}
        ]

        module = run_module({"state": "absent", "name": "app-policy"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.delete_policy.assert_called_once_with("pol-1")

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_delete_nonexistent_policy_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = []

        module = run_module({"state": "absent", "name": "app-policy"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSPolicyCheckMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_check_mode_create_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = []

        module = run_module(
            {"state": "present", "name": "app-policy", "rules": []},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.create_policy.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_policy.SvKMSClient")
    def test_check_mode_delete_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_policies.return_value = [
            {"id": "pol-1", "name": "app-policy"}
        ]

        module = run_module(
            {"state": "absent", "name": "app-policy"},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.delete_policy.assert_not_called()
