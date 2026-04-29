from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_backup


def run_module(module_args, check_mode=False):
    set_module_args = {
        "_ansible_check_mode": check_mode,
        "_ansible_diff": False,
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
