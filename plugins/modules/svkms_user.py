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
  - stormagic.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create an admin user
  stormagic.stormagic.svkms_user:
    username: admin-user
    role: admin
    auth_type: password
    state: present

- name: Create an operator with certificate auth
  stormagic.stormagic.svkms_user:
    username: ops-user
    role: operator
    auth_type: certificate
    state: present

- name: Delete a user
  stormagic.stormagic.svkms_user:
    username: ops-user
    state: absent
"""

RETURN = r"""
user:
  description: The user object returned by SvKMS.
  type: dict
  returned: when state is present
  sample:
    username: "admin-user"
    role: "admin"
    auth_type: "password"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def find_user_by_username(client, username):
    users = client.list_users()
    for user in users:
        if user.get("username") == username:
            return user
    return None


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        username=dict(type="str", required=True),
        role=dict(type="str", default="operator", choices=["admin", "operator", "auditor"]),
        auth_type=dict(type="str", default="password", choices=["password", "certificate"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]
    username = module.params["username"]
    role = module.params.get("role", "operator")
    auth_type = module.params.get("auth_type", "password")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
        )

        existing_user = find_user_by_username(client, username)

        if state == "present":
            if existing_user:
                module.exit_json(changed=False, user=existing_user)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, user={})
                user = client.create_user(username=username, role=role, auth_type=auth_type)
                module.exit_json(changed=True, user=user)

        elif state == "absent":
            if not existing_user:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True)
                client.delete_user(existing_user["id"])
                module.exit_json(changed=True)

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
