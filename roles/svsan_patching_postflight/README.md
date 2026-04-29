# svsan_patching_postflight

Post-patching verification role for StorMagic SvSAN. Confirms VSA health after ESXi patching.

## Role Variables

- `svsan_vsa_hostname` (required) - VSA hostname or IP
- `svsan_vsa_username` (required) - VSA admin username
- `svsan_vsa_password` (required) - VSA admin password
- `svsan_postflight_checks` - List of checks to run (default: connectivity, targets, mirrors)
- `svsan_postflight_mirror_sync_threshold` - Minimum mirror sync % (default: 100)
- `svsan_windows_mgmt_host` - Windows management host for delegation

## License

GPL-3.0-or-later
