$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    $zigCompiler = Join-Path $projectRoot 'tools/zig-windows-x86_64-0.13.0/zig.exe'
    if (!(Test-Path $zigCompiler)) { throw 'Extract official Zig 0.13.0 for Windows x86_64 under tools first. See README.md.' }
    & $zigCompiler c++ src/benchmark.cpp -O2 -std=c++17 -fno-unroll-loops -fno-vectorize -fno-slp-vectorize -o benchmark.exe
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    & $zigCompiler c++ src/benchmark.cpp -O2 -std=c++17 -fno-unroll-loops -fno-vectorize -fno-slp-vectorize -S -o data/current_benchmark.s
    if ($LASTEXITCODE -ne 0) { throw 'Assembly generation failed' }
} finally { Pop-Location }
