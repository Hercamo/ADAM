<#
.SYNOPSIS
    ADAM Deployment Status Dashboard (PowerShell)

.DESCRIPTION
    Renders a one-shot health dashboard for an ADAM SpecPack deployment:
    container states, service-endpoint probes, Flight Recorder summary,
    agent-mesh totals.

    Origin: ADAM v1.7 / Sovereignty Connector 1.2 / audit log Section 0210.
    Canonical replacement for the deployment-emitted status.ps1 that
    suffered from the Write-Host array-join defect documented in 0210.

.PARAMETER DeploymentRoot
    Path to the deployment root (the directory containing iac/, agents/,
    flight_recorder/, etc.). Defaults to D:\ADAM\deployment\<company>.

.PARAMETER ComposeFile
    Optional path to a docker-compose.yml. If supplied, `docker compose ps`
    is used. If omitted, falls back to `docker ps` filtered by the ADAM label.

.NOTES
    The Containers block uses an EXPLICIT array-join on
    [Environment]::NewLine before passing to Write-Host. Do NOT
    "simplify" this back to `Write-Host $array` — PowerShell joins
    array arguments with $OFS (default single space) and the entire
    block collapses to one line. See audit log Section 0210 / Issue A.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $DeploymentRoot,

    [string] $ComposeFile = $null
)

$ErrorActionPreference = "Continue"

function Write-Section {
    param([string] $Title)
    Write-Host ""
    Write-Host ("== $Title ==")
}

function Probe-Endpoint {
    param([string] $Url, [string] $Label)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400) {
            Write-Host ("  {0,-25}  [OK  ]  {1}" -f $Label, $Url)
        } else {
            Write-Host ("  {0,-25}  [WARN]  {1}  (HTTP {2})" -f $Label, $Url, $r.StatusCode)
        }
    } catch {
        Write-Host ("  {0,-25}  [DOWN]  {1}  ({2})" -f $Label, $Url, $_.Exception.Message)
    }
}

Write-Section "Containers"
# IMPORTANT: docker ps with --format returns a STRING ARRAY (one element per row).
# `Write-Host $psOut` would join with $OFS = ' ' and collapse all rows onto one
# line. ALWAYS use `-join [Environment]::NewLine` to preserve row breaks.
# Audit log Section 0210 / Issue A. Do NOT simplify this.
if ($ComposeFile -and (Test-Path $ComposeFile)) {
    $psOut = & docker compose -f $ComposeFile ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
} else {
    $psOut = & docker ps --filter "label=adam.deployment" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}
Write-Host ($psOut -join [Environment]::NewLine)

Write-Section "Service Endpoints"
Probe-Endpoint -Url "http://localhost:8181/health"        -Label "OPA"
Probe-Endpoint -Url "http://localhost:8200/health"        -Label "Flight Recorder"
Probe-Endpoint -Url "http://localhost:8210/health"        -Label "BOSS Scorer"
Probe-Endpoint -Url "http://localhost:8220/health"        -Label "Exception Router"
Probe-Endpoint -Url "http://localhost:8230/health"        -Label "Mesh Heartbeat"

Write-Section "Flight Recorder Summary"
$frPath = Join-Path $DeploymentRoot "flight_recorder\flight_recorder.py"
if (Test-Path $frPath) {
    $verifyOut = & python $frPath verify 2>&1
    Write-Host ($verifyOut -join [Environment]::NewLine)
} else {
    Write-Host "  Flight Recorder script not found at $frPath"
}

Write-Section "Agent Mesh Totals"
$registryPath = Join-Path $DeploymentRoot "agents\agent-registry.json"
if (Test-Path $registryPath) {
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json
    $total = ($registry.agents | Measure-Object).Count
    $byClass = $registry.agents | Group-Object -Property class | Sort-Object Name
    Write-Host ("  Total agents: {0}" -f $total)
    foreach ($g in $byClass) {
        Write-Host ("    {0,-30} {1,3}" -f $g.Name, $g.Count)
    }
} else {
    Write-Host "  Agent registry not found at $registryPath"
}

Write-Host ""
Write-Host "Status dashboard complete."
