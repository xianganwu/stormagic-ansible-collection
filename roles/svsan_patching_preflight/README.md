# svsan_patching_preflight

Pre-patching health gate role for StorMagic SvSAN. Validates VSA health, target paths, and mirror synchronization before ESXi patching.

## Role Variables

- `svsan_vsa_hostname` (required) - VSA hostname or IP
- `svsan_vsa_username` (required) - VSA admin username
- `svsan_vsa_password` (required) - VSA admin password
- `svsan_preflight_checks` - List of checks to run (default: all)
- `svsan_mirror_sync_threshold` - Minimum mirror sync % (default: 100)
- `svsan_min_datastore_paths` - Minimum paths per target (default: 2)
- `svsan_windows_mgmt_host` - Windows management host for delegation

## License

GPL-3.0-or-later
