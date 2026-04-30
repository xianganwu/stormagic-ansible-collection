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
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
  register: health

- name: Assert healthy
  ansible.builtin.assert:
    that: health.health.status == 'healthy'

- name: Check SvKMS health without certificate validation
  xianganwu.stormagic.svkms_health_check:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    validate_certs: false
  register: health

- name: Test health check connectivity in check mode
  xianganwu.stormagic.svkms_health_check:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
  check_mode: true
  register: result
"""

RETURN = r"""
health:
  description: Health status from SvKMS.
  type: dict
  returned: on success
  contains:
    status:
      description: Server health status.
      type: str
      returned: always
    version:
      description: SvKMS server version.
      type: str
      returned: always
  sample:
    status: "healthy"
    version: "4.2.0"
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

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=SVKMS_MUTUALLY_EXCLUSIVE,
        required_one_of=SVKMS_REQUIRED_ONE_OF,
        required_together=SVKMS_REQUIRED_TOGETHER,
    )

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
        health = client.health_check()
        status = health.get("status", "unknown") if isinstance(health, dict) else "unknown"
        if status not in ("healthy", "ok"):
            module.fail_json(
                msg="SvKMS server reports unhealthy status: {0}".format(status),
                health=health,
            )
        module.exit_json(changed=False, health=health)
    except SvKMSAPIError as e:
        error_msg = "SvKMS health check failed: {0}".format(str(e))
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
