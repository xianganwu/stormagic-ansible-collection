# StorMagic Ansible Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and certify `stormagic.stormagic` Ansible collection with SvKMS (Python/httpapi) and SvSAN (PowerShell/WinRM) modules that pass Red Hat Ansible Certified Content requirements.

**Architecture:** Dual-language collection — Python modules talk to SvKMS REST API via an httpapi connection plugin, PowerShell modules talk to SvSAN via native SmCmdlet on Windows management hosts. Each `.ps1` module has a companion `.py` doc stub. Collection must pass `ansible-test sanity`, `ansible-lint`, and `galaxy-importer` on ansible-core 2.16, 2.17, and devel.

**Tech Stack:** Python 3.10+, PowerShell 5.1+, ansible-core 2.16+, pytest, Pester, Docker (for local sanity tests on macOS), GitHub Actions CI.

**Design Spec:** `docs/superpowers/specs/2026-04-29-stormagic-ansible-collection-design.md`

---

## File Map

Every file this plan creates, organized by responsibility:

```
ansible_collections/stormagic/stormagic/
│
│── galaxy.yml                          # Task 1 — collection metadata
│── meta/runtime.yml                    # Task 1 — ansible version floor
│── LICENSE                             # Task 1 — GPL-3.0-or-later full text
│── README.md                           # Task 19 — Red Hat certified README
│── CHANGELOG.rst                       # Task 19 — release notes
│── .ansible-lint                       # Task 2 — lint config
│── .github/workflows/ci.yml            # Task 2 — CI pipeline
│
│── plugins/
│   ├── module_utils/
│   │   ├── common.py                   # Task 5 — shared argument specs
│   │   ├── svkms_api.py                # Task 3 — SvKMS REST client
│   │   └── SvSAN.psm1                  # Task 10 — shared PS utilities
│   ├── httpapi/
│   │   └── svkms.py                    # Task 4 — httpapi connection plugin
│   ├── doc_fragments/
│   │   ├── svkms.py                    # Task 5 — SvKMS common docs
│   │   └── svsan.py                    # Task 11 — SvSAN common docs
│   └── modules/
│       ├── svkms_key.py                # Task 6 — key lifecycle
│       ├── svkms_key_info.py           # Task 7 — read-only key info
│       ├── svkms_health_check.py       # Task 8 — KMS health check
│       ├── svkms_certificate.py        # Task 9 — cert management
│       ├── svkms_user.py               # Task 9 — user management
│       ├── svkms_policy.py             # Task 9 — policy management
│       ├── svkms_backup.py             # Task 9 — backup/restore
│       ├── svsan_health_check.ps1      # Task 12 — VSA health check
│       ├── svsan_health_check.py       # Task 12 — doc stub
│       ├── svsan_target.ps1            # Task 13 — target management
│       ├── svsan_target.py             # Task 13 — doc stub
│       ├── svsan_target_info.ps1       # Task 13 — read-only target info
│       ├── svsan_target_info.py        # Task 13 — doc stub
│       ├── svsan_mirror.ps1            # Task 14 — mirror management
│       ├── svsan_mirror.py             # Task 14 — doc stub
│       ├── svsan_mirror_info.ps1       # Task 14 — doc stub pair
│       ├── svsan_mirror_info.py        # Task 14
│       ├── svsan_pool.ps1              # Task 14
│       ├── svsan_pool.py               # Task 14
│       ├── svsan_pool_info.ps1         # Task 14
│       ├── svsan_pool_info.py          # Task 14
│       ├── svsan_license.ps1           # Task 14
│       ├── svsan_license.py            # Task 14
│       ├── svsan_config.ps1            # Task 14
│       ├── svsan_config.py             # Task 14
│       ├── svsan_config_info.ps1       # Task 14
│       ├── svsan_config_info.py        # Task 14
│       ├── svsan_vsa.ps1               # Task 14
│       └── svsan_vsa.py                # Task 14
│
│── roles/
│   ├── svsan_patching_preflight/       # Task 15
│   ├── svsan_patching_postflight/      # Task 16
│   ├── svsan_deploy/                   # Task 17
│   └── svkms_setup/                    # Task 17
│
│── playbooks/                          # Task 17
│   ├── svkms_key_rotation.yml
│   ├── svsan_ha_setup.yml
│   └── svsan_patching_workflow.yml
│
│── tests/
│   ├── unit/plugins/module_utils/
│   │   └── test_svkms_api.py           # Task 3
│   ├── unit/plugins/modules/
│   │   ├── test_svkms_key.py           # Task 6
│   │   ├── test_svkms_key_info.py      # Task 7
│   │   ├── test_svkms_health_check.py  # Task 8
│   │   └── test_svkms_certificate.py   # Task 9 (pattern for all SvKMS)
│   ├── unit/plugins/httpapi/
│   │   └── test_svkms.py               # Task 4
│   ├── integration/
│   │   ├── targets/svkms_key/          # Task 18
│   │   ├── targets/svsan_health_check/ # Task 18
│   │   └── integration_config.yml.template  # Task 18
│   └── sanity/
│       ├── ignore-2.16.txt             # Task 2
│       └── ignore-2.17.txt             # Task 2
│
└── docs/
    ├── svkms_quickstart.md             # Task 19
    ├── svsan_quickstart.md             # Task 19
    └── patching_workflow.md            # Task 19
```

---

## Phase 1: Collection Scaffold & CI

### Task 1: Collection Scaffold

**Files:**
- Create: `galaxy.yml`
- Create: `meta/runtime.yml`
- Create: `LICENSE`

- [ ] **Step 1: Create the collection directory structure**

The collection MUST live under `ansible_collections/stormagic/stormagic/` for `ansible-test` to work. Create this as a symlink-based dev setup:

```bash
cd /Users/frawu/stormagic-ansible-collection
mkdir -p ansible_collections/stormagic
ln -s "$(pwd)" ansible_collections/stormagic/stormagic
```

Verify the structure:

```bash
ls -la ansible_collections/stormagic/stormagic/galaxy.yml 2>/dev/null || echo "Not yet — we'll create galaxy.yml next"
```

- [ ] **Step 2: Create galaxy.yml**

```yaml
# galaxy.yml
namespace: stormagic
name: stormagic
version: 1.0.0
readme: README.md
authors:
  - StorMagic Ltd <support@stormagic.com>
description: >-
  Ansible collection for managing StorMagic SvKMS encryption key management
  and SvSAN virtual storage appliances. Provides health checks, key lifecycle
  management, storage target and mirror management, and patching workflow roles.
license:
  - GPL-3.0-or-later
tags:
  - stormagic
  - svkms
  - svsan
  - encryption
  - key_management
  - storage
  - hci
  - edge
  - health_check
dependencies: {}
repository: https://github.com/xianganwu/stormagic-ansible-collection
documentation: https://github.com/xianganwu/stormagic-ansible-collection/blob/main/README.md
homepage: https://stormagic.com
issues: https://github.com/xianganwu/stormagic-ansible-collection/issues
build_ignore:
  - .github
  - .gitignore
  - tests/integration
  - ansible_collections
```

- [ ] **Step 3: Create meta/runtime.yml**

```bash
mkdir -p meta
```

```yaml
# meta/runtime.yml
requires_ansible: ">=2.16.0"
```

- [ ] **Step 4: Create LICENSE file**

Download the GPL-3.0 full text:

```bash
curl -sL https://www.gnu.org/licenses/gpl-3.0.txt > LICENSE
```

- [ ] **Step 5: Create placeholder README.md**

```markdown
# StorMagic Collection for Ansible

This collection provides modules for managing StorMagic SvKMS and SvSAN.

## Requirements

- ansible-core >= 2.16.0
- Python >= 3.10 (controller)
- PowerShell 5.1+ (Windows management host, for SvSAN modules)
- StorMagic PowerShell Toolkit (for SvSAN modules)

## License

GPL-3.0-or-later
```

- [ ] **Step 6: Create required directory stubs**

```bash
mkdir -p plugins/modules plugins/module_utils plugins/httpapi plugins/doc_fragments
mkdir -p roles playbooks docs
mkdir -p tests/unit/plugins/modules tests/unit/plugins/module_utils tests/unit/plugins/httpapi
mkdir -p tests/integration/targets tests/sanity
```

- [ ] **Step 7: Commit scaffold**

```bash
git add galaxy.yml meta/ LICENSE README.md plugins/ roles/ playbooks/ docs/ tests/
git commit -m "feat: initialize collection scaffold with galaxy.yml, meta/runtime.yml, LICENSE"
```

---

### Task 2: CI Pipeline & Local Dev Environment

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.ansible-lint`
- Create: `tests/sanity/ignore-2.16.txt`
- Create: `tests/sanity/ignore-2.17.txt`

- [ ] **Step 1: Create .ansible-lint config**

```yaml
# .ansible-lint
exclude_paths:
  - .github/
  - tests/integration/
  - ansible_collections/
  - docs/superpowers/
```

- [ ] **Step 2: Create sanity ignore files**

These files list known sanity test exclusions. Start empty — we add entries only when necessary and justified.

```bash
touch tests/sanity/ignore-2.16.txt
touch tests/sanity/ignore-2.17.txt
```

- [ ] **Step 3: Create GitHub Actions CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  sanity:
    name: Sanity (ansible-core ${{ matrix.ansible }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        ansible:
          - stable-2.16
          - stable-2.17
          - devel
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          path: ansible_collections/stormagic/stormagic

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ansible-core (${{ matrix.ansible }})
        run: pip install https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz

      - name: Run sanity tests
        run: ansible-test sanity --docker -v --color --coverage
        working-directory: ansible_collections/stormagic/stormagic

  units:
    name: Unit Tests (Python ${{ matrix.python }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python:
          - "3.12"
          - "3.13"
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          path: ansible_collections/stormagic/stormagic

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}

      - name: Install ansible-core
        run: pip install ansible-core

      - name: Run unit tests
        run: ansible-test units --docker -v --color --coverage --python ${{ matrix.python }}
        working-directory: ansible_collections/stormagic/stormagic

  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ansible-lint
        run: pip install ansible-lint

      - name: Run ansible-lint
        run: ansible-lint --strict
```

- [ ] **Step 4: Verify local dev environment works**

Install the local toolchain and run the first sanity test to confirm the scaffold is valid:

```bash
pip install ansible-core ansible-lint galaxy-importer
cd /Users/frawu/stormagic-ansible-collection
ansible-test sanity --docker -v --test yamllint 2>&1 | head -30
```

Expected: Either PASS (nothing to lint yet) or a Docker pull + clean run. If Docker is not available, use `--local` instead of `--docker`:

```bash
ansible-test sanity --local -v --test yamllint
```

- [ ] **Step 5: Commit CI configuration**

```bash
git add .github/ .ansible-lint tests/sanity/
git commit -m "ci: add GitHub Actions sanity, unit tests, and lint workflows"
```

---

## Phase 2: SvKMS Python Backend

### Task 3: SvKMS REST API Client (module_utils)

**Files:**
- Create: `plugins/module_utils/svkms_api.py`
- Create: `tests/unit/plugins/module_utils/test_svkms_api.py`

- [ ] **Step 1: Write failing unit tests for the API client**

```python
# tests/unit/plugins/module_utils/test_svkms_api.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


class TestSvKMSClientInit:
    def test_base_url_construction(self):
        client = SvKMSClient(host="kms.example.com", port=1443)
        assert client.base_url == "https://kms.example.com:1443/v0"

    def test_default_port(self):
        client = SvKMSClient(host="kms.example.com")
        assert client.base_url == "https://kms.example.com:1443/v0"

    def test_custom_port(self):
        client = SvKMSClient(host="kms.example.com", port=8443)
        assert client.base_url == "https://kms.example.com:8443/v0"


class TestSvKMSClientRequest:
    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_get_request_success(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "key-1", "name": "test"}).encode()
        mock_response.getcode.return_value = 200
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com")
        result = client.request("GET", "/keys/key-1")

        assert result == {"id": "key-1", "name": "test"}
        mock_open_url.assert_called_once()

    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_post_request_with_body(self, mock_open_url):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"id": "key-2"}).encode()
        mock_response.getcode.return_value = 201
        mock_open_url.return_value = mock_response

        client = SvKMSClient(host="kms.example.com", api_key="test-api-key")
        result = client.request("POST", "/keys", data={"name": "newkey", "algorithm": "AES"})

        assert result == {"id": "key-2"}
        call_kwargs = mock_open_url.call_args
        assert "test-api-key" in str(call_kwargs)

    @patch("ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api.open_url")
    def test_request_error_raises(self, mock_open_url):
        from urllib.error import HTTPError
        mock_open_url.side_effect = HTTPError(
            url="https://kms.example.com:1443/v0/keys/bad",
            code=404, msg="Not Found", hdrs={}, fp=MagicMock()
        )

        client = SvKMSClient(host="kms.example.com")
        with pytest.raises(SvKMSAPIError) as exc_info:
            client.request("GET", "/keys/bad")
        assert exc_info.value.status_code == 404


class TestSvKMSClientKeyOperations:
    @patch.object(SvKMSClient, "request")
    def test_create_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        client = SvKMSClient(host="kms.example.com")
        result = client.create_key(name="mykey", algorithm="AES", length=256)
        mock_request.assert_called_once_with("POST", "/keys", data={"name": "mykey", "algorithm": "AES", "length": 256})
        assert result["id"] == "key-1"

    @patch.object(SvKMSClient, "request")
    def test_get_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "name": "mykey"}
        client = SvKMSClient(host="kms.example.com")
        result = client.get_key("key-1")
        mock_request.assert_called_once_with("GET", "/keys/key-1")
        assert result["name"] == "mykey"

    @patch.object(SvKMSClient, "request")
    def test_list_keys(self, mock_request):
        mock_request.return_value = [{"id": "key-1"}, {"id": "key-2"}]
        client = SvKMSClient(host="kms.example.com")
        result = client.list_keys()
        mock_request.assert_called_once_with("GET", "/keys")
        assert len(result) == 2

    @patch.object(SvKMSClient, "request")
    def test_rotate_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "version": 2}
        client = SvKMSClient(host="kms.example.com")
        result = client.rotate_key("key-1")
        mock_request.assert_called_once_with("POST", "/keys/key-1/rotate")
        assert result["version"] == 2

    @patch.object(SvKMSClient, "request")
    def test_destroy_key(self, mock_request):
        mock_request.return_value = {}
        client = SvKMSClient(host="kms.example.com")
        client.destroy_key("key-1")
        mock_request.assert_called_once_with("DELETE", "/keys/key-1")

    @patch.object(SvKMSClient, "request")
    def test_retire_key(self, mock_request):
        mock_request.return_value = {"id": "key-1", "state": "retired"}
        client = SvKMSClient(host="kms.example.com")
        result = client.retire_key("key-1")
        mock_request.assert_called_once_with("POST", "/keys/key-1/retire")
        assert result["state"] == "retired"


class TestSvKMSClientHealthCheck:
    @patch.object(SvKMSClient, "request")
    def test_health_check_healthy(self, mock_request):
        mock_request.return_value = {"status": "healthy", "version": "4.2.0"}
        client = SvKMSClient(host="kms.example.com")
        result = client.health_check()
        mock_request.assert_called_once_with("GET", "/health")
        assert result["status"] == "healthy"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/frawu/stormagic-ansible-collection
python -m pytest tests/unit/plugins/module_utils/test_svkms_api.py -v 2>&1 | tail -20
```

Expected: `ModuleNotFoundError: No module named 'ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api'`

- [ ] **Step 3: Implement the SvKMS API client**

```python
# plugins/module_utils/svkms_api.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError


class SvKMSAPIError(Exception):
    def __init__(self, message, status_code=None, response_body=None):
        super(SvKMSAPIError, self).__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class SvKMSClient(object):
    def __init__(self, host, port=1443, api_key=None, username=None,
                 password=None, validate_certs=True, ca_path=None):
        self.base_url = "https://{0}:{1}/v0".format(host, port)
        self.api_key = api_key
        self.username = username
        self.password = password
        self.validate_certs = validate_certs
        self.ca_path = ca_path
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

        try:
            response = open_url(
                url,
                data=body,
                headers=headers,
                method=method,
                validate_certs=self.validate_certs,
                ca_path=self.ca_path,
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
            raise SvKMSAPIError(
                "HTTP {0}: {1}".format(e.code, e.reason),
                status_code=e.code,
                response_body=error_body,
            )
        except URLError as e:
            raise SvKMSAPIError("Connection error: {0}".format(str(e.reason)))

    def create_key(self, name, algorithm, length, **kwargs):
        payload = {"name": name, "algorithm": algorithm, "length": length}
        payload.update(kwargs)
        return self.request("POST", "/keys", data=payload)

    def get_key(self, key_id):
        return self.request("GET", "/keys/{0}".format(key_id))

    def list_keys(self, filters=None):
        path = "/keys"
        if filters:
            query = "&".join("{0}={1}".format(k, v) for k, v in filters.items())
            path = "{0}?{1}".format(path, query)
        return self.request("GET", path)

    def rotate_key(self, key_id):
        return self.request("POST", "/keys/{0}/rotate".format(key_id))

    def retire_key(self, key_id):
        return self.request("POST", "/keys/{0}/retire".format(key_id))

    def destroy_key(self, key_id):
        return self.request("DELETE", "/keys/{0}".format(key_id))

    def get_certificate(self, cert_id):
        return self.request("GET", "/certificates/{0}".format(cert_id))

    def list_certificates(self):
        return self.request("GET", "/certificates")

    def create_user(self, username, role, auth_type="password"):
        return self.request("POST", "/users", data={
            "username": username, "role": role, "auth_type": auth_type,
        })

    def get_user(self, user_id):
        return self.request("GET", "/users/{0}".format(user_id))

    def delete_user(self, user_id):
        return self.request("DELETE", "/users/{0}".format(user_id))

    def create_policy(self, name, rules):
        return self.request("POST", "/policies", data={"name": name, "rules": rules})

    def get_policy(self, policy_id):
        return self.request("GET", "/policies/{0}".format(policy_id))

    def delete_policy(self, policy_id):
        return self.request("DELETE", "/policies/{0}".format(policy_id))

    def backup(self, destination=None):
        payload = {}
        if destination:
            payload["destination"] = destination
        return self.request("POST", "/backup", data=payload)

    def restore(self, source):
        return self.request("POST", "/restore", data={"source": source})

    def health_check(self):
        return self.request("GET", "/health")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/frawu/stormagic-ansible-collection
PYTHONPATH=. python -m pytest tests/unit/plugins/module_utils/test_svkms_api.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Run sanity check on the new file**

```bash
cd /Users/frawu/stormagic-ansible-collection/ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test pep8 plugins/module_utils/svkms_api.py
ansible-test sanity --local -v --test pylint plugins/module_utils/svkms_api.py
```

Expected: PASS with no errors.

- [ ] **Step 6: Commit**

```bash
git add plugins/module_utils/svkms_api.py tests/unit/plugins/module_utils/test_svkms_api.py
git commit -m "feat: add SvKMS REST API client with full key lifecycle operations"
```

---

### Task 4: httpapi Connection Plugin

**Files:**
- Create: `plugins/httpapi/svkms.py`
- Create: `tests/unit/plugins/httpapi/test_svkms.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/plugins/httpapi/test_svkms.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import MagicMock, patch

from ansible_collections.stormagic.stormagic.plugins.httpapi.svkms import HttpApi


class TestSvKMSHttpApiLogin:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)

    def test_login_sends_credentials(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"token": "abc123"}).encode()
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, mock_response.read.return_value)

        self.httpapi.login("admin", "password123")

        self.connection.send.assert_called_once()
        call_args = self.connection.send.call_args
        assert "/v0/auth/login" in str(call_args)
        assert self.connection._auth == {"Authorization": "Bearer abc123"}

    def test_login_with_api_key(self):
        self.httpapi.set_option("api_key", "myapikey")
        self.httpapi.login(None, None)
        assert self.connection._auth == {"X-API-Key": "myapikey"}


class TestSvKMSHttpApiLogout:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)
        self.connection._auth = {"Authorization": "Bearer abc123"}

    def test_logout_clears_auth(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"{}"
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, mock_response.read.return_value)

        self.httpapi.logout()
        assert self.connection._auth is None


class TestSvKMSHttpApiSendRequest:
    def setup_method(self):
        self.connection = MagicMock()
        self.httpapi = HttpApi(self.connection)

    def test_send_request_get(self):
        mock_response = MagicMock()
        response_data = json.dumps({"id": "key-1"}).encode()
        mock_response.read.return_value = response_data
        mock_response.getcode.return_value = 200
        self.connection.send.return_value = (mock_response, response_data)

        code, result = self.httpapi.send_request("/keys/key-1", method="GET")

        assert code == 200
        assert result == {"id": "key-1"}

    def test_send_request_post_with_data(self):
        mock_response = MagicMock()
        response_data = json.dumps({"id": "key-2"}).encode()
        mock_response.read.return_value = response_data
        mock_response.getcode.return_value = 201
        self.connection.send.return_value = (mock_response, response_data)

        code, result = self.httpapi.send_request(
            "/keys", method="POST",
            data={"name": "test", "algorithm": "AES"}
        )

        assert code == 201
        assert result["id"] == "key-2"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/httpapi/test_svkms.py -v 2>&1 | tail -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement the httpapi plugin**

```python
# plugins/httpapi/svkms.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: svkms
author: StorMagic Ltd
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

    def send_request(self, path, method="GET", data=None):
        headers = dict(BASE_HEADERS)
        body = None
        if data is not None:
            body = json.dumps(data)

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/httpapi/test_svkms.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/httpapi/svkms.py tests/unit/plugins/httpapi/test_svkms.py
git commit -m "feat: add SvKMS httpapi connection plugin with token and API key auth"
```

---

### Task 5: Doc Fragments & Common Module Utils

**Files:**
- Create: `plugins/doc_fragments/svkms.py`
- Create: `plugins/module_utils/common.py`

- [ ] **Step 1: Create the SvKMS doc fragment**

```python
# plugins/doc_fragments/svkms.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options: {}
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
  platform:
    platforms: httpapi
notes:
  - This module requires the C(stormagic.stormagic.svkms) httpapi plugin.
  - Set C(ansible_network_os=stormagic.stormagic.svkms) in your inventory.
  - Set C(ansible_connection=ansible.netcommon.httpapi) for the SvKMS host.
  - Authentication uses username/password or API key via C(ansible_httpapi_svkms_api_key).
seealso:
  - name: StorMagic SvKMS Documentation
    description: Official StorMagic SvKMS documentation.
    link: https://stormagic.com/encryption-key-management/documentation/
"""
```

- [ ] **Step 2: Create common module_utils**

```python
# plugins/module_utils/common.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type


SVKMS_COMMON_ARGS = dict(
    state=dict(type="str", default="present", choices=["present", "absent"]),
)

SVKMS_KEY_STATES = dict(
    state=dict(type="str", default="present", choices=["present", "absent", "rotated", "retired"]),
)
```

- [ ] **Step 3: Commit**

```bash
git add plugins/doc_fragments/svkms.py plugins/module_utils/common.py
git commit -m "feat: add SvKMS doc fragment and common argument specs"
```

---

## Phase 3: SvKMS Python Modules

### Task 6: svkms_key Module (Reference Python Module — Full TDD)

**Files:**
- Create: `plugins/modules/svkms_key.py`
- Create: `tests/unit/plugins/modules/test_svkms_key.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/plugins/modules/test_svkms_key.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.modules import svkms_key


# Helper to run the module with given params
def run_module(module_args, check_mode=False):
    set_module_args = {
        "_ansible_check_mode": check_mode,
        "_ansible_diff": False,
    }
    set_module_args.update(module_args)

    with pytest.raises(SystemExit) as exc_info:
        with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.AnsibleModule") as mock_module_cls:
            mock_module = MagicMock()
            mock_module.params = set_module_args
            mock_module.check_mode = check_mode
            mock_module_cls.return_value = mock_module

            mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
            mock_module.fail_json = MagicMock(side_effect=SystemExit(1))

            svkms_key.main()

    return mock_module


class TestSvKMSKeyCreate:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_create_new_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []
        client.create_key.return_value = {
            "id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256,
        }

        module = run_module({
            "state": "present", "name": "mykey", "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["key"]["id"] == "key-1"

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_key_already_exists_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "mykey", "algorithm": "AES", "length": 256}
        ]

        module = run_module({
            "state": "present", "name": "mykey", "algorithm": "AES", "length": 256,
        })

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSKeyDelete:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_existing_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]
        client.destroy_key.return_value = {}

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_delete_nonexistent_key_no_change(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module({"state": "absent", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False


class TestSvKMSKeyRotate:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_rotate_existing_key(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [{"id": "key-1", "name": "mykey"}]
        client.rotate_key.return_value = {"id": "key-1", "name": "mykey", "version": 2}

        module = run_module({"state": "rotated", "name": "mykey"})

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        assert call_kwargs["key"]["version"] == 2


class TestSvKMSKeyCheckMode:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key.SvKMSClient")
    def test_check_mode_create_reports_changed(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = []

        module = run_module(
            {"state": "present", "name": "mykey", "algorithm": "AES", "length": 256},
            check_mode=True,
        )

        module.exit_json.assert_called_once()
        call_kwargs = module.exit_json.call_args[1]
        assert call_kwargs["changed"] is True
        client.create_key.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_key.py -v 2>&1 | tail -5
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement the svkms_key module**

```python
# plugins/modules/svkms_key.py
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_key
short_description: Manage encryption keys on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Create, rotate, retire, and destroy encryption keys on a StorMagic SvKMS server.
  - Supports idempotent key creation and check mode.
options:
  state:
    description:
      - Desired state of the key.
      - C(present) ensures the key exists, creating it if necessary.
      - C(absent) ensures the key does not exist, destroying it if necessary.
      - C(rotated) rotates an existing key to a new version.
      - C(retired) marks an existing key as retired.
    type: str
    default: present
    choices: [present, absent, rotated, retired]
  name:
    description:
      - Name of the encryption key. Used for idempotent lookups.
    type: str
    required: true
  key_id:
    description:
      - ID of an existing key. If provided, used instead of name for lookups.
    type: str
  algorithm:
    description:
      - Encryption algorithm for the key.
    type: str
    default: AES
    choices: [AES, RSA, EC]
  length:
    description:
      - Key length in bits.
    type: int
    default: 256
  metadata:
    description:
      - Custom metadata to attach to the key.
    type: dict
extends_documentation_fragment:
  - stormagic.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Create an AES-256 encryption key
  stormagic.stormagic.svkms_key:
    name: app-encryption-key
    algorithm: AES
    length: 256
    state: present

- name: Rotate an existing key
  stormagic.stormagic.svkms_key:
    name: app-encryption-key
    state: rotated

- name: Retire a key
  stormagic.stormagic.svkms_key:
    name: app-encryption-key
    state: retired

- name: Destroy a key
  stormagic.stormagic.svkms_key:
    name: app-encryption-key
    state: absent
"""

RETURN = r"""
key:
  description: The key object returned by SvKMS.
  type: dict
  returned: when state is present, rotated, or retired
  sample:
    id: "key-abc123"
    name: "app-encryption-key"
    algorithm: "AES"
    length: 256
    version: 1
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def find_key_by_name(client, name):
    keys = client.list_keys()
    for key in keys:
        if key.get("name") == name:
            return key
    return None


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent", "rotated", "retired"]),
        name=dict(type="str", required=True),
        key_id=dict(type="str"),
        algorithm=dict(type="str", default="AES", choices=["AES", "RSA", "EC"]),
        length=dict(type="int", default=256),
        metadata=dict(type="dict"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params["state"]
    name = module.params["name"]
    key_id = module.params.get("key_id")
    algorithm = module.params["algorithm"]
    length = module.params["length"]
    metadata = module.params.get("metadata")

    try:
        client = SvKMSClient(
            host=module.params.get("host", "localhost"),
            port=module.params.get("port", 1443),
        )

        existing_key = None
        if key_id:
            try:
                existing_key = client.get_key(key_id)
            except SvKMSAPIError:
                existing_key = None
        else:
            existing_key = find_key_by_name(client, name)

        if state == "present":
            if existing_key:
                module.exit_json(changed=False, key=existing_key)
            else:
                if module.check_mode:
                    module.exit_json(changed=True, key={})
                key = client.create_key(name=name, algorithm=algorithm, length=length)
                module.exit_json(changed=True, key=key)

        elif state == "absent":
            if not existing_key:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True)
                client.destroy_key(existing_key["id"])
                module.exit_json(changed=True)

        elif state == "rotated":
            if not existing_key:
                module.fail_json(msg="Cannot rotate key '{0}': key not found".format(name))
            if module.check_mode:
                module.exit_json(changed=True, key=existing_key)
            key = client.rotate_key(existing_key["id"])
            module.exit_json(changed=True, key=key)

        elif state == "retired":
            if not existing_key:
                module.fail_json(msg="Cannot retire key '{0}': key not found".format(name))
            if module.check_mode:
                module.exit_json(changed=True, key=existing_key)
            key = client.retire_key(existing_key["id"])
            module.exit_json(changed=True, key=key)

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_key.py -v
```

Expected: All PASS.

- [ ] **Step 5: Run sanity on the module**

```bash
cd ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test validate-modules plugins/modules/svkms_key.py
ansible-test sanity --local -v --test pep8 plugins/modules/svkms_key.py
```

Fix any sanity errors before proceeding.

- [ ] **Step 6: Commit**

```bash
git add plugins/modules/svkms_key.py tests/unit/plugins/modules/test_svkms_key.py
git commit -m "feat: add svkms_key module with idempotent create, rotate, retire, destroy"
```

---

### Task 7: svkms_key_info Module

**Files:**
- Create: `plugins/modules/svkms_key_info.py`
- Create: `tests/unit/plugins/modules/test_svkms_key_info.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/plugins/modules/test_svkms_key_info.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.modules import svkms_key_info


class TestSvKMSKeyInfo:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key_info.SvKMSClient")
    def test_list_all_keys(self, MockClient):
        client = MockClient.return_value
        client.list_keys.return_value = [
            {"id": "key-1", "name": "key-a", "algorithm": "AES"},
            {"id": "key-2", "name": "key-b", "algorithm": "RSA"},
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key_info.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {"name": None, "key_id": None}
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_key_info.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert len(call_kwargs["keys"]) == 2

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key_info.SvKMSClient")
    def test_get_specific_key(self, MockClient):
        client = MockClient.return_value
        client.get_key.return_value = {"id": "key-1", "name": "key-a"}

        with pytest.raises(SystemExit):
            with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_key_info.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {"name": None, "key_id": "key-1"}
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_key_info.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["keys"][0]["id"] == "key-1"
```

- [ ] **Step 2: Run tests, verify failure**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_key_info.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Implement svkms_key_info**

```python
# plugins/modules/svkms_key_info.py
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_key_info
short_description: Gather information about encryption keys on StorMagic SvKMS
version_added: "1.0.0"
description:
  - Retrieve information about one or all encryption keys from a StorMagic SvKMS server.
  - This module does not make any changes (read-only).
options:
  name:
    description:
      - Filter keys by name. If not provided, returns all keys.
    type: str
  key_id:
    description:
      - Retrieve a specific key by ID. Takes precedence over name.
    type: str
extends_documentation_fragment:
  - stormagic.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: List all keys
  stormagic.stormagic.svkms_key_info:
  register: all_keys

- name: Get a specific key by ID
  stormagic.stormagic.svkms_key_info:
    key_id: key-abc123
  register: my_key
"""

RETURN = r"""
keys:
  description: List of key objects from SvKMS.
  type: list
  elements: dict
  returned: always
  sample:
    - id: "key-abc123"
      name: "app-encryption-key"
      algorithm: "AES"
      length: 256
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        key_id=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params.get("name")
    key_id = module.params.get("key_id")

    try:
        client = SvKMSClient(host=module.params.get("host", "localhost"))

        if key_id:
            key = client.get_key(key_id)
            module.exit_json(changed=False, keys=[key])
        elif name:
            all_keys = client.list_keys()
            filtered = [k for k in all_keys if k.get("name") == name]
            module.exit_json(changed=False, keys=filtered)
        else:
            keys = client.list_keys()
            module.exit_json(changed=False, keys=keys)

    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS API error: {0}".format(str(e)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify pass**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_key_info.py -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/modules/svkms_key_info.py tests/unit/plugins/modules/test_svkms_key_info.py
git commit -m "feat: add svkms_key_info read-only module"
```

---

### Task 8: svkms_health_check Module

**Files:**
- Create: `plugins/modules/svkms_health_check.py`
- Create: `tests/unit/plugins/modules/test_svkms_health_check.py`

- [ ] **Step 1: Write failing unit tests**

```python
# tests/unit/plugins/modules/test_svkms_health_check.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.modules import svkms_health_check


class TestSvKMSHealthCheck:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_health_check.SvKMSClient")
    def test_healthy_server(self, MockClient):
        client = MockClient.return_value
        client.health_check.return_value = {"status": "healthy", "version": "4.2.0"}

        with pytest.raises(SystemExit):
            with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_health_check.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {}
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_health_check.main()

        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs["changed"] is False
        assert call_kwargs["health"]["status"] == "healthy"

    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_health_check.SvKMSClient")
    def test_unhealthy_server_fails(self, MockClient):
        client = MockClient.return_value
        from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import SvKMSAPIError
        client.health_check.side_effect = SvKMSAPIError("Connection refused")

        with pytest.raises(SystemExit):
            with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_health_check.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {}
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_module.fail_json = MagicMock(side_effect=SystemExit(1))
                mock_cls.return_value = mock_module
                svkms_health_check.main()

        mock_module.fail_json.assert_called_once()
```

- [ ] **Step 2: Run tests, verify failure**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_health_check.py -v 2>&1 | tail -5
```

- [ ] **Step 3: Implement svkms_health_check**

```python
# plugins/modules/svkms_health_check.py
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svkms_health_check
short_description: Check health of a StorMagic SvKMS server
version_added: "1.0.0"
description:
  - Query the SvKMS health endpoint and return server status.
  - Fails the task if the server is unreachable or reports unhealthy.
options: {}
extends_documentation_fragment:
  - stormagic.stormagic.svkms
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Check SvKMS health
  stormagic.stormagic.svkms_health_check:
  register: health

- name: Assert healthy
  ansible.builtin.assert:
    that: health.health.status == 'healthy'
"""

RETURN = r"""
health:
  description: Health status from SvKMS.
  type: dict
  returned: on success
  sample:
    status: "healthy"
    version: "4.2.0"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stormagic.stormagic.plugins.module_utils.svkms_api import (
    SvKMSClient,
    SvKMSAPIError,
)


def main():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True,
    )

    try:
        client = SvKMSClient(host=module.params.get("host", "localhost"))
        health = client.health_check()
        module.exit_json(changed=False, health=health)
    except SvKMSAPIError as e:
        module.fail_json(msg="SvKMS health check failed: {0}".format(str(e)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify pass**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_health_check.py -v
```

- [ ] **Step 5: Commit**

```bash
git add plugins/modules/svkms_health_check.py tests/unit/plugins/modules/test_svkms_health_check.py
git commit -m "feat: add svkms_health_check module"
```

---

### Task 9: Remaining SvKMS Modules (certificate, user, policy, backup)

**Files:**
- Create: `plugins/modules/svkms_certificate.py`
- Create: `plugins/modules/svkms_user.py`
- Create: `plugins/modules/svkms_policy.py`
- Create: `plugins/modules/svkms_backup.py`
- Create: `tests/unit/plugins/modules/test_svkms_certificate.py`

These four modules follow the exact same pattern as `svkms_key`. Each one:
1. Has `DOCUMENTATION`, `EXAMPLES`, `RETURN` YAML blocks
2. Imports `AnsibleModule` + `SvKMSClient`
3. Uses `supports_check_mode=True`
4. Implements idempotent `present`/`absent` state management
5. Uses `extends_documentation_fragment: stormagic.stormagic.svkms`

- [ ] **Step 1: Create svkms_certificate.py**

Follow the `svkms_key.py` pattern. Key differences:
- `state`: `present`/`absent`
- Parameters: `name`, `cert_type` (choices: `ca`, `auth`, `tls`), `cert_id`
- API calls: `client.get_certificate()`, `client.list_certificates()`

- [ ] **Step 2: Create svkms_user.py**

Follow the `svkms_key.py` pattern. Key differences:
- Parameters: `username`, `role` (choices: `admin`, `operator`, `auditor`), `auth_type` (choices: `password`, `certificate`)
- API calls: `client.create_user()`, `client.get_user()`, `client.delete_user()`

- [ ] **Step 3: Create svkms_policy.py**

Follow the `svkms_key.py` pattern. Key differences:
- Parameters: `name`, `rules` (type: list of dicts)
- API calls: `client.create_policy()`, `client.get_policy()`, `client.delete_policy()`

- [ ] **Step 4: Create svkms_backup.py**

Different pattern — no state management, action-based:
- Parameters: `action` (choices: `backup`, `restore`), `destination`, `source`
- `backup` action calls `client.backup()`
- `restore` action calls `client.restore()`
- Always returns `changed=True` (backups are not idempotent)

- [ ] **Step 5: Write unit tests for svkms_certificate (covers the pattern)**

```python
# tests/unit/plugins/modules/test_svkms_certificate.py
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.stormagic.stormagic.plugins.modules import svkms_certificate


class TestSvKMSCertificate:
    @patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_certificate.SvKMSClient")
    def test_list_certificates(self, MockClient):
        client = MockClient.return_value
        client.list_certificates.return_value = [
            {"id": "cert-1", "type": "ca", "subject": "CN=SvKMS CA"}
        ]

        with pytest.raises(SystemExit):
            with patch("ansible_collections.stormagic.stormagic.plugins.modules.svkms_certificate.AnsibleModule") as mock_cls:
                mock_module = MagicMock()
                mock_module.params = {"state": "present", "name": None, "cert_id": None, "cert_type": "ca"}
                mock_module.check_mode = False
                mock_module.exit_json = MagicMock(side_effect=SystemExit(0))
                mock_cls.return_value = mock_module
                svkms_certificate.main()

        mock_module.exit_json.assert_called_once()
```

- [ ] **Step 6: Run all SvKMS unit tests**

```bash
PYTHONPATH=. python -m pytest tests/unit/plugins/modules/test_svkms_*.py -v
```

Expected: All PASS.

- [ ] **Step 7: Run sanity on all new modules**

```bash
cd ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test validate-modules plugins/modules/svkms_*.py
```

- [ ] **Step 8: Commit**

```bash
git add plugins/modules/svkms_certificate.py plugins/modules/svkms_user.py \
       plugins/modules/svkms_policy.py plugins/modules/svkms_backup.py \
       tests/unit/plugins/modules/test_svkms_certificate.py
git commit -m "feat: add svkms_certificate, svkms_user, svkms_policy, svkms_backup modules"
```

---

## Phase 4: SvSAN PowerShell Backend

### Task 10: SvSAN PowerShell Module Utils

**Files:**
- Create: `plugins/module_utils/SvSAN.psm1`

- [ ] **Step 1: Create the shared PowerShell module utility**

```powershell
# plugins/module_utils/SvSAN.psm1
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

Function New-SmCredentialFromParams {
    <#
    .SYNOPSIS
        Creates a PSCredential from module parameters.
    #>
    [CmdletBinding()]
    [OutputType([PSCredential])]
    Param(
        [Parameter(Mandatory = $true)]
        [string]$Username,

        [Parameter(Mandatory = $true)]
        [string]$Password
    )

    $securePass = ConvertTo-SecureString -String $Password -AsPlainText -Force
    return New-Object PSCredential($Username, $securePass)
}


Function Connect-SmVsa {
    <#
    .SYNOPSIS
        Establishes a session to a StorMagic VSA and returns the session object.
    #>
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)]
        [string]$Hostname,

        [Parameter(Mandatory = $true)]
        [PSCredential]$Credential
    )

    try {
        $session = New-SmSession -HostName $Hostname -Credential $Credential
        return $session
    }
    catch {
        throw "Failed to connect to VSA '{0}': {1}" -f $Hostname, $_.Exception.Message
    }
}


Function Invoke-SmHealthChecks {
    <#
    .SYNOPSIS
        Runs a set of health checks against a VSA session and returns structured results.
    #>
    [CmdletBinding()]
    [OutputType([hashtable])]
    Param(
        [Parameter(Mandatory = $true)]
        $Session,

        [string[]]$Checks = @("connectivity", "license", "targets", "mirrors", "pools"),

        [int]$MirrorSyncThreshold = 100,

        [int]$PoolCapacityWarnPct = 80
    )

    $results = @{
        checks  = @{}
        overall = "pass"
        details = @{}
    }

    $results.checks.connectivity = "pass"

    if ($Checks -contains "license") {
        try {
            $license = Get-SmLicense -Session $Session
            $results.details.license = $license
            $results.checks.license = if ($license.IsValid) { "pass" } else { "fail" }
        }
        catch {
            $results.checks.license = "fail"
            $results.details.license = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "targets") {
        try {
            $targets = @(Get-SmTargets -Session $Session)
            $results.details.targets = $targets
            $results.checks.targets = "pass"
            foreach ($t in $targets) {
                if ($t.Status -ne "Online") {
                    $results.checks.targets = "fail"
                    break
                }
            }
        }
        catch {
            $results.checks.targets = "fail"
            $results.details.targets = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "mirrors") {
        try {
            $mirrors = @(Get-SmMirrorStatus -Session $Session)
            $results.details.mirrors = $mirrors
            $results.checks.mirrors = "pass"
            foreach ($m in $mirrors) {
                if ($m.SyncPercentage -lt $MirrorSyncThreshold) {
                    $results.checks.mirrors = "fail"
                    break
                }
            }
        }
        catch {
            $results.checks.mirrors = "fail"
            $results.details.mirrors = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "pools") {
        try {
            $pools = @(Get-SmPools -Session $Session)
            $results.details.pools = $pools
            $results.checks.pools = "pass"
            foreach ($p in $pools) {
                if ($p.TotalCapacity -gt 0) {
                    $usedPct = ($p.UsedCapacity / $p.TotalCapacity) * 100
                    if ($usedPct -ge $PoolCapacityWarnPct) {
                        $results.checks.pools = "warn"
                    }
                }
            }
        }
        catch {
            $results.checks.pools = "fail"
            $results.details.pools = @{ error = $_.Exception.Message }
        }
    }

    if ($results.checks.Values -contains "fail") {
        $results.overall = "fail"
    }
    elseif ($results.checks.Values -contains "warn") {
        $results.overall = "warn"
    }

    return $results
}

Export-ModuleMember -Function * -Cmdlet *
```

- [ ] **Step 2: Commit**

```bash
git add plugins/module_utils/SvSAN.psm1
git commit -m "feat: add SvSAN PowerShell module utils with health check functions"
```

---

### Task 11: SvSAN Doc Fragment

**Files:**
- Create: `plugins/doc_fragments/svsan.py`

- [ ] **Step 1: Create the SvSAN doc fragment**

```python
# plugins/doc_fragments/svsan.py
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
  vsa_username:
    description:
      - Username for authenticating to the VSA.
    type: str
    required: true
  vsa_password:
    description:
      - Password for authenticating to the VSA.
    type: str
    required: true
    no_log: true
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
```

- [ ] **Step 2: Commit**

```bash
git add plugins/doc_fragments/svsan.py
git commit -m "feat: add SvSAN doc fragment with connection requirements"
```

---

## Phase 5: SvSAN PowerShell Modules

### Task 12: svsan_health_check Module (Flagship — Full TDD)

**Files:**
- Create: `plugins/modules/svsan_health_check.ps1`
- Create: `plugins/modules/svsan_health_check.py` (doc stub)

- [ ] **Step 1: Create the PowerShell module**

```powershell
# plugins/modules/svsan_health_check.ps1
#!powershell

# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ansible_collections.stormagic.stormagic.plugins.module_utils.SvSAN

$spec = @{
    options = @{
        vsa_hostname = @{ type = "str"; required = $true }
        vsa_username = @{ type = "str"; required = $true }
        vsa_password = @{ type = "str"; required = $true; no_log = $true }
        checks = @{
            type = "list"
            elements = "str"
            default = @("connectivity", "license", "targets", "mirrors", "pools")
        }
        mirror_sync_threshold = @{ type = "int"; default = 100 }
        pool_capacity_warn_pct = @{ type = "int"; default = 80 }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

try {
    $cred = New-SmCredentialFromParams -Username $module.Params.vsa_username `
                                        -Password $module.Params.vsa_password

    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $health = Invoke-SmHealthChecks -Session $session `
        -Checks $module.Params.checks `
        -MirrorSyncThreshold $module.Params.mirror_sync_threshold `
        -PoolCapacityWarnPct $module.Params.pool_capacity_warn_pct

    $module.Result.health = $health
    $module.Result.changed = $false

    if ($health.overall -eq "fail") {
        $module.FailJson("VSA health check failed", $module.Result)
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("Health check error: $_", $_)
}
```

- [ ] **Step 2: Create the Python doc stub**

```python
# plugins/modules/svsan_health_check.py
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: svsan_health_check
short_description: Run health checks on a StorMagic SvSAN VSA
version_added: "1.0.0"
description:
  - Performs comprehensive health checks against a StorMagic SvSAN Virtual Storage Appliance.
  - Checks connectivity, license validity, target status, mirror synchronization, and pool capacity.
  - Returns structured pass/warn/fail results for use in patching workflows.
  - Fails the task if any check returns fail status.
options:
  vsa_hostname:
    description:
      - Hostname or IP of the target SvSAN VSA.
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
  checks:
    description:
      - List of health checks to perform.
    type: list
    elements: str
    default: [connectivity, license, targets, mirrors, pools]
  mirror_sync_threshold:
    description:
      - Minimum acceptable mirror synchronization percentage.
    type: int
    default: 100
  pool_capacity_warn_pct:
    description:
      - Pool usage percentage that triggers a warning.
    type: int
    default: 80
extends_documentation_fragment:
  - stormagic.stormagic.svsan
author:
  - StorMagic Ltd (@stormagic)
"""

EXAMPLES = r"""
- name: Run full VSA health check
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_vsa_password }}"
  delegate_to: "{{ windows_mgmt_host }}"
  register: health

- name: Pre-patching health gate
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_host }}"
    vsa_username: "{{ svsan_user }}"
    vsa_password: "{{ svsan_pass }}"
    checks:
      - connectivity
      - mirrors
      - targets
    mirror_sync_threshold: 100
  delegate_to: "{{ windows_mgmt_host }}"
  register: preflight

- name: Abort if unhealthy
  ansible.builtin.fail:
    msg: "VSA not ready for patching"
  when: preflight.health.overall != 'pass'
"""

RETURN = r"""
health:
  description: Structured health check results.
  type: dict
  returned: always
  contains:
    overall:
      description: Overall status — pass, warn, or fail.
      type: str
      returned: always
    checks:
      description: Individual check results.
      type: dict
      returned: always
    details:
      description: Detailed data for each check.
      type: dict
      returned: always
  sample:
    overall: "pass"
    checks:
      connectivity: "pass"
      license: "pass"
      targets: "pass"
      mirrors: "pass"
      pools: "warn"
    details:
      license:
        is_valid: true
        expiry: "2027-01-01"
"""
```

- [ ] **Step 3: Run sanity on the module pair**

```bash
cd ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test validate-modules plugins/modules/svsan_health_check.py
```

- [ ] **Step 4: Commit**

```bash
git add plugins/modules/svsan_health_check.ps1 plugins/modules/svsan_health_check.py
git commit -m "feat: add svsan_health_check PowerShell module — flagship health check for patching workflows"
```

---

### Task 13: svsan_target and svsan_target_info Modules

**Files:**
- Create: `plugins/modules/svsan_target.ps1` + `svsan_target.py`
- Create: `plugins/modules/svsan_target_info.ps1` + `svsan_target_info.py`

Follow the exact same pattern as Task 12. Each module needs:

1. A `.ps1` file with `#!powershell`, `#AnsibleRequires` directives, `Ansible.Basic` arg spec, and SmCmdlet calls
2. A `.py` doc stub with `DOCUMENTATION`, `EXAMPLES`, `RETURN`

- [ ] **Step 1: Create svsan_target.ps1** — manages iSCSI targets (create/delete/modify) using `New-SmTarget`, `Remove-SmTarget`, `Set-SmTarget`

- [ ] **Step 2: Create svsan_target.py** — doc stub with state parameter (present/absent), name, size, pool, mirror options

- [ ] **Step 3: Create svsan_target_info.ps1** — read-only, uses `Get-SmTargets`, returns target list with path counts, sizes, mirror status

- [ ] **Step 4: Create svsan_target_info.py** — doc stub matching the return schema from the design spec (section 6.3)

- [ ] **Step 5: Run sanity**

```bash
cd ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test validate-modules plugins/modules/svsan_target*.py
```

- [ ] **Step 6: Commit**

```bash
git add plugins/modules/svsan_target*
git commit -m "feat: add svsan_target and svsan_target_info modules"
```

---

### Task 14: Remaining SvSAN Modules

**Files:**
- Create: `plugins/modules/svsan_mirror.ps1` + `.py`
- Create: `plugins/modules/svsan_mirror_info.ps1` + `.py`
- Create: `plugins/modules/svsan_pool.ps1` + `.py`
- Create: `plugins/modules/svsan_pool_info.ps1` + `.py`
- Create: `plugins/modules/svsan_license.ps1` + `.py`
- Create: `plugins/modules/svsan_config.ps1` + `.py`
- Create: `plugins/modules/svsan_config_info.ps1` + `.py`
- Create: `plugins/modules/svsan_vsa.ps1` + `.py`

All follow the svsan_health_check pattern. Each pair has:
- `.ps1`: `#!powershell`, `#AnsibleRequires -CSharpUtil Ansible.Basic`, `#AnsibleRequires -PowerShell ..module_utils.SvSAN`, arg spec, SmCmdlet calls
- `.py`: `DOCUMENTATION`, `EXAMPLES`, `RETURN`, `extends_documentation_fragment: stormagic.stormagic.svsan`

- [ ] **Step 1: Create svsan_mirror.ps1/.py** — `New-SmMirror`, `Remove-SmMirror`. State: present/absent.
- [ ] **Step 2: Create svsan_mirror_info.ps1/.py** — `Get-SmMirrorStatus`. Returns sync percentage, remote VSA.
- [ ] **Step 3: Create svsan_pool.ps1/.py** — pool management.
- [ ] **Step 4: Create svsan_pool_info.ps1/.py** — pool capacity info.
- [ ] **Step 5: Create svsan_license.ps1/.py** — `Set-SmLicense`. State: present.
- [ ] **Step 6: Create svsan_config.ps1/.py** — `Get-SmConfig`, `Set-SmConfig`. Read/write VSA configuration.
- [ ] **Step 7: Create svsan_config_info.ps1/.py** — read-only config facts via `Get-SmConfig`.
- [ ] **Step 8: Create svsan_vsa.ps1/.py** — `Install-SmVcVSA` for vSphere VSA deployment.

- [ ] **Step 9: Run sanity on all SvSAN modules**

```bash
cd ansible_collections/stormagic/stormagic
ansible-test sanity --local -v --test validate-modules plugins/modules/svsan_*.py
```

- [ ] **Step 10: Commit**

```bash
git add plugins/modules/svsan_mirror* plugins/modules/svsan_pool* \
       plugins/modules/svsan_license* plugins/modules/svsan_config* \
       plugins/modules/svsan_vsa*
git commit -m "feat: add remaining SvSAN modules — mirror, pool, license, config, vsa"
```

---

## Phase 6: Roles & Playbooks

### Task 15: svsan_patching_preflight Role

**Files:**
- Create: `roles/svsan_patching_preflight/tasks/main.yml`
- Create: `roles/svsan_patching_preflight/defaults/main.yml`
- Create: `roles/svsan_patching_preflight/meta/main.yml`

- [ ] **Step 1: Create role defaults**

```yaml
# roles/svsan_patching_preflight/defaults/main.yml
---
svsan_preflight_checks:
  - connectivity
  - license
  - targets
  - mirrors
  - pools

svsan_mirror_sync_threshold: 100
svsan_pool_capacity_warn_pct: 80
svsan_min_datastore_paths: 2
svsan_windows_mgmt_host: "{{ groups['windows_mgmt'][0] | default(omit) }}"
```

- [ ] **Step 2: Create role tasks**

```yaml
# roles/svsan_patching_preflight/tasks/main.yml
---
- name: Run StorMagic VSA health check
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
    checks: "{{ svsan_preflight_checks }}"
    mirror_sync_threshold: "{{ svsan_mirror_sync_threshold }}"
    pool_capacity_warn_pct: "{{ svsan_pool_capacity_warn_pct }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
  register: svsan_health_result

- name: Fail if VSA health check failed
  ansible.builtin.fail:
    msg: >-
      VSA {{ svsan_vsa_hostname }} failed pre-patching health check.
      Overall: {{ svsan_health_result.health.overall }}
      Details: {{ svsan_health_result.health.checks }}
  when: svsan_health_result.health.overall == 'fail'

- name: Gather target information
  stormagic.stormagic.svsan_target_info:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
  register: svsan_target_result

- name: Verify minimum datastore paths
  ansible.builtin.assert:
    that:
      - item.path_count >= svsan_min_datastore_paths
    fail_msg: "Target {{ item.name }} has only {{ item.path_count }} paths (minimum: {{ svsan_min_datastore_paths }})"
    quiet: true
  loop: "{{ svsan_target_result.targets }}"
  loop_control:
    label: "{{ item.name }}"

- name: Verify all mirrors are synchronized
  ansible.builtin.assert:
    that:
      - item.mirror.sync_pct >= svsan_mirror_sync_threshold
    fail_msg: "Target {{ item.name }} mirror sync at {{ item.mirror.sync_pct }}% (threshold: {{ svsan_mirror_sync_threshold }}%)"
    quiet: true
  loop: "{{ svsan_target_result.targets | selectattr('mirror.enabled', 'equalto', true) | list }}"
  loop_control:
    label: "{{ item.name }}"
  when: svsan_target_result.targets | selectattr('mirror.enabled', 'equalto', true) | list | length > 0
```

- [ ] **Step 3: Create role metadata**

```yaml
# roles/svsan_patching_preflight/meta/main.yml
---
galaxy_info:
  role_name: svsan_patching_preflight
  author: StorMagic Ltd
  description: Pre-patching health gate for StorMagic SvSAN
  license: GPL-3.0-or-later
  min_ansible_version: "2.16"
  platforms:
    - name: Windows
      versions:
        - all
dependencies: []
```

- [ ] **Step 4: Commit**

```bash
git add roles/svsan_patching_preflight/
git commit -m "feat: add svsan_patching_preflight role for pre-patching health gates"
```

---

### Task 16: svsan_patching_postflight Role

**Files:**
- Create: `roles/svsan_patching_postflight/tasks/main.yml`
- Create: `roles/svsan_patching_postflight/defaults/main.yml`
- Create: `roles/svsan_patching_postflight/meta/main.yml`

- [ ] **Step 1: Create postflight role**

```yaml
# roles/svsan_patching_postflight/defaults/main.yml
---
svsan_postflight_checks:
  - connectivity
  - targets
  - mirrors
svsan_postflight_mirror_sync_threshold: 100
svsan_windows_mgmt_host: "{{ groups['windows_mgmt'][0] | default(omit) }}"
```

```yaml
# roles/svsan_patching_postflight/tasks/main.yml
---
- name: Run post-patching VSA health check
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
    checks: "{{ svsan_postflight_checks }}"
    mirror_sync_threshold: "{{ svsan_postflight_mirror_sync_threshold }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
  register: svsan_postflight_result

- name: Report post-patching health status
  ansible.builtin.debug:
    msg: "VSA {{ svsan_vsa_hostname }} post-patching status: {{ svsan_postflight_result.health.overall }}"

- name: Fail if VSA unhealthy after patching
  ansible.builtin.fail:
    msg: >-
      VSA {{ svsan_vsa_hostname }} is unhealthy after patching.
      Checks: {{ svsan_postflight_result.health.checks }}
  when: svsan_postflight_result.health.overall == 'fail'
```

```yaml
# roles/svsan_patching_postflight/meta/main.yml
---
galaxy_info:
  role_name: svsan_patching_postflight
  author: StorMagic Ltd
  description: Post-patching verification for StorMagic SvSAN
  license: GPL-3.0-or-later
  min_ansible_version: "2.16"
  platforms:
    - name: Windows
      versions:
        - all
dependencies: []
```

- [ ] **Step 2: Commit**

```bash
git add roles/svsan_patching_postflight/
git commit -m "feat: add svsan_patching_postflight role"
```

---

### Task 17: Remaining Roles & Example Playbooks

**Files:**
- Create: `roles/svsan_deploy/` (tasks, defaults, meta)
- Create: `roles/svkms_setup/` (tasks, defaults, meta)
- Create: `playbooks/svkms_key_rotation.yml`
- Create: `playbooks/svsan_ha_setup.yml`
- Create: `playbooks/svsan_patching_workflow.yml`

- [ ] **Step 1: Create svsan_deploy role** — orchestrates `svsan_vsa` module to deploy a 2-node VSA pair

- [ ] **Step 2: Create svkms_setup role** — initial SvKMS configuration (create admin user, base policies, generate CA cert)

- [ ] **Step 3: Create example playbooks**

```yaml
# playbooks/svsan_patching_workflow.yml
---
- name: StorMagic SvSAN Patching Workflow
  hosts: esxi_hosts
  vars:
    windows_mgmt_host: win-mgmt.example.com
  tasks:
    - name: Pre-flight checks
      ansible.builtin.include_role:
        name: stormagic.stormagic.svsan_patching_preflight
      vars:
        svsan_vsa_hostname: "{{ hostvars[inventory_hostname].svsan_vsa }}"
        svsan_vsa_username: "{{ vault_svsan_user }}"
        svsan_vsa_password: "{{ vault_svsan_pass }}"
        svsan_windows_mgmt_host: "{{ windows_mgmt_host }}"

    # ESXi patching steps would go here (using VMware modules)

    - name: Post-flight verification
      ansible.builtin.include_role:
        name: stormagic.stormagic.svsan_patching_postflight
      vars:
        svsan_vsa_hostname: "{{ hostvars[inventory_hostname].svsan_vsa }}"
        svsan_vsa_username: "{{ vault_svsan_user }}"
        svsan_vsa_password: "{{ vault_svsan_pass }}"
        svsan_windows_mgmt_host: "{{ windows_mgmt_host }}"
```

```yaml
# playbooks/svkms_key_rotation.yml
---
- name: Rotate SvKMS Encryption Keys
  hosts: svkms_servers
  connection: ansible.netcommon.httpapi
  vars:
    ansible_network_os: stormagic.stormagic.svkms
    ansible_httpapi_use_ssl: true
  tasks:
    - name: Rotate the application encryption key
      stormagic.stormagic.svkms_key:
        name: app-encryption-key
        state: rotated
```

- [ ] **Step 4: Run ansible-lint on roles and playbooks**

```bash
ansible-lint roles/ playbooks/ --strict
```

- [ ] **Step 5: Commit**

```bash
git add roles/svsan_deploy/ roles/svkms_setup/ playbooks/
git commit -m "feat: add deployment roles and example playbooks"
```

---

## Phase 7: Integration Tests, Docs & Certification

### Task 18: Integration Test Framework

**Files:**
- Create: `tests/integration/integration_config.yml.template`
- Create: `tests/integration/targets/svkms_key/tasks/main.yml`
- Create: `tests/integration/targets/svsan_health_check/tasks/main.yml`

- [ ] **Step 1: Create integration config template**

```yaml
# tests/integration/integration_config.yml.template
---
# SvKMS connection
svkms_host: "kms.example.com"
svkms_port: 1443
svkms_username: "admin"
svkms_password: "changeme"
svkms_validate_certs: false

# SvSAN connection
svsan_vsa_hostname: "vsa1.example.com"
svsan_vsa_username: "admin"
svsan_vsa_password: "changeme"
svsan_windows_mgmt_host: "win-mgmt.example.com"
```

- [ ] **Step 2: Create svkms_key integration test**

```yaml
# tests/integration/targets/svkms_key/tasks/main.yml
---
- name: Create a test key
  stormagic.stormagic.svkms_key:
    name: integration-test-key
    algorithm: AES
    length: 256
    state: present
  register: create_result

- name: Verify key was created
  ansible.builtin.assert:
    that:
      - create_result.changed
      - create_result.key.name == "integration-test-key"

- name: Create same key again (idempotency)
  stormagic.stormagic.svkms_key:
    name: integration-test-key
    algorithm: AES
    length: 256
    state: present
  register: idem_result

- name: Verify no change on repeat
  ansible.builtin.assert:
    that:
      - not idem_result.changed

- name: Rotate the key
  stormagic.stormagic.svkms_key:
    name: integration-test-key
    state: rotated
  register: rotate_result

- name: Verify rotation
  ansible.builtin.assert:
    that:
      - rotate_result.changed
      - rotate_result.key.version | int > 1

- name: Destroy the test key
  stormagic.stormagic.svkms_key:
    name: integration-test-key
    state: absent
  register: delete_result

- name: Verify deletion
  ansible.builtin.assert:
    that:
      - delete_result.changed

- name: Destroy again (idempotency)
  stormagic.stormagic.svkms_key:
    name: integration-test-key
    state: absent
  register: idem_delete

- name: Verify no change
  ansible.builtin.assert:
    that:
      - not idem_delete.changed
```

- [ ] **Step 3: Create svsan_health_check integration test**

```yaml
# tests/integration/targets/svsan_health_check/tasks/main.yml
---
- name: Run health check
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
  register: health_result

- name: Verify structured response
  ansible.builtin.assert:
    that:
      - health_result.health is defined
      - health_result.health.overall in ['pass', 'warn', 'fail']
      - health_result.health.checks.connectivity == 'pass'
      - health_result.health.details is defined
      - not health_result.changed

- name: Run check mode
  stormagic.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
  check_mode: true
  register: check_result

- name: Verify check mode
  ansible.builtin.assert:
    that:
      - not check_result.changed
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "test: add integration test framework with svkms_key and svsan_health_check targets"
```

---

### Task 19: Documentation (README, Quickstarts, Changelog)

**Files:**
- Modify: `README.md`
- Create: `docs/svkms_quickstart.md`
- Create: `docs/svsan_quickstart.md`
- Create: `docs/patching_workflow.md`
- Create: `CHANGELOG.rst`

- [ ] **Step 1: Write the full README following Red Hat's certified template**

Required sections: Description, Requirements, Installation, Use Cases (3-5), Testing, Contributing, Support, Release Notes, Related Information, License. All links must be full URLs. No GitHub installation references. Installation focuses on Automation Hub.

- [ ] **Step 2: Create quickstart docs**

`docs/svkms_quickstart.md` — inventory setup, first key creation, key rotation example.
`docs/svsan_quickstart.md` — WinRM setup, Windows host requirements, first health check.
`docs/patching_workflow.md` — full enterprise-style patching workflow with preflight/postflight.

- [ ] **Step 3: Create CHANGELOG.rst**

```rst
============================
StorMagic Collection Release Notes
============================

.. contents:: Topics

v1.0.0
======

Release Summary
---------------
Initial release of the StorMagic Ansible collection.

New Modules
-----------
- stormagic.stormagic.svkms_key - Manage encryption keys on SvKMS
- stormagic.stormagic.svkms_key_info - Gather key information from SvKMS
- stormagic.stormagic.svkms_health_check - Check SvKMS server health
- stormagic.stormagic.svkms_certificate - Manage certificates on SvKMS
- stormagic.stormagic.svkms_user - Manage users on SvKMS
- stormagic.stormagic.svkms_policy - Manage key access policies on SvKMS
- stormagic.stormagic.svkms_backup - Backup and restore SvKMS
- stormagic.stormagic.svsan_health_check - Run health checks on SvSAN VSA
- stormagic.stormagic.svsan_target - Manage iSCSI targets on SvSAN
- stormagic.stormagic.svsan_target_info - Gather target info from SvSAN
- stormagic.stormagic.svsan_mirror - Manage mirrored storage on SvSAN
- stormagic.stormagic.svsan_mirror_info - Gather mirror status from SvSAN
- stormagic.stormagic.svsan_pool - Manage storage pools on SvSAN
- stormagic.stormagic.svsan_pool_info - Gather pool info from SvSAN
- stormagic.stormagic.svsan_license - Manage SvSAN licenses
- stormagic.stormagic.svsan_config - Manage VSA configuration
- stormagic.stormagic.svsan_config_info - Gather VSA configuration
- stormagic.stormagic.svsan_vsa - Deploy VSA instances

New Roles
---------
- stormagic.stormagic.svsan_patching_preflight - Pre-patching health gate
- stormagic.stormagic.svsan_patching_postflight - Post-patching verification
- stormagic.stormagic.svsan_deploy - Deploy SvSAN VSA pair
- stormagic.stormagic.svkms_setup - Initial SvKMS configuration

New Plugins
-----------
- httpapi: stormagic.stormagic.svkms - HttpApi plugin for SvKMS REST API
```

- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.rst docs/
git commit -m "docs: add certified README, quickstarts, changelog for v1.0.0"
```

---

### Task 20: Final Certification Validation & Build

**Files:**
- No new files — validation and build

- [ ] **Step 1: Run full sanity suite locally with Docker**

```bash
cd /Users/frawu/stormagic-ansible-collection/ansible_collections/stormagic/stormagic
ansible-test sanity --docker -v --color 2>&1 | tee /tmp/sanity-results.txt
```

Fix any errors. Common issues:
- Missing `from __future__` imports
- Line length > 160
- Missing `DOCUMENTATION` in doc stubs
- Invalid YAML in doc strings

- [ ] **Step 2: Run ansible-lint**

```bash
cd /Users/frawu/stormagic-ansible-collection
ansible-lint --strict 2>&1 | tee /tmp/lint-results.txt
```

- [ ] **Step 3: Run all unit tests**

```bash
cd /Users/frawu/stormagic-ansible-collection/ansible_collections/stormagic/stormagic
ansible-test units --docker -v --color 2>&1 | tee /tmp/unit-results.txt
```

- [ ] **Step 4: Build the collection tarball**

```bash
cd /Users/frawu/stormagic-ansible-collection
ansible-galaxy collection build --force
```

Expected: `Created collection for stormagic.stormagic at stormagic-stormagic-1.0.0.tar.gz`

- [ ] **Step 5: Validate with galaxy-importer**

```bash
pip install galaxy-importer
python -m galaxy_importer.main stormagic-stormagic-1.0.0.tar.gz 2>&1 | tee /tmp/importer-results.txt
```

Expected: PASS with no errors.

- [ ] **Step 6: Test local installation**

```bash
ansible-galaxy collection install stormagic-stormagic-1.0.0.tar.gz --force
ansible-doc stormagic.stormagic.svkms_key
ansible-doc stormagic.stormagic.svsan_health_check
```

Expected: Both docs render correctly.

- [ ] **Step 7: Final commit and tag**

```bash
git add -A
git commit -m "chore: final certification fixes for v1.0.0"
git tag -a v1.0.0 -m "v1.0.0 — initial certified release"
git push stormagic main --tags
```

---

## Post-Implementation: Red Hat Certification Submission

These steps happen after development is complete and require StorMagic business coordination:

1. **StorMagic registers** as Red Hat Technology Partner at `connect.redhat.com`
2. **Email** `ansiblepartners@redhat.com` to request the `stormagic` namespace
3. **Upload** `stormagic-stormagic-1.0.0.tar.gz` to Automation Hub
4. **Red Hat reviews** the collection — may request changes
5. **Iterate** until certified
6. **Monitor** `news-for-maintainers` tag on Ansible Forum for ongoing requirements
