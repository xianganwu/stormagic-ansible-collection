#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_health_check
short_description: Run health checks on a StorMagic SvSAN VSA
version_added: "1.0.0"
description:
  - Performs comprehensive health checks against a StorMagic SvSAN Virtual Storage Appliance.
  - Checks connectivity, license validity, target status, mirror synchronization, and pool capacity.
  - Returns structured pass/warn/fail results for use in patching workflows.
  - Fails the task if any check returns fail status.
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
  checks:
    description:
      - List of health checks to perform.
    type: list
    elements: str
    default: [connectivity, license, targets, mirrors, pools]
  mirror_sync_threshold:
    description:
      - Minimum acceptable mirror synchronization percentage.
    type: int
    default: 100
  pool_capacity_warn_pct:
    description:
      - Pool usage percentage that triggers a warning.
    type: int
    default: 80
extends_documentation_fragment:
  - xianganwu.stormagic.svsan
seealso:
  - module: xianganwu.stormagic.svsan_vsa
  - module: xianganwu.stormagic.svsan_esxi_preflight
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Run full VSA health check
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: health

- name: Pre-patching health gate
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_host }}"
    vsa_username: "{{ svsan_user }}"
    vsa_password: "{{ svsan_pass }}"
    checks:
      - connectivity
      - mirrors
      - targets
    mirror_sync_threshold: 100
  delegate_to: "{{ windows_mgmt_host }}"
  register: preflight

- name: Abort if unhealthy
  ansible.builtin.fail:
    msg: "VSA not ready for patching"
  when: preflight.health.overall != 'pass'

- name: Health check with custom pool capacity threshold
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    pool_capacity_warn_pct: 90
    mirror_sync_threshold: 95
  delegate_to: "{{ windows_mgmt_host }}"
  register: health

- name: Test health check connectivity in check mode
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    checks:
      - connectivity
  delegate_to: "{{ windows_mgmt_host }}"
  check_mode: true
  register: result
"""

RETURN = r"""
health:
  description: Structured health check results.
  type: dict
  returned: always
  contains:
    overall:
      description: Overall status — pass, warn, or fail.
      type: str
      returned: always
    checks:
      description: Individual check results.
      type: dict
      returned: always
    details:
      description: Detailed data for each check.
      type: dict
      returned: always
  sample:
    overall: "pass"
    checks:
      connectivity: "pass"
      license: "pass"
      targets: "pass"
      mirrors: "pass"
      pools: "warn"
    details:
      license:
        is_valid: true
        expiry: "2027-01-01"
"""
