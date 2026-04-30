from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.xianganwu.stormagic.plugins.modules import svkms_key_info


class TestSvKMSKeyInfo:
    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.SvKMSClient")
    def test_list_all_keys(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "key-a", "algorithm": "AES"},
            {"id": "key-2", "name": "key-b", "algorithm": "RSA"},
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "ca_path": None, "name": None, "key_id": None,
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_key_info.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert len(call_kwargs["key_list"]) == 2

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.SvKMSClient")
    def test_get_specific_key(self, MockClient):
        client = MockClient.return_value
        client.get_key.return_value = {"id": "key-1", "name": "key-a"}

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "ca_path": None, "name": None, "key_id": "key-1",
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_key_info.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["key_list"][0]["id"] == "key-1"

    @patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.SvKMSClient")
    def test_filter_by_name(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "key-a", "algorithm": "AES"},
            {"id": "key-2", "name": "key-b", "algorithm": "RSA"},
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.xianganwu.stormagic.plugins.modules.svkms_key_info.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {
                    "host": "kms.example.com", "port": 1443,
                    "ca_path": None, "name": "key-a", "key_id": None,
                }
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_key_info.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert len(call_kwargs["key_list"]) == 1
        assert call_kwargs["key_list"][0]["name"] == "key-a"
