# svsan_patching_postflight

Post-patching verification for StorMagic SvSAN. Waits for mirror resynchronization, runs health checks, and optionally compares against the preflight baseline to detect degradation.

## Requirements

- **Ansible**: >= 2.15
- **Collections**: `xianganwu.stormagic`, `vmware.vmware >= 2.0.0`
- **Platform**: Requires a Windows management host with PowerShell for SvSAN module delegation.

### Connection Model

SvSAN modules use PowerShell cmdlets delegated to a Windows management host. The role delegates module tasks to the host specified by `svsan_patching_postflight_windows_mgmt_host` (defaults to the first host in the `windows_mgmt` inventory group). The control node needs WinRM connectivity to that Windows host.

## Role Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `svsan_patching_postflight_vsa_hostname` | yes | -- | VSA hostname or IP address |
| `svsan_patching_postflight_vsa_username` | yes | -- | VSA admin username |
| `svsan_patching_postflight_vsa_password` | yes | -- | VSA admin password |
| `svsan_patching_postflight_checks` | no | connectivity, targets, mirrors | Health checks to run |
| `svsan_patching_postflight_mirror_sync_threshold` | no | `100` | Minimum mirror sync percentage to pass |
| `svsan_patching_postflight_windows_mgmt_host` | no | first `windows_mgmt` host | Windows host for PowerShell delegation |
| `svsan_patching_postflight_resync_wait` | no | `true` | Wait for mirrors to resynchronize before health check |
| `svsan_patching_postflight_resync_retries` | no | `30` | Maximum mirror sync poll attempts |
| `svsan_patching_postflight_resync_delay` | no | `60` | Seconds between mirror sync polls |
| `svsan_patching_postflight_preflight_baseline` | no | auto from preflight | Preflight health baseline for degradation detection |

## Output Variables

| Variable | Description |
|----------|-------------|
| `svsan_patching_postflight_status` | Overall health result: `pass`, `warn`, or `fail` |

## Mirror Resync Behavior

After an ESXi reboot, SvSAN mirrors need time to resynchronize. When `resync_wait` is true (default), the role polls mirror status every `resync_delay` seconds for up to `resync_retries` attempts before running the health check. For large mirrors, increase the limits:

```yaml
svsan_patching_postflight_resync_retries: 60   # Poll for up to 60 minutes
svsan_patching_postflight_resync_delay: 120     # Check every 2 minutes
```

## Example

```yaml
- name: Post-patching verification
  ansible.builtin.include_role:
    name: xianganwu.stormagic.svsan_patching_postflight
  vars:
    svsan_patching_postflight_vsa_hostname: "{{ hostvars[inventory_hostname].svsan_vsa }}"
    svsan_patching_postflight_vsa_username: "{{ vault_vsa_username }}"
    svsan_patching_postflight_vsa_password: "{{ vault_vsa_password }}"
    svsan_patching_postflight_windows_mgmt_host: "{{ groups['windows_mgmt'][0] }}"

- name: Report result
  ansible.builtin.debug:
    msg: "Post-patching status: {{ svsan_patching_postflight_status }}"
```

See [docs/patching_workflow.md](../../docs/patching_workflow.md) for the complete patching workflow.

## License

GPL-3.0-or-later
