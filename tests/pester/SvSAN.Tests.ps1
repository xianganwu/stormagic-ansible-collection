# tests/pester/SvSAN.Tests.ps1
# Pester 5.x tests for plugins/module_utils/SvSAN.psm1

BeforeAll {
    Import-Module /tests/mock/SmCmdlet.psm1 -Force
    Import-Module /tests/sut/SvSAN.psm1 -Force
}

Describe "New-SmCredentialFromParam" {
    It "creates a PSCredential with the given username" {
        $cred = New-SmCredentialFromParam -Username "admin" -Password "secret123"
        $cred | Should -BeOfType [PSCredential]
        $cred.UserName | Should -Be "admin"
    }

    It "password round-trips through GetNetworkCredential" {
        $cred = New-SmCredentialFromParam -Username "user1" -Password "myP@ss!"
        $cred.GetNetworkCredential().Password | Should -Be "myP@ss!"
    }
}

Describe "Connect-SmVsa" {
    BeforeEach {
        Reset-SmMockState
    }

    It "returns a session object on successful connection" {
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
        $session | Should -Not -BeNullOrEmpty
        $session.Connected | Should -Be $true
        $session.HostName | Should -Be "vsa1.local"
    }

    It "throws with formatted error message on connection failure" {
        Set-SmMockSessionFailure -ErrorMessage "Connection refused"
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        { Connect-SmVsa -Hostname "bad.host" -Credential $cred -MaxRetries 1 } |
            Should -Throw "*Failed to connect to VSA*"
    }

    It "error message includes the hostname" {
        Set-SmMockSessionFailure -ErrorMessage "timeout"
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        { Connect-SmVsa -Hostname "vsa99.local" -Credential $cred -MaxRetries 1 } |
            Should -Throw "*vsa99.local*"
    }
}

Describe "Invoke-SmHealthCheck" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:testSession = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "All checks pass" {
        BeforeEach {
            $mockParams = @{
                License = @{ IsValid = $true; Key = "VALID"; Expiry = "2027-01-01" }
                Targets = @(
                    [PSCustomObject]@{ Name = "t1"; Status = "Online"; SizeGB = 100; PathCount = 2; Pool = "pool1" }
                )
                Mirrors = @(
                    [PSCustomObject]@{ Name = "m1"; SyncPercentage = 100; TargetName = "t1"; RemoteVSA = "vsa2" }
                )
                Pools = @(
                    [PSCustomObject]@{ Name = "pool1"; TotalCapacity = 1000; UsedCapacity = 200 }
                )
            }
            Set-SmMockData @mockParams
        }

        It "returns overall 'pass'" {
            $result = Invoke-SmHealthCheck -Session $script:testSession
            $result.overall | Should -Be "pass"
        }

        It "connectivity is always 'pass'" {
            $result = Invoke-SmHealthCheck -Session $script:testSession
            $result.checks.connectivity | Should -Be "pass"
        }

        It "includes license details in results" {
            $result = Invoke-SmHealthCheck -Session $script:testSession
            $result.details.license | Should -Not -BeNullOrEmpty
        }

        It "includes targets in details" {
            $result = Invoke-SmHealthCheck -Session $script:testSession
            $result.details.targets | Should -HaveCount 1
        }
    }

    Context "License invalid" {
        BeforeEach {
            Set-SmMockData -License @{ IsValid = $false; Key = "EXPIRED"; Expiry = "2020-01-01" }
        }

        It "returns overall 'fail' when IsValid is false" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("license")
            $result.overall | Should -Be "fail"
            $result.checks.license | Should -Be "fail"
        }
    }

    Context "Target offline" {
        BeforeEach {
            $targets = @(
                [PSCustomObject]@{ Name = "t1"; Status = "Online"; SizeGB = 100; PathCount = 2; Pool = "p1" },
                [PSCustomObject]@{ Name = "t2"; Status = "Offline"; SizeGB = 100; PathCount = 0; Pool = "p1" }
            )
            Set-SmMockData -Targets $targets
        }

        It "returns overall 'fail' when any target Status is not Online" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("targets")
            $result.overall | Should -Be "fail"
            $result.checks.targets | Should -Be "fail"
        }
    }

    Context "Mirror below sync threshold" {
        BeforeEach {
            $mirrors = @(
                [PSCustomObject]@{ Name = "m1"; SyncPercentage = 50; TargetName = "t1"; RemoteVSA = "vsa2" }
            )
            Set-SmMockData -Mirrors $mirrors
        }

        It "returns overall 'fail' when SyncPercentage below default threshold 100" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("mirrors")
            $result.overall | Should -Be "fail"
            $result.checks.mirrors | Should -Be "fail"
        }

        It "passes when SyncPercentage at or above custom threshold" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("mirrors") -MirrorSyncThreshold 50
            $result.checks.mirrors | Should -Be "pass"
        }

        It "fails when SyncPercentage below custom threshold" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("mirrors") -MirrorSyncThreshold 75
            $result.checks.mirrors | Should -Be "fail"
        }
    }

    Context "Pool capacity warning" {
        It "returns overall 'warn' when usage at or above PoolCapacityWarnPct" {
            $pools = @([PSCustomObject]@{ Name = "pool1"; TotalCapacity = 100; UsedCapacity = 85 })
            Set-SmMockData -Pools $pools
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("pools") -PoolCapacityWarnPct 80
            $result.overall | Should -Be "warn"
            $result.checks.pools | Should -Be "warn"
        }

        It "returns 'pass' when usage is below threshold" {
            $pools = @([PSCustomObject]@{ Name = "pool1"; TotalCapacity = 100; UsedCapacity = 50 })
            Set-SmMockData -Pools $pools
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("pools") -PoolCapacityWarnPct 80
            $result.checks.pools | Should -Be "pass"
        }

        It "handles zero TotalCapacity without division error" {
            $pools = @([PSCustomObject]@{ Name = "empty"; TotalCapacity = 0; UsedCapacity = 0 })
            Set-SmMockData -Pools $pools
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("pools")
            $result.checks.pools | Should -Be "pass"
        }
    }

    Context "Subset of checks" {
        BeforeEach {
            Set-SmMockData -License @{ IsValid = $true }
        }

        It "only runs specified checks" {
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("license")
            $result.checks.Keys | Should -Contain "connectivity"
            $result.checks.Keys | Should -Contain "license"
            $result.checks.Keys | Should -Not -Contain "targets"
            $result.checks.Keys | Should -Not -Contain "mirrors"
            $result.checks.Keys | Should -Not -Contain "pools"
        }
    }

    Context "Overall status priority" {
        It "'fail' takes precedence over 'warn'" {
            $pools = @([PSCustomObject]@{ Name = "p1"; TotalCapacity = 100; UsedCapacity = 95 })
            Set-SmMockData -License @{ IsValid = $false } -Pools $pools
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("license", "pools") -PoolCapacityWarnPct 80
            $result.overall | Should -Be "fail"
        }
    }

    Context "Error handling" {
        It "sets check to 'fail' when cmdlet throws" {
            Set-SmMockData -License @{ IsValid = $true }
            Mock Get-SmTargets { throw "Network error" } -ModuleName SvSAN
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("targets")
            $result.checks.targets | Should -Be "fail"
        }

        It "includes error message in details when cmdlet throws" {
            Mock Get-SmPools { throw "Pool service unavailable" } -ModuleName SvSAN
            $result = Invoke-SmHealthCheck -Session $script:testSession -Checks @("pools")
            $result.details.pools.error | Should -BeLike "*Pool service unavailable*"
        }
    }
}
