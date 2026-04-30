# -*- coding: utf-8 -*-

# Copyright: (c) 2026, StorMagic <support@stormagic.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  host:
    description:
      - Hostname or IP address of the SvKMS server.
    type: str
    required: true
  port:
    description:
      - Port for the SvKMS REST API.
    type: int
    default: 1443
  validate_certs:
    description:
      - Whether to validate SSL/TLS certificates when connecting to SvKMS.
      - Set to C(false) for environments using self-signed certificates.
    type: bool
    default: true
  ca_path:
    description:
      - Path to a CA certificate bundle for SSL/TLS verification.
      - Only used when I(validate_certs) is C(true).
    type: str
attributes:
  check_mode:
    description: Supports check mode.
    support: full
  diff_mode:
    description: Returns before/after state for changed resources.
    support: full
  platform:
    description: Target OS/API for this module.
    platforms: httpapi
    support: N/A
notes:
  - This module requires the C(xianganwu.stormagic.svkms) httpapi plugin.
  - Set C(ansible_network_os=xianganwu.stormagic.svkms) in your inventory.
  - Set C(ansible_connection=ansible.netcommon.httpapi) for the SvKMS host.
  - Authentication uses username/password or API key via C(ansible_httpapi_svkms_api_key).
seealso:
  - name: StorMagic SvKMS Documentation
    description: Official StorMagic SvKMS documentation.
    link: https://stormagic.com/encryption-key-management/documentation/
"""
