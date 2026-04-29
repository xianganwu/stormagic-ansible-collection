#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_pool
short_description: Manage StorMagic SvSAN storage pools
version_added: "1.0.0"
description:
  - Creates and removes storage pools in StorMagic SvSAN.
  - Storage pools aggregate physical disks for target provisioning.
  - Supports check mode for safe pre-flight validation.
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
  state:
    description:
      - Desired state of the storage pool.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Name of the storage pool.
    type: str
    required: true
  disk_ids:
    description:
      - List of disk identifiers to include in the pool.
    type: list
    elements: str
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create storage pool
  xianganwu.stormagic.svsan_pool:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: pool1
    disk_ids:
      - "disk-0"
      - "disk-1"
    state: present
  delegate_to: "{{ windows_mgmt_host }}"

- name: Remove storage pool
  xianganwu.stormagic.svsan_pool:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: pool1
    state: absent
  delegate_to: "{{ windows_mgmt_host }}"
"""

RETURN = r"""
pool:
  description: Storage pool details.
  type: dict
  returned: when state=present
  contains:
    name:
      description: Pool name.
      type: str
    total_gb:
      description: Total capacity in GB.
      type: int
    free_gb:
      description: Free capacity in GB.
      type: int
  sample:
    name: "pool1"
    total_gb: 500
    free_gb: 250
"""
