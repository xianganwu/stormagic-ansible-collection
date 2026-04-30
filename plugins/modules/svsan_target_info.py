#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_target_info
short_description: Gather information about iSCSI targets on StorMagic SvSAN
version_added: "1.0.0"
description:
  - Retrieve information about all iSCSI targets from a StorMagic SvSAN VSA.
  - Returns target details including path counts, sizes, and mirror status.
  - Read-only — does not make any changes.
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_target
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Get all target information
  xianganwu.stormagic.svsan_target_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: targets

- name: Verify minimum datastore paths
  ansible.builtin.assert:
    that: item.path_count >= 2
    fail_msg: "Target {{ item.name }} has only {{ item.path_count }} paths"
  loop: "{{ targets.targets }}"

- name: Get all targets and display their status
  xianganwu.stormagic.svsan_target_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: target_info

- name: Show offline targets
  ansible.builtin.debug:
    msg: "Target {{ item.name }} is {{ item.status }}"
  loop: "{{ target_info.targets }}"
  when: item.status != 'Online'
"""

RETURN = r"""
targets:
  description: List of target objects from SvSAN.
  type: list
  elements: dict
  returned: always
  contains:
    name:
      description: Target name.
      type: str
      returned: always
    size_gb:
      description: Target size in GB.
      type: int
      returned: always
    status:
      description: Target status.
      type: str
      returned: always
    path_count:
      description: Number of iSCSI paths.
      type: int
      returned: always
    pool:
      description: Storage pool name.
      type: str
      returned: always
  sample:
    - name: "datastore1"
      size_gb: 500
      status: "Online"
      path_count: 4
      pool: "pool1"
      mirror:
        enabled: true
        sync_pct: 100
        remote_vsa: "vsa2.example.com"
"""
