# StorMagic Ansible Collection — Design Specification

**Date:** 2026-04-29
**Status:** Draft
**Author:** Frank Wu / Agent JodoKast

---

## 1. Overview

Build a unified Red Hat Ansible Certified Collection (`stormagic.stormagic`) that provides automation modules for both StorMagic products:

- **SvKMS** (Encryption Key Management) — via REST API
- **SvSAN** (Virtual SAN / HCI) — via PowerShell SmCmdlet Toolkit

The collection targets Red Hat Ansible Automation Hub certification and addresses a documented gap: the Sheetz AAP engagement (Aug 2025, 680+ stores, 1,600 ESXi hosts) identified that "there are currently no Ansible modules" for StorMagic operations and recommended that "Sheetz may contact StorMagic and request they consider supporting Ansible as a supported automation method and develop Ansible modules."

## 2. Goals

1. Provide idiomatic Ansible modules for StorMagic SvKMS and SvSAN
2. Pass Red Hat Ansible Certified Content requirements (sanity, lint, galaxy-importer)
3. Include health check modules that enable pre/post-patching workflows (the Sheetz use case)
4. Support at least 2 ansible-core versions (2.16, 2.17) plus devel
5. Use GPL-3.0-or-later license
6. Publish to both Ansible Galaxy and Automation Hub

## 3. Non-Goals

- REST API for SvSAN (does not exist; no public roadmap)
- Edge Control cloud API integration (no public API available)
- Community collection on Galaxy first — go directly to certified

## 4. Architecture

### 4.1 Dual-Language Collection

The collection contains two backend types:

| Backend | Language | Connection | Target Host |
|---------|----------|------------|-------------|
| SvKMS modules | Python | httpapi (HTTPS) | Ansible controller → SvKMS server |
| SvSAN modules | PowerShell (.ps1) | WinRM/PSRP | Windows management host with SmCmdlet |

This follows the established Ansible pattern: `ansible.windows` is a Red Hat-certified collection containing native PowerShell modules with Python documentation stubs.

### 4.2 Why Native PowerShell for SvSAN (Not Python Wrappers)

The initial architecture considered Python modules that build PowerShell command strings via `module.run_command()`. This was rejected because:

1. **Security**: Embedding credentials in command strings risks command injection and process-listing exposure
2. **Fragility**: String-building a translation layer between Python and PowerShell doubles maintenance burden
3. **Ansible guidance**: The official docs state Windows modules should be native PowerShell (.ps1) running on the Windows target via WinRM
4. **Precedent**: `ansible.windows` (certified) uses this exact pattern
5. **StorMagic's SDK**: SmCmdlet is a PowerShell module — native PS modules import it directly with no translation layer

### 4.3 SvKMS Architecture (Python + httpapi)

```
Ansible Controller (Linux)
  └── httpapi connection plugin (plugins/httpapi/svkms.py)
        ├── Handles: auth (primary: username/password → session token;
        │   alternative: API key header; alternative: client certificate)
        ├── Handles: session management, TLS cert validation, headers
        └── Sends: HTTPS requests to SvKMS REST API (/v0/keys/...)

  └── module_utils/svkms_api.py
        ├── SvKMSClient class (urllib-based, no external deps)
        ├── Key lifecycle: create, get, list, rotate, retire, destroy
        ├── User/policy/cert management
        └── Health check endpoint

  └── modules/svkms_*.py
        ├── Import SvKMSClient from module_utils
        ├── Standard AnsibleModule argument_spec
        ├── Idempotent state management (present/absent)
        └── Check mode support
```

### 4.4 SvSAN Architecture (PowerShell + WinRM)

```
Ansible Controller (Linux)
  └── WinRM/PSRP connection to Windows Management Host
        └── PowerShell modules execute on Windows host
              ├── Import SmCmdlet.dll natively
              ├── Import collection module_utils/SvSAN.psm1
              ├── Create SmSession to target VSA
              ├── Execute SmCmdlet cmdlets
              └── Return structured results via Ansible.Basic

Windows Management Host
  ├── StorMagic PowerShell Toolkit (SmCmdlet.dll) — bundled with SvSAN
  ├── WinRM configured (Kerberos or NTLM auth)
  └── Network access to SvSAN VSA(s)
```

### 4.5 Data Flow — Sheetz-Style Patching Workflow

```
AAP Workflow Template
  │
  ├── Step 1: Pre-flight Health Check
  │   └── stormagic.stormagic.svsan_health_check
  │       ├── Target: Windows mgmt host (via WinRM)
  │       ├── Checks: connectivity, license, targets, mirrors, pools
  │       └── Gate: fail workflow if any check fails
  │
  ├── Step 2: Get Target/Path Info
  │   └── stormagic.stormagic.svsan_target_info
  │       ├── Verify path count >= 2 per datastore
  │       └── Verify mirror sync at 100%
  │
  ├── Step 3: ESXi Patching (existing VMware modules)
  │   └── vmware.vmware.esxi_maintenance_mode + existing ESXi patching
  │
  └── Step 4: Post-flight Verification
      └── stormagic.stormagic.svsan_health_check
          └── Confirm VSA healthy after patching
```

## 5. Collection Structure

```
stormagic/stormagic/
├── galaxy.yml
├── README.md                         # Red Hat certified README template
├── LICENSE                           # GPL-3.0-or-later
├── CHANGELOG.rst
├── meta/
│   └── runtime.yml                   # requires_ansible: ">=2.16.0"
├── plugins/
│   ├── httpapi/
│   │   └── svkms.py                  # httpapi plugin for SvKMS REST API
│   ├── modules/
│   │   ├── svkms_key.py              # Key lifecycle management
│   │   ├── svkms_key_info.py         # Read-only key info
│   │   ├── svkms_certificate.py      # Certificate management
│   │   ├── svkms_user.py             # User management
│   │   ├── svkms_policy.py           # Key access policies
│   │   ├── svkms_backup.py           # Backup and restore
│   │   ├── svkms_health_check.py     # KMS health check
│   │   ├── svsan_health_check.ps1    # VSA health check (PowerShell)
│   │   ├── svsan_health_check.py     # Doc stub for ansible-doc
│   │   ├── svsan_target.ps1          # Target management
│   │   ├── svsan_target.py           # Doc stub
│   │   ├── svsan_target_info.ps1     # Read-only target info
│   │   ├── svsan_target_info.py      # Doc stub
│   │   ├── svsan_mirror.ps1          # Mirror management
│   │   ├── svsan_mirror.py           # Doc stub
│   │   ├── svsan_mirror_info.ps1     # Read-only mirror status
│   │   ├── svsan_mirror_info.py      # Doc stub
│   │   ├── svsan_pool.ps1            # Pool management
│   │   ├── svsan_pool.py             # Doc stub
│   │   ├── svsan_pool_info.ps1       # Read-only pool info
│   │   ├── svsan_pool_info.py        # Doc stub
│   │   ├── svsan_license.ps1         # License management
│   │   ├── svsan_license.py          # Doc stub
│   │   ├── svsan_config.ps1          # VSA configuration
│   │   ├── svsan_config.py           # Doc stub
│   │   ├── svsan_config_info.ps1     # Read-only config facts
│   │   ├── svsan_config_info.py      # Doc stub
│   │   ├── svsan_vsa.ps1             # VSA deployment (vSphere)
│   │   └── svsan_vsa.py              # Doc stub
│   ├── module_utils/
│   │   ├── svkms_api.py              # SvKMS REST API client (Python, urllib)
│   │   ├── SvSAN.psm1               # Shared PowerShell utilities
│   │   └── common.py                 # Shared argument specs
│   └── doc_fragments/
│       ├── svkms.py                   # Common SvKMS connection docs
│       └── svsan.py                   # Common SvSAN connection docs
├── roles/
│   ├── svsan_patching_preflight/     # Pre-patching health gate workflow
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   ├── svsan_patching_postflight/    # Post-patching verification
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   ├── svsan_deploy/                 # Deploy SvSAN VSA pair
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── meta/main.yml
│   └── svkms_setup/                  # Initial SvKMS configuration
│       ├── tasks/main.yml
│       ├── defaults/main.yml
│       └── meta/main.yml
├── playbooks/
│   ├── svkms_key_rotation.yml        # Example: automated key rotation
│   ├── svsan_ha_setup.yml            # Example: HA storage deployment
│   └── svsan_patching_workflow.yml   # Example: full patching workflow
├── tests/
│   ├── unit/
│   │   ├── plugins/modules/
│   │   │   ├── test_svkms_key.py                # pytest
│   │   │   ├── test_svkms_api.py                # pytest
│   │   │   ├── test_svsan_health_check.Tests.ps1 # Pester
│   │   │   └── test_svsan_target.Tests.ps1       # Pester
│   │   └── plugins/module_utils/
│   │       ├── test_svkms_api.py
│   │       └── test_SvSAN.Tests.ps1
│   ├── integration/
│   │   ├── targets/
│   │   │   ├── svkms_key/
│   │   │   │   └── tasks/main.yml
│   │   │   ├── svsan_health_check/
│   │   │   │   └── tasks/main.yml
│   │   │   ├── svsan_target/
│   │   │   │   └── tasks/main.yml
│   │   │   └── ...
│   │   └── integration_config.yml.template
│   └── sanity/
│       ├── ignore-2.16.txt
│       └── ignore-2.17.txt
├── docs/
│   ├── svkms_quickstart.md
│   ├── svsan_quickstart.md
│   └── patching_workflow.md
└── .github/
    └── workflows/
        ├── certification.yml          # Red Hat partner-certification-checker
        └── ci.yml                     # Unit tests + PSScriptAnalyzer
```

## 6. Module Details

### 6.1 SvSAN Health Check Module (`svsan_health_check`)

The flagship module — directly addresses the Sheetz gap.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `vsa_hostname` | str | yes | - | VSA hostname or IP |
| `vsa_username` | str | yes | - | VSA admin username |
| `vsa_password` | str | yes (no_log) | - | VSA admin password |
| `checks` | list[str] | no | all | Which checks to run |
| `mirror_sync_threshold` | int | no | 100 | Minimum mirror sync % |
| `pool_capacity_warn_pct` | int | no | 80 | Pool usage warning threshold |

**Available checks:** `connectivity`, `license`, `targets`, `mirrors`, `pools`

**Return data:**

```json
{
  "changed": false,
  "health": {
    "overall": "pass|warn|fail",
    "checks": {
      "connectivity": "pass",
      "license": "pass",
      "targets": "pass",
      "mirrors": "pass",
      "pools": "warn"
    },
    "details": {
      "license": {"is_valid": true, "expiry": "2027-01-01"},
      "mirrors": [{"name": "mirror1", "sync_pct": 100}],
      "targets": [{"name": "target1", "status": "Online", "paths": 4}],
      "pools": [{"name": "pool1", "used_pct": 82, "total_gb": 1000}]
    }
  }
}
```

### 6.2 SvKMS Key Module (`svkms_key`)

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `state` | str | no | present | present, absent, rotated, retired |
| `name` | str | yes | - | Key name |
| `key_id` | str | no | - | Key ID (for existing keys) |
| `algorithm` | str | no | AES | Algorithm (AES, RSA, etc.) |
| `length` | int | no | 256 | Key length in bits |
| `metadata` | dict | no | - | Custom key metadata |

### 6.3 SvSAN Target Info Module (`svsan_target_info`)

Returns datastore path counts, sizes, mirror status — the exact data Sheetz needed for pre-patching validation.

**Return data:**

```json
{
  "changed": false,
  "targets": [
    {
      "name": "datastore1",
      "size_gb": 500,
      "status": "Online",
      "path_count": 4,
      "mirror": {
        "enabled": true,
        "sync_pct": 100,
        "remote_vsa": "vsa2.example.com"
      },
      "pool": "pool1"
    }
  ]
}
```

## 7. Testing Strategy

### 7.1 Layer 1: Static Analysis (every PR)

- `ansible-test sanity` against ansible-core 2.16, 2.17, devel
- `ansible-lint` with strict mode
- `PSScriptAnalyzer` for PowerShell modules
- Runs in GitHub Actions CI

### 7.2 Layer 2: Unit Tests (every PR)

- **Python (pytest):** Mock `urllib` responses, test SvKMS module logic and idempotency
- **PowerShell (Pester):** Mock SmCmdlet functions, test SvSAN module logic and health check outcomes
- Target: 80%+ code coverage on module_utils

### 7.3 Layer 3: Integration Tests (pre-release, manual)

- Requires live SvKMS instance + SvSAN VSA pair + Windows management host
- Molecule scenarios for end-to-end validation
- Tests create/read/update/delete cycles with real API calls
- Health check validation against known-good and known-degraded states

### 7.4 Layer 4: Certification Checks (pre-upload)

- Red Hat partner-certification-checker GitHub Action
- `galaxy-importer` validation
- Build tarball and test import locally before Automation Hub upload

## 8. Red Hat Certification Workflow

### 8.1 Prerequisites

1. StorMagic registers as Red Hat Technology Partner at connect.redhat.com
2. Accept partnership and certification agreements
3. Email ansiblepartners@redhat.com to request `stormagic` namespace
4. Namespace registered on both Ansible Galaxy and Automation Hub

### 8.2 Development & Testing

5. Develop collection following this spec
6. Pass all 4 test layers
7. README follows Red Hat certified collection template (required sections: Description, Requirements, Installation, Use Cases, Testing, Support, Release Notes, License)
8. galaxy.yml metadata complete and accurate
9. No dependencies on community collections (only certified or ansible-core builtins)

### 8.3 Submission

10. Build tarball: `ansible-galaxy collection build`
11. Upload to Automation Hub
12. Red Hat reviews and certifies
13. Collection available to AAP subscribers

### 8.4 Ongoing Maintenance

14. Support 2+ ansible-core versions tied to supported AAP versions
15. Monitor `news-for-maintainers` tag on Ansible Forum
16. Update sanity ignore files per new ansible-core releases
17. Collections not maintained are subject to deprecation and removal

## 9. galaxy.yml

```yaml
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
repository: https://github.com/stormagic/ansible-collection-stormagic
documentation: https://github.com/stormagic/ansible-collection-stormagic/blob/main/README.md
homepage: https://stormagic.com
issues: https://github.com/stormagic/ansible-collection-stormagic/issues
build_ignore:
  - .github
  - .gitignore
  - tests/integration
```

## 10. meta/runtime.yml

```yaml
requires_ansible: ">=2.16.0"
```

## 11. Dependencies

### Python (SvKMS modules — controller side)

- `ansible-core >= 2.16` (provides urllib, json, base64)
- No external PyPI packages (urllib is stdlib)

### PowerShell (SvSAN modules — Windows target side)

- PowerShell 5.1+ (Windows Server 2016+)
- StorMagic PowerShell Toolkit (SmCmdlet.dll) — bundled with SvSAN installation
- WinRM or PSRP connection configured (Kerberos or NTLM auth)

### Ansible collection dependencies

- None (no dependency on community.general, community.windows, or any non-certified collection)

## 12. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| SvKMS REST API docs not publicly available | High | Obtain API reference from SvKMS instance Support section; work with StorMagic engineering |
| SmCmdlet cmdlet names/params differ between SvSAN versions | Medium | Test against 6.2 and 6.3; document minimum SvSAN version; use version detection |
| Red Hat certification rejects PowerShell modules | Low | `ansible.windows` (certified) sets precedent; engage Ansible Partner Engineering early |
| StorMagic adds REST API to SvSAN, obsoleting PS modules | Low (no roadmap) | Architecture supports both backends; add Python modules alongside PS if/when API appears |
| WinRM connection issues at scale (Sheetz hit 40+ concurrent limit) | Medium | Document WinRM MaxShellsPerUser tuning; roles include prereq checks |

## 13. Success Criteria

1. Collection passes `ansible-test sanity` on 2.16, 2.17, and devel
2. Collection passes `ansible-lint --strict`
3. Collection passes Red Hat partner-certification-checker
4. `svsan_health_check` module returns accurate health data from a live VSA
5. `svkms_key` module can create, rotate, and destroy keys via REST API
6. `svsan_patching_preflight` role gates patching on health status
7. Collection uploads and certifies on Automation Hub
8. README passes Red Hat's certified collection template requirements

## 14. References

- [Red Hat Ansible Certified Content FAQ](https://access.redhat.com/articles/4916901)
- [Red Hat Ansible Certification Portal](https://connect.redhat.com/en/partner-with-us/red-hat-ansible-automation-certification)
- [Partner Certification Checker](https://github.com/ansible-collections/partner-certification-checker)
- [Ansible Collection Structure](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_structure.html)
- [Windows Module Development](https://docs.ansible.com/projects/ansible/latest/dev_guide/developing_modules_general_windows.html)
- [httpapi Plugin Docs](https://docs.ansible.com/ansible/latest/plugins/httpapi.html)
- [StorMagic SvKMS REST API](https://stormagic.com/encryption-key-management/features/rest-api/)
- [StorMagic PowerShell Toolkit](https://stormagic.com/doc/svsan/6-2/en/Content/PT-introduction.htm)
- [Sheetz Case Study](https://stormagic.com/resources/case-studies/sheetz-case-study/)
- [Sheetz AAP Close Out Presentation](internal — Aug 2025)
