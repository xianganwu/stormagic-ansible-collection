FROM mcr.microsoft.com/powershell:lts-ubuntu-22.04

RUN pwsh -Command "Set-PSRepository PSGallery -InstallationPolicy Trusted; Install-Module -Name Pester -RequiredVersion 5.6.1 -Force -Scope AllUsers"

WORKDIR /tests

COPY plugins/module_utils/SvSAN.psm1 /tests/sut/SvSAN.psm1
COPY tests/mock_svsan/SmCmdlet.psm1 /tests/mock/SmCmdlet.psm1
COPY tests/pester/SvSAN.Tests.ps1 /tests/SvSAN.Tests.ps1

ENTRYPOINT ["pwsh", "-Command", "Import-Module /tests/mock/SmCmdlet.psm1 -Global -Force; Invoke-Pester /tests/SvSAN.Tests.ps1 -Output Detailed -CI"]
