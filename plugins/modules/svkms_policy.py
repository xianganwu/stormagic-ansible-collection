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
notes:
  - O(rules) is required when O(state=present).
  - Each rule in O(rules) must include O(rules[].principal), O(rules[].actions), and O(rules[].resources).
options:
  state:
    description:
      - Desired state of the policy.
      - C(present) ensures the policy exists, creating it if necessary.
      - C(absent) ensures the policy does not exist, deleting it if necessary.
    type: str
    default: present
    choices: [present, absent]
    version_added: "1.0.0"
  name:
    description:
      - Name of the policy.
    type: str
    required: true
    version_added: "1.0.0"
  rules:
    description:
      - List of policy rules. Each rule defines access permissions.
      - Required when O(state=present).
    type: list
    elements: dict
    suboptions:
      principal:
        description:
          - Username or group that this rule applies to.
        type: str
        required: true
      actions:
        description:
          - List of permitted actions (e.g., V(encrypt), V(decrypt), V(sign), V(verify)).
        type: list
        elements: str
        required: true
      resources:
        description:
          - List of key names or IDs that this rule grants access to.
        type: list
        elements: str
        required: true
    version_added: "1.0.0"
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
seealso:
  - module: xianganwu.stormagic.svkms_key
  - module: xianganwu.stormagic.svkms_user
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create a key access policy
  xianganwu.stormagic.svkms_policy:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    name: app-key-policy
    rules:
      - principal: "app-user"
        actions: ["encrypt", "decrypt"]
        resources: ["key-abc123"]
    state: present

- name: Delete a policy
  xianganwu.stormagic.svkms_policy:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    name: app-key-policy
    state: absent

- name: Test policy creation in check mode
  xianganwu.stormagic.svkms_policy:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    name: staging-policy
    rules:
      - principal: "staging-user"
        actions: ["encrypt", "decrypt"]
        resources: ["key-staging"]
    state: present
  check_mode: true
  register: result
"""

RETURN = r"""
policy:
  description: The policy object returned by SvKMS.
  type: dict
  returned: when state is present
  contains:
    name:
      description: Policy name.
      type: str
      returned: always
    rules:
      description: List of access rules for this policy.
      type: list
      returned: always
  sample:
    name: "app-key-policy"
    rules:
      - principal: "app-user"
        actions: ["encrypt", "decrypt"]
        resources: ["key-abc123"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
    svkms_argument_spec,
    SVKMS_MUTUALLY_EXCLUSIVE,
    SVKMS_REQUIRED_ONE_OF,
    SVKMS_REQUIRED_TOGETHER,
)


def find_policy_by_name(client, name):
    policies = client.list_policies()
    for policy in policies:
        if policy.get("name") == name:
            return policy
    return None


def main():
    argument_spec = svkms_argument_spec()
    argument_spec.update(dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        name=dict(type="str", required=True),
        rules=dict(type="list", elements="dict"),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=SVKMS_MUTUALLY_EXCLUSIVE,
        required_one_of=SVKMS_REQUIRED_ONE_OF,
        required_together=SVKMS_REQUIRED_TOGETHER,
        required_if=[
            ("state", "present", ["rules"]),
        ],
    )

    state = module.params["state"]
    name = module.params["name"]
    rules = module.params.get("rules")

    client = None
    try:
        host = module.params["host"]

        client = SvKMSClient(
            host=host,
            port=module.params["port"],
            api_key=module.params.get("api_key"),
            username=module.params.get("username"),
            password=module.params.get("password"),
            validate_certs=module.params.get("validate_certs", True),
            ca_path=module.params.get("ca_path"),
        )
        client.login()

        existing_policy = find_policy_by_name(client, name)

        if state == "present":
            if existing_policy:
                if rules is not None and existing_policy.get("rules") != rules:
                    if module.check_mode:
                        after = dict(existing_policy)
                        after["rules"] = rules
                        module.exit_json(changed=True, policy=existing_policy, diff={"before": existing_policy, "after": after})
                    updated = client.update_policy(existing_policy["id"], rules)
                    module.exit_json(changed=True, policy=updated, diff={"before": existing_policy, "after": updated})
                module.exit_json(changed=False, policy=existing_policy)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, policy={}, diff={"before": {}, "after": {"name": name}})
                policy = client.create_policy(name=name, rules=rules)
                module.exit_json(changed=True, policy=policy, diff={"before": {}, "after": policy})

        elif state == "absent":
            if not existing_policy:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, diff={"before": existing_policy, "after": {}})
                client.delete_policy(existing_policy["id"])
                module.exit_json(changed=True, diff={"before": existing_policy, "after": {}})

    except SvKMSAPIError as e:
        error_msg = "SvKMS API error: {0}".format(str(e))
        if e.response_body and isinstance(e.response_body, dict):
            detail = e.response_body.get("detail") or e.response_body.get("message", "")
            if detail:
                error_msg += " - {0}".format(detail)
        module.fail_json(msg=error_msg, status_code=getattr(e, "status_code", None))
    finally:
        if client:
            client.logout()


if __name__ == "__main__":
    main()
