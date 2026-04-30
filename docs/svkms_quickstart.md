# SvKMS Quickstart Guide

This guide covers the essential steps to get started with the StorMagic SvKMS modules for Ansible.

## Prerequisites

- ansible-core >= 2.16.0
- Python >= 3.10 on the Ansible controller
- Network access to SvKMS server (REST API, typically port 1443)
- Valid SvKMS credentials (API key or username/password)

## 1. Installation

Install the collection from Automation Hub:

```bash
ansible-galaxy collection install xianganwu.stormagic
```

## 2. Authentication

SvKMS modules connect directly to the SvKMS REST API from the Ansible controller. No special connection plugin is needed.

Two authentication methods are supported:

### API Key (recommended for automation)

```yaml
- name: Health check with API key
  xianganwu.stormagic.svkms_health_check:
    host: svkms1.example.com
    api_key: "{{ vault_kms_api_key }}"
```

### Username / Password

```yaml
- name: Health check with username/password
  xianganwu.stormagic.svkms_health_check:
    host: svkms1.example.com
    username: admin
    password: "{{ vault_kms_password }}"
```

## 3. Store Credentials Securely

Use Ansible Vault for secrets:

```bash
ansible-vault create group_vars/all/vault.yml
```

**group_vars/all/vault.yml:**
```yaml
vault_kms_api_key: your_api_key_here
# -- or --
vault_kms_password: your_secure_password_here
```

Use variables throughout your playbooks:

```yaml
vars:
  svkms_host: svkms1.example.com
  svkms_api_key: "{{ vault_kms_api_key }}"
```

## 4. Test Connectivity

Check SvKMS server health to verify connectivity:

**playbooks/kms_health_check.yml:**
```yaml
---
- name: Check SvKMS server health
  hosts: localhost
  gather_facts: false
  vars:
    svkms_host: svkms1.example.com
    svkms_api_key: "{{ vault_kms_api_key }}"

  tasks:
    - name: Run health check
      xianganwu.stormagic.svkms_health_check:
        host: "{{ svkms_host }}"
        api_key: "{{ svkms_api_key }}"
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
ansible-playbook playbooks/kms_health_check.yml --ask-vault-pass
```

## 5. Create Your First Encryption Key

**playbooks/create_key.yml:**
```yaml
---
- name: Create encryption key
  hosts: localhost
  gather_facts: false
  vars:
    svkms_host: svkms1.example.com
    svkms_api_key: "{{ vault_kms_api_key }}"

  tasks:
    - name: Create AES-256 key
      xianganwu.stormagic.svkms_key:
        host: "{{ svkms_host }}"
        api_key: "{{ svkms_api_key }}"
        name: app-encryption-key
        algorithm: AES
        length: 256
        state: present
      register: key_result

    - name: Display key info
      ansible.builtin.debug:
        msg: "Key ID: {{ key_result.key.id }}, Algorithm: {{ key_result.key.algorithm }}"
```

Run the playbook:

```bash
ansible-playbook playbooks/create_key.yml --ask-vault-pass
```

## 6. Rotate an Encryption Key

Key rotation is a critical security practice. The SvKMS module makes it simple:

**playbooks/rotate_key.yml:**
```yaml
---
- name: Rotate encryption key
  hosts: localhost
  gather_facts: false
  vars:
    svkms_host: svkms1.example.com
    svkms_api_key: "{{ vault_kms_api_key }}"

  tasks:
    - name: Rotate key to new version
      xianganwu.stormagic.svkms_key:
        host: "{{ svkms_host }}"
        api_key: "{{ svkms_api_key }}"
        name: app-encryption-key
        state: rotated
      register: rotated_key

    - name: Display new version
      ansible.builtin.debug:
        msg: "Key rotated. New version: {{ rotated_key.key.version }}"
```

Run the playbook:

```bash
ansible-playbook playbooks/rotate_key.yml --ask-vault-pass
```

## 7. Gather Key Information

Retrieve information about existing keys:

**playbooks/list_keys.yml:**
```yaml
---
- name: List all keys
  hosts: localhost
  gather_facts: false
  vars:
    svkms_host: svkms1.example.com
    svkms_api_key: "{{ vault_kms_api_key }}"

  tasks:
    - name: Get key information
      xianganwu.stormagic.svkms_key_info:
        host: "{{ svkms_host }}"
        api_key: "{{ svkms_api_key }}"
      register: all_keys

    - name: Display all keys
      ansible.builtin.debug:
        msg: "{{ all_keys.key_list }}"

    - name: Get specific key info
      xianganwu.stormagic.svkms_key_info:
        host: "{{ svkms_host }}"
        api_key: "{{ svkms_api_key }}"
        name: app-encryption-key
      register: specific_key

    - name: Display specific key
      ansible.builtin.debug:
        msg: "Found {{ specific_key.key_list | length }} key(s) matching 'app-encryption-key'"
```

## Common Patterns

### Idempotent Key Creation

The `svkms_key` module is idempotent. Running the same playbook multiple times won't create duplicate keys:

```yaml
- name: Ensure key exists
  xianganwu.stormagic.svkms_key:
    host: "{{ svkms_host }}"
    api_key: "{{ svkms_api_key }}"
    name: my-key
    algorithm: AES
    length: 256
    state: present
```

This will create the key if it doesn't exist, or do nothing if it already exists.

### Self-Signed Certificates

For dev/test environments with self-signed certificates:

```yaml
- name: Connect with self-signed cert
  xianganwu.stormagic.svkms_health_check:
    host: "{{ svkms_host }}"
    api_key: "{{ svkms_api_key }}"
    validate_certs: false
```

For production with a custom CA:

```yaml
- name: Connect with custom CA
  xianganwu.stormagic.svkms_health_check:
    host: "{{ svkms_host }}"
    api_key: "{{ svkms_api_key }}"
    ca_path: /etc/ssl/certs/svkms-ca.pem
```

### Error Handling

Add error handling for production playbooks:

```yaml
- name: Create key with error handling
  xianganwu.stormagic.svkms_key:
    host: "{{ svkms_host }}"
    api_key: "{{ svkms_api_key }}"
    name: important-key
    algorithm: AES
    length: 256
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
1. Verify the SvKMS server is running: `curl -k https://svkms1.example.com:1443/v0/health`
2. Check firewall rules allow HTTPS traffic from the Ansible controller
3. Verify the `port` parameter matches your SvKMS configuration (default: 1443)

### SSL Certificate Errors

For self-signed certificates in dev/test environments, set `validate_certs: false` on the module task.

For production, provide the CA bundle path via `ca_path`.

### Authentication Failures

1. Verify credentials with curl:
   ```bash
   curl -k -H "X-API-Key: YOUR_KEY" https://svkms1.example.com:1443/v0/health
   ```
2. Check that the API key or username/password are correct
3. Ensure the user has appropriate permissions on SvKMS

## Additional Resources

- [SvKMS Module Documentation](../plugins/modules/svkms_key.py)
- [StorMagic SvKMS Documentation](https://stormagic.com/encryption-key-management/documentation/)
