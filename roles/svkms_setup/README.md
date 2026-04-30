# svkms_setup

Initial configuration for a StorMagic SvKMS server. Creates the initial admin user, configures default key access policies, and generates a root CA certificate.

## Requirements

- **Ansible**: >= 2.15
- **Collections**: `xianganwu.stormagic`
- **Platform**: Any control node with HTTPS access to the SvKMS server (port 1443). No agents or SSH access to the KMS appliance required.

### Connection Model

SvKMS modules are REST API-based — they connect directly to the KMS server via the `host` parameter over HTTPS. They do **not** use Ansible's SSH connection layer. You must set `ansible_connection: local` in inventory for the SvKMS host group, or use `delegate_to: localhost` on tasks. Also set `gather_facts: false` since facts cannot be gathered from the KMS appliance.

```yaml
# inventory group_vars/svkms_servers.yml
ansible_connection: local
```

## Role Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `svkms_setup_host` | yes | — | SvKMS server hostname or IP address |
| `svkms_setup_api_key` | yes | — | API key for SvKMS authentication |
| `svkms_setup_admin_username` | no | `admin` | Username for the initial admin account |
| `svkms_setup_default_policies` | no | see below | List of default key policies to create |
| `svkms_setup_ca_common_name` | no | `StorMagic SvKMS Root CA` | Common name for the root CA certificate |

### Default Policies

When `svkms_setup_default_policies` is not set, the role creates two policies:

- **default-rotation-policy** — allows encrypt, decrypt, and rotate operations for AES-256 keys
- **high-security-policy** — allows encrypt and decrypt operations for AES-256 keys

Each policy entry requires `name` and `rules` (a list of rule objects accepted by `svkms_policy`).

## Example

```yaml
- name: Set up SvKMS
  hosts: localhost
  roles:
    - role: xianganwu.stormagic.svkms_setup
      svkms_setup_host: svkms.example.com
      svkms_setup_api_key: "{{ vault_kms_api_key }}"
      svkms_setup_admin_username: admin
```

## License

GPL-3.0-or-later
