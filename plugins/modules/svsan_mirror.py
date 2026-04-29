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
  state:
    description:
      - Desired state of the mirror.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Name of the mirror configuration.
    type: str
    required: true
  remote_vsa:
    description:
      - Hostname or IP of the remote VSA for mirroring.
    type: str
  remote_pool:
    description:
      - Storage pool on the remote VSA to mirror to.
    type: str
extends_documentation_fragment:
  - stormagic.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create storage mirror
  stormagic.stormagic.svsan_mirror:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: mirror1
    remote_vsa: vsa2.example.com
    remote_pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"

- name: Remove storage mirror
  stormagic.stormagic.svsan_mirror:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: mirror1
    state: absent
  delegate_to: "{{ windows_mgmt_host }}"
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
    remote_vsa:
      description: Remote VSA hostname.
      type: str
    sync_pct:
      description: Synchronization percentage.
      type: int
  sample:
    name: "mirror1"
    remote_vsa: "vsa2.example.com"
    sync_pct: 100
"""
