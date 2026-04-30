# svkms_key_rotation

Rotate one or more encryption keys on a StorMagic SvKMS server. Gathers key info first, optionally fails on missing keys, then rotates.

## Role Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `svkms_key_rotation_host` | yes | — | SvKMS server hostname or IP address |
| `svkms_key_rotation_api_key` | yes | — | API key for SvKMS authentication |
| `svkms_key_rotation_keys` | yes | — | List of key names to rotate |
| `svkms_key_rotation_fail_on_missing` | no | `false` | Fail if a key name is not found |

## Example

```yaml
- name: Rotate encryption keys
  hosts: localhost
  roles:
    - role: xianganwu.stormagic.svkms_key_rotation
      svkms_key_rotation_host: svkms.example.com
      svkms_key_rotation_api_key: "{{ vault_kms_api_key }}"
      svkms_key_rotation_keys:
        - app-encryption-key
        - db-encryption-key
      svkms_key_rotation_fail_on_missing: true
```

## License

GPL-3.0-or-later
