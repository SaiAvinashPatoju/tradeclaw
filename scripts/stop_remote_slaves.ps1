$ErrorActionPreference = "Continue"

$workers = @(
    "tradeclaw-remote-worker-1",
    "tradeclaw-remote-worker-2"
)

foreach ($worker in $workers) {
    Write-Host "Stopping $worker ..."
    & docker rm -f $worker *> $null
}

Write-Host "Remote worker cleanup complete."
