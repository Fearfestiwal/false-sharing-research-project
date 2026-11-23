# When More Threads Become Slower: Investigating False Sharing and Its Mitigation

**Course:** Architecture of Computers — Student Research Challenge 2026 (Vistula University)  
**Team (Group-4):** Zeynep Uyan (`75616`), Muhammed Enes Aksoy (`75569`)

## Overview

This repository contains the reproducible cross-platform C++ benchmark and step-by-step learning exercises for investigating **false sharing** in multithreaded counters and separating:
1. **Memory layout effects (Padding):** Adjacent 8-byte counters vs. `alignas(64)` (x86-64 cache line) vs. `alignas(128)` (Apple Silicon ARM64 cache line).
2. **Update frequency effects (Batching / Local Accumulation):** Publishing every `1`, `16`, `256` iterations vs. once at the end.
3. **Memory operation type:** Normal `volatile` stores vs. `std::atomic::exchange(..., std::memory_order_relaxed)`.

## Repository Structure

```text
├── src/
│   └── benchmark_crossplatform.cpp   # Full Windows / macOS / Linux benchmark (8B vs 64B vs 128B)
├── scripts/
│   ├── run_windows.ps1               # Build & run on Windows (MSVC or g++)
│   └── run_macos.sh                  # Build & run on macOS (Apple Silicon / Intel clang++)
└── .gitignore
```

## Quick Start

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_windows.ps1 -Threads 4 -Iterations 1000000 -Repetitions 5
```

### macOS (Terminal — Apple Silicon M1/M2/M3/M4 or Intel)
```bash
chmod +x scripts/run_macos.sh
./scripts/run_macos.sh 4 1000000 5
```

Both commands generate:
- `raw.csv` — All warm-up (`rep = -1`) and measured (`rep >= 0`) runs with correctness verification.
- `addresses.csv` — Verified runtime memory addresses, `sizeof`, `alignof`, and 64B/128B cache-line indices.
