#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_health_check
short_description: Check health of a StorMagic SvKMS server
version_added: "1.0.0"
description:
  - Query the SvKMS health endpoint and return server status.
  - Fails the task if the server is unreachable or reports unhealthy.
options: {}
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Check SvKMS health
  xianganwu.stormagic.svkms_health_check:
  register: health

- name: Assert healthy
  ansible.builtin.assert:
    that: health.health.status == 'healthy'
"""

RETURN = r"""
health:
  description: Health status from SvKMS.
  type: dict
  returned: on success
  sample:
    status: "healthy"
    version: "4.2.0"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def main():
    argument_spec = dict(
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
            validate_certs=module.params.get("validate_certs", True),
            ca_path=module.params.get("ca_path"),
        )
        health = client.health_check()
        module.exit_json(changed=False, health=health)
    except SvKMSAPIError as e:
        error_msg = "SvKMS health check failed: {0}".format(str(e))
        if e.response_body and isinstance(e.response_body, dict):
            detail = e.response_body.get("detail") or e.response_body.get("message", "")
            if detail:
                error_msg += " - {0}".format(detail)
        module.fail_json(msg=error_msg, status_code=getattr(e, "status_code", None))


if __name__ == "__main__":
    main()
