#!powershell

# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ansible_collections.xianganwu.stormagic.plugins.module_utils.SvSAN

$spec = @{
    options = @{
        vsa_hostname = @{ type = "str"; required = $true }
        vsa_username = @{ type = "str"; required = $true }
        vsa_password = @{ type = "str"; required = $true; no_log = $true }
        state = @{ type = "str"; default = "present"; choices = @("present") }
        name = @{ type = "str"; required = $true }
        vcenter = @{ type = "str" }
        datacenter = @{ type = "str" }
        cluster = @{ type = "str" }
        datastore = @{ type = "str" }
        network = @{ type = "str" }
        disk_size_gb = @{ type = "int" }
    }
    required_if = @(
        ,@("state", "present", @("vcenter", "datacenter", "cluster", "datastore", "network", "disk_size_gb"))
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$session = $null
try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password
    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    if ($module.Params.state -eq "present") {
        $existing = Get-SmVcVSA -Session $session -Name $module.Params.name

        if ($existing) {
            $module.Diff.before = $existing
            $module.Diff.after = $existing
            $module.Result.changed = $false
            $module.Result.vsa = $existing
            $module.ExitJson()
        }

        if ($module.CheckMode) {
            $module.Diff.before = @{}
            $module.Diff.after = @{ Name = $module.Params.name }
            $module.Result.changed = $true
            $module.ExitJson()
        }

        $module.Diff.before = @{}
        $params = @{
            Session = $session
            Name = $module.Params.name
        }
        if ($module.Params.vcenter) { $params.VCenter = $module.Params.vcenter }
        if ($module.Params.datacenter) { $params.Datacenter = $module.Params.datacenter }
        if ($module.Params.cluster) { $params.Cluster = $module.Params.cluster }
        if ($module.Params.datastore) { $params.Datastore = $module.Params.datastore }
        if ($module.Params.network) { $params.Network = $module.Params.network }
        if ($module.Params.disk_size_gb) { $params.DiskSizeGB = $module.Params.disk_size_gb }

        $vsa = Install-SmVcVSA @params
        $module.Diff.after = $vsa
        $module.Result.changed = $true
        $module.Result.vsa = $vsa
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("VSA deployment error on $($module.Params.vsa_hostname): $_", $_)
}
finally {
    if ($session) { Disconnect-SmSession -Session $session }
}
