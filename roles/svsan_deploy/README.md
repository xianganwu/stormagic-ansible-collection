# svsan_deploy

Deploy a StorMagic SvSAN VSA pair on vSphere.

## Role Variables

- `svsan_deploy_vcenter` (required) - vCenter hostname
- `svsan_deploy_datacenter` (required) - vSphere datacenter name
- `svsan_deploy_cluster` (required) - vSphere cluster name
- `svsan_deploy_nodes` (required) - List of VSA node definitions
- `svsan_deploy_pool_name` - Storage pool name (default: pool1)
- `svsan_deploy_create_mirror` - Enable mirroring (default: true)

## License

GPL-3.0-or-later
