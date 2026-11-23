param(
    [int]$Threads = 4,
    [uint64]$Iterations = 1000000,
    [int]$Repetitions = 5,
    [string]$Machine = "muhammed_windows"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$compiled = $false

# 1) Try Visual Studio (any edition / BuildTools) via vswhere.exe
$VsWhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $VsWhere) {
    $vsPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vsPath) {
        $VsDevCmd = Join-Path $vsPath "Common7\Tools\VsDevCmd.bat"
        if (Test-Path $VsDevCmd) {
            Write-Host "[INFO] Compiling with MSVC ($vsPath)..."
            cmd /c "`"$VsDevCmd`" -arch=amd64 -no_logo >nul && cl /nologo /O2 /EHsc /std:c++17 src\benchmark_crossplatform.cpp /Fe:benchmark.exe"
            if ($LASTEXITCODE -eq 0) { $compiled = $true }
        }
    }
}

# 2) Try g++ (PATH or common MSYS2 / MinGW / Scoop / WinLibs locations)
if (-not $compiled) {
    $gppCandidates = @(
        (Get-Command g++ -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "C:\msys64\ucrt64\bin\g++.exe",
        "C:\msys64\mingw64\bin\g++.exe",
        "C:\mingw64\bin\g++.exe",
        "C:\MinGW\bin\g++.exe",
        "$env:USERPROFILE\scoop\shims\g++.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($gppCandidates.Count -gt 0) {
        $gpp = $gppCandidates[0]
        Write-Host "[INFO] Compiling with g++ ($gpp)..."
        & $gpp -O2 -std=c++17 -pthread src/benchmark_crossplatform.cpp -o benchmark.exe
        if ($LASTEXITCODE -eq 0) { $compiled = $true }
    }
}

# 3) Try clang++ (PATH or LLVM default install)
if (-not $compiled) {
    $clangCandidates = @(
        (Get-Command clang++ -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "C:\Program Files\LLVM\bin\clang++.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($clangCandidates.Count -gt 0) {
        $clang = $clangCandidates[0]
        Write-Host "[INFO] Compiling with clang++ ($clang)..."
        & $clang -O2 -std=c++17 src/benchmark_crossplatform.cpp -o benchmark.exe
        if ($LASTEXITCODE -eq 0) { $compiled = $true }
    }
}

$ExeToRun = ".\benchmark.exe"
if (-not $compiled) {
    $FallbackExe = Join-Path $RepoRoot "bin\benchmark_win64.exe"
    if (Test-Path $FallbackExe) {
        Write-Host "[INFO] No local C++ compiler found; using prebuilt static binary: bin\benchmark_win64.exe"
        $ExeToRun = $FallbackExe
    } else {
        Write-Error "No C++ compiler found and bin\benchmark_win64.exe is missing."
        exit 1
    }
}

$OutDir = Join-Path $RepoRoot "results\$Machine"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

& $ExeToRun $Threads $Iterations $Repetitions
Move-Item -Force "$RepoRoot\raw.csv" "$OutDir\raw.csv"
Move-Item -Force "$RepoRoot\addresses.csv" "$OutDir\addresses.csv"
Write-Host "Results saved to: $OutDir"
