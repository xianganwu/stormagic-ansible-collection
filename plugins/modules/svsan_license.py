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
  license_key:
    description:
      - SvSAN license key to apply.
    type: str
    required: true
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_vsa
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Apply SvSAN license
  xianganwu.stormagic.svsan_license:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    license_key: "{{ vault_svsan_license }}"
  delegate_to: "{{ windows_mgmt_host }}"

- name: Check license application (dry run)
  xianganwu.stormagic.svsan_license:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    license_key: "{{ vault_svsan_license }}"
  check_mode: true
  delegate_to: "{{ windows_mgmt_host }}"

- name: Apply license to all VSAs in inventory
  xianganwu.stormagic.svsan_license:
    vsa_hostname: "{{ svsan_host }}"
    vsa_username: "{{ svsan_user }}"
    vsa_password: "{{ svsan_pass }}"
    license_key: "{{ vault_svsan_license }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: license_result
"""

RETURN = r"""
license:
  description: License information returned by the VSA.
  type: dict
  returned: always
  contains:
    Key:
      description: The license key string.
      type: str
    IsValid:
      description: Whether the license is valid.
      type: bool
  sample:
    Key: "XXXX-XXXX-XXXX-XXXX"
    IsValid: true
"""
