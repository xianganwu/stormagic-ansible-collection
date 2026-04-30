# svkms_key_rotation

Rotate one or more encryption keys on a StorMagic SvKMS server.

## Role Variables

- `svkms_key_rotation_keys` (required) - List of key names to rotate
- `svkms_key_rotation_fail_on_missing` - Fail if a key is not found (default: false)

## Example

```yaml
- name: Rotate encryption keys
  hosts: svkms_servers
  roles:
    - role: xianganwu.stormagic.svkms_key_rotation
      svkms_key_rotation_keys:
        - app-encryption-key
        - db-encryption-key
      svkms_key_rotation_fail_on_missing: true
```

## License

GPL-3.0-or-later
