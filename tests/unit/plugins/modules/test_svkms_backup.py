from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_backup


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
        with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_backup.main()

    return mock_module


class TestSvKMSBackup:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_backup_creates_backup(self, MockClient):
        client = MockClient.return_value
        client.backup.return_value = {
            "action": "backup", "path": "/backup/svkms.tar.gz", "status": "success",
        }

        module = run_module({
            "action": "backup", "destination": "/backup/svkms.tar.gz", "source": None,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["result"]["status"] == "success"
        client.backup.assert_called_once_with("/backup/svkms.tar.gz")

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_restore_from_backup(self, MockClient):
        client = MockClient.return_value
        client.restore.return_value = {
            "action": "restore", "path": "/backup/svkms.tar.gz", "status": "success",
        }

        module = run_module({
            "action": "restore", "source": "/backup/svkms.tar.gz", "destination": None,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.restore.assert_called_once_with("/backup/svkms.tar.gz")


class TestSvKMSBackupCheckMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_check_mode_backup(self, MockClient):
        client = MockClient.return_value

        module = run_module(
            {"action": "backup", "destination": "/backup/svkms.tar.gz", "source": None},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.backup.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_check_mode_restore(self, MockClient):
        client = MockClient.return_value

        module = run_module(
            {"action": "restore", "source": "/backup/svkms.tar.gz", "destination": None},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.restore.assert_not_called()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_check_mode_backup_result_has_check_status(self, MockClient):
        client = MockClient.return_value

        module = run_module(
            {"action": "backup", "destination": "/backup/svkms.tar.gz", "source": None},
            check_mode=True,
        )

        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["result"]["status"] == "check"
        assert call_kwargs["result"]["action"] == "backup"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_check_mode_restore_result_has_check_status(self, MockClient):
        client = MockClient.return_value

        module = run_module(
            {"action": "restore", "source": "/backup/svkms.tar.gz", "destination": None},
            check_mode=True,
        )

        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["result"]["status"] == "check"
        assert call_kwargs["result"]["action"] == "restore"


class TestSvKMSBackupErrors:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_api_error_on_backup(self, MockClient):
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client = MockClient.return_value
        client.backup.side_effect = SvKMSAPIError(
            "HTTP 500", status_code=500,
            response_body={"detail": "disk full"},
        )

        module = run_module({"action": "backup", "destination": "/backup/test.tar.gz", "source": None})

        module.fail_json.assert_called_once()
        assert "disk full" in module.fail_json.call_args[1]["msg"]

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_api_error_on_restore(self, MockClient):
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client = MockClient.return_value
        client.restore.side_effect = SvKMSAPIError("HTTP 400", status_code=400)

        module = run_module({"action": "restore", "source": "/backup/test.tar.gz", "destination": None})

        module.fail_json.assert_called_once()


class TestSvKMSBackupDiffMode:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_backup_produces_diff(self, MockClient):
        client = MockClient.return_value
        result = {"action": "backup", "path": "/backup/test.tar.gz", "status": "success"}
        client.backup.return_value = result

        module = run_module({"action": "backup", "destination": "/backup/test.tar.gz", "source": None})

        call_kwargs = module.exit_json.call_args[1]
        assert "diff" in call_kwargs
        assert call_kwargs["diff"]["before"] == {}

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_backup.SvKMSClient")
    def test_check_mode_backup_produces_diff(self, MockClient):
        module = run_module(
            {"action": "backup", "destination": "/backup/test.tar.gz", "source": None},
            check_mode=True,
        )

        call_kwargs = module.exit_json.call_args[1]
        assert "diff" in call_kwargs
        assert call_kwargs["diff"]["after"]["action"] == "backup"
