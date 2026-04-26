<#
.SYNOPSIS
    ADAM Rego Preflight Validator (PowerShell)

.DESCRIPTION
    Runs `opa parse` and `opa check --v1-compatible` against every .rego file
    under the supplied root directory BEFORE the bootstrap script applies the
    bundle to a live OPA service.

    Origin: ADAM v1.7 / Sovereignty Connector 1.2 / audit log Section 0210.
    The NetStreamX initial deployment took 7 OPA-restart iterations to clear
    a sequence of grammar booby-traps that this validator catches in one shot.

.PARAMETER PolicyRoot
    Path to the directory containing .rego files. Defaults to
    `D:\ADAM\deployment\<company>\rego` if not specified.

.PARAMETER OpaImage
    Docker image to use for parse + check. Defaults to openpolicyagent/opa:0.64.1.
    Pinned because earlier OPA versions do not support --v1-compatible mode.

.PARAMETER FlightRecorderPath
    Optional path to flight_recorder.py. If supplied, emits a Flight Recorder
    event (preflight_passed or preflight_failed) with the result.

.EXAMPLE
    .\validate-rego.ps1 -PolicyRoot D:\ADAM\deployment\NetStreamX\rego

.EXAMPLE
    .\validate-rego.ps1 -PolicyRoot .\rego -FlightRecorderPath .\flight_recorder\flight_recorder.py

.NOTES
    Exits 0 on clean validation, non-zero on any failure. Suitable for use as
    a CI gate or pre-bootstrap check.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $PolicyRoot,

    [string] $OpaImage = "openpolicyagent/opa:0.64.1",

    [string] $FlightRecorderPath = $null
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string] $Title)
    Write-Host ""
    Write-Host ("=" * 70)
    Write-Host " $Title"
    Write-Host ("=" * 70)
}

function Emit-FlightRecorder {
    param(
        [string] $EventType,
        [string] $Summary
    )
    if (-not $FlightRecorderPath) { return }
    if (-not (Test-Path $FlightRecorderPath)) {
        Write-Warning "Flight Recorder script not found at $FlightRecorderPath; skipping FR emit."
        return
    }
    $payload = @{
        validator      = "scripts/preflight/validate-rego.ps1"
        adam_version   = "1.7"
        opa_image      = $OpaImage
        v1_compatible  = $true
        summary        = $Summary
    } | ConvertTo-Json -Compress
    & python $FlightRecorderPath append `
        --event-type $EventType `
        --agent-id meta-integrity `
        --payload $payload | Out-Null
}

Write-Section "ADAM Rego Preflight Validator"
Write-Host "Policy root : $PolicyRoot"
Write-Host "OPA image   : $OpaImage"
Write-Host "v1 mode     : enabled (--v1-compatible)"

if (-not (Test-Path $PolicyRoot)) {
    Write-Error "Policy root not found: $PolicyRoot"
    Emit-FlightRecorder -EventType "preflight_failed" -Summary "Policy root missing"
    exit 2
}

$regoFiles = Get-ChildItem -Path $PolicyRoot -Recurse -Filter "*.rego" -File
if ($regoFiles.Count -eq 0) {
    Write-Warning "No .rego files found under $PolicyRoot"
    Emit-FlightRecorder -EventType "preflight_failed" -Summary "No rego files found"
    exit 3
}

Write-Host "Found $($regoFiles.Count) .rego file(s) to validate:"
foreach ($f in $regoFiles) {
    Write-Host "  - $($f.FullName)"
}

# Verify Docker is available
try {
    $null = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "docker version failed" }
} catch {
    Write-Error "Docker is not available. The Rego validator requires Docker to run the OPA image."
    Emit-FlightRecorder -EventType "preflight_failed" -Summary "Docker unavailable"
    exit 4
}

Write-Section "Stage 1 — opa parse (per file)"
$parseFailed = $false
foreach ($f in $regoFiles) {
    $relPath = (Resolve-Path $f.FullName).Path
    $mountDir = Split-Path -Parent $relPath
    $fileName = Split-Path -Leaf $relPath
    Write-Host -NoNewline "  [parse] $fileName ... "
    $out = docker run --rm -v "${mountDir}:/p:ro" $OpaImage parse "/p/$fileName" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK"
    } else {
        Write-Host "FAIL"
        Write-Host ($out -join [Environment]::NewLine)  # array-join: see status.ps1 fix in audit 0210
        $parseFailed = $true
    }
}

if ($parseFailed) {
    Write-Section "PREFLIGHT FAILED at parse stage"
    Emit-FlightRecorder -EventType "preflight_failed" -Summary "Rego parse stage failed"
    exit 10
}

Write-Section "Stage 2 — opa check --v1-compatible (whole bundle)"
$checkOut = docker run --rm -v "${PolicyRoot}:/p:ro" $OpaImage check --v1-compatible /p 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [check] bundle ... OK"
} else {
    Write-Host "  [check] bundle ... FAIL"
    Write-Host ($checkOut -join [Environment]::NewLine)
    Emit-FlightRecorder -EventType "preflight_failed" -Summary "Rego check stage failed"
    exit 11
}

Write-Section "PREFLIGHT PASSED"
Write-Host "All $($regoFiles.Count) rego file(s) parse cleanly under v1-compatible mode."
Write-Host "Bundle is safe to load into a live OPA service invoked with --v1-compatible."
Emit-FlightRecorder -EventType "preflight_passed" -Summary "All rego files validated"
exit 0
