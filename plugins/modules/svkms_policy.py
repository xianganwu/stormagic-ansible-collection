#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_policy
short_description: Manage key access policies on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Create, update, and delete key access policies on a StorMagic SvKMS server.
  - Supports idempotent policy creation and check mode.
options:
  state:
    description:
      - Desired state of the policy.
      - C(present) ensures the policy exists, creating it if necessary.
      - C(absent) ensures the policy does not exist, deleting it if necessary.
    type: str
    default: present
    choices: [present, absent]
  name:
    description:
      - Name of the policy.
    type: str
    required: true
  rules:
    description:
      - List of policy rules. Each rule defines access permissions.
    type: list
    elements: dict
extends_documentation_fragment:
  - stormagic.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create a key access policy
  stormagic.stormagic.svkms_policy:
    name: app-key-policy
    rules:
      - principal: "app-user"
        actions: ["encrypt", "decrypt"]
        resources: ["key-abc123"]
    state: present

- name: Delete a policy
  stormagic.stormagic.svkms_policy:
    name: app-key-policy
    state: absent
"""

RETURN = r"""
policy:
  description: The policy object returned by SvKMS.
  type: dict
  returned: when state is present
  sample:
    name: "app-key-policy"
    rules:
      - principal: "app-user"
        actions: ["encrypt", "decrypt"]
        resources: ["key-abc123"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def find_policy_by_name(client, name):
    policies = client.list_policies()
    for policy in policies:
        if policy.get("name") == name:
            return policy
    return None


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        name=dict(type="str", required=True),
        rules=dict(type="list", elements="dict"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]
    name = module.params["name"]
    rules = module.params.get("rules")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
        )

        existing_policy = find_policy_by_name(client, name)

        if state == "present":
            if existing_policy:
                module.exit_json(changed=False, policy=existing_policy)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, policy={})
                policy = client.create_policy(name=name, rules=rules)
                module.exit_json(changed=True, policy=policy)

        elif state == "absent":
            if not existing_policy:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True)
                client.delete_policy(name)
                module.exit_json(changed=True)

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
