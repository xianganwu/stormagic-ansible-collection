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
  vsa_username:
    description: Username for VSA authentication.
    type: str
    required: true
  vsa_password:
    description: Password for VSA authentication.
    type: str
    required: true
  state:
    description: Desired state of the target.
    type: str
    default: present
    choices: [present, absent]
  name:
    description: Name of the iSCSI target.
    type: str
    required: true
  size_gb:
    description: Size of the target in GB (required for creation).
    type: int
  pool:
    description: Storage pool to use for the target.
    type: str
  mirror:
    description: Enable mirroring for this target.
    type: bool
    default: false
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
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
