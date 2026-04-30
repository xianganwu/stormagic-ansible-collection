#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_user
short_description: Manage users on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Create, update, and delete users on a StorMagic SvKMS server.
  - Supports idempotent user creation and check mode.
options:
  state:
    description:
      - Desired state of the user.
      - C(present) ensures the user exists, creating it if necessary.
      - C(absent) ensures the user does not exist, deleting it if necessary.
    type: str
    default: present
    choices: [present, absent]
  username:
    description:
      - Username for the SvKMS user.
    type: str
    required: true
  role:
    description:
      - Role assigned to the user.
    type: str
    choices: [admin, operator, auditor]
    default: operator
  auth_type:
    description:
      - Authentication type for the user.
    type: str
    choices: [password, certificate]
    default: password
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create an admin user
  xianganwu.stormagic.svkms_user:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    username: admin-user
    role: admin
    auth_type: password
    state: present

- name: Create an operator with certificate auth
  xianganwu.stormagic.svkms_user:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    username: ops-user
    role: operator
    auth_type: certificate
    state: present

- name: Delete a user
  xianganwu.stormagic.svkms_user:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    username: ops-user
    state: absent
"""

RETURN = r"""
user:
  description: The user object returned by SvKMS.
  type: dict
  returned: when state is present
  contains:
    username:
      description: Username of the SvKMS user.
      type: str
      returned: always
    role:
      description: Role assigned to the user.
      type: str
      returned: always
    auth_type:
      description: Authentication type for the user.
      type: str
      returned: always
  sample:
    username: "admin-user"
    role: "admin"
    auth_type: "password"
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


def find_user_by_username(client, username):
    users = client.list_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None


def main():
    argument_spec = svkms_argument_spec()
    argument_spec.update(dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        username=dict(type="str", required=True),
        role=dict(type="str", default="operator", choices=["admin", "operator", "auditor"]),
        auth_type=dict(type="str", default="password", choices=["password", "certificate"]),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=SVKMS_MUTUALLY_EXCLUSIVE,
        required_one_of=SVKMS_REQUIRED_ONE_OF,
        required_together=SVKMS_REQUIRED_TOGETHER,
    )

    state = module.params["state"]
    username = module.params["username"]
    role = module.params.get("role", "operator")
    auth_type = module.params.get("auth_type", "password")

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

        existing_user = find_user_by_username(client, username)

        if state == "present":
            if existing_user:
                updates = {}
                if existing_user.get("role") != role:
                    updates["role"] = role
                if existing_user.get("auth_type") != auth_type:
                    updates["auth_type"] = auth_type
                if updates:
                    if module.check_mode:
                        after = dict(existing_user)
                        after.update(updates)
                        module.exit_json(changed=True, user=existing_user, diff={"before": existing_user, "after": after})
                    updated = client.update_user(existing_user["id"], **updates)
                    module.exit_json(changed=True, user=updated, diff={"before": existing_user, "after": updated})
                module.exit_json(changed=False, user=existing_user)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, user={}, diff={"before": {}, "after": {"username": username}})
                user = client.create_user(username=username, role=role, auth_type=auth_type)
                module.exit_json(changed=True, user=user, diff={"before": {}, "after": user})

        elif state == "absent":
            if not existing_user:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, diff={"before": existing_user, "after": {}})
                client.delete_user(existing_user["id"])
                module.exit_json(changed=True, diff={"before": existing_user, "after": {}})

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
