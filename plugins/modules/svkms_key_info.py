#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_key_info
short_description: Gather information about encryption keys on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Retrieve information about one or all encryption keys from a StorMagic SvKMS server.
  - This module does not make any changes (read-only).
options:
  name:
    description:
      - Filter keys by name. If not provided, returns all keys.
    type: str
  key_id:
    description:
      - Retrieve a specific key by ID. Takes precedence over name.
    type: str
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: List all keys
  xianganwu.stormagic.svkms_key_info:
  register: all_keys

- name: Get a specific key by ID
  xianganwu.stormagic.svkms_key_info:
    key_id: key-abc123
  register: my_key

- name: Filter keys by name
  xianganwu.stormagic.svkms_key_info:
    name: app-encryption-key
  register: filtered_keys
"""

RETURN = r"""
key_list:
  description: List of key objects from SvKMS.
  type: list
  elements: dict
  returned: always
  sample:
    - id: "key-abc123"
      name: "app-encryption-key"
      algorithm: "AES"
      length: 256
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        key_id=dict(type="str"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params.get("name")
    key_id = module.params.get("key_id")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
            validate_certs=module.params.get("validate_certs", True),
            ca_path=module.params.get("ca_path"),
        )

        if key_id:
            key = client.get_key(key_id)
            module.exit_json(changed=False, key_list=[key])
        elif name:
            all_keys = client.list_keys()
            filtered = [k for k in all_keys if k.get("name") == name]
            module.exit_json(changed=False, key_list=filtered)
        else:
            keys = client.list_keys()
            module.exit_json(changed=False, key_list=keys)

    except SvKMSAPIError as e:
        error_msg = "SvKMS API error: {0}".format(str(e))
        if e.response_body and isinstance(e.response_body, dict):
            detail = e.response_body.get("detail") or e.response_body.get("message", "")
            if detail:
                error_msg += " - {0}".format(detail)
        module.fail_json(msg=error_msg, status_code=getattr(e, "status_code", None))


if __name__ == "__main__":
    main()
