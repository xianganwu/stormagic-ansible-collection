# ESXi Patching Workflow with SvSAN Health Gates

This guide demonstrates a complete ESXi patching workflow using the StorMagic SvSAN patching roles. This workflow is based on the Sheetz use case, where SvSAN VSA health gates ensure storage reliability before and after ESXi patching.

## Workflow Overview

1. **Pre-Patching Health Gate** — Validate SvSAN VSA health before patching ESXi hosts
2. **ESXi Patching** — Apply patches to ESXi hosts
3. **Post-Patching Verification** — Validate SvSAN VSA health after patching

The preflight and postflight roles ensure that:
- VSAs are healthy before patching begins
- Mirrors are in sync (out of sync < threshold)
- Storage pools have sufficient capacity
- VSA services are running
- Post-patch health matches pre-patch health

## Prerequisites

- ansible-core >= 2.16.0
- Windows management host with StorMagic PowerShell Toolkit
- WinRM connectivity to Windows management host
- Network access from Windows management host to SvSAN VSAs
- VMware ESXi infrastructure with SvSAN

## Inventory Setup

**inventory/hosts.yml:**
```yaml
all:
  children:
    windows_mgmt:
      hosts:
        win-mgmt:
          ansible_host: win-mgmt.example.com
          ansible_connection: winrm
          ansible_user: administrator
          ansible_password: "{{ vault_windows_password }}"
    
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
        ansible_password: "{{ vault_esxi_password }}"
        vcenter_hostname: vcenter.example.com
        vcenter_username: "{{ vault_vcenter_username }}"
        vcenter_password: "{{ vault_vcenter_password }}"
```

## Group Variables

Store common SvSAN settings in group_vars:

**inventory/group_vars/esxi_hosts/svsan.yml:**
```yaml
svsan_windows_mgmt_host: win-mgmt
svsan_vsa_username: admin
svsan_vsa_password: "{{ vault_vsa_password }}"

# Health check thresholds
svsan_mirror_sync_threshold: 100         # Fail if mirror out of sync > 100MB
svsan_pool_capacity_warn_pct: 80         # Warn at 80% pool capacity
svsan_pool_capacity_critical_pct: 90     # Fail at 90% pool capacity
```

**inventory/group_vars/all/vault.yml:**
```yaml
vault_windows_password: windows_admin_password
vault_esxi_password: esxi_root_password
vault_vsa_password: vsa_admin_password
vault_vcenter_username: administrator@vsphere.local
vault_vcenter_password: vcenter_password
```

Encrypt the vault file:
```bash
ansible-vault encrypt inventory/group_vars/all/vault.yml
```

## Complete Patching Playbook

**playbooks/esxi_patching_with_health_gates.yml:**
```yaml
---
- name: ESXi patching workflow with SvSAN health gates
  hosts: esxi_hosts
  serial: 1  # Patch one host at a time
  
  tasks:
    # ========================================
    # PHASE 1: Pre-Patching Health Gate
    # ========================================
    - name: Run pre-patching health checks
      ansible.builtin.include_role:
        name: xianganwu.stormagic.svsan_patching_preflight
      vars:
        svsan_vsa_hostname: "{{ svsan_vsa }}"
        svsan_vsa_username: "{{ svsan_vsa_username }}"
        svsan_vsa_password: "{{ svsan_vsa_password }}"
        svsan_windows_mgmt_host: "{{ svsan_windows_mgmt_host }}"
        svsan_mirror_sync_threshold: "{{ svsan_mirror_sync_threshold }}"
        svsan_pool_capacity_warn_pct: "{{ svsan_pool_capacity_warn_pct }}"
        svsan_pool_capacity_critical_pct: "{{ svsan_pool_capacity_critical_pct }}"
    
    - name: Display pre-patch health status
      ansible.builtin.debug:
        msg: "Pre-patch health: {{ preflight_health_status }}"
    
    - name: Fail if pre-patch health check failed
      ansible.builtin.fail:
        msg: "Pre-patch health check failed. Aborting patching for {{ inventory_hostname }}"
      when: preflight_health_status != 'healthy'
    
    # ========================================
    # PHASE 2: ESXi Patching
    # ========================================
    - name: Enter maintenance mode
      vmware.vmware.esxi_maintenance_mode:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: false
        esxi_host_name: "{{ inventory_hostname }}"
        enable_maintenance_mode: true
      delegate_to: localhost
    
    - name: Copy ESXi patch bundle
      ansible.builtin.copy:
        src: "{{ esxi_patch_bundle }}"
        dest: /tmp/esxi_patch.zip
    
    - name: Install ESXi patch
      ansible.builtin.command:
        cmd: esxcli software vib install -d /tmp/esxi_patch.zip
      register: patch_result
    
    - name: Display patch result
      ansible.builtin.debug:
        msg: "{{ patch_result.stdout }}"
    
    - name: Reboot ESXi host
      ansible.builtin.reboot:
        reboot_timeout: 600
    
    - name: Wait for ESXi to come back online
      ansible.builtin.wait_for_connection:
        timeout: 600
        delay: 60
    
    - name: Exit maintenance mode
      vmware.vmware.esxi_maintenance_mode:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: false
        esxi_host_name: "{{ inventory_hostname }}"
        enable_maintenance_mode: false
      delegate_to: localhost
    
    # ========================================
    # PHASE 3: Post-Patching Verification
    # ========================================
    - name: Run post-patching health checks
      ansible.builtin.include_role:
        name: xianganwu.stormagic.svsan_patching_postflight
      vars:
        svsan_vsa_hostname: "{{ svsan_vsa }}"
        svsan_vsa_username: "{{ svsan_vsa_username }}"
        svsan_vsa_password: "{{ svsan_vsa_password }}"
        svsan_windows_mgmt_host: "{{ svsan_windows_mgmt_host }}"
        svsan_mirror_sync_threshold: "{{ svsan_mirror_sync_threshold }}"
        svsan_pool_capacity_warn_pct: "{{ svsan_pool_capacity_warn_pct }}"
        svsan_pool_capacity_critical_pct: "{{ svsan_pool_capacity_critical_pct }}"
        svsan_preflight_health: "{{ preflight_health_result }}"
    
    - name: Display post-patch health status
      ansible.builtin.debug:
        msg: "Post-patch health: {{ postflight_health_status }}"
    
    - name: Fail if post-patch health check failed
      ansible.builtin.fail:
        msg: "Post-patch health check failed for {{ inventory_hostname }}"
      when: postflight_health_status != 'healthy'
    
    - name: Patching complete
      ansible.builtin.debug:
        msg: "Successfully patched {{ inventory_hostname }}"
```

## Run the Playbook

```bash
ansible-playbook -i inventory/hosts.yml playbooks/esxi_patching_with_health_gates.yml --ask-vault-pass -e esxi_patch_bundle=/path/to/patch.zip
```

## What the Roles Do

### svsan_patching_preflight Role

The preflight role performs these checks:

1. **VSA Health Check**
   - Verifies VSA is reachable
   - Checks VSA service status
   - Validates overall health

2. **Mirror Sync Check**
   - Retrieves mirror status
   - Ensures mirrors are in sync (out_of_sync_mb < threshold)
   - Fails if any mirror is excessively out of sync

3. **Storage Pool Capacity**
   - Checks pool capacity
   - Warns if capacity > warn_pct
   - Fails if capacity > critical_pct

4. **Baseline Capture**
   - Captures pre-patch health metrics
   - Stores results in `preflight_health_result` variable
   - Used for comparison in postflight

**Output variables:**
- `preflight_health_status` — `healthy` or `unhealthy`
- `preflight_health_result` — Full health check result (for postflight comparison)

### svsan_patching_postflight Role

The postflight role performs these checks:

1. **VSA Health Check**
   - Verifies VSA is still healthy after patching
   - Checks service status

2. **Mirror Sync Check**
   - Ensures mirrors are in sync
   - Fails if sync degraded after patching

3. **Storage Pool Capacity**
   - Checks pool capacity hasn't changed unexpectedly

4. **Comparison with Preflight**
   - Compares postflight health to preflight baseline
   - Ensures no degradation occurred during patching

**Input variables:**
- `svsan_preflight_health` — Output from preflight role (used for comparison)

**Output variables:**
- `postflight_health_status` — `healthy` or `unhealthy`
- `postflight_health_result` — Full health check result

## Customizing Health Thresholds

Adjust thresholds in group_vars or as extra vars:

```yaml
# Be strict about mirror sync
svsan_mirror_sync_threshold: 50  # Fail if > 50MB out of sync

# Be conservative about capacity
svsan_pool_capacity_warn_pct: 70
svsan_pool_capacity_critical_pct: 85
```

Or pass as extra vars:

```bash
ansible-playbook playbooks/esxi_patching_with_health_gates.yml \
  --ask-vault-pass \
  -e esxi_patch_bundle=/path/to/patch.zip \
  -e svsan_mirror_sync_threshold=50 \
  -e svsan_pool_capacity_critical_pct=85
```

## Advanced Patterns

### Patch Multiple Hosts in Parallel (with Safeguards)

```yaml
- name: ESXi patching workflow
  hosts: esxi_hosts
  serial: 2  # Patch 2 hosts at a time
  max_fail_percentage: 0  # Abort if any host fails
```

### Retry Logic for Transient Failures

```yaml
- name: Run pre-patching health checks
  ansible.builtin.include_role:
    name: xianganwu.stormagic.svsan_patching_preflight
  vars:
    svsan_vsa_hostname: "{{ svsan_vsa }}"
    svsan_vsa_username: "{{ svsan_vsa_username }}"
    svsan_vsa_password: "{{ svsan_vsa_password }}"
    svsan_windows_mgmt_host: "{{ svsan_windows_mgmt_host }}"
  retries: 3
  delay: 30
  until: preflight_health_status == 'healthy'
```

### Notification on Failure

```yaml
- name: Send notification if patching fails
  ansible.builtin.mail:
    host: smtp.example.com
    to: ops@example.com
    subject: "ESXi patching failed for {{ inventory_hostname }}"
    body: "Health check failed. Status: {{ preflight_health_status }}"
  when: preflight_health_status != 'healthy'
  delegate_to: localhost
```

### Generate Pre/Post Health Report

```yaml
- name: Generate health report
  ansible.builtin.copy:
    content: |
      ESXi Patching Report for {{ inventory_hostname }}
      
      Pre-Patch Health:
      {{ preflight_health_result | to_nice_yaml }}
      
      Post-Patch Health:
      {{ postflight_health_result | to_nice_yaml }}
    dest: "/tmp/patching_report_{{ inventory_hostname }}_{{ ansible_date_time.iso8601_basic_short }}.txt"
  delegate_to: localhost
```

## Troubleshooting

### Preflight Fails: Mirrors Out of Sync

If preflight fails due to mirror sync issues:

1. Check mirror status manually:
   ```yaml
   - name: Check mirror status
     xianganwu.stormagic.svsan_mirror_info:
       vsa_hostname: vsa1.example.com
       vsa_username: admin
       vsa_password: "{{ vault_vsa_password }}"
     delegate_to: win-mgmt
   ```

2. Wait for mirrors to sync before patching:
   ```yaml
   - name: Wait for mirrors to sync
     xianganwu.stormagic.svsan_mirror_info:
       vsa_hostname: "{{ svsan_vsa }}"
       vsa_username: "{{ svsan_vsa_username }}"
       vsa_password: "{{ svsan_vsa_password }}"
     delegate_to: "{{ svsan_windows_mgmt_host }}"
     register: mirror_status
     until: mirror_status.mirrors | selectattr('out_of_sync_mb', 'gt', svsan_mirror_sync_threshold) | list | length == 0
     retries: 10
     delay: 60
   ```

### Postflight Fails: Health Degraded

If postflight detects health degradation:

1. Review the health comparison output
2. Check VSA logs on the Windows management host
3. Manually verify VSA status with PowerShell:
   ```powershell
   Import-Module "C:\Program Files\StorMagic\SmCmdlet.dll"
   Get-SvSanHealth -VSA vsa1.example.com -Username admin -Password (Read-Host -AsSecureString)
   ```

### WinRM Timeout During Health Checks

If health checks timeout:

1. Increase WinRM timeout:
   ```yaml
   windows_mgmt:
     hosts:
       win-mgmt:
         ansible_winrm_operation_timeout_sec: 120
         ansible_winrm_read_timeout_sec: 150
   ```

2. Or increase async timeout in the role:
   ```yaml
   - name: Run preflight (with longer timeout)
     ansible.builtin.include_role:
       name: xianganwu.stormagic.svsan_patching_preflight
     vars:
       svsan_health_check_timeout: 300
   ```

## Best Practices

1. **Always run preflight before patching** — Never skip health checks
2. **Patch one host at a time** — Use `serial: 1` for safety
3. **Use Ansible Vault** — Never store passwords in plain text
4. **Monitor mirror sync** — Ensure mirrors are in sync before starting
5. **Capture health baselines** — Save pre-patch health for comparison
6. **Test in dev first** — Validate the workflow in a dev environment
7. **Document thresholds** — Make thresholds clear in group_vars
8. **Set up notifications** — Alert on failures

## Additional Resources

- [SvSAN Preflight Role](../roles/svsan_patching_preflight/README.md)
- [SvSAN Postflight Role](../roles/svsan_patching_postflight/README.md)
- [SvSAN Health Check Module](../plugins/modules/svsan_health_check.py)
- [StorMagic SvSAN Patching Best Practices](https://stormagic.com/svsan/documentation/)
