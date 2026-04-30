# -*- coding: utf-8 -*-

# Copyright: (c) 2026, StorMagic Ltd <support@stormagic.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

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
  api_key:
    description:
      - API key for SvKMS authentication.
      - Mutually exclusive with I(username)/I(password).
      - One of I(api_key) or I(username) is required.
    type: str
  username:
    description:
      - Username for SvKMS authentication.
      - Mutually exclusive with I(api_key).
      - Required together with I(password).
    type: str
  password:
    description:
      - Password for SvKMS authentication.
      - Required together with I(username).
    type: str
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
    platforms: controller
    support: N/A
notes:
  - Modules connect directly to the SvKMS REST API.
  - Authenticate with either I(api_key) or I(username)/I(password).
seealso:
  - name: StorMagic SvKMS Documentation
    description: Official StorMagic SvKMS documentation.
    link: https://stormagic.com/encryption-key-management/documentation/
"""
