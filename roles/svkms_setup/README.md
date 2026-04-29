# svkms_setup

Initial configuration for a StorMagic SvKMS server.

## Role Variables

- `svkms_setup_admin_username` - Admin username (default: admin)
- `svkms_setup_admin_password` (required) - Admin password
- `svkms_setup_admin_email` - Admin email (default: admin@example.com)
- `svkms_setup_default_policies` - List of default policy definitions
- `svkms_setup_ca_common_name` - CA certificate common name (default: StorMagic SvKMS Root CA)
- `svkms_setup_ca_organization` - CA organization (default: StorMagic Ltd)
- `svkms_setup_ca_validity_days` - CA validity in days (default: 3650)

## License

GPL-3.0-or-later
