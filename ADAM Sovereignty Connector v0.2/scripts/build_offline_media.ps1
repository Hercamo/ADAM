# Build the ADAM_Offline_Media folder on a *connected* Windows workstation.
# Run this once with internet access, then copy the resulting folder to the
# air-gapped target host next to adam_sovereignty_connector.exe.
#
# Requirements on the build host:
#   - PowerShell 7+
#   - Docker Desktop installed and running
#   - ~30 GB free disk
[CmdletBinding()]
param(
    [string]$Output = "$PSScriptRoot\..\ADAM_Offline_Media",
    [string]$KubectlVersion = "v1.30.0",
    [string]$HelmVersion = "v3.14.4",
    [string]$K3dVersion = "v5.6.3",
    [string]$DockerDesktopUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
)

$ErrorActionPreference = "Stop"
$binaries = Join-Path $Output "binaries"
$images = Join-Path $Output "images"
New-Item -ItemType Directory -Force -Path $binaries,$images | Out-Null

Write-Host "==> downloading kubectl $KubectlVersion"
Invoke-WebRequest "https://dl.k8s.io/release/$KubectlVersion/bin/windows/amd64/kubectl.exe" `
    -OutFile "$binaries\kubectl.exe"

Write-Host "==> downloading helm $HelmVersion"
$helmZip = "$env:TEMP\helm-$HelmVersion.zip"
Invoke-WebRequest "https://get.helm.sh/helm-$HelmVersion-windows-amd64.zip" -OutFile $helmZip
Expand-Archive -Force -Path $helmZip -DestinationPath $env:TEMP\helmx
Copy-Item "$env:TEMP\helmx\windows-amd64\helm.exe" "$binaries\helm.exe"

Write-Host "==> downloading k3d $K3dVersion"
Invoke-WebRequest "https://github.com/k3d-io/k3d/releases/download/$K3dVersion/k3d-windows-amd64.exe" `
    -OutFile "$binaries\k3d.exe"

Write-Host "==> downloading Docker Desktop installer"
Invoke-WebRequest $DockerDesktopUrl -OutFile "$binaries\docker-desktop-installer.exe"

Write-Host "==> saving k3d/k3s base images"
docker pull rancher/k3s:v1.29.5-k3s1
docker pull ghcr.io/k3d-io/k3d-proxy:$K3dVersion
docker save rancher/k3s:v1.29.5-k3s1 ghcr.io/k3d-io/k3d-proxy:$K3dVersion `
    -o "$images\k3d-bundle.tar"

$adamImages = @(
    @{ name = "adam-core-engine";            tag = "adam/core-engine:0.1" }
    @{ name = "adam-boss-score";             tag = "adam/boss-score:0.1" }
    @{ name = "adam-flight-recorder";        tag = "adam/flight-recorder:0.1" }
    @{ name = "adam-constitution-director";  tag = "adam/director:0.1" }
    @{ name = "adam-agent";                  tag = "adam/agent:0.1" }
)

$placeholderDir = Join-Path $PSScriptRoot "placeholder_images"
if (-not (Test-Path $placeholderDir)) {
    Write-Host "==> writing placeholder FastAPI Dockerfile"
    New-Item -ItemType Directory -Force -Path $placeholderDir | Out-Null
    @"
FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi uvicorn
WORKDIR /app
COPY app.py /app/app.py
ENV PORT=8080
EXPOSE 8080
CMD [`"uvicorn`", `"app:app`", `"--host`", `"0.0.0.0`", `"--port`", `"8080`"]
"@ | Set-Content "$placeholderDir\Dockerfile"

    @"
import os
from fastapi import FastAPI
app = FastAPI()
role = os.environ.get('DIRECTOR_ROLE') or os.environ.get('AGENT_ORDINAL') or 'generic'

@app.get('/health')
def health():
    return {'ok': True, 'role': role}

@app.get('/')
def root():
    return {'service': 'adam-placeholder', 'role': role}
"@ | Set-Content "$placeholderDir\app.py"
}

foreach ($img in $adamImages) {
    Write-Host "==> building $($img.tag)"
    docker build -t $img.tag $placeholderDir
    docker save $img.tag -o (Join-Path $images "$($img.name).tar")
}

Write-Host "==> writing MANIFEST.json"
$manifest = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    versions = @{
        kubectl = $KubectlVersion
        helm    = $HelmVersion
        k3d     = $K3dVersion
    }
    binaries = (Get-ChildItem $binaries | ForEach-Object { @{
        name = $_.Name
        size = $_.Length
        sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    } })
    images = (Get-ChildItem $images | ForEach-Object { @{
        name = $_.Name
        size = $_.Length
        sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    } })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content "$Output\MANIFEST.json"

Write-Host ""
Write-Host "Offline media ready at: $Output"
Write-Host "Next: copy this folder to the air-gapped host alongside adam_sovereignty_connector.exe."
