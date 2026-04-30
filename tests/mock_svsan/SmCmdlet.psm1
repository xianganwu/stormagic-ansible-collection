# tests/mock_svsan/SmCmdlet.psm1
# Mock implementation of StorMagic SmCmdlet.dll for Pester testing.
# Provides in-memory fakes of all cmdlet functions used by SvSAN.psm1
# and the SvSAN Ansible modules.

$script:Sessions = @{}
$script:License = @{
    IsValid = $true
    Key = "EVAL-KEY"
    Expiry = "2027-01-01"
    Type = "Evaluation"
}
$script:Targets = [System.Collections.ArrayList]@()
$script:Pools = [System.Collections.ArrayList]@()
$script:Mirrors = [System.Collections.ArrayList]@()
$script:Config = @{}
$script:FailNextSession = $false
$script:NextSessionError = "Connection refused"

Function Reset-SmMockState {
    [CmdletBinding()]
    Param()

    $script:Sessions = @{}
    $script:License = @{
        IsValid = $true
        Key = "EVAL-KEY"
        Expiry = "2027-01-01"
        Type = "Evaluation"
    }
    $script:Targets = [System.Collections.ArrayList]@()
    $script:Pools = [System.Collections.ArrayList]@()
    $script:Mirrors = [System.Collections.ArrayList]@()
    $script:Config = @{}
    $script:FailNextSession = $false
    $script:NextSessionError = "Connection refused"
}

Function Set-SmMockData {
    [CmdletBinding()]
    Param(
        [PSCustomObject[]]$Targets,
        [PSCustomObject[]]$Pools,
        [PSCustomObject[]]$Mirrors,
        [hashtable]$License,
        [hashtable]$Config
    )

    if ($PSBoundParameters.ContainsKey('Targets')) {
        $script:Targets = [System.Collections.ArrayList]@($Targets)
    }
    if ($PSBoundParameters.ContainsKey('Pools')) {
        $script:Pools = [System.Collections.ArrayList]@($Pools)
    }
    if ($PSBoundParameters.ContainsKey('Mirrors')) {
        $script:Mirrors = [System.Collections.ArrayList]@($Mirrors)
    }
    if ($PSBoundParameters.ContainsKey('License')) {
        $script:License = $License
    }
    if ($PSBoundParameters.ContainsKey('Config')) {
        $script:Config = $Config
    }
}

Function Set-SmMockSessionFailure {
    [CmdletBinding()]
    Param(
        [string]$ErrorMessage = "Connection refused"
    )
    $script:FailNextSession = $true
    $script:NextSessionError = $ErrorMessage
}

Function New-SmSession {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        [string]$HostName,

        [Parameter(Mandatory)]
        [PSCredential]$Credential
    )

    if ($script:FailNextSession) {
        $script:FailNextSession = $false
        throw $script:NextSessionError
    }

    $sessionId = [guid]::NewGuid().ToString()
    $session = [PSCustomObject]@{
        SessionId = $sessionId
        HostName = $HostName
        UserName = $Credential.UserName
        Connected = $true
    }
    $script:Sessions[$sessionId] = $session
    return $session
}

Function Get-SmLicense {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    return [PSCustomObject]$script:License
}

Function Get-SmTargets {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '')]
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    return @($script:Targets)
}

Function Get-SmMirrorStatus {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    return @($script:Mirrors)
}

Function Get-SmPools {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '')]
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    return @($script:Pools)
}

Function Get-SmConfig {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    return $script:Config.Clone()
}

Function Set-SmConfig {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        $Value
    )
    $script:Config[$Name] = $Value
}

Function New-SmTarget {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name,

        [int]$SizeGB = 100,

        [string]$Pool = "default"
    )

    $target = [PSCustomObject]@{
        Name = $Name
        Status = "Online"
        SizeGB = $SizeGB
        PathCount = 2
        Pool = $Pool
    }
    [void]$script:Targets.Add($target)
    return $target
}

Function Remove-SmTarget {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name
    )

    $idx = -1
    for ($i = 0; $i -lt $script:Targets.Count; $i++) {
        if ($script:Targets[$i].Name -eq $Name) { $idx = $i; break }
    }
    if ($idx -ge 0) { $script:Targets.RemoveAt($idx) }
}

Function New-SmPool {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name,

        [string[]]$DiskIds = @()
    )

    $pool = [PSCustomObject]@{
        Name = $Name
        TotalCapacity = 1000
        UsedCapacity = 0
        DiskIds = $DiskIds
    }
    [void]$script:Pools.Add($pool)
    return $pool
}

Function Remove-SmPool {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name
    )

    $idx = -1
    for ($i = 0; $i -lt $script:Pools.Count; $i++) {
        if ($script:Pools[$i].Name -eq $Name) { $idx = $i; break }
    }
    if ($idx -ge 0) { $script:Pools.RemoveAt($idx) }
}

Function New-SmMirror {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name,

        [string]$RemoteVsa = "",

        [string]$RemotePool = ""
    )

    $mirror = [PSCustomObject]@{
        Name = $Name
        SyncPercentage = 100
        TargetName = $Name
        RemoteVSA = $RemoteVsa
        RemotePool = $RemotePool
    }
    [void]$script:Mirrors.Add($mirror)
    return $mirror
}

Function Remove-SmMirror {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name
    )

    $idx = -1
    for ($i = 0; $i -lt $script:Mirrors.Count; $i++) {
        if ($script:Mirrors[$i].Name -eq $Name) { $idx = $i; break }
    }
    if ($idx -ge 0) { $script:Mirrors.RemoveAt($idx) }
}

Function Remove-SmSession {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session
    )
    if ($Session.SessionId -and $script:Sessions.ContainsKey($Session.SessionId)) {
        $script:Sessions.Remove($Session.SessionId)
    }
}

Function Set-SmLicense {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$LicenseKey
    )

    $script:License.Key = $LicenseKey
    $script:License.IsValid = $true
    $script:License.Type = "Licensed"
}

Function Install-SmVcVSA {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory)]
        $Session,

        [Parameter(Mandatory)]
        [string]$Name,

        [string]$VCenter = "",
        [string]$Datacenter = "",
        [string]$Cluster = "",
        [string]$Datastore = "",
        [string]$Network = "",
        [int]$DiskSizeGB = 100
    )

    return [PSCustomObject]@{
        Name = $Name
        VCenter = $VCenter
        Datacenter = $Datacenter
        Cluster = $Cluster
        Datastore = $Datastore
        Network = $Network
        DiskSizeGB = $DiskSizeGB
        Status = "Deployed"
    }
}

Export-ModuleMember -Function *
