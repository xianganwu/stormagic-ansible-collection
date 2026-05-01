# StorMagic Collection Examples

Ready-to-use project scaffolding for the `xianganwu.stormagic` Ansible collection.

## Quick Start

Copy the example files into your project:

```bash
# Install the collection
ansible-galaxy collection install xianganwu.stormagic

# Copy example project structure
COLLECTION_PATH=$(ansible-galaxy collection list xianganwu.stormagic --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.keys())[0])")
cp -r "${COLLECTION_PATH}/xianganwu/stormagic/examples/" ~/my-stormagic-project/
cd ~/my-stormagic-project/

# Edit inventory with your hosts
vi inventory/hosts.yml

# Edit the vault template with your real credentials, then encrypt it
vi inventory/group_vars/all/vault.yml
ansible-vault encrypt inventory/group_vars/all/vault.yml

# Test connectivity
ansible -i inventory/hosts.yml localhost -m ping
ansible -i inventory/hosts.yml win-mgmt -m win_ping --ask-vault-pass
```

## Directory Structure

```
examples/
  ansible.cfg                              # Recommended Ansible configuration
  inventory/
    hosts.yml                              # Inventory template (all host groups)
    group_vars/
      all/
        vault.yml                          # Vault variable template (credentials)
      svkms_servers/
        svkms.yml                          # SvKMS connection defaults
      svsan_vsas/
        svsan.yml                          # SvSAN connection defaults
```

## Included Playbooks

The collection ships sample playbooks in the `playbooks/` directory:

| Playbook | Description |
|----------|-------------|
| `svkms_full_setup.yml` | Day-1: Health check, create users, policies, keys |
| `svkms_key_rotation.yml` | Rotate encryption keys with health verification |
| `svkms_backup.yml` | Back up SvKMS server |
| `svsan_ha_setup.yml` | Deploy a 2-node SvSAN HA cluster |
| `svsan_add_storage.yml` | Add targets with mirrors to an existing cluster |
| `svsan_capacity_report.yml` | Gather pool/target/mirror status from all VSAs |
| `svsan_patching_workflow.yml` | Full ESXi patching with SvSAN health gates |

Run any playbook:

```bash
ansible-playbook -i inventory/hosts.yml \
  ~/.ansible/collections/ansible_collections/xianganwu/stormagic/playbooks/svkms_full_setup.yml \
  --ask-vault-pass
```

Or copy the playbooks directory into your project and run locally:

```bash
cp -r "${COLLECTION_PATH}/xianganwu/stormagic/playbooks/" ~/my-stormagic-project/playbooks/
ansible-playbook -i inventory/hosts.yml playbooks/svkms_full_setup.yml --ask-vault-pass
```

## What to Customize

1. **inventory/hosts.yml** — Replace placeholder hostnames and IPs with your environment
2. **inventory/group_vars/all/vault.yml** — Fill in real credentials (use `ansible-vault encrypt`)
3. **inventory/group_vars/svkms_servers/svkms.yml** — Adjust SvKMS connection settings (port, TLS)
4. **inventory/group_vars/svsan_vsas/svsan.yml** — Set your Windows management host
5. **ansible.cfg** — Adjust forks, timeouts, and vault settings for your environment
