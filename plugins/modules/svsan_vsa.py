#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_vsa
short_description: Deploy StorMagic SvSAN VSA instances on vSphere
version_added: "1.0.0"
description:
  - Deploys StorMagic SvSAN Virtual Storage Appliance instances to VMware vSphere.
  - Automates OVA deployment and initial VSA configuration.
  - Removal not supported — manage via vSphere directly.
options:
  vsa_hostname:
    description:
      - Hostname or IP for the new VSA instance.
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
      - Desired state of the VSA instance.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Name for the VSA VM in vSphere.
    type: str
    required: true
  vcenter:
    description:
      - vCenter hostname or IP.
    type: str
  datacenter:
    description:
      - vSphere datacenter name.
    type: str
  cluster:
    description:
      - vSphere cluster name.
    type: str
  datastore:
    description:
      - vSphere datastore for VSA storage.
    type: str
  network:
    description:
      - vSphere network/portgroup for VSA.
    type: str
  disk_size_gb:
    description:
      - Storage disk size in GB.
    type: int
extends_documentation_fragment:
  - stormagic.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Deploy VSA to vSphere
  stormagic.stormagic.svsan_vsa:
    vsa_hostname: vsa3.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
    name: vsa3
    vcenter: vcenter.example.com
    datacenter: DC1
    cluster: Cluster1
    datastore: datastore1
    network: "VM Network"
    disk_size_gb: 500
    state: present
  delegate_to: "{{ windows_mgmt_host }}"
"""

RETURN = r"""
vsa:
  description: VSA deployment details.
  type: dict
  returned: when state=present
  contains:
    name:
      description: VSA name.
      type: str
    hostname:
      description: VSA hostname.
      type: str
    deployed:
      description: Whether deployment succeeded.
      type: bool
  sample:
    name: "vsa3"
    hostname: "vsa3.example.com"
    deployed: true
"""
