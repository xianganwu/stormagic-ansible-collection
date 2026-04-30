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
        checks = @{
            type = "list"
            elements = "str"
            default = @("connectivity", "license", "targets", "mirrors", "pools")
        }
        mirror_sync_threshold = @{ type = "int"; default = 100 }
        pool_capacity_warn_pct = @{ type = "int"; default = 80 }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$session = $null
try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password

    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $health = Invoke-SmHealthCheck -Session $session `
        -Checks $module.Params.checks `
        -MirrorSyncThreshold $module.Params.mirror_sync_threshold `
        -PoolCapacityWarnPct $module.Params.pool_capacity_warn_pct

    $module.Result.health = $health
    $module.Result.changed = $false

    if ($health.overall -eq "fail" -and -not $module.CheckMode) {
        $module.FailJson("VSA health check failed", $module.Result)
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("Health check error on $($module.Params.vsa_hostname): $_", $_)
}
finally {
    if ($session) { Disconnect-SmSession -Session $session }
}
