# svkms_setup

Initial configuration for a StorMagic SvKMS server. Creates the initial admin user, configures default key access policies, and generates a root CA certificate.

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
