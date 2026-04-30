#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_key
short_description: Manage encryption keys on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Create, rotate, retire, and destroy encryption keys on a StorMagic SvKMS server.
  - Supports idempotent key creation and check mode.
options:
  state:
    description:
      - Desired state of the key.
      - C(present) ensures the key exists, creating it if necessary.
      - C(absent) ensures the key does not exist, destroying it if necessary.
      - C(rotated) rotates an existing key to a new version.
      - C(retired) marks an existing key as retired.
    type: str
    default: present
    choices: [present, absent, rotated, retired]
  name:
    description:
      - Name of the encryption key. Used for idempotent lookups.
    type: str
    required: true
  key_id:
    description:
      - ID of an existing key. If provided, used instead of name for lookups.
    type: str
  algorithm:
    description:
      - Encryption algorithm for the key.
    type: str
    default: AES
    choices: [AES, RSA, EC]
  length:
    description:
      - Key length in bits.
    type: int
    default: 256
  metadata:
    description:
      - Custom metadata to attach to the key.
    type: dict
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create an AES-256 encryption key
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    algorithm: AES
    length: 256
    state: present

- name: Rotate an existing key
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    state: rotated

- name: Retire a key
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    state: retired

- name: Destroy a key
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    state: absent
"""

RETURN = r"""
key:
  description: The key object returned by SvKMS.
  type: dict
  returned: when state is present, rotated, or retired
  contains:
    id:
      description: Unique key identifier.
      type: str
      returned: always
    name:
      description: Key name.
      type: str
      returned: always
    algorithm:
      description: Encryption algorithm.
      type: str
      returned: always
    length:
      description: Key length in bits.
      type: int
      returned: always
    version:
      description: Key version number.
      type: int
      returned: always
  sample:
    id: "key-abc123"
    name: "app-encryption-key"
    algorithm: "AES"
    length: 256
    version: 1
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def find_key_by_name(client, name):
    keys = client.list_keys()
    for key in keys:
        if key.get("name") == name:
            return key
    return None


def main():
    argument_spec = dict(
        host=dict(type="str"),
        port=dict(type="int", default=1443),
        state=dict(type="str", default="present", choices=["present", "absent", "rotated", "retired"]),
        name=dict(type="str", required=True),
        key_id=dict(type="str"),
        algorithm=dict(type="str", default="AES", choices=["AES", "RSA", "EC"]),
        length=dict(type="int", default=256),
        metadata=dict(type="dict"),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]
    name = module.params["name"]
    key_id = module.params.get("key_id")
    algorithm = module.params.get("algorithm", "AES")
    length = module.params.get("length", 256)
    metadata = module.params.get("metadata")

    try:
        host = module.params.get("host")
        if not host:
            module.fail_json(msg="'host' is required when not using httpapi connection")

        client = SvKMSClient(
            host=host,
            port=module.params["port"],
            validate_certs=module.params.get("validate_certs", True),
            ca_path=module.params.get("ca_path"),
        )

        existing_key = None
        if key_id:
            try:
                existing_key = client.get_key(key_id)
            except SvKMSAPIError:
                existing_key = None
        else:
            existing_key = find_key_by_name(client, name)

        if state == "present":
            if existing_key:
                module.exit_json(changed=False, key=existing_key)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, key={}, diff={"before": {}, "after": {"name": name, "algorithm": algorithm, "length": length}})
                key = client.create_key(name=name, algorithm=algorithm, length=length)
                module.exit_json(changed=True, key=key, diff={"before": {}, "after": key})

        elif state == "absent":
            if not existing_key:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, diff={"before": existing_key, "after": {}})
                client.destroy_key(existing_key["id"])
                module.exit_json(changed=True, diff={"before": existing_key, "after": {}})

        elif state == "rotated":
            if not existing_key:
                module.fail_json(msg="Cannot rotate key '{0}': key not found".format(name))
            if module.check_mode:
                module.exit_json(changed=True, key=existing_key, diff={"before": existing_key, "after": {"name": name, "state": "rotated"}})
            key = client.rotate_key(existing_key["id"])
            module.exit_json(changed=True, key=key, diff={"before": existing_key, "after": key})

        elif state == "retired":
            if not existing_key:
                module.fail_json(msg="Cannot retire key '{0}': key not found".format(name))
            if module.check_mode:
                module.exit_json(changed=True, key=existing_key, diff={"before": existing_key, "after": {"name": name, "state": "retired"}})
            key = client.retire_key(existing_key["id"])
            module.exit_json(changed=True, key=key, diff={"before": existing_key, "after": key})

    except SvKMSAPIError as e:
        error_msg = "SvKMS API error: {0}".format(str(e))
        if e.response_body and isinstance(e.response_body, dict):
            detail = e.response_body.get("detail") or e.response_body.get("message", "")
            if detail:
                error_msg += " - {0}".format(detail)
        module.fail_json(msg=error_msg, status_code=getattr(e, "status_code", None))


if __name__ == "__main__":
    main()
