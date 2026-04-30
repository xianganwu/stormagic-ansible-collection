from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_certificate


class TestSvKMSCertificate:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.SvKMSClient")
    def test_list_certificates(self, MockClient):
        client = MockClient.return_value
        client.list_certificates.return_value = [
            {"id": "cert-1", "type": "ca", "subject": "CN=SvKMS CA"}
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "validate_certs": True, "ca_path": None,
                    "state": "present", "name": None,
                    "cert_id": None, "cert_type": "ca",
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_certificate.main()

        mock_module.exit_json.assert_called_once()
        call_args = mock_module.exit_json.call_args
        assert call_args[1]["changed"] is False
        assert "certificates" in call_args[1]

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.SvKMSClient")
    def test_find_certificate_by_name(self, MockClient):
        client = MockClient.return_value
        client.list_certificates.return_value = [
            {"id": "cert-1", "type": "ca", "subject": "CN=SvKMS Root CA"}
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "validate_certs": True, "ca_path": None,
                    "state": "present", "name": "Root CA",
                    "cert_id": None, "cert_type": "ca",
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_certificate.main()

        mock_module.exit_json.assert_called_once()
        call_args = mock_module.exit_json.call_args
        assert call_args[1]["changed"] is False
        assert "certificate" in call_args[1]

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.SvKMSClient")
    def test_certificate_not_found(self, MockClient):
        client = MockClient.return_value
        client.list_certificates.return_value = []

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_certificate.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "validate_certs": True, "ca_path": None,
                    "state": "present", "name": "missing-cert",
                    "cert_id": None, "cert_type": "ca",
                }
                mock_module.check_mode = False
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_certificate.main()

        mock_module.fail_json.assert_called_once()
        call_args = mock_module.fail_json.call_args
        assert "not found" in call_args[1]["msg"]
