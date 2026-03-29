Param(
    [switch]$InstallDockerDesktop
)

$ErrorActionPreference = "Stop"

function Test-DockerInstalled {
    return [bool](Get-Command docker -ErrorAction SilentlyContinue)
}

Write-Host "[Worker Setup][1/3] Checking Docker CLI..."
if (-not (Test-DockerInstalled)) {
    if ($InstallDockerDesktop) {
        Write-Host "Docker not found. Installing Docker Desktop via winget..."
        & winget install -e --id Docker.DockerDesktop
        Write-Host "Installation requested. Reopen terminal after Docker Desktop launch, then rerun this script."
        exit 0
    }

    throw "Docker CLI not found. Install Docker Desktop first or rerun with -InstallDockerDesktop."
}

Write-Host "[Worker Setup][2/3] Checking Docker daemon..."
& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker daemon is not running. Open Docker Desktop and rerun."
}

Write-Host "[Worker Setup][3/3] Pulling Spark image..."
& docker pull apache/spark:3.5.1
if ($LASTEXITCODE -ne 0) {
    throw "Failed to pull apache/spark:3.5.1"
}

Write-Host "Worker machine is ready."
