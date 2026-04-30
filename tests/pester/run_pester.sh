#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Prefer native pwsh if available (faster, no Docker overhead).
# Falls back to Docker for CI or systems without pwsh.
PWSH=""
if command -v pwsh &>/dev/null; then
    PWSH="pwsh"
elif command -v pwsh-preview &>/dev/null; then
    PWSH="pwsh-preview"
fi

if [ -n "$PWSH" ]; then
    echo "==> Running Pester tests with native $PWSH..."
    "$PWSH" -Command "
        Import-Module ./tests/mock_svsan/SmCmdlet.psm1 -Global -Force
        Import-Module ./plugins/module_utils/SvSAN.psm1 -Force

        \$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) 'pester-svsan'
        New-Item -ItemType Directory -Path \$tempDir -Force | Out-Null

        foreach (\$testFile in @('SvSAN.Tests.ps1', 'SvSAN_Modules.Tests.ps1', 'SvSAN_Advanced.Tests.ps1')) {
            \$testContent = Get-Content ./tests/pester/\$testFile -Raw
            \$testContent = \$testContent -replace '/tests/mock/SmCmdlet.psm1', './tests/mock_svsan/SmCmdlet.psm1'
            \$testContent = \$testContent -replace '/tests/sut/SvSAN.psm1', './plugins/module_utils/SvSAN.psm1'
            Set-Content -Path (Join-Path \$tempDir \$testFile) -Value \$testContent
        }

        Invoke-Pester \$tempDir -Output Detailed -CI
        Remove-Item \$tempDir -Recurse -ErrorAction SilentlyContinue
    "
else
    echo "==> Building Pester test image (Docker)..."
    docker build -f tests/mock_svsan/Dockerfile -t svsan-pester:test .
    echo "==> Running SvSAN Pester tests in Docker..."
    docker run --rm --name svsan-pester-test svsan-pester:test
fi
