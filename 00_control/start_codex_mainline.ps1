param(
    [switch]$FullGate
)

$ErrorActionPreference = "Stop"
chcp 65001 | Out-Null
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $Root

Write-Host "== Codex mainline startup =="
Write-Host "Root: project workspace"

py -3.12 .\30_extraction\scripts\build_codex_mainline_context.py
py -3.12 .\30_extraction\scripts\review_handoff_and_encoding_health.py

if ($FullGate) {
    py -3.12 .\30_extraction\scripts\verify_project_implementation.py
}

Write-Host "== Mainline context ready =="
Write-Host "Read: 40_quality_evidence/codex_mainline_context_20260604.md"
Write-Host "Next: follow the global AI simulation rebaseline; continue AI workbench, method/data object pool, simulation task entry, and legacy artifact trust mapping."
