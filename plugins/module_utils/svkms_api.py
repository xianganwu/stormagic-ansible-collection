# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import time

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.six.moves.urllib.parse import quote


def svkms_argument_spec():
    return dict(
        host=dict(type="str", required=True),
        port=dict(type="int", default=1443),
        api_key=dict(type="str", no_log=True),
        username=dict(type="str"),
        password=dict(type="str", no_log=True),
        validate_certs=dict(type="bool", default=True),
        ca_path=dict(type="str"),
    )


SVKMS_MUTUALLY_EXCLUSIVE = [["api_key", "username"]]
SVKMS_REQUIRED_ONE_OF = [["api_key", "username"]]
SVKMS_REQUIRED_TOGETHER = [["username", "password"]]


class SvKMSAPIError(Exception):
    def __init__(self, message, status_code=None, response_body=None):
        super(SvKMSAPIError, self).__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class SvKMSClient(object):
    def __init__(self, host, port=1443, api_key=None, username=None,
                 password=None, validate_certs=True, ca_path=None,
                 max_retries=3, retry_delay=1, timeout=30):
        self.base_url = "https://{0}:{1}/v0".format(host, port)
        self.api_key = api_key
        self.username = username
        self.password = password
        self.validate_certs = validate_certs
        self.ca_path = ca_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._session_token = None

    def _get_headers(self):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self._session_token:
            headers["Authorization"] = "Bearer {0}".format(self._session_token)
        return headers

    def login(self):
        if self.username and self.password and not self.api_key:
            result = self.request("POST", "/auth/login", data={
                "username": self.username,
                "password": self.password,
            })
            self._session_token = result.get("token")
            self.password = None
            return self._session_token
        return None

    def logout(self):
        if self._session_token:
            try:
                self.request("POST", "/auth/logout")
            except SvKMSAPIError:
                pass
            self._session_token = None

    def request(self, method, path, data=None):
        url = "{0}{1}".format(self.base_url, path)
        headers = self._get_headers()
        body = None
        if data is not None:
            body = json.dumps(data)

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = open_url(
                    url,
                    data=body,
                    headers=headers,
                    method=method,
                    validate_certs=self.validate_certs,
                    ca_path=self.ca_path,
                    timeout=self.timeout,
                )
                response_body = response.read()
                if response_body:
                    return json.loads(response_body)
                return {}
            except HTTPError as e:
                error_body = None
                try:
                    error_body = json.loads(e.read())
                except Exception:
                    pass
                if 400 <= e.code < 500 and e.code != 429:
                    raise SvKMSAPIError(
                        "HTTP {0}: {1}".format(e.code, e.reason),
                        status_code=e.code,
                        response_body=error_body,
                    )
                last_exception = SvKMSAPIError(
                    "HTTP {0}: {1}".format(e.code, e.reason),
                    status_code=e.code,
                    response_body=error_body,
                )
            except URLError as e:
                last_exception = SvKMSAPIError(
                    "Connection error: {0}".format(str(e.reason))
                )

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))

        raise last_exception

    def create_key(self, name, algorithm, length, **kwargs):
        payload = {"name": name, "algorithm": algorithm, "length": length}
        payload.update(kwargs)
        return self.request("POST", "/keys", data=payload)

    def get_key(self, key_id):
        return self.request("GET", "/keys/{0}".format(quote(str(key_id), safe="")))

    def list_keys(self, filters=None):
        path = "/keys"
        if filters:
            query = "&".join(
                "{0}={1}".format(quote(str(k), safe=""), quote(str(v), safe=""))
                for k, v in filters.items()
            )
            path = "{0}?{1}".format(path, query)
        return self.request("GET", path)

    def rotate_key(self, key_id):
        return self.request("POST", "/keys/{0}/rotate".format(quote(str(key_id), safe="")))

    def retire_key(self, key_id):
        return self.request("POST", "/keys/{0}/retire".format(quote(str(key_id), safe="")))

    def destroy_key(self, key_id):
        return self.request("DELETE", "/keys/{0}".format(quote(str(key_id), safe="")))

    def get_certificate(self, cert_id):
        return self.request("GET", "/certificates/{0}".format(quote(str(cert_id), safe="")))

    def list_certificates(self):
        return self.request("GET", "/certificates")

    def create_user(self, username, role, auth_type="password"):
        return self.request("POST", "/users", data={
            "username": username, "role": role, "auth_type": auth_type,
        })

    def get_user(self, user_id):
        return self.request("GET", "/users/{0}".format(quote(str(user_id), safe="")))

    def list_users(self):
        return self.request("GET", "/users")

    def update_user(self, user_id, **kwargs):
        return self.request("PUT", "/users/{0}".format(quote(str(user_id), safe="")), data=kwargs)

    def delete_user(self, user_id):
        return self.request("DELETE", "/users/{0}".format(quote(str(user_id), safe="")))

    def create_policy(self, name, rules):
        return self.request("POST", "/policies", data={"name": name, "rules": rules})

    def get_policy(self, policy_id):
        return self.request("GET", "/policies/{0}".format(quote(str(policy_id), safe="")))

    def list_policies(self):
        return self.request("GET", "/policies")

    def update_policy(self, policy_id, rules):
        return self.request("PUT", "/policies/{0}".format(quote(str(policy_id), safe="")), data={"rules": rules})

    def delete_policy(self, policy_id):
        return self.request("DELETE", "/policies/{0}".format(quote(str(policy_id), safe="")))

    def backup(self, destination=None):
        payload = {}
        if destination:
            payload["destination"] = destination
        return self.request("POST", "/backup", data=payload)

    def restore(self, source):
        return self.request("POST", "/restore", data={"source": source})

    def health_check(self):
        return self.request("GET", "/health")
