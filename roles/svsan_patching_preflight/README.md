# svsan_patching_preflight

Pre-patching health gate for StorMagic SvSAN. Validates VSA health, target datastore paths, and mirror synchronization before ESXi patching. Fails the play if any check is below threshold.

## Requirements

- **Ansible**: >= 2.15
- **Collections**: `xianganwu.stormagic`. The patching workflow playbook also requires `vmware.vmware >= 2.0.0` for ESXi maintenance mode management.
- **Platform**: Requires a Windows management host with PowerShell for SvSAN module delegation. Optional ESXi preflight checks (`check_esxi: true`) require PowerCLI on the Windows host and vCenter credentials.

### Connection Model

SvSAN modules use PowerShell cmdlets delegated to a Windows management host. The role delegates module tasks to the host specified by `svsan_patching_preflight_windows_mgmt_host` (defaults to the first host in the `windows_mgmt` inventory group). The control node needs WinRM connectivity to that Windows host.

## Role Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `svsan_patching_preflight_vsa_hostname` | yes | -- | VSA hostname or IP address |
| `svsan_patching_preflight_vsa_username` | yes | -- | VSA admin username |
| `svsan_patching_preflight_vsa_password` | yes | -- | VSA admin password |
| `svsan_patching_preflight_checks` | no | all 5 checks | Health checks to run (connectivity, license, targets, mirrors, pools) |
| `svsan_patching_preflight_mirror_sync_threshold` | no | `100` | Minimum mirror sync percentage to pass |
| `svsan_patching_preflight_pool_capacity_warn_pct` | no | `80` | Pool capacity percentage that triggers a warning |
| `svsan_patching_preflight_min_datastore_paths` | no | `2` | Minimum datastore paths required per target |
| `svsan_patching_preflight_windows_mgmt_host` | no | first `windows_mgmt` host | Windows host for PowerShell delegation |
| `svsan_patching_preflight_check_esxi` | no | `false` | Run ESXi preflight checks via vCenter (requires PowerCLI) |
| `svsan_patching_preflight_vcenter_hostname` | no | -- | vCenter hostname (required when `check_esxi` is true) |
| `svsan_patching_preflight_vcenter_username` | no | -- | vCenter username (required when `check_esxi` is true) |
| `svsan_patching_preflight_vcenter_password` | no | -- | vCenter password (required when `check_esxi` is true) |
| `svsan_patching_preflight_esxi_hostname` | no | `inventory_hostname` | ESXi hostname to check |
| `svsan_patching_preflight_vcenter_validate_certs` | no | `true` | Validate vCenter TLS certificates |

## Output Variables

The role sets these facts for use in subsequent tasks:

| Variable | Description |
|----------|-------------|
| `svsan_patching_preflight_status` | Overall health result: `pass`, `warn`, or `fail` |
| `svsan_patching_preflight_baseline` | Full health data dict (passed to postflight for comparison) |

## Example

```yaml
- name: Pre-patching health gate
  ansible.builtin.include_role:
    name: xianganwu.stormagic.svsan_patching_preflight
  vars:
    svsan_patching_preflight_vsa_hostname: "{{ hostvars[inventory_hostname].svsan_vsa }}"
    svsan_patching_preflight_vsa_username: "{{ vault_vsa_username }}"
    svsan_patching_preflight_vsa_password: "{{ vault_vsa_password }}"
    svsan_patching_preflight_windows_mgmt_host: "{{ groups['windows_mgmt'][0] }}"
    svsan_patching_preflight_mirror_sync_threshold: 100

- name: Abort if VSA unhealthy
  ansible.builtin.fail:
    msg: "VSA not ready for patching"
  when: svsan_patching_preflight_status != 'pass'
```

See [docs/patching_workflow.md](../../docs/patching_workflow.md) for the complete patching workflow.

## License

GPL-3.0-or-later
