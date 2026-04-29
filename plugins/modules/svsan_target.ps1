#!powershell

# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -PowerShell ansible_collections.stormagic.stormagic.plugins.module_utils.SvSAN

$spec = @{
    options = @{
        vsa_hostname = @{ type = "str"; required = $true }
        vsa_username = @{ type = "str"; required = $true }
        vsa_password = @{ type = "str"; required = $true; no_log = $true }
        state = @{ type = "str"; default = "present"; choices = @("present", "absent") }
        name = @{ type = "str"; required = $true }
        size_gb = @{ type = "int" }
        pool = @{ type = "str" }
        mirror = @{ type = "bool"; default = $false }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

try {
    $cred = New-SmCredentialFromParams -Username $module.Params.vsa_username `
                                        -Password $module.Params.vsa_password
    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $existing = $null
    $targets = @(Get-SmTargets -Session $session)
    foreach ($t in $targets) {
        if ($t.Name -eq $module.Params.name) {
            $existing = $t
            break
        }
    }

    if ($module.Params.state -eq "present") {
        if ($existing) {
            $module.Result.changed = $false
            $module.Result.target = $existing
        } else {
            if ($module.CheckMode) {
                $module.Result.changed = $true
                $module.ExitJson()
            }
            $params = @{
                Session = $session
                Name = $module.Params.name
            }
            if ($module.Params.size_gb) { $params.SizeGB = $module.Params.size_gb }
            if ($module.Params.pool) { $params.Pool = $module.Params.pool }
            $target = New-SmTarget @params
            $module.Result.changed = $true
            $module.Result.target = $target
        }
    }
    elseif ($module.Params.state -eq "absent") {
        if (-not $existing) {
            $module.Result.changed = $false
        } else {
            if ($module.CheckMode) {
                $module.Result.changed = $true
                $module.ExitJson()
            }
            Remove-SmTarget -Session $session -Name $module.Params.name
            $module.Result.changed = $true
        }
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("Target management error: $_", $_)
}
