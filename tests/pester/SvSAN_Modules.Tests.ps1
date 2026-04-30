# tests/pester/SvSAN_Modules.Tests.ps1
# Pester 5.x tests for SvSAN module CRUD operations.
# Tests the SmCmdlet operations in the patterns used by each .ps1 module.

BeforeAll {
    Import-Module /tests/mock/SmCmdlet.psm1 -Force
    Import-Module /tests/sut/SvSAN.psm1 -Force
}

Describe "Target Operations (svsan_target)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "state=present, target does not exist" {
        It "creates a new target and returns it" {
            $target = New-SmTarget -Session $script:session -Name "iscsi-t1" -SizeGB 200 -Pool "pool1"
            $target.Name | Should -Be "iscsi-t1"
            $target.SizeGB | Should -Be 200
            $target.Pool | Should -Be "pool1"
            $target.Status | Should -Be "Online"
        }
    }

    Context "state=present, target already exists (idempotency)" {
        It "finds existing target by name without creating a duplicate" {
            New-SmTarget -Session $script:session -Name "iscsi-t1" -SizeGB 100
            $targets = @(Get-SmTargets -Session $script:session)
            $existing = $targets | Where-Object { $_.Name -eq "iscsi-t1" }
            $existing | Should -Not -BeNullOrEmpty
            $existing.Name | Should -Be "iscsi-t1"

            New-SmTarget -Session $script:session -Name "iscsi-t2"
            $allTargets = @(Get-SmTargets -Session $script:session)
            $allTargets | Should -HaveCount 2
        }
    }

    Context "state=absent, target exists" {
        It "removes the target" {
            New-SmTarget -Session $script:session -Name "iscsi-t1"
            $before = @(Get-SmTargets -Session $script:session)
            $before | Should -HaveCount 1

            Remove-SmTarget -Session $script:session -Name "iscsi-t1"
            $after = @(Get-SmTargets -Session $script:session)
            $after | Should -HaveCount 0
        }
    }

    Context "state=absent, target does not exist" {
        It "removing a non-existent target is a no-op" {
            Remove-SmTarget -Session $script:session -Name "nonexistent"
            $targets = @(Get-SmTargets -Session $script:session)
            $targets | Should -HaveCount 0
        }
    }

    Context "lookup by name" {
        It "returns null when no match found" {
            New-SmTarget -Session $script:session -Name "iscsi-t1"
            $targets = @(Get-SmTargets -Session $script:session)
            $match = $null
            foreach ($t in $targets) {
                if ($t.Name -eq "nonexistent") { $match = $t; break }
            }
            $match | Should -BeNullOrEmpty
        }

        It "finds exact name match among multiple targets" {
            New-SmTarget -Session $script:session -Name "iscsi-t1"
            New-SmTarget -Session $script:session -Name "iscsi-t2"
            New-SmTarget -Session $script:session -Name "iscsi-t3"
            $targets = @(Get-SmTargets -Session $script:session)
            $match = $null
            foreach ($t in $targets) {
                if ($t.Name -eq "iscsi-t2") { $match = $t; break }
            }
            $match | Should -Not -BeNullOrEmpty
            $match.Name | Should -Be "iscsi-t2"
        }
    }
}

Describe "Pool Operations (svsan_pool)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "state=present, pool does not exist" {
        It "creates a new pool" {
            $pool = New-SmPool -Session $script:session -Name "data-pool"
            $pool.Name | Should -Be "data-pool"
            $pool.TotalCapacity | Should -BeGreaterThan 0
        }

        It "creates a pool with disk IDs" {
            $pool = New-SmPool -Session $script:session -Name "ssd-pool" -DiskIds @("disk-0", "disk-1")
            $pool.DiskIds | Should -HaveCount 2
        }
    }

    Context "state=present, pool already exists (idempotency)" {
        It "finds existing pool without creating a duplicate" {
            New-SmPool -Session $script:session -Name "data-pool"
            $pools = @(Get-SmPools -Session $script:session)
            $existing = $null
            foreach ($p in $pools) {
                if ($p.Name -eq "data-pool") { $existing = $p; break }
            }
            $existing | Should -Not -BeNullOrEmpty
        }
    }

    Context "state=absent" {
        It "removes an existing pool" {
            New-SmPool -Session $script:session -Name "data-pool"
            Remove-SmPool -Session $script:session -Name "data-pool"
            $pools = @(Get-SmPools -Session $script:session)
            $pools | Should -HaveCount 0
        }

        It "removing a non-existent pool is a no-op" {
            Remove-SmPool -Session $script:session -Name "nonexistent"
            $pools = @(Get-SmPools -Session $script:session)
            $pools | Should -HaveCount 0
        }
    }
}

Describe "Mirror Operations (svsan_mirror)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "state=present, mirror does not exist" {
        It "creates a new mirror with remote VSA" {
            $mirror = New-SmMirror -Session $script:session -Name "m1" -RemoteVsa "vsa2.local" -RemotePool "pool1"
            $mirror.Name | Should -Be "m1"
            $mirror.RemoteVSA | Should -Be "vsa2.local"
            $mirror.RemotePool | Should -Be "pool1"
            $mirror.SyncPercentage | Should -Be 100
        }
    }

    Context "state=present, mirror already exists (idempotency)" {
        It "finds existing mirror by name" {
            New-SmMirror -Session $script:session -Name "m1" -RemoteVsa "vsa2.local"
            $mirrors = @(Get-SmMirrorStatus -Session $script:session)
            $existing = $null
            foreach ($m in $mirrors) {
                if ($m.Name -eq "m1") { $existing = $m; break }
            }
            $existing | Should -Not -BeNullOrEmpty
            $existing.RemoteVSA | Should -Be "vsa2.local"
        }
    }

    Context "state=absent" {
        It "removes an existing mirror" {
            New-SmMirror -Session $script:session -Name "m1"
            Remove-SmMirror -Session $script:session -Name "m1"
            $mirrors = @(Get-SmMirrorStatus -Session $script:session)
            $mirrors | Should -HaveCount 0
        }

        It "removing a non-existent mirror is a no-op" {
            Remove-SmMirror -Session $script:session -Name "nonexistent"
            $mirrors = @(Get-SmMirrorStatus -Session $script:session)
            $mirrors | Should -HaveCount 0
        }
    }
}

Describe "License Operations (svsan_license)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    It "reads current license before applying" {
        $currentLicense = Get-SmLicense -Session $script:session
        $currentLicense.Key | Should -Be "EVAL-KEY"
        $currentLicense.IsValid | Should -Be $true
    }

    It "applies a new license key" {
        Set-SmLicense -Session $script:session -LicenseKey "PROD-12345"
        $license = Get-SmLicense -Session $script:session
        $license.Key | Should -Be "PROD-12345"
        $license.IsValid | Should -Be $true
        $license.Type | Should -Be "Licensed"
    }

    It "overwrites an existing license" {
        Set-SmLicense -Session $script:session -LicenseKey "KEY-A"
        Set-SmLicense -Session $script:session -LicenseKey "KEY-B"
        $license = Get-SmLicense -Session $script:session
        $license.Key | Should -Be "KEY-B"
    }
}

Describe "Config Operations (svsan_config / svsan_config_info)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "svsan_config_info (read-only)" {
        It "returns current config as a hashtable" {
            Set-SmMockData -Config @{ dns = "8.8.8.8"; ntp = "pool.ntp.org" }
            $config = Get-SmConfig -Session $script:session
            $config.dns | Should -Be "8.8.8.8"
            $config.ntp | Should -Be "pool.ntp.org"
        }

        It "returns empty config when nothing is set" {
            $config = Get-SmConfig -Session $script:session
            $config.Count | Should -Be 0
        }
    }

    Context "svsan_config (set values)" {
        It "sets a new config value" {
            Set-SmConfig -Session $script:session -Name "dns" -Value "1.1.1.1"
            $config = Get-SmConfig -Session $script:session
            $config.dns | Should -Be "1.1.1.1"
        }

        It "detects changes when desired differs from current" {
            Set-SmMockData -Config @{ dns = "8.8.8.8" }
            $current = Get-SmConfig -Session $script:session
            $desiredSettings = @{ dns = "1.1.1.1" }
            $changed = $false
            $updates = @{}
            foreach ($key in $desiredSettings.Keys) {
                if ($current[$key] -ne $desiredSettings[$key]) {
                    $changed = $true
                    $updates[$key] = $desiredSettings[$key]
                }
            }
            $changed | Should -Be $true
            $updates.dns | Should -Be "1.1.1.1"
        }

        It "detects no changes when desired matches current (idempotency)" {
            Set-SmMockData -Config @{ dns = "8.8.8.8" }
            $current = Get-SmConfig -Session $script:session
            $desiredSettings = @{ dns = "8.8.8.8" }
            $changed = $false
            foreach ($key in $desiredSettings.Keys) {
                if ($current[$key] -ne $desiredSettings[$key]) {
                    $changed = $true
                }
            }
            $changed | Should -Be $false
        }

        It "applies multiple config updates" {
            Set-SmConfig -Session $script:session -Name "dns" -Value "1.1.1.1"
            Set-SmConfig -Session $script:session -Name "ntp" -Value "time.google.com"
            $config = Get-SmConfig -Session $script:session
            $config.dns | Should -Be "1.1.1.1"
            $config.ntp | Should -Be "time.google.com"
        }
    }
}

Describe "VSA Deployment (svsan_vsa)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "state=present" {
        It "deploys a new VSA with full parameters" {
            $vsa = Install-SmVcVSA -Session $script:session `
                -Name "svsan-vsa-01" `
                -VCenter "vcenter.local" `
                -Datacenter "DC1" `
                -Cluster "Cluster1" `
                -Datastore "ds-ssd" `
                -Network "VM Network" `
                -DiskSizeGB 500
            $vsa.Name | Should -Be "svsan-vsa-01"
            $vsa.VCenter | Should -Be "vcenter.local"
            $vsa.Datacenter | Should -Be "DC1"
            $vsa.DiskSizeGB | Should -Be 500
            $vsa.Status | Should -Be "Deployed"
        }

        It "deploys with minimal parameters" {
            $vsa = Install-SmVcVSA -Session $script:session -Name "svsan-vsa-02"
            $vsa.Name | Should -Be "svsan-vsa-02"
            $vsa.Status | Should -Be "Deployed"
        }
    }
}

Describe "Info Modules (svsan_target_info, svsan_mirror_info, svsan_pool_info)" {
    BeforeEach {
        Reset-SmMockState
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        $script:session = Connect-SmVsa -Hostname "vsa1.local" -Credential $cred
    }

    Context "target_info" {
        It "returns empty list when no targets exist" {
            $targets = @(Get-SmTargets -Session $script:session)
            $targets | Should -HaveCount 0
        }

        It "returns all targets with properties" {
            Set-SmMockData -Targets @(
                [PSCustomObject]@{ Name = "t1"; Status = "Online"; SizeGB = 100; PathCount = 2; Pool = "p1" },
                [PSCustomObject]@{ Name = "t2"; Status = "Online"; SizeGB = 200; PathCount = 2; Pool = "p1" }
            )
            $targets = @(Get-SmTargets -Session $script:session)
            $targets | Should -HaveCount 2
            $targets[0].Name | Should -Be "t1"
            $targets[1].SizeGB | Should -Be 200
        }
    }

    Context "mirror_info" {
        It "returns empty list when no mirrors exist" {
            $mirrors = @(Get-SmMirrorStatus -Session $script:session)
            $mirrors | Should -HaveCount 0
        }

        It "returns mirrors with sync status" {
            Set-SmMockData -Mirrors @(
                [PSCustomObject]@{ Name = "m1"; SyncPercentage = 100; TargetName = "t1"; RemoteVSA = "vsa2" }
            )
            $mirrors = @(Get-SmMirrorStatus -Session $script:session)
            $mirrors | Should -HaveCount 1
            $mirrors[0].SyncPercentage | Should -Be 100
            $mirrors[0].RemoteVSA | Should -Be "vsa2"
        }
    }

    Context "pool_info" {
        It "returns empty list when no pools exist" {
            $pools = @(Get-SmPools -Session $script:session)
            $pools | Should -HaveCount 0
        }

        It "returns pools with capacity info" {
            Set-SmMockData -Pools @(
                [PSCustomObject]@{ Name = "pool1"; TotalCapacity = 1000; UsedCapacity = 300 }
            )
            $pools = @(Get-SmPools -Session $script:session)
            $pools | Should -HaveCount 1
            $pools[0].TotalCapacity | Should -Be 1000
            $pools[0].UsedCapacity | Should -Be 300
        }
    }
}

Describe "Connection Error Handling" {
    BeforeEach {
        Reset-SmMockState
    }

    It "all modules fail gracefully when connection is refused" {
        Set-SmMockSessionFailure -ErrorMessage "Connection refused"
        $cred = New-SmCredentialFromParam -Username "admin" -Password "pass"
        { Connect-SmVsa -Hostname "bad.host" -Credential $cred -MaxRetries 1 } |
            Should -Throw "*Failed to connect to VSA*"
    }

    It "all modules fail gracefully on authentication error" {
        Set-SmMockSessionFailure -ErrorMessage "Access denied"
        $cred = New-SmCredentialFromParam -Username "wrong" -Password "wrong"
        { Connect-SmVsa -Hostname "vsa1.local" -Credential $cred -MaxRetries 1 } |
            Should -Throw "*Failed to connect*"
    }
}
