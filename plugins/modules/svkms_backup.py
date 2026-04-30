#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_backup
short_description: Backup and restore StorMagic SvKMS data
version_added: "1.0.0"
description:
  - Perform backup and restore operations on a StorMagic SvKMS server.
  - This is an action-based module - it always reports changed=true.
options:
  action:
    description:
      - Action to perform.
      - C(backup) creates a backup of SvKMS data.
      - C(restore) restores SvKMS data from a backup.
    type: str
    required: true
    choices: [backup, restore]
  destination:
    description:
      - Destination path for backup files.
      - Required when action is backup.
    type: str
  source:
    description:
      - Source path for restore operation.
      - Required when action is restore.
    type: str
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
seealso:
  - module: xianganwu.stormagic.svkms_health_check
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Backup SvKMS data
  xianganwu.stormagic.svkms_backup:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    action: backup
    destination: /backup/svkms-backup.tar.gz

- name: Restore SvKMS data
  xianganwu.stormagic.svkms_backup:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    action: restore
    source: /backup/svkms-backup.tar.gz

- name: Test backup in check mode
  xianganwu.stormagic.svkms_backup:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    action: backup
    destination: /backup/svkms-backup.tar.gz
  check_mode: true
  register: result

- name: Backup before upgrade and register result
  xianganwu.stormagic.svkms_backup:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    action: backup
    destination: "/backup/svkms-pre-upgrade-{{ ansible_date_time.date }}.tar.gz"
  register: backup_result
"""

RETURN = r"""
result:
  description: The result of the backup or restore operation.
  type: dict
  returned: always
  contains:
    action:
      description: The action that was performed.
      type: str
      returned: always
    path:
      description: File path used for the operation.
      type: str
      returned: always
    status:
      description: Outcome of the operation.
      type: str
      returned: always
  sample:
    action: "backup"
    path: "/backup/svkms-backup.tar.gz"
    status: "success"
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


def main():
    argument_spec = svkms_argument_spec()
    argument_spec.update(dict(
        action=dict(type="str", required=True, choices=["backup", "restore"]),
        destination=dict(type="str"),
        source=dict(type="str"),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=SVKMS_MUTUALLY_EXCLUSIVE,
        required_one_of=SVKMS_REQUIRED_ONE_OF,
        required_together=SVKMS_REQUIRED_TOGETHER,
        required_if=[
            ("action", "backup", ["destination"]),
            ("action", "restore", ["source"]),
        ],
    )

    action = module.params["action"]
    destination = module.params.get("destination")
    source = module.params.get("source")

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

        if action == "backup":
            if module.check_mode:
                check_result = {"action": "backup", "path": destination, "status": "check"}
                module.exit_json(changed=True, result=check_result,
                                 diff={"before": {}, "after": {"action": "backup"}})
            result = client.backup(destination)
            module.exit_json(changed=True, result=result, diff={"before": {}, "after": result})

        elif action == "restore":
            if module.check_mode:
                check_result = {"action": "restore", "path": source, "status": "check"}
                module.exit_json(changed=True, result=check_result,
                                 diff={"before": {}, "after": {"action": "restore"}})
            result = client.restore(source)
            module.exit_json(changed=True, result=result, diff={"before": {}, "after": result})

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
