FROM ubuntu:22.04

ARG PS_VERSION=7.4.7
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates libicu70 libssl3 \
    && PS_ARCH=$([ "$TARGETARCH" = "arm64" ] && echo "arm64" || echo "x64") \
    && wget -q "https://github.com/PowerShell/PowerShell/releases/download/v${PS_VERSION}/powershell-${PS_VERSION}-linux-${PS_ARCH}.tar.gz" \
    && mkdir -p /opt/microsoft/powershell/7 \
    && tar xzf "powershell-${PS_VERSION}-linux-${PS_ARCH}.tar.gz" -C /opt/microsoft/powershell/7 \
    && rm "powershell-${PS_VERSION}-linux-${PS_ARCH}.tar.gz" \
    && chmod +x /opt/microsoft/powershell/7/pwsh \
    && ln -s /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh \
    && rm -rf /var/lib/apt/lists/*

RUN pwsh -Command "Set-PSRepository PSGallery -InstallationPolicy Trusted; Install-Module -Name Pester -RequiredVersion 5.6.1 -Force -Scope AllUsers"

WORKDIR /tests

COPY plugins/module_utils/SvSAN.psm1 /tests/sut/SvSAN.psm1
COPY tests/mock_svsan/SmCmdlet.psm1 /tests/mock/SmCmdlet.psm1
COPY tests/pester/SvSAN.Tests.ps1 /tests/SvSAN.Tests.ps1
COPY tests/pester/SvSAN_Modules.Tests.ps1 /tests/SvSAN_Modules.Tests.ps1
COPY tests/pester/SvSAN_Advanced.Tests.ps1 /tests/SvSAN_Advanced.Tests.ps1

ENTRYPOINT ["pwsh", "-Command", "Import-Module /tests/mock/SmCmdlet.psm1 -Global -Force; Invoke-Pester /tests -Output Detailed -CI"]
