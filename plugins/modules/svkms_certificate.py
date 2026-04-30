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
    type: str
    default: present
    choices: [present]
  name:
    description:
      - Name of the certificate. Used for idempotent lookups.
    type: str
    required: false
  cert_id:
    description:
      - ID of an existing certificate. If provided, used for lookups.
    type: str
extends_documentation_fragment:
  - xianganwu.stormagic.svkms
seealso:
  - module: xianganwu.stormagic.svkms_key
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Check if CA certificate exists
  xianganwu.stormagic.svkms_certificate:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    name: root-ca
    state: present

- name: List all certificates and register result
  xianganwu.stormagic.svkms_certificate:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    state: present
  register: all_certs

- name: Display all certificates
  ansible.builtin.debug:
    var: all_certs.certificates

- name: Verify CA certificate exists in check mode
  xianganwu.stormagic.svkms_certificate:
    host: svkms.example.com
    api_key: "{{ vault_kms_api_key }}"
    name: root-ca
    state: present
  check_mode: true
  register: result
"""

RETURN = r"""
certificate:
  description: The certificate object returned by SvKMS.
  type: dict
  returned: when state is present
  contains:
    id:
      description: Unique certificate identifier.
      type: str
      returned: always
    type:
      description: Certificate type.
      type: str
      returned: always
    subject:
      description: Certificate subject distinguished name.
      type: str
      returned: always
  sample:
    id: "cert-abc123"
    type: "ca"
    subject: "CN=SvKMS CA"
certificates:
  description: List of all certificates when name is not specified.
  type: list
  elements: dict
  returned: when state is present and name is not specified
  contains:
    id:
      description: Unique certificate identifier.
      type: str
      returned: always
    type:
      description: Certificate type.
      type: str
      returned: always
    subject:
      description: Certificate subject distinguished name.
      type: str
      returned: always
  sample:
    - id: "cert-1"
      type: "ca"
      subject: "CN=SvKMS CA"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.xianganwu.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
    svkms_argument_spec,
    SVKMS_MUTUALLY_EXCLUSIVE,
    SVKMS_REQUIRED_ONE_OF,
    SVKMS_REQUIRED_TOGETHER,
)


def find_certificate_by_name(client, name):
    certs = client.list_certificates()
    for cert in certs:
        if cert.get("name") == name:
            return cert
        subject = cert.get("subject", "")
        if subject.startswith("CN=") and subject[3:].split(",")[0].strip() == name:
            return cert
    return None


def main():
    argument_spec = svkms_argument_spec()
    argument_spec.update(dict(
        state=dict(type="str", default="present", choices=["present"]),
        name=dict(type="str"),
        cert_id=dict(type="str"),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=SVKMS_MUTUALLY_EXCLUSIVE,
        required_one_of=SVKMS_REQUIRED_ONE_OF,
        required_together=SVKMS_REQUIRED_TOGETHER,
    )

    state = module.params["state"]
    name = module.params.get("name")
    cert_id = module.params.get("cert_id")
    client = None
    try:
        host = module.params["host"]

        client = SvKMSClient(
            host=host,
            port=module.params["port"],
            api_key=module.params.get("api_key"),
            username=module.params.get("username"),
            password=module.params.get("password"),
            validate_certs=module.params.get("validate_certs", True),
            ca_path=module.params.get("ca_path"),
        )
        client.login()

        existing_cert = None
        if cert_id:
            try:
                existing_cert = client.get_certificate(cert_id)
            except SvKMSAPIError as e:
                if e.status_code == 404:
                    existing_cert = None
                else:
                    raise
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

    except SvKMSAPIError as e:
        error_msg = "SvKMS API error: {0}".format(str(e))
        if e.response_body and isinstance(e.response_body, dict):
            detail = e.response_body.get("detail") or e.response_body.get("message", "")
            if detail:
                error_msg += " - {0}".format(detail)
        module.fail_json(msg=error_msg, status_code=getattr(e, "status_code", None))
    finally:
        if client:
            client.logout()


if __name__ == "__main__":
    main()
