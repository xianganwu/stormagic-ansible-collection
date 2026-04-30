from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_health_check


class TestSvKMSHealthCheck:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.SvKMSClient")
    def test_healthy_server(self, MockClient):
        client = MockClient.return_value
        client.health_check.return_value = {"status": "healthy", "version": "4.2.0"}

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "api_key": "test-api-key", "username": None,
                    "password": None, "validate_certs": True,
                    "ca_path": None,
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_health_check.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert call_kwargs["health"]["status"] == "healthy"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.SvKMSClient")
    def test_connection_error_fails(self, MockClient):
        client = MockClient.return_value
        from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client.health_check.side_effect = SvKMSAPIError("Connection refused")

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "api_key": "test-api-key", "username": None,
                    "password": None, "validate_certs": True,
                    "ca_path": None,
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_health_check.main()

        mock_module.fail_json.assert_called_once()

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.SvKMSClient")
    def test_unhealthy_status_fails(self, MockClient):
        client = MockClient.return_value
        client.health_check.return_value = {"status": "degraded", "version": "4.2.0"}

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_health_check.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "api_key": "test-api-key", "username": None,
                    "password": None, "validate_certs": True,
                    "ca_path": None,
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_health_check.main()

        mock_module.fail_json.assert_called_once()
        call_kwargs = mock_module.fail_json.call_args[1]
        assert "unhealthy" in call_kwargs["msg"]
        assert call_kwargs["health"]["status"] == "degraded"
