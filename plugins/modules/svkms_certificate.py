#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_certificate
short_description: Manage certificates on StorMagic SvKMS
version_added: "1.0.0"
description:
  - List and track certificates on a StorMagic SvKMS server.
  - Supports certificate state validation and check mode.
options:
  state:
    description:
      - Desired state of the certificate.
      - C(present) ensures the certificate exists.
      - C(absent) ensures the certificate does not exist.
    type: str
    default: present
    choices: [present, absent]
  name:
    description:
      - Name of the certificate. Used for idempotent lookups.
    type: str
    required: false
  cert_id:
    description:
      - ID of an existing certificate. If provided, used for lookups.
    type: str
  cert_type:
    description:
      - Type of certificate.
    type: str
    choices: [ca, auth, tls]
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Check if CA certificate exists
  xianganwu.stormagic.svkms_certificate:
    name: root-ca
    cert_type: ca
    state: present

- name: List all certificates
  xianganwu.stormagic.svkms_certificate:
    state: present
"""

RETURN = r"""
certificate:
  description: The certificate object returned by SvKMS.
  type: dict
  returned: when state is present
  sample:
    id: "cert-abc123"
    type: "ca"
    subject: "CN=SvKMS CA"
certificates:
  description: List of all certificates when name is not specified.
  type: list
  returned: when state is present and name is not specified
  sample:
    - id: "cert-1"
      type: "ca"
      subject: "CN=SvKMS CA"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def find_certificate_by_name(client, name):
    certs = client.list_certificates()
    for cert in certs:
        if cert.get("subject") and name in cert.get("subject", ""):
            return cert
    return None


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        name=dict(type="str"),
        cert_id=dict(type="str"),
        cert_type=dict(type="str", choices=["ca", "auth", "tls"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]
    name = module.params.get("name")
    cert_id = module.params.get("cert_id")
    cert_type = module.params.get("cert_type")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
        )

        existing_cert = None
        if cert_id:
            try:
                existing_cert = client.get_certificate(cert_id)
            except SvKMSAPIError:
                existing_cert = None
        elif name:
            existing_cert = find_certificate_by_name(client, name)

        if state == "present":
            if not name and not cert_id:
                # List all certificates
                certs = client.list_certificates()
                module.exit_json(changed=False, certificates=certs)
            elif existing_cert:
                module.exit_json(changed=False, certificate=existing_cert)
            else:
                module.fail_json(msg="Certificate '{0}' not found. Certificates must be imported via SvKMS admin interface.".format(name or cert_id))

        elif state == "absent":
            if not existing_cert:
                module.exit_json(changed=False)
            else:
                module.fail_json(msg="Certificate deletion not supported via API. Use SvKMS admin interface.")

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
