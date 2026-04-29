#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_config_info
short_description: Gather facts about StorMagic SvSAN VSA configuration
version_added: "1.0.0"
description:
  - Retrieves configuration settings from a StorMagic SvSAN VSA.
  - Returns full configuration dictionary for fact gathering.
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
  - stormagic.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Get VSA configuration
  stormagic.stormagic.svsan_config_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: vsa_config

- name: Display heartbeat interval
  ansible.builtin.debug:
    msg: "Heartbeat interval: {{ vsa_config.config.heartbeat_interval }}"
"""

RETURN = r"""
config:
  description: Full VSA configuration dictionary.
  type: dict
  returned: always
  sample:
    heartbeat_interval: 30
    log_level: "INFO"
    auto_failover: true
    max_targets: 128
"""
