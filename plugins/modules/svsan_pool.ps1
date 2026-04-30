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
        state = @{ type = "str"; default = "present"; choices = @("present", "absent") }
        name = @{ type = "str"; required = $true }
        disk_ids = @{ type = "list"; elements = "str" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$session = $null
try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password
    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $existing = $null
    $pools = @(Get-SmPools -Session $session)
    foreach ($p in $pools) {
        if ($p.Name -eq $module.Params.name) {
            $existing = $p
            break
        }
    }

    if ($module.Params.state -eq "present") {
        if ($existing) {
            $module.Diff.before = $existing
            $module.Diff.after = $existing
            $module.Result.changed = $false
            $module.Result.pool = $existing
        }
        else {
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
            if ($module.Params.disk_ids) { $params.DiskIds = $module.Params.disk_ids }
            $pool = New-SmPool @params
            $module.Diff.after = $pool
            $module.Result.changed = $true
            $module.Result.pool = $pool
        }
    }
    elseif ($module.Params.state -eq "absent") {
        if (-not $existing) {
            $module.Diff.before = @{}
            $module.Diff.after = @{}
            $module.Result.changed = $false
        }
        else {
            if ($module.CheckMode) {
                $module.Diff.before = $existing
                $module.Diff.after = @{}
                $module.Result.changed = $true
                $module.ExitJson()
            }
            $module.Diff.before = $existing
            $module.Diff.after = @{}
            Remove-SmPool -Session $session -Name $module.Params.name
            $module.Result.changed = $true
        }
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("Pool management error on $($module.Params.vsa_hostname): $_", $_)
}
finally {
    if ($session) { Disconnect-SmSession -Session $session }
}
