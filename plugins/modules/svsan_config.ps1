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
        settings = @{ type = "dict" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$session = $null
try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password
    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $currentConfig = Get-SmConfig -Session $session

    $changed = $false
    $updates = @{}

    if ($module.Params.settings) {
        foreach ($key in $module.Params.settings.Keys) {
            $desiredValue = $module.Params.settings[$key]
            $currentValue = $currentConfig[$key]

            if ($currentValue -ne $desiredValue) {
                $changed = $true
                $updates[$key] = $desiredValue
            }
        }
    }

    if ($changed) {
        $module.Diff.before = $currentConfig

        if ($module.CheckMode) {
            $module.Result.changed = $true
            $module.Result.updates = $updates
            $module.ExitJson()
        }

        foreach ($key in $updates.Keys) {
            Set-SmConfig -Session $session -Name $key -Value $updates[$key]
        }

        $newConfig = Get-SmConfig -Session $session
        $module.Diff.after = $newConfig

        $module.Result.changed = $true
        $module.Result.updates = $updates
    }
    else {
        $module.Result.changed = $false
    }

    $module.Result.config = Get-SmConfig -Session $session

    $module.ExitJson()
}
catch {
    $module.FailJson("Configuration management error on $($module.Params.vsa_hostname): $_", $_)
}
finally {
    if ($session) { Disconnect-SmSession -Session $session }
}
