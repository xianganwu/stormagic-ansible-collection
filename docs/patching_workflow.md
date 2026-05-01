# ESXi Patching Workflow with SvSAN Health Gates

Complete ESXi patching workflow using the StorMagic SvSAN patching roles.
The preflight and postflight roles ensure StorMagic VSA health before and
after ESXi patching, with optional vCenter alert checking.

## Workflow Overview

1. **ESXi Preflight** (optional) — Check vCenter alerts, get build number
2. **SvSAN Preflight** — Validate VSA health, mirror sync, datastore paths
3. **Maintenance Mode** — Enter via vCenter
4. **Patch** — Apply ESXi patches (customer-specific)
5. **Reboot** — Reboot and wait for recovery
6. **Exit Maintenance** — Exit via vCenter
7. **Mirror Resync Wait** — Poll until mirrors reach sync threshold
8. **SvSAN Postflight** — Validate VSA health, compare against baseline

### Workflow Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  ESXi Preflight  │────▶│  SvSAN Preflight  │────▶│ Enter Maintenance│
│   (optional)     │     │  (health gate)    │     │   Mode           │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                         FAIL = stop patching              ▼
                                                  ┌──────────────────┐
┌──────────────────┐     ┌──────────────────┐     │   Apply Patch    │
│ SvSAN Postflight │◀────│  Mirror Resync   │◀────│   + Reboot       │
│ (health compare) │     │   Wait           │     └──────────────────┘
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Exit Maintenance │
│   Mode           │
└──────────────────┘
```

## Prerequisites

- ansible-core >= 2.16.0
- Windows management host with StorMagic PowerShell Toolkit
- WinRM connectivity to Windows management host
- VMware PowerCLI (only if using ESXi preflight checks)
- `vmware.vmware` collection >= 2.0.0

## Inventory Setup

```yaml
# inventory/hosts.yml
all:
  children:
    windows_mgmt:
      hosts:
        win-mgmt:
          ansible_host: win-mgmt.example.com
          ansible_connection: winrm
          ansible_user: administrator
          ansible_password: "{{ vault_windows_password }}"
          ansible_winrm_operation_timeout_sec: 120
          ansible_winrm_read_timeout_sec: 150

    esxi_hosts:
      hosts:
        esxi1:
          ansible_host: esxi1.example.com
          svsan_vsa: vsa1.example.com
        esxi2:
          ansible_host: esxi2.example.com
          svsan_vsa: vsa2.example.com
      vars:
        ansible_connection: ssh
        ansible_user: root
        vcenter_hostname: vcenter.example.com
        vcenter_username: "{{ vault_vcenter_username }}"
        vcenter_password: "{{ vault_vcenter_password }}"
```

### Per-vCenter Inventory (Multi-Site Scale)

For large environments with multiple vCenters, create separate inventory
files per vCenter and run the workflow against each:

```yaml
# inventory/vcenter1.yml
all:
  children:
    windows_mgmt:
      hosts:
        win-mgmt-dc1:
          ansible_host: win-mgmt-dc1.example.com
          ansible_connection: winrm
          ansible_user: administrator
          ansible_password: "{{ vault_windows_password }}"

    esxi_hosts:
      children:
        esxi_batch_01:
          hosts:
            esxi-dc1-001: { ansible_host: 10.1.0.1, svsan_vsa: vsa-dc1-001 }
            esxi-dc1-002: { ansible_host: 10.1.0.2, svsan_vsa: vsa-dc1-001 }
            # ... up to 10 hosts per batch
        esxi_batch_02:
          hosts:
            esxi-dc1-011: { ansible_host: 10.1.0.11, svsan_vsa: vsa-dc1-002 }
            # ...
      vars:
        vcenter_hostname: vcenter-dc1.example.com
        vcenter_username: "{{ vault_vcenter_username }}"
        vcenter_password: "{{ vault_vcenter_password }}"
```

## Run the Workflow

```bash
# Basic usage (serial: 10 by default)
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/hosts.yml --ask-vault-pass

# Custom batch size
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/hosts.yml --ask-vault-pass \
  -e svsan_patching_batch_size=5

# With ESXi preflight checks (requires PowerCLI)
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/hosts.yml --ask-vault-pass \
  -e svsan_patching_check_esxi=true

# Per-vCenter (run separately for each vCenter)
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/vcenter1.yml --ask-vault-pass &
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/vcenter2.yml --ask-vault-pass &
```

## Playbook Structure

The `svsan_patching_workflow.yml` playbook runs with `serial` batching to patch hosts in controlled groups:

```yaml
# Simplified structure — see playbooks/svsan_patching_workflow.yml for full source
- hosts: esxi_hosts
  serial: "{{ svsan_patching_batch_size | default(10) }}"
  tasks:
    - include_role: xianganwu.stormagic.svsan_patching_preflight  # tags: svsan_preflight
    - vmware.vmware.esxi_maintenance_mode: ...                     # tags: svsan_maintenance
    - name: Apply patches (customize for your environment)         # tags: svsan_patch
    - name: Reboot ESXi host                                       # tags: svsan_reboot
    - vmware.vmware.esxi_maintenance_mode: state=absent            # tags: svsan_maintenance
    - include_role: xianganwu.stormagic.svsan_patching_postflight  # tags: svsan_postflight
```

Each step is tagged for selective execution. See [Recovery and Re-Run](#recovery-and-re-run) for resuming after failures.

## Role Reference

### svsan_patching_preflight

Validates SvSAN VSA health before patching.

**Input variables:**

| Variable | Required | Default | Description |
|---|---|---|---|
| `svsan_patching_preflight_vsa_hostname` | yes | — | VSA hostname/IP |
| `svsan_patching_preflight_vsa_username` | yes | — | VSA username |
| `svsan_patching_preflight_vsa_password` | yes | — | VSA password |
| `svsan_patching_preflight_windows_mgmt_host` | no | first `windows_mgmt` host | Delegation target |
| `svsan_patching_preflight_checks` | no | all 5 checks | Health checks to run |
| `svsan_patching_preflight_mirror_sync_threshold` | no | 100 | Min mirror sync % |
| `svsan_patching_preflight_pool_capacity_warn_pct` | no | 80 | Pool capacity warning |
| `svsan_patching_preflight_min_datastore_paths` | no | 2 | Min paths per target |
| `svsan_patching_preflight_check_esxi` | no | false | Enable vCenter checks |
| `svsan_patching_preflight_vcenter_hostname` | no | — | vCenter hostname |
| `svsan_patching_preflight_vcenter_username` | no | — | vCenter username |
| `svsan_patching_preflight_vcenter_password` | no | — | vCenter password |

**Output variables (set_fact):**

| Variable | Description |
|---|---|
| `svsan_patching_preflight_status` | Overall health: `pass`, `warn`, or `fail` |
| `svsan_patching_preflight_baseline` | Full health dict (for postflight comparison) |

### svsan_patching_postflight

Verifies SvSAN VSA health after patching with mirror resync wait.

**Input variables:**

| Variable | Required | Default | Description |
|---|---|---|---|
| `svsan_patching_postflight_vsa_hostname` | yes | — | VSA hostname/IP |
| `svsan_patching_postflight_vsa_username` | yes | — | VSA username |
| `svsan_patching_postflight_vsa_password` | yes | — | VSA password |
| `svsan_patching_postflight_windows_mgmt_host` | no | first `windows_mgmt` host | Delegation target |
| `svsan_patching_postflight_resync_wait` | no | true | Wait for mirror resync |
| `svsan_patching_postflight_resync_retries` | no | 30 | Max resync poll attempts |
| `svsan_patching_postflight_resync_delay` | no | 60 | Seconds between polls |
| `svsan_patching_postflight_preflight_baseline` | no | auto from preflight | Baseline for comparison |

**Output variables (set_fact):**

| Variable | Description |
|---|---|
| `svsan_patching_postflight_status` | Overall health: `pass`, `warn`, or `fail` |

## Recovery and Re-Run

If the workflow fails partway through, use tags to resume from the failed step:

| Failure Point | Recovery Command |
|---|---|
| Preflight failed | Fix the VSA issue, then re-run the full workflow |
| Patch/reboot failed | `--tags svsan_patch,svsan_reboot,svsan_postflight` |
| Postflight failed | `--tags svsan_postflight` (mirrors may still be syncing) |
| Mirror resync timeout | Increase `resync_retries` / `resync_delay` and re-run `--tags svsan_postflight` |

To run a single host instead of a batch:

```bash
ansible-playbook playbooks/svsan_patching_workflow.yml \
  -i inventory/hosts.yml --limit esxi1 --ask-vault-pass
```

## WinRM Concurrency (Scale Environments)

For environments with 40+ concurrent hosts (e.g. 10 hosts
per vCenter across 4 vCenters), configure the Windows management host:

```powershell
# On the Windows management host — increase shell limits
Set-Item WSMan:\localhost\Shell\MaxShellsPerUser -Value 100
Set-Item WSMan:\localhost\Shell\MaxConcurrentUsers -Value 50
Set-Item WSMan:\localhost\Plugin\microsoft.powershell\Quotas\MaxConcurrentUsers -Value 50
```

In `ansible.cfg`:
```ini
[defaults]
forks = 20

[connection]
pipelining = true
```

## Troubleshooting

### Postflight fails: mirrors not syncing

The postflight role polls mirror sync status with configurable retries.
If mirrors are slow to resync, increase the limits:

```yaml
svsan_patching_postflight_resync_retries: 60   # Poll for up to 60 minutes
svsan_patching_postflight_resync_delay: 120    # Check every 2 minutes
```

### WinRM timeout during health checks

```yaml
# In inventory — increase WinRM timeouts
windows_mgmt:
  hosts:
    win-mgmt:
      ansible_winrm_operation_timeout_sec: 120
      ansible_winrm_read_timeout_sec: 150
```
