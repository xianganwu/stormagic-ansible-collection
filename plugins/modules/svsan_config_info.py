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
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_config
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Get VSA configuration
  xianganwu.stormagic.svsan_config_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: vsa_config

- name: Display heartbeat interval
  ansible.builtin.debug:
    msg: "Heartbeat interval: {{ vsa_config.config.heartbeat_interval }}"

- name: Get configuration and verify auto-failover is enabled
  xianganwu.stormagic.svsan_config_info:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: config_info

- name: Assert auto-failover is enabled
  ansible.builtin.assert:
    that: config_info.config.auto_failover == true
    fail_msg: "Auto-failover is not enabled on this VSA"
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
