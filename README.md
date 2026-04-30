# StorMagic Collection for Ansible

[![CI](https://github.com/xianganwu/stormagic-ansible-collection/actions/workflows/ci.yml/badge.svg)](https://github.com/xianganwu/stormagic-ansible-collection/actions)

This collection provides Ansible modules for managing **StorMagic SvKMS** (Encryption Key Management) and **StorMagic SvSAN** (Virtual SAN / HCI) infrastructure.

## Description

The `xianganwu.stormagic` collection enables automation of:

- **SvKMS**: Key lifecycle management (create, rotate, retire, destroy), user and policy management, certificate management, backup and restore, and health monitoring via the SvKMS REST API.
- **SvSAN**: Virtual Storage Appliance health checks, iSCSI target and mirror management, storage pool management, VSA deployment, license and configuration management via the StorMagic PowerShell Toolkit.

The collection includes pre-built roles for common workflows such as pre/post-patching health gates and initial deployment.

## Requirements

### Ansible

- ansible-core >= 2.16.0

### Python

- Python >= 3.10 (on the Ansible controller)

### PowerShell (for SvSAN modules)

- PowerShell 5.1 or later (on the Windows management host)
- StorMagic PowerShell Toolkit (SmCmdlet.dll) — bundled with SvSAN installation
- WinRM or PSRP connectivity configured between the Ansible controller and the Windows management host

### Collection Dependencies

| Collection | Version | Purpose |
|------------|---------|---------|
| `vmware.vmware` | >= 2.0.0 | Required by the `svsan_deploy` role for vSphere VM operations |

## Installation

### Automation Hub (Recommended)

Install from Red Hat Ansible Automation Hub:

```bash
ansible-galaxy collection install xianganwu.stormagic
```

### From Source

```bash
git clone https://github.com/xianganwu/stormagic-ansible-collection.git
cd stormagic-ansible-collection
ansible-galaxy collection build
ansible-galaxy collection install xianganwu-stormagic-*.tar.gz
```

## Use Cases

### 1. Pre-Patching Health Gate

Validate SvSAN VSA health before ESXi patching:

```yaml
- name: Pre-patching health check
  hosts: esxi_hosts
  tasks:
    - name: Run preflight checks
      ansible.builtin.include_role:
        name: xianganwu.stormagic.svsan_patching_preflight
      vars:
        svsan_vsa_hostname: "{{ svsan_vsa }}"
        svsan_vsa_username: "{{ vault_user }}"
        svsan_vsa_password: "{{ vault_pass }}"
        svsan_windows_mgmt_host: win-mgmt.example.com
```

### 2. Automated Key Rotation

Rotate encryption keys on SvKMS:

```yaml
- name: Rotate encryption key
  xianganwu.stormagic.svkms_key:
    name: app-encryption-key
    state: rotated
```

### 3. VSA Health Monitoring

Check VSA health with configurable thresholds:

```yaml
- name: Check VSA health
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_pass }}"
    mirror_sync_threshold: 100
    pool_capacity_warn_pct: 80
  delegate_to: "{{ windows_mgmt_host }}"
```

### 4. Storage Target Management

Create and manage iSCSI targets:

```yaml
- name: Create iSCSI target
  xianganwu.stormagic.svsan_target:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: "{{ vault_pass }}"
    name: datastore1
    size_gb: 500
    pool: pool1
    state: present
  delegate_to: "{{ windows_mgmt_host }}"
```

### 5. KMS Health Check

Verify SvKMS server health:

```yaml
- name: Check KMS health
  xianganwu.stormagic.svkms_health_check:
  register: health

- name: Assert healthy
  ansible.builtin.assert:
    that: health.health.status == 'healthy'
```

## Included Content

### Modules

| Module | Description |
|--------|-------------|
| `svkms_key` | Manage encryption keys on SvKMS |
| `svkms_key_info` | Gather key information from SvKMS |
| `svkms_health_check` | Check SvKMS server health |
| `svkms_certificate` | Manage certificates on SvKMS |
| `svkms_user` | Manage users on SvKMS |
| `svkms_policy` | Manage key access policies on SvKMS |
| `svkms_backup` | Backup and restore SvKMS |
| `svsan_health_check` | Run health checks on SvSAN VSA |
| `svsan_target` | Manage iSCSI targets on SvSAN |
| `svsan_target_info` | Gather target info from SvSAN |
| `svsan_mirror` | Manage mirrored storage on SvSAN |
| `svsan_mirror_info` | Gather mirror status from SvSAN |
| `svsan_pool` | Manage storage pools on SvSAN |
| `svsan_pool_info` | Gather pool info from SvSAN |
| `svsan_license` | Manage SvSAN licenses |
| `svsan_config` | Manage VSA configuration |
| `svsan_config_info` | Gather VSA configuration |
| `svsan_vsa` | Deploy VSA instances |

### Roles

| Role | Description |
|------|-------------|
| `svsan_patching_preflight` | Pre-patching health gate |
| `svsan_patching_postflight` | Post-patching verification |
| `svsan_deploy` | Deploy SvSAN VSA pair |
| `svkms_setup` | Initial SvKMS configuration |
| `svkms_key_rotation` | Rotate encryption keys on SvKMS |

### Plugins

| Plugin | Type | Description |
|--------|------|-------------|
| `svkms` | httpapi | HttpApi plugin for SvKMS REST API |

## Testing

### Sanity Tests

```bash
ansible-test sanity --docker -v
```

### Unit Tests

```bash
ansible-test units --docker -v
```

### Integration Tests

Integration tests require live SvKMS and SvSAN infrastructure:

```bash
cp tests/integration/integration_config.yml.template tests/integration/integration_config.yml
# Edit integration_config.yml with your connection details
ansible-test integration -v
```

## Contributing

We welcome contributions. Please submit pull requests to the [GitHub repository](https://github.com/xianganwu/stormagic-ansible-collection).

## Support

As Red Hat Ansible Certified Content, this collection is entitled to support through
[Ansible Automation Platform](https://access.redhat.com/products/red-hat-ansible-automation-platform/).

For issues with this collection, please open a [GitHub issue](https://github.com/xianganwu/stormagic-ansible-collection/issues).

For StorMagic product support, contact [StorMagic Support](https://stormagic.com/support/).

## Release Notes

See the [CHANGELOG](https://github.com/xianganwu/stormagic-ansible-collection/blob/main/CHANGELOG.rst) for release notes.

## Related Information

- [StorMagic SvKMS Documentation](https://stormagic.com/encryption-key-management/documentation/)
- [StorMagic SvSAN Documentation](https://stormagic.com/svsan/documentation/)
- [StorMagic PowerShell Toolkit](https://stormagic.com/doc/svsan/6-2/en/Content/PT-introduction.htm)
- [Ansible Collection Development Guide](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)

## License

GPL-3.0-or-later — see [LICENSE](https://github.com/xianganwu/stormagic-ansible-collection/blob/main/LICENSE) for the full text.
