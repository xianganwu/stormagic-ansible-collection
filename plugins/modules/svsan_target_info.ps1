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
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password
    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $targets = @(Get-SmTargets -Session $session)
    $mirrorStatus = @(Get-SmMirrorStatus -Session $session)

    $targetList = @()
    foreach ($t in $targets) {
        $mirror = $mirrorStatus | Where-Object { $_.TargetName -eq $t.Name } | Select-Object -First 1
        $info = @{
            name = $t.Name
            size_gb = $t.SizeGB
            status = $t.Status
            path_count = $t.PathCount
            pool = $t.Pool
            mirror = @{
                enabled = ($null -ne $mirror)
                sync_pct = if ($mirror) { $mirror.SyncPercentage } else { 0 }
                remote_vsa = if ($mirror) { $mirror.RemoteVSA } else { "" }
            }
        }
        $targetList += $info
    }

    $module.Result.changed = $false
    $module.Result.targets = $targetList
    $module.ExitJson()
}
catch {
    $module.FailJson("Target info error on $($module.Params.vsa_hostname): $_", $_)
}
