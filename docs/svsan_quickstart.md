# SvSAN Quickstart Guide

This guide covers the essential steps to get started with the StorMagic SvSAN modules for Ansible.

## Prerequisites

- ansible-core >= 2.16.0
- Python >= 3.10 on the Ansible controller
- A **Windows management host** with:
  - PowerShell 5.1 or later
  - StorMagic PowerShell Toolkit (SmCmdlet.dll) installed
  - Network access to SvSAN VSAs
- WinRM or PSRP connectivity configured between the Ansible controller and the Windows management host

## Architecture Overview

Unlike SvKMS, which connects directly to the REST API, SvSAN modules execute PowerShell commands on a Windows management host. This is because StorMagic SvSAN management requires the StorMagic PowerShell Toolkit, which only runs on Windows.

**Workflow:**
1. Ansible controller connects to Windows management host via WinRM/PSRP
2. Windows host executes PowerShell commands using the StorMagic Toolkit
3. StorMagic Toolkit communicates with SvSAN VSAs
4. Results are returned to the Ansible controller

## 1. Installation

Install the collection from Automation Hub:

```bash
ansible-galaxy collection install xianganwu.stormagic
```

## 2. Windows Management Host Setup

### Install StorMagic PowerShell Toolkit

On your Windows management host:

1. Install the StorMagic SvSAN software (which includes the PowerShell Toolkit)
2. Verify the toolkit is available:

```powershell
Import-Module "C:\Program Files\StorMagic\SmCmdlet.dll"
Get-Command -Module SmCmdlet
```

You should see StorMagic cmdlets like `Get-SvSanHealth`, `Get-SvSanTarget`, etc.

### Configure WinRM

Enable WinRM on the Windows management host:

```powershell
# Run as Administrator
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true  # Only for dev/test
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
```

For production, configure HTTPS transport with certificates:

```powershell
# Create self-signed cert (or use your CA cert)
$cert = New-SelfSignedCertificate -DnsName "win-mgmt.example.com" -CertStoreLocation "Cert:\LocalMachine\My"

# Enable HTTPS listener
New-Item -Path WSMan:\LocalHost\Listener -Transport HTTPS -Address * -CertificateThumbPrint $cert.Thumbprint -Force

# Allow HTTPS
New-NetFirewallRule -DisplayName "WinRM HTTPS" -Direction Inbound -LocalPort 5986 -Protocol TCP -Action Allow
```

## 3. Inventory Setup

Configure your inventory with the Windows management host and SvSAN VSAs:

**inventory/hosts.yml:**
```yaml
all:
  children:
    windows_mgmt:
      hosts:
        win-mgmt:
          ansible_host: win-mgmt.example.com
          ansible_connection: winrm
          ansible_winrm_transport: basic
          ansible_winrm_server_cert_validation: ignore  # Only for dev/test
          ansible_user: administrator
          ansible_password: "{{ vault_windows_password }}"
    
    svsan_vsas:
      hosts:
        vsa1:
          svsan_vsa_hostname: vsa1.example.com
          svsan_vsa_username: admin
          svsan_vsa_password: "{{ vault_vsa_password }}"
        vsa2:
          svsan_vsa_hostname: vsa2.example.com
          svsan_vsa_username: admin
          svsan_vsa_password: "{{ vault_vsa_password }}"
      vars:
        # All SvSAN operations delegate to this Windows host
        svsan_windows_mgmt_host: win-mgmt
```

**Important:** SvSAN modules require `delegate_to: "{{ svsan_windows_mgmt_host }}"` to run on the Windows management host.

## 4. Store Credentials Securely

Use Ansible Vault for passwords:

```bash
ansible-vault create inventory/group_vars/all/vault.yml
```

**inventory/group_vars/all/vault.yml:**
```yaml
vault_windows_password: your_windows_admin_password
vault_vsa_password: your_vsa_admin_password
```

## 5. Test Connectivity

Test WinRM connectivity to the Windows management host:

```bash
ansible -i inventory/hosts.yml win-mgmt -m win_ping --ask-vault-pass
```

Expected output:
```
win-mgmt | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## 6. Run Your First Health Check

Check SvSAN VSA health:

**playbooks/svsan_health_check.yml:**
```yaml
---
- name: Check SvSAN VSA health
  hosts: svsan_vsas
  gather_facts: false
  
  tasks:
    - name: Run health check on VSA
      xianganwu.stormagic.svsan_health_check:
        vsa_hostname: "{{ svsan_vsa_hostname }}"
        vsa_username: "{{ svsan_vsa_username }}"
        vsa_password: "{{ svsan_vsa_password }}"
      delegate_to: "{{ svsan_windows_mgmt_host }}"
      register: health_result
    
    - name: Display health status
      ansible.builtin.debug:
        msg: "VSA {{ svsan_vsa_hostname }}: {{ health_result.health.status }}"
      delegate_to: localhost
    
    - name: Assert VSA is healthy
      ansible.builtin.assert:
        that:
          - health_result.health.status == 'healthy'
        fail_msg: "VSA {{ svsan_vsa_hostname }} is not healthy"
      delegate_to: localhost
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/svsan_health_check.yml --ask-vault-pass
```

## 7. List Storage Targets

Retrieve information about iSCSI targets:

**playbooks/list_targets.yml:**
```yaml
---
- name: List all storage targets
  hosts: svsan_vsas
  gather_facts: false
  
  tasks:
    - name: Get target information
      xianganwu.stormagic.svsan_target_info:
        vsa_hostname: "{{ svsan_vsa_hostname }}"
        vsa_username: "{{ svsan_vsa_username }}"
        vsa_password: "{{ svsan_vsa_password }}"
      delegate_to: "{{ svsan_windows_mgmt_host }}"
      register: targets
    
    - name: Display targets
      ansible.builtin.debug:
        msg: "Targets on {{ svsan_vsa_hostname }}: {{ targets.targets }}"
      delegate_to: localhost
```

## 8. Create a Storage Target

Create a new iSCSI target:

**playbooks/create_target.yml:**
```yaml
---
- name: Create storage target
  hosts: vsa1
  gather_facts: false
  
  tasks:
    - name: Create 500GB target in pool1
      xianganwu.stormagic.svsan_target:
        vsa_hostname: "{{ svsan_vsa_hostname }}"
        vsa_username: "{{ svsan_vsa_username }}"
        vsa_password: "{{ svsan_vsa_password }}"
        name: datastore1
        size_gb: 500
        pool: pool1
        state: present
      delegate_to: "{{ svsan_windows_mgmt_host }}"
      register: target_result
    
    - name: Display target info
      ansible.builtin.debug:
        msg: "Target {{ target_result.target.name }} created with size {{ target_result.target.size_gb }}GB"
      delegate_to: localhost
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/create_target.yml --ask-vault-pass
```

## 9. Check Mirror Status

Check the status of mirrored storage:

**playbooks/check_mirrors.yml:**
```yaml
---
- name: Check mirror status
  hosts: svsan_vsas
  gather_facts: false
  
  tasks:
    - name: Get mirror information
      xianganwu.stormagic.svsan_mirror_info:
        vsa_hostname: "{{ svsan_vsa_hostname }}"
        vsa_username: "{{ svsan_vsa_username }}"
        vsa_password: "{{ svsan_vsa_password }}"
      delegate_to: "{{ svsan_windows_mgmt_host }}"
      register: mirrors
    
    - name: Display mirror status
      ansible.builtin.debug:
        msg: "Mirror {{ item.name }}: sync_pct={{ item.sync_pct }}%"
      loop: "{{ mirrors.mirrors }}"
      delegate_to: localhost
    
    - name: Assert mirrors are in sync
      ansible.builtin.assert:
        that:
          - item.sync_pct == 100
        fail_msg: "Mirror {{ item.name }} is only {{ item.sync_pct }}% synced"
      loop: "{{ mirrors.mirrors }}"
      delegate_to: localhost
```

## Common Patterns

### Using delegate_to Correctly

**All SvSAN modules MUST use `delegate_to`** to run on the Windows management host:

```yaml
- name: Any SvSAN operation
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: vsa1.example.com
    vsa_username: admin
    vsa_password: secret
  delegate_to: "{{ svsan_windows_mgmt_host }}"
```

### Group Variables for Common Settings

Store common variables in group_vars:

**inventory/group_vars/svsan_vsas/svsan.yml:**
```yaml
svsan_windows_mgmt_host: win-mgmt
svsan_vsa_username: admin
svsan_vsa_password: "{{ vault_vsa_password }}"
```

Then simplify your tasks:

```yaml
- name: Health check (simplified)
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
  delegate_to: "{{ svsan_windows_mgmt_host }}"
```

### Custom Health Check Thresholds

Configure health check thresholds:

```yaml
- name: Check VSA health with custom thresholds
  xianganwu.stormagic.svsan_health_check:
    vsa_hostname: "{{ svsan_vsa_hostname }}"
    vsa_username: "{{ svsan_vsa_username }}"
    vsa_password: "{{ svsan_vsa_password }}"
    mirror_sync_threshold: 50        # Warn if sync percentage below 50%
    pool_capacity_warn_pct: 75       # Warn at 75% capacity
  delegate_to: "{{ svsan_windows_mgmt_host }}"
```

## Next Steps

- Review the **svsan_patching_preflight** and **svsan_patching_postflight** roles for ESXi patching workflows
- Explore the **svsan_pool** module for storage pool management
- Use **svsan_vsa** to deploy new VSA instances
- See the **patching_workflow.md** guide for a complete Sheetz-style patching workflow

## Troubleshooting

### WinRM Connection Failures

If you see "WinRM connection failed" errors:

1. Verify WinRM is enabled on the Windows host:
   ```powershell
   winrm quickconfig
   ```

2. Test connectivity from the Ansible controller:
   ```bash
   ansible win-mgmt -m win_ping -i inventory/hosts.yml
   ```

3. Check firewall rules allow WinRM (ports 5985/HTTP, 5986/HTTPS)

### PowerShell Toolkit Not Found

If you see "SmCmdlet.dll not found" errors:

1. Verify the toolkit is installed on the Windows management host:
   ```powershell
   Test-Path "C:\Program Files\StorMagic\SmCmdlet.dll"
   ```

2. Check the module search path in the module code (defaults to `C:\Program Files\StorMagic\SmCmdlet.dll`)

3. Ensure the StorMagic SvSAN software is fully installed

### delegate_to Errors

If tasks fail with "module not found" or similar errors, ensure:

1. You're using `delegate_to: "{{ svsan_windows_mgmt_host }}"`
2. The Windows management host is defined in your inventory
3. The Windows management host has WinRM enabled

### VSA Connection Failures

If the Windows host can't reach the VSA:

1. Verify network connectivity from Windows host:
   ```powershell
   Test-NetConnection vsa1.example.com -Port 443
   ```

2. Check VSA credentials are correct
3. Ensure the VSA is powered on and accessible

## Additional Resources

- [SvSAN Module Documentation](../plugins/modules/svsan_health_check.py)
- [StorMagic SvSAN Documentation](https://stormagic.com/svsan/documentation/)
- [StorMagic PowerShell Toolkit Reference](https://stormagic.com/doc/svsan/6-2/en/Content/PT-introduction.htm)
- [Ansible WinRM Guide](https://docs.ansible.com/ansible/latest/user_guide/windows_winrm.html)
