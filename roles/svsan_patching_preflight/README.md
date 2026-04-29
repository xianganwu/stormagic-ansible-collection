# svsan_patching_preflight

Pre-patching health gate role for StorMagic SvSAN. Validates VSA health, target paths, and mirror synchronization before ESXi patching.

## Role Variables

- `svsan_patching_preflight_vsa_hostname` (required) - VSA hostname or IP
- `svsan_patching_preflight_vsa_username` (required) - VSA admin username
- `svsan_patching_preflight_vsa_password` (required) - VSA admin password
- `svsan_patching_preflight_checks` - List of checks to run (default: all)
- `svsan_patching_preflight_mirror_sync_threshold` - Minimum mirror sync % (default: 100)
- `svsan_patching_preflight_min_datastore_paths` - Minimum paths per target (default: 2)
- `svsan_patching_preflight_pool_capacity_warn_pct` - Pool capacity warning % (default: 80)
- `svsan_patching_preflight_windows_mgmt_host` - Windows management host for delegation

## License

GPL-3.0-or-later
