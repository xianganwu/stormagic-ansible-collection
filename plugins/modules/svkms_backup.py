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
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Backup SvKMS data
  xianganwu.stormagic.svkms_backup:
    action: backup
    destination: /backup/svkms-backup.tar.gz

- name: Restore SvKMS data
  xianganwu.stormagic.svkms_backup:
    action: restore
    source: /backup/svkms-backup.tar.gz
"""

RETURN = r"""
result:
  description: The result of the backup or restore operation.
  type: dict
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
)


def main():
    argument_spec = dict(
        action=dict(type="str", required=True, choices=["backup", "restore"]),
        destination=dict(type="str"),
        source=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ("action", "backup", ["destination"]),
            ("action", "restore", ["source"]),
        ],
    )

    action = module.params["action"]
    destination = module.params.get("destination")
    source = module.params.get("source")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
        )

        if action == "backup":
            if module.check_mode:
                module.exit_json(changed=True, result={"action": "backup", "path": destination})
            result = client.backup(destination)
            module.exit_json(changed=True, result=result)

        elif action == "restore":
            if module.check_mode:
                module.exit_json(changed=True, result={"action": "restore", "path": source})
            result = client.restore(source)
            module.exit_json(changed=True, result=result)

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
