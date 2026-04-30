# plugins/module_utils/SvSAN.psm1
# Copyright: (c) 2026, StorMagic Ltd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

Function New-SmCredentialFromParam {
    [CmdletBinding()]
    [OutputType([PSCredential])]
    Param(
        [Parameter(Mandatory = $true)]
        [string]$Username,

        [Parameter(Mandatory = $true)]
        [string]$Password
    )

    $securePass = ConvertTo-SecureString -String $Password -AsPlainText -Force
    return New-Object PSCredential($Username, $securePass)
}


Function Connect-SmVsa {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)]
        [string]$Hostname,

        [Parameter(Mandatory = $true)]
        [PSCredential]$Credential,

        [int]$MaxRetries = 3,

        [int]$RetryDelay = 1
    )

    $lastError = $null
    for ($attempt = 0; $attempt -lt $MaxRetries; $attempt++) {
        try {
            $session = New-SmSession -HostName $Hostname -Credential $Credential
            return $session
        }
        catch {
            $lastError = $_
            if ($attempt -lt ($MaxRetries - 1)) {
                $sleepSeconds = $RetryDelay * [Math]::Pow(2, $attempt)
                Start-Sleep -Seconds $sleepSeconds
            }
        }
    }
    throw "Failed to connect to VSA '{0}' after {1} attempts: {2}" -f $Hostname, $MaxRetries, $lastError.Exception.Message
}


Function Invoke-SmHealthCheck {
    [CmdletBinding()]
    [OutputType([hashtable])]
    Param(
        [Parameter(Mandatory = $true)]
        $Session,

        [string[]]$Checks = @("connectivity", "license", "targets", "mirrors", "pools"),

        [int]$MirrorSyncThreshold = 100,

        [int]$PoolCapacityWarnPct = 80
    )

    $results = @{
        checks = @{}
        overall = "pass"
        details = @{}
    }

    $results.checks.connectivity = "pass"

    if ($Checks -contains "license") {
        try {
            $license = Get-SmLicense -Session $Session
            $results.details.license = $license
            $results.checks.license = if ($license.IsValid) { "pass" } else { "fail" }
        }
        catch {
            $results.checks.license = "fail"
            $results.details.license = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "targets") {
        try {
            $targets = @(Get-SmTargets -Session $Session)
            $results.details.targets = $targets
            $results.checks.targets = "pass"
            foreach ($t in $targets) {
                if ($t.Status -ne "Online") {
                    $results.checks.targets = "fail"
                    break
                }
            }
        }
        catch {
            $results.checks.targets = "fail"
            $results.details.targets = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "mirrors") {
        try {
            $mirrors = @(Get-SmMirrorStatus -Session $Session)
            $results.details.mirrors = $mirrors
            $results.checks.mirrors = "pass"
            foreach ($m in $mirrors) {
                if ($m.SyncPercentage -lt $MirrorSyncThreshold) {
                    $results.checks.mirrors = "fail"
                    break
                }
            }
        }
        catch {
            $results.checks.mirrors = "fail"
            $results.details.mirrors = @{ error = $_.Exception.Message }
        }
    }

    if ($Checks -contains "pools") {
        try {
            $pools = @(Get-SmPools -Session $Session)
            $results.details.pools = $pools
            $results.checks.pools = "pass"
            foreach ($p in $pools) {
                if ($p.TotalCapacity -gt 0) {
                    $usedPct = ($p.UsedCapacity / $p.TotalCapacity) * 100
                    if ($usedPct -ge $PoolCapacityWarnPct) {
                        $results.checks.pools = "warn"
                    }
                }
            }
        }
        catch {
            $results.checks.pools = "fail"
            $results.details.pools = @{ error = $_.Exception.Message }
        }
    }

    if ($results.checks.Values -contains "fail") {
        $results.overall = "fail"
    }
    elseif ($results.checks.Values -contains "warn") {
        $results.overall = "warn"
    }

    return $results
}

Function Disconnect-SmSession {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)]
        $Session
    )
    try { Remove-SmSession -Session $Session }
    catch { }
}

Export-ModuleMember -Function * -Cmdlet *
