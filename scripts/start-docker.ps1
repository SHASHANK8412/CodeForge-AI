<#
Starts Docker Desktop on Windows when it crashes at startup with
  "initializing Inference manager: listening on unix://.../Docker/run/dockerInference:
   remove ...: The file cannot be accessed by the system."

Docker Desktop leaves AF_UNIX socket files behind when it exits, and Windows refuses to delete
them (error 1920), so the next start fails. Renaming the folders that hold them lets Docker
create fresh ones. Nothing is deleted; old folders are kept with a ".stale-<timestamp>" suffix
and can be removed after a reboot.

Usage:  powershell -ExecutionPolicy Bypass -File scripts\start-docker.ps1
#>
$ErrorActionPreference = "Stop"
$docker = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe"
$app = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"
if (-not (Test-Path $app)) {
    $docker = Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe"
    $app = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
}

& $docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "Docker is already running."; exit 0 }

Get-Process "Docker Desktop", "com.docker.backend", "com.docker.build" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
foreach ($dir in (Join-Path $env:LOCALAPPDATA "Docker\run"), (Join-Path $env:LOCALAPPDATA "docker-secrets-engine")) {
    if (Test-Path $dir) {
        Rename-Item -LiteralPath $dir -NewName ((Split-Path $dir -Leaf) + ".stale-$stamp")
        Write-Host "Moved aside $dir"
    }
}

Start-Process $app
for ($i = 0; $i -lt 50; $i++) {
    Start-Sleep -Seconds 6
    & $docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "Docker engine is up."; exit 0 }
}
Write-Error "Docker did not start within 5 minutes; check Docker Desktop's window for errors."
