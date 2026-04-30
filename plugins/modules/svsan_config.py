#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_config
short_description: Manage StorMagic SvSAN VSA configuration
version_added: "1.0.0"
description:
  - Manages configuration settings for a StorMagic SvSAN VSA.
  - Idempotent — only applies changes when current config differs from desired.
  - Reads current configuration and applies only modified settings.
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
  settings:
    description:
      - Dictionary of configuration settings to apply.
    type: dict
    version_added: "1.0.0"
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_config_info
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Configure VSA settings
  xianganwu.stormagic.svsan_config:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    settings:
      heartbeat_interval: 30
      log_level: "INFO"
      auto_failover: true
  delegate_to: "{{ windows_mgmt_host }}"

- name: Check configuration changes (dry run)
  xianganwu.stormagic.svsan_config:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    settings:
      heartbeat_interval: 30
  check_mode: true
  delegate_to: "{{ windows_mgmt_host }}"
  register: config_changes

- name: Enable auto-failover and adjust logging
  xianganwu.stormagic.svsan_config:
    vsa_hostname: "{{ svsan_host }}"
    vsa_username: "{{ svsan_user }}"
    vsa_password: "{{ svsan_pass }}"
    settings:
      auto_failover: true
      log_level: "WARN"
      heartbeat_interval: 15
  delegate_to: "{{ windows_mgmt_host }}"
  register: config_result
"""

RETURN = r"""
config:
  description: Current VSA configuration after changes.
  type: dict
  returned: always
  sample:
    heartbeat_interval: 30
    log_level: "INFO"
    auto_failover: true
updates:
  description: Dictionary of settings that were changed.
  type: dict
  returned: when changed
  sample:
    heartbeat_interval: 30
"""
