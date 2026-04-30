# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd <support@stormagic.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: svkms
author: StorMagic Ltd (@stormagic)
short_description: HttpApi Plugin for StorMagic SvKMS
description:
  - This HttpApi plugin provides methods to connect to and manage
    StorMagic SvKMS encryption key management servers via their REST API.
version_added: "1.0.0"
options:
  api_key:
    type: str
    description:
      - API key for authentication. If provided, username/password login is skipped.
    vars:
      - name: ansible_httpapi_svkms_api_key
    env:
      - name: SVKMS_API_KEY
  api_port:
    type: int
    description:
      - Port for the SvKMS REST API.
    default: 1443
    vars:
      - name: ansible_httpapi_port
"""

EXAMPLES = r"""
# Inventory configuration for SvKMS httpapi connection
# inventory/hosts.yml:
#
# svkms_servers:
#   hosts:
#     kms01.example.com:
#       ansible_network_os: xianganwu.stormagic.svkms
#       ansible_connection: ansible.netcommon.httpapi
#       ansible_httpapi_port: 1443
#       ansible_httpapi_use_ssl: true
#       ansible_httpapi_validate_certs: false
#       ansible_user: admin
#       ansible_password: "{{ vault_svkms_password }}"
#
# Using API key authentication instead of username/password:
#
# svkms_servers:
#   hosts:
#     kms01.example.com:
#       ansible_network_os: xianganwu.stormagic.svkms
#       ansible_connection: ansible.netcommon.httpapi
#       ansible_httpapi_port: 1443
#       ansible_httpapi_use_ssl: true
#       ansible_httpapi_svkms_api_key: "{{ vault_svkms_api_key }}"

- name: Check SvKMS health using httpapi connection
  xianganwu.stormagic.svkms_health_check:
  delegate_to: kms01.example.com

- name: Create a key using httpapi connection
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    algorithm: AES
    length: 256
    state: present
"""

import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase


BASE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class HttpApi(HttpApiBase):

    def login(self, username, password):
        api_key = self.get_option("api_key") if hasattr(self, "get_option") else None

        if api_key:
            self.connection._auth = {"X-API-Key": api_key}
            return

        if not username or not password:
            raise AnsibleConnectionFailure("Username and password are required when api_key is not set")

        payload = json.dumps({"username": username, "password": password})
        try:
            response, response_data = self.connection.send(
                "/v0/auth/login", payload, method="POST", headers=BASE_HEADERS
            )
            result = json.loads(response_data)
            token = result.get("token")
            if not token:
                raise AnsibleConnectionFailure("Login succeeded but no token returned")
            self.connection._auth = {"Authorization": "Bearer {0}".format(token)}
        except HTTPError as e:
            raise AnsibleConnectionFailure("Login failed: HTTP {0}".format(e.code))

    def logout(self):
        if self.connection._auth:
            try:
                self.connection.send("/v0/auth/logout", None, method="POST", headers=BASE_HEADERS)
            except Exception:
                pass
            self.connection._auth = None

    def send_request(self, data, **message_kwargs):
        path = data
        method = message_kwargs.get("method", "GET")
        request_data = message_kwargs.get("body")
        headers = dict(BASE_HEADERS)
        body = None
        if request_data is not None:
            body = json.dumps(request_data)

        full_path = "/v0{0}".format(path) if not path.startswith("/v0") else path

        try:
            response, response_data = self.connection.send(
                full_path, body, method=method, headers=headers
            )
            status_code = response.getcode()
            result = {}
            if response_data:
                result = json.loads(response_data)
            return status_code, result
        except HTTPError as e:
            error_body = {}
            try:
                error_body = json.loads(e.read())
            except Exception:
                pass
            return e.code, error_body

    def handle_httperror(self, exc):
        if exc.code == 401:
            return False
        return exc
