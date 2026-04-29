# -*- coding: utf-8 -*-

# Copyright: (c) 2025, StorMagic <support@stormagic.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


SVKMS_COMMON_ARGS = dict(
    state=dict(type="str", default="present", choices=["present", "absent"]),
)

SVKMS_KEY_STATES = dict(
    state=dict(type="str", default="present", choices=["present", "absent", "rotated", "retired"]),
)
