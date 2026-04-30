#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_mirror_info
short_description: Gather facts about StorMagic SvSAN mirrors
version_added: "1.0.0"
description:
  - Retrieves mirror status and synchronization information from a StorMagic SvSAN VSA.
  - Returns details for all configured mirrors including sync percentage and remote VSA.
  - Read-only module that never modifies VSA state.
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
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_mirror
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Get mirror status
  xianganwu.stormagic.svsan_mirror_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: mirror_facts

- name: Check mirror sync status
  ansible.builtin.debug:
    msg: "Mirror {{ item.name }} is {{ item.sync_pct }}% synced"
  loop: "{{ mirror_facts.mirrors }}"
  when: item.sync_pct < 100

- name: Get mirrors and assert all are fully synced
  xianganwu.stormagic.svsan_mirror_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: mirror_info

- name: Assert all mirrors are at 100 percent sync
  ansible.builtin.assert:
    that: item.sync_pct == 100
    fail_msg: "Mirror {{ item.name }} is only {{ item.sync_pct }}% synced"
  loop: "{{ mirror_info.mirrors }}"
"""

RETURN = r"""
mirrors:
  description: List of mirror configurations and their status.
  type: list
  returned: always
  elements: dict
  contains:
    name:
      description: Mirror name.
      type: str
    sync_pct:
      description: Synchronization percentage (0-100).
      type: int
    remote_vsa:
      description: Remote VSA hostname.
      type: str
    target_name:
      description: Associated target name.
      type: str
  sample:
    - name: "mirror1"
      sync_pct: 100
      remote_vsa: "vsa2.example.com"
      target_name: "target1"
"""
