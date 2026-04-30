#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_mirror
short_description: Manage StorMagic SvSAN mirrored storage
version_added: "1.0.0"
description:
  - Creates and removes mirrored storage configurations in StorMagic SvSAN.
  - Mirrors provide high availability by synchronizing storage between VSAs.
  - Supports check mode for safe pre-flight validation.
notes:
  - O(remote_vsa) and O(remote_pool) are required when O(state=present).
options:
  state:
    description:
      - Desired state of the mirror.
    type: str
    choices: [present, absent]
    default: present
    version_added: "1.0.0"
  name:
    description:
      - Name of the mirror configuration.
    type: str
    required: true
    version_added: "1.0.0"
  remote_vsa:
    description:
      - Hostname or IP of the remote VSA for mirroring.
    type: str
    version_added: "1.0.0"
  remote_pool:
    description:
      - Storage pool on the remote VSA to mirror to.
    type: str
    version_added: "1.0.0"
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_mirror_info
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create storage mirror
  xianganwu.stormagic.svsan_mirror:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: mirror1
    remote_vsa: vsa2.example.com
    remote_pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"

- name: Remove storage mirror
  xianganwu.stormagic.svsan_mirror:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: mirror1
    state: absent
  delegate_to: "{{ windows_mgmt_host }}"

- name: Test mirror creation in check mode
  xianganwu.stormagic.svsan_mirror:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: mirror-staging
    remote_vsa: vsa2.example.com
    remote_pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"
  check_mode: true
  register: result
"""

RETURN = r"""
mirror:
  description: Mirror configuration details.
  type: dict
  returned: when state=present
  contains:
    name:
      description: Mirror name.
      type: str
      returned: always
    remote_vsa:
      description: Remote VSA hostname.
      type: str
      returned: always
    sync_pct:
      description: Synchronization percentage.
      type: int
      returned: always
  sample:
    name: "mirror1"
    remote_vsa: "vsa2.example.com"
    sync_pct: 100
"""
