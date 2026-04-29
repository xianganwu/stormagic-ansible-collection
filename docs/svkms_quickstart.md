# SvKMS Quickstart Guide

This guide covers the essential steps to get started with the StorMagic SvKMS modules for Ansible.

## Prerequisites

- ansible-core >= 2.16.0
- Python >= 3.10 on the Ansible controller
- Network access to SvKMS server (REST API, typically port 443)
- Valid SvKMS credentials (username/password or API token)

## 1. Installation

Install the collection from Automation Hub:

```bash
ansible-galaxy collection install stormagic.stormagic
```

## 2. Inventory Setup

SvKMS uses the `httpapi` connection plugin. Configure your inventory with the SvKMS server:

**inventory/hosts.yml:**
```yaml
all:
  children:
    kms_servers:
      hosts:
        svkms1:
          ansible_host: svkms1.example.com
          ansible_network_os: stormagic.stormagic.svkms
          ansible_connection: httpapi
          ansible_httpapi_port: 443
          ansible_httpapi_use_ssl: true
          ansible_httpapi_validate_certs: true
          ansible_user: admin
          ansible_password: "{{ vault_kms_password }}"
```

**Important parameters:**
- `ansible_network_os` — Must be set to `stormagic.stormagic.svkms`
- `ansible_connection` — Must be `httpapi`
- `ansible_httpapi_use_ssl` — Enable SSL (recommended)
- `ansible_httpapi_validate_certs` — Validate SSL certificates (set to `false` for self-signed certs in dev environments)

## 3. Store Credentials Securely

Use Ansible Vault for passwords:

```bash
ansible-vault create inventory/group_vars/kms_servers/vault.yml
```

**inventory/group_vars/kms_servers/vault.yml:**
```yaml
vault_kms_password: your_secure_password_here
```

## 4. Test Connectivity

Check SvKMS server health to verify connectivity:

**playbooks/kms_health_check.yml:**
```yaml
---
- name: Check SvKMS server health
  hosts: kms_servers
  gather_facts: false
  
  tasks:
    - name: Run health check
      stormagic.stormagic.svkms_health_check:
      register: health_result
    
    - name: Display health status
      ansible.builtin.debug:
        msg: "SvKMS status: {{ health_result.health.status }}"
    
    - name: Assert healthy
      ansible.builtin.assert:
        that:
          - health_result.health.status == 'healthy'
        fail_msg: "SvKMS is not healthy"
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/kms_health_check.yml --ask-vault-pass
```

## 5. Create Your First Encryption Key

**playbooks/create_key.yml:**
```yaml
---
- name: Create encryption key
  hosts: kms_servers
  gather_facts: false
  
  tasks:
    - name: Create AES-256 key
      stormagic.stormagic.svkms_key:
        name: app-encryption-key
        algorithm: AES256
        description: "Application encryption key"
        state: present
      register: key_result
    
    - name: Display key info
      ansible.builtin.debug:
        msg: "Key ID: {{ key_result.key.id }}, Status: {{ key_result.key.status }}"
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/create_key.yml --ask-vault-pass
```

## 6. Rotate an Encryption Key

Key rotation is a critical security practice. The SvKMS module makes it simple:

**playbooks/rotate_key.yml:**
```yaml
---
- name: Rotate encryption key
  hosts: kms_servers
  gather_facts: false
  
  tasks:
    - name: Rotate key to new version
      stormagic.stormagic.svkms_key:
        name: app-encryption-key
        state: rotated
      register: rotated_key
    
    - name: Display new version
      ansible.builtin.debug:
        msg: "Key rotated. New version: {{ rotated_key.key.version }}"
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/rotate_key.yml --ask-vault-pass
```

## 7. Gather Key Information

Retrieve information about existing keys:

**playbooks/list_keys.yml:**
```yaml
---
- name: List all keys
  hosts: kms_servers
  gather_facts: false
  
  tasks:
    - name: Get key information
      stormagic.stormagic.svkms_key_info:
      register: all_keys
    
    - name: Display all keys
      ansible.builtin.debug:
        msg: "{{ all_keys.keys }}"
    
    - name: Get specific key info
      stormagic.stormagic.svkms_key_info:
        name: app-encryption-key
      register: specific_key
    
    - name: Display specific key
      ansible.builtin.debug:
        msg: "Key: {{ specific_key.key.name }}, Algorithm: {{ specific_key.key.algorithm }}, Version: {{ specific_key.key.version }}"
```

## Common Patterns

### Using API Tokens Instead of Passwords

For production environments, use API tokens:

```yaml
svkms1:
  ansible_host: svkms1.example.com
  ansible_network_os: stormagic.stormagic.svkms
  ansible_connection: httpapi
  ansible_httpapi_use_ssl: true
  ansible_httpapi_validate_certs: true
  ansible_user: api_token
  ansible_password: "{{ vault_kms_api_token }}"
```

### Idempotent Key Creation

The `svkms_key` module is idempotent. Running the same playbook multiple times won't create duplicate keys:

```yaml
- name: Ensure key exists
  stormagic.stormagic.svkms_key:
    name: my-key
    algorithm: AES256
    state: present
```

This will create the key if it doesn't exist, or do nothing if it already exists.

### Error Handling

Add error handling for production playbooks:

```yaml
- name: Create key with error handling
  stormagic.stormagic.svkms_key:
    name: important-key
    algorithm: AES256
    state: present
  register: key_result
  ignore_errors: true

- name: Handle failure
  ansible.builtin.fail:
    msg: "Failed to create key: {{ key_result.msg }}"
  when: key_result.failed
```

## Next Steps

- Explore the **svkms_policy** module to manage key access policies
- Use **svkms_user** to manage KMS users
- Set up **svkms_backup** for disaster recovery
- Review the **svkms_certificate** module for certificate management

## Troubleshooting

### Connection Refused

If you see "Connection refused" errors:
1. Verify the SvKMS server is running: `curl -k https://svkms1.example.com/api/health`
2. Check firewall rules allow HTTPS traffic from the Ansible controller
3. Verify `ansible_httpapi_port` matches your SvKMS configuration

### SSL Certificate Errors

For self-signed certificates in dev/test environments:
```yaml
ansible_httpapi_validate_certs: false
```

For production, install the CA certificate on the Ansible controller.

### Authentication Failures

1. Verify credentials with curl:
   ```bash
   curl -k -u admin:password https://svkms1.example.com/api/keys
   ```
2. Check that `ansible_user` and `ansible_password` are correct
3. Ensure the user has appropriate permissions on SvKMS

## Additional Resources

- [SvKMS Module Documentation](../plugins/modules/svkms_key.py)
- [StorMagic SvKMS Documentation](https://stormagic.com/encryption-key-management/documentation/)
- [Ansible httpapi Connection Plugin](https://docs.ansible.com/ansible/latest/collections/ansible/netcommon/httpapi_connection.html)
