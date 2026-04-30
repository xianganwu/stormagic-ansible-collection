#!powershell

# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        vcenter_hostname = @{ type = "str"; required = $true }
        vcenter_username = @{ type = "str"; required = $true }
        vcenter_password = @{ type = "str"; required = $true; no_log = $true }
        esxi_hostname = @{ type = "str"; required = $true }
        validate_certs = @{ type = "bool"; default = $true }
        alert_severity = @{
            type = "list"
            elements = "str"
            default = @("error", "warning")
        }
        max_alerts = @{ type = "int"; default = 100 }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

try {
    if (-not (Get-Module -ListAvailable -Name VMware.PowerCLI)) {
        $module.FailJson("VMware PowerCLI is not installed on this host")
    }

    $connectParams = @{
        Server = $module.Params.vcenter_hostname
        User = $module.Params.vcenter_username
        Password = $module.Params.vcenter_password
        Force = $true
    }
    if (-not $module.Params.validate_certs) {
        Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false -Scope Session | Out-Null
    }

    $viServer = Connect-VIServer @connectParams -ErrorAction Stop

    $vmHost = Get-VMHost -Server $viServer -Name $module.Params.esxi_hostname -ErrorAction Stop

    $module.Result.esxi_build = $vmHost.Build
    $module.Result.esxi_version = $vmHost.Version
    $module.Result.maintenance_mode = ($vmHost.ConnectionState -eq "Maintenance")

    $alertTypes = @()
    foreach ($sev in $module.Params.alert_severity) {
        switch ($sev.ToLower()) {
            "error" { $alertTypes += "Error" }
            "warning" { $alertTypes += "Warning" }
            "info" { $alertTypes += "Info" }
        }
    }

    $eventParams = @{
        Entity = $vmHost
        MaxSamples = $module.Params.max_alerts
        Start = (Get-Date).AddDays(-7)
    }

    $events = @(
        Get-VIEvent @eventParams -ErrorAction SilentlyContinue |
            Where-Object {
                ($_ -is [VMware.Vim.AlarmStatusChangedEvent]) -or
                ($_.Severity -and $alertTypes -contains $_.Severity)
            }
    )

    $alertList = @()
    foreach ($evt in $events) {
        $alertList += @{
            time = $evt.CreatedTime.ToString("o")
            severity = if ($evt.Severity) { $evt.Severity.ToString() } else { "unknown" }
            message = $evt.FullFormattedMessage
        }
    }

    $module.Result.alerts = $alertList
    $module.Result.alert_count = $alertList.Count
    $module.Result.has_blocking_alerts = (
        $alertList | Where-Object { $_.severity -eq "Error" }
    ).Count -gt 0
    $module.Result.changed = $false

    Disconnect-VIServer -Server $viServer -Confirm:$false -ErrorAction SilentlyContinue

    $module.ExitJson()
}
catch {
    $module.FailJson("ESXi preflight check failed for $($module.Params.esxi_hostname): $_", $_)
}
