param(
    [int]$Threads = 4,
    [uint64]$Iterations = 1000000,
    [int]$Repetitions = 5
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

.\benchmark.exe $Threads $Iterations $Repetitions
