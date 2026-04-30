#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_target
short_description: Manage iSCSI targets on StorMagic SvSAN
version_added: "1.0.0"
description:
  - Create or remove iSCSI targets on a StorMagic SvSAN VSA.
  - Idempotent — checks for existing targets before creating.
options:
  vsa_hostname:
    description: Hostname or IP of the target SvSAN VSA.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_username:
    description: Username for VSA authentication.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_password:
    description: Password for VSA authentication.
    type: str
    required: true
    version_added: "1.0.0"
  state:
    description: Desired state of the target.
    type: str
    default: present
    choices: [present, absent]
    version_added: "1.0.0"
  name:
    description: Name of the iSCSI target.
    type: str
    required: true
    version_added: "1.0.0"
  size_gb:
    description: Size of the target in GB (required for creation).
    type: int
    version_added: "1.0.0"
  pool:
    description: Storage pool to use for the target.
    type: str
    version_added: "1.0.0"
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_target_info
  - module: xianganwu.stormagic.svsan_pool
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create an iSCSI target
  xianganwu.stormagic.svsan_target:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: datastore1
    size_gb: 500
    pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"

- name: Remove an iSCSI target
  xianganwu.stormagic.svsan_target:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: datastore1
    state: absent
  delegate_to: "{{ windows_mgmt_host }}"

- name: Test target creation in check mode
  xianganwu.stormagic.svsan_target:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: datastore-staging
    size_gb: 250
    pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"
  check_mode: true
  register: result
"""

RETURN = r"""
target:
  description: The target object returned by SvSAN.
  type: dict
  returned: when state is present
  sample:
    name: "datastore1"
    size_gb: 500
    status: "Online"
    pool: "pool1"
"""
