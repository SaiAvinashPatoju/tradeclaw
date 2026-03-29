Param(
    [Parameter(Mandatory = $true)]
    [string]$MasterIp
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\worker_install_and_prepare.ps1"

$workerName = "tradeclaw-remote-worker-1"
$hostUiPort = 8091

Write-Host "Starting $workerName attached to master $MasterIp ..."
& docker rm -f $workerName *> $null

$runArgs = @(
    "run", "-d",
    "--name", $workerName,
    "--restart", "unless-stopped",
    "--add-host", "spark-master:$MasterIp",
    "-p", "$hostUiPort`:8081",
    "apache/spark:3.5.1",
    "/opt/spark/bin/spark-class",
    "org.apache.spark.deploy.worker.Worker",
    "spark://spark-master:7077",
    "--webui-port", "8081",
    "--cores", "2",
    "--memory", "2g"
)

& docker @runArgs
if ($LASTEXITCODE -ne 0) {
    throw "Failed to start $workerName"
}

Write-Host "Worker started. Local UI: http://localhost:$hostUiPort"
& docker ps --filter "name=$workerName"
