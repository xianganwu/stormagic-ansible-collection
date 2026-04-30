# svsan_deploy

Deploy a StorMagic SvSAN VSA pair on vSphere. Deploys VMs from a template, configures guest customization for static IP addressing, and creates an initial storage pool on the primary node.

## Requirements

- **Ansible**: >= 2.15
- **Collections**: `xianganwu.stormagic`, `vmware.vmware >= 2.0.0`
- **Platform**: Requires a Windows management host with PowerShell for SvSAN module delegation. The control node connects to vCenter for VM operations and to the Windows host for SvSAN PowerShell cmdlets.

### Connection Model

This role runs on `localhost` and delegates SvSAN module tasks to a Windows management host. Set the target Windows host via `delegate_to` or the `svsan_deploy_nodes` variable. vCenter API calls are made from the control node.

## Role Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `svsan_deploy_vcenter_hostname` | yes | — | vCenter hostname or IP address |
| `svsan_deploy_vcenter_username` | yes | — | vCenter username |
| `svsan_deploy_vcenter_password` | yes | — | vCenter password |
| `svsan_deploy_validate_certs` | no | `true` | Validate SSL certificates for vCenter |
| `svsan_deploy_vcenter_datacenter` | yes | — | vSphere datacenter name |
| `svsan_deploy_vcenter_cluster` | yes | — | vSphere cluster name |
| `svsan_deploy_nodes` | yes | — | List of VSA node definitions (hostname, ip_address, node_id) |
| `svsan_deploy_datastore` | yes | — | Datastore for VSA VMs |
| `svsan_deploy_admin_password` | yes | — | Initial admin password for the VSA appliances |
| `svsan_deploy_pool_name` | no | `default-pool` | Storage pool name |
| `svsan_deploy_vm_name_prefix` | no | `svsan-vsa` | VM name prefix |
| `svsan_deploy_template` | no | `StorMagic-VSA-Template` | vSphere template name |
| `svsan_deploy_template_folder` | no | `""` | vSphere folder containing the template |
| `svsan_deploy_network` | no | `VM Network` | vSphere network for VM adapter |
| `svsan_deploy_adapter_type` | no | `vmxnet3` | Network adapter type |
| `svsan_deploy_cpus` | no | `2` | vCPUs per VSA VM |
| `svsan_deploy_memory_mb` | no | `4096` | Memory in MB per VSA VM |
| `svsan_deploy_domain` | no | `local` | DNS domain for guest customization |
| `svsan_deploy_netmask` | no | `255.255.255.0` | Subnet mask for guest customization |
| `svsan_deploy_gateway` | no | `""` | Default gateway for guest customization |
| `svsan_deploy_dns_servers` | no | `[]` | List of DNS server IP addresses |
| `svsan_deploy_vsa_username` | no | `admin` | Username for VSA appliance authentication |

## Example

```yaml
- name: Deploy SvSAN cluster
  hosts: localhost
  roles:
    - role: xianganwu.stormagic.svsan_deploy
      svsan_deploy_vcenter_hostname: vcenter.example.com
      svsan_deploy_vcenter_username: "administrator@vsphere.local"
      svsan_deploy_vcenter_password: "{{ vault_vcenter_password }}"
      svsan_deploy_vcenter_datacenter: DC1
      svsan_deploy_vcenter_cluster: Cluster1
      svsan_deploy_datastore: shared-storage
      svsan_deploy_admin_password: "{{ vault_vsa_password }}"
      svsan_deploy_nodes:
        - hostname: svsan-vsa-01
          ip_address: 192.168.1.10
          node_id: 1
        - hostname: svsan-vsa-02
          ip_address: 192.168.1.11
          node_id: 2
```

## License

GPL-3.0-or-later
