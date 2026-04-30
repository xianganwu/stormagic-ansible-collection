#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_pool_info
short_description: Gather facts about StorMagic SvSAN storage pools
version_added: "1.0.0"
description:
  - Retrieves storage pool information from a StorMagic SvSAN VSA.
  - Returns capacity, usage, and configuration details for all pools.
  - Read-only module that never modifies VSA state.
options:
  vsa_hostname:
    description:
      - Hostname or IP of the target SvSAN VSA.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_username:
    description:
      - Username for VSA authentication.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_password:
    description:
      - Password for VSA authentication.
    type: str
    required: true
    version_added: "1.0.0"
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_pool
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Get pool information
  xianganwu.stormagic.svsan_pool_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: pool_facts

- name: Check pool capacity
  ansible.builtin.debug:
    msg: "Pool {{ item.name }} is {{ item.used_pct }}% full"
  loop: "{{ pool_facts.pools }}"
  when: item.used_pct > 80

- name: Get pools and assert capacity is below threshold
  xianganwu.stormagic.svsan_pool_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: pool_info

- name: Assert no pool exceeds 90 percent usage
  ansible.builtin.assert:
    that: item.used_pct < 90
    fail_msg: "Pool {{ item.name }} is at {{ item.used_pct }}% capacity"
  loop: "{{ pool_info.pools }}"
"""

RETURN = r"""
pools:
  description: List of storage pools and their status.
  type: list
  returned: always
  elements: dict
  contains:
    name:
      description: Pool name.
      type: str
    used_pct:
      description: Percentage of pool capacity used (0-100).
      type: int
    total_gb:
      description: Total pool capacity in GB.
      type: int
    free_gb:
      description: Free capacity in GB.
      type: int
  sample:
    - name: "pool1"
      used_pct: 45
      total_gb: 500
      free_gb: 275
"""
