# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  vsa_hostname:
    description:
      - Hostname or IP address of the StorMagic SvSAN VSA to manage.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_username:
    description:
      - Username for authenticating to the VSA.
    type: str
    required: true
    version_added: "1.0.0"
  vsa_password:
    description:
      - Password for authenticating to the VSA.
    type: str
    required: true
    no_log: true
    version_added: "1.0.0"
attributes:
  check_mode:
    description: Supports check mode.
    support: full
  diff_mode:
    description: Returns before/after state for changed resources.
    support: full
  platform:
    description: Target OS/API for this module.
    platforms: windows
    support: N/A
notes:
  - This module runs on a Windows host with the StorMagic PowerShell Toolkit installed.
  - Set C(ansible_connection=winrm) or C(ansible_connection=psrp) for the Windows management host.
  - The StorMagic PowerShell Toolkit (SmCmdlet) must be installed on the target Windows host.
  - Use C(delegate_to) when targeting ESXi hosts but needing to run StorMagic commands on a Windows host.
requirements:
  - StorMagic PowerShell Toolkit (SmCmdlet.dll) — bundled with SvSAN installation
  - PowerShell 5.1 or later
  - WinRM or PSRP connectivity to the Windows management host
seealso:
  - name: StorMagic SvSAN Documentation
    description: Official StorMagic SvSAN documentation.
    link: https://stormagic.com/svsan/documentation/
"""
