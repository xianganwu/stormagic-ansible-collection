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
        remote_vsa = @{ type = "str" }
        remote_pool = @{ type = "str" }
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
    $mirrors = @(Get-SmMirrorStatus -Session $session)
    foreach ($m in $mirrors) {
        if ($m.Name -eq $module.Params.name) {
            $existing = $m
            break
        }
    }

    if ($module.Params.state -eq "present") {
        if ($existing) {
            $module.Result.changed = $false
            $module.Result.mirror = $existing
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
            if ($module.Params.remote_vsa) { $params.RemoteVsa = $module.Params.remote_vsa }
            if ($module.Params.remote_pool) { $params.RemotePool = $module.Params.remote_pool }
            $mirror = New-SmMirror @params
            $module.Diff.after = $mirror
            $module.Result.changed = $true
            $module.Result.mirror = $mirror
        }
    }
    elseif ($module.Params.state -eq "absent") {
        if (-not $existing) {
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
            Remove-SmMirror -Session $session -Name $module.Params.name
            $module.Result.changed = $true
        }
    }

    $module.ExitJson()
}
catch {
    $module.FailJson("Mirror management error on $($module.Params.vsa_hostname): $_", $_)
}
finally {
    if ($session) { Disconnect-SmSession -Session $session }
}
