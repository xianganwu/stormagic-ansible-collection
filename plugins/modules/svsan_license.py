#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_license
short_description: Manage StorMagic SvSAN licenses
version_added: "1.0.0"
description:
  - Applies license keys to StorMagic SvSAN VSAs.
  - Licenses cannot be removed once applied.
  - Supports check mode for validation without applying.
options:
  vsa_hostname:
    description:
      - Hostname or IP of the target SvSAN VSA.
    type: str
    required: true
  vsa_username:
    description:
      - Username for VSA authentication.
    type: str
    required: true
  vsa_password:
    description:
      - Password for VSA authentication.
    type: str
    required: true
    no_log: true
  license_key:
    description:
      - SvSAN license key to apply.
    type: str
    required: true
    no_log: true
extends_documentation_fragment:
  - stormagic.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Apply SvSAN license
  stormagic.stormagic.svsan_license:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    license_key: "{{ vault_svsan_license }}"
  delegate_to: "{{ windows_mgmt_host }}"

- name: Check license application (dry run)
  stormagic.stormagic.svsan_license:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    license_key: "{{ vault_svsan_license }}"
  check_mode: true
  delegate_to: "{{ windows_mgmt_host }}"
"""

RETURN = r"""
license_applied:
  description: Whether the license was successfully applied.
  type: bool
  returned: always
  sample: true
"""
