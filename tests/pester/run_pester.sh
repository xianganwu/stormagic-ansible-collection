#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Prefer native pwsh if available (faster, no Docker overhead).
# Falls back to Docker for CI or systems without pwsh.
if command -v pwsh &>/dev/null; then
    echo "==> Running Pester tests with native pwsh..."
    pwsh -Command "
        Import-Module ./tests/mock_svsan/SmCmdlet.psm1 -Global -Force
        Import-Module ./plugins/module_utils/SvSAN.psm1 -Force

        \$testContent = Get-Content ./tests/pester/SvSAN.Tests.ps1 -Raw
        \$testContent = \$testContent -replace '/tests/mock/SmCmdlet.psm1', './tests/mock_svsan/SmCmdlet.psm1'
        \$testContent = \$testContent -replace '/tests/sut/SvSAN.psm1', './plugins/module_utils/SvSAN.psm1'
        \$tempTest = Join-Path ([System.IO.Path]::GetTempPath()) 'SvSAN.Tests.ps1'
        Set-Content -Path \$tempTest -Value \$testContent

        Invoke-Pester \$tempTest -Output Detailed -CI
        Remove-Item \$tempTest -ErrorAction SilentlyContinue
    "
else
    echo "==> Building Pester test image (Docker)..."
    docker build -f tests/mock_svsan/Dockerfile -t svsan-pester:test .
    echo "==> Running SvSAN Pester tests in Docker..."
    docker run --rm --name svsan-pester-test svsan-pester:test
fi
