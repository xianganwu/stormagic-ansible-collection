# svsan_deploy

Deploy a StorMagic SvSAN VSA pair on vSphere.

## Role Variables

- `svsan_deploy_vcenter_hostname` (required) - vCenter hostname
- `svsan_deploy_vcenter_username` (required) - vCenter username
- `svsan_deploy_vcenter_password` (required) - vCenter password
- `svsan_deploy_vcenter_datacenter` (required) - vSphere datacenter name
- `svsan_deploy_vcenter_cluster` (required) - vSphere cluster name
- `svsan_deploy_nodes` (required) - List of VSA node definitions
- `svsan_deploy_datastore` (required) - Datastore for VSA VMs
- `svsan_deploy_admin_password` (required) - VSA admin password
- `svsan_deploy_pool_name` - Storage pool name (default: default-pool)
- `svsan_deploy_pool_size_gb` - Pool size in GB (default: 100)
- `svsan_deploy_vm_name_prefix` - VM name prefix (default: svsan-vsa)
- `svsan_deploy_template` - VM template name (default: StorMagic-VSA-Template)
- `svsan_deploy_network` - VM network (default: VM Network)
- `svsan_deploy_cpus` - VM CPU count (default: 2)
- `svsan_deploy_memory_mb` - VM memory in MB (default: 4096)

## License

GPL-3.0-or-later
