param([UInt64]$Iterations=16000000,[int]$Repetitions=9,[ValidateSet('store','atomic')][string]$Mode='store')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runDirectory = Join-Path $projectRoot ('runs/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $runDirectory 'data') -Force | Out-Null
Push-Location $runDirectory
try {
    Get-Date -Format o | Set-Content data/start_time.txt
    powercfg /getactivescheme | Out-File data/power_plan.txt
    & (Join-Path $projectRoot 'benchmark.exe') $Iterations $Repetitions $Mode
    if ($LASTEXITCODE -ne 0) { throw "Benchmark failed: $LASTEXITCODE" }
    Get-Date -Format o | Set-Content data/end_time.txt
    Write-Output "Results saved separately: $runDirectory"
} finally { Pop-Location }
