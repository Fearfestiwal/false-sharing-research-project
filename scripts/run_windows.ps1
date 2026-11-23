param(
    [int]$Threads = 4,
    [uint64]$Iterations = 1000000,
    [int]$Repetitions = 5,
    [string]$Machine = "muhammed_windows"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$VsDevCmd = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat"
if (Test-Path $VsDevCmd) {
    cmd /c "`"$VsDevCmd`" -arch=amd64 -no_logo >nul && cl /nologo /O2 /EHsc /std:c++17 src\benchmark_crossplatform.cpp /Fe:benchmark.exe"
} else {
    g++ -O2 -std=c++17 -pthread src/benchmark_crossplatform.cpp -o benchmark.exe
}

$OutDir = Join-Path $RepoRoot "results\$Machine"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

.\benchmark.exe $Threads $Iterations $Repetitions
Move-Item -Force "$RepoRoot\raw.csv" "$OutDir\raw.csv"
Move-Item -Force "$RepoRoot\addresses.csv" "$OutDir\addresses.csv"
Write-Host "Results saved to: $OutDir"
