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
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

try {
    $cred = New-SmCredentialFromParam -Username $module.Params.vsa_username `
        -Password $module.Params.vsa_password

    $session = Connect-SmVsa -Hostname $module.Params.vsa_hostname -Credential $cred

    $mirrors = @(Get-SmMirrorStatus -Session $session)

    $module.Result.mirrors = $mirrors
    $module.Result.changed = $false

    $module.ExitJson()
}
catch {
    $module.FailJson("Mirror info retrieval error: $_", $_)
}
