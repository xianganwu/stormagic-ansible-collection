#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_esxi_preflight
short_description: Pre-patching checks for ESXi hosts via vCenter
version_added: "1.2.0"
description:
  - Gathers ESXi host information from vCenter for patching decisions.
  - Retrieves active alerts, build number, version, and maintenance mode status.
  - Requires VMware PowerCLI on the Windows management host.
  - Designed to run before ESXi patching to verify the host is safe to patch.
options:
  vcenter_hostname:
    description:
      - Hostname or IP of the vCenter Server.
    type: str
    required: true
    version_added: "1.2.0"
  vcenter_username:
    description:
      - Username for vCenter authentication.
    type: str
    required: true
    version_added: "1.2.0"
  vcenter_password:
    description:
      - Password for vCenter authentication.
    type: str
    required: true
    version_added: "1.2.0"
  esxi_hostname:
    description:
      - Hostname or IP of the ESXi host to check.
    type: str
    required: true
    version_added: "1.2.0"
  validate_certs:
    description:
      - Whether to validate vCenter TLS certificates.
    type: bool
    default: true
    version_added: "1.2.0"
  alert_severity:
    description:
      - Alert severity levels to retrieve.
    type: list
    elements: str
    default: ["error", "warning"]
    version_added: "1.2.0"
  max_alerts:
    description:
      - Maximum number of alert events to retrieve.
    type: int
    default: 100
    version_added: "1.2.0"
notes:
  - Requires VMware PowerCLI installed on the Windows management host.
  - Must be delegated to a Windows host with C(delegate_to).
  - Alerts are retrieved from the last 7 days.
requirements:
  - VMware PowerCLI >= 12.0
  - PowerShell 5.1+
seealso:
  - module: xianganwu.stormagic.svsan_health_check
  - module: vmware.vmware.esxi_maintenance_mode
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Run ESXi preflight checks
  xianganwu.stormagic.svsan_esxi_preflight:
    vcenter_hostname: vcenter.example.com
    vcenter_username: "administrator@vsphere.local"
    vcenter_password: "{{ vault_vcenter_password }}"
    esxi_hostname: esxi1.example.com
  delegate_to: "{{ windows_mgmt_host }}"
  register: esxi_preflight

- name: Skip patching if already at target build
  ansible.builtin.debug:
    msg: "Host already at target build {{ esxi_preflight.esxi_build }}"
  when: esxi_preflight.esxi_build == target_esxi_build

- name: Abort if blocking alerts exist
  ansible.builtin.fail:
    msg: >-
      ESXi host {{ inventory_hostname }} has {{ esxi_preflight.alert_count }}
      active alerts — resolve before patching
  when: esxi_preflight.has_blocking_alerts
"""

RETURN = r"""
esxi_build:
  description: ESXi build number.
  type: str
  returned: always
  sample: "21495797"
esxi_version:
  description: ESXi version string.
  type: str
  returned: always
  sample: "8.0.0"
maintenance_mode:
  description: Whether the host is currently in maintenance mode.
  type: bool
  returned: always
alerts:
  description: List of active alerts on the ESXi host.
  type: list
  elements: dict
  returned: always
  contains:
    time:
      description: Alert timestamp in ISO 8601 format.
      type: str
    severity:
      description: Alert severity level.
      type: str
    message:
      description: Full alert message.
      type: str
  sample:
    - time: "2026-04-29T10:30:00Z"
      severity: "Warning"
      message: "Host memory usage exceeded threshold"
alert_count:
  description: Number of active alerts.
  type: int
  returned: always
has_blocking_alerts:
  description: Whether any error-severity alerts exist.
  type: bool
  returned: always
"""
