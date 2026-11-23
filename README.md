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
├── results/
│   ├── muhammed_windows/             # Machine 1: Muhammed's Windows PC (x86-64, 16 logical CPUs)
│   ├── macbook_m1/                   # Machine 2: MacBook Air (Apple M1 ARM64, 8 CPUs, 128B line)
│   └── zeynep_windows/               # Machine 3: Zeynep's Windows PC (x86-64, 6 P-core + 4 E-core)
└── .gitignore
```

## Quick Start

### Windows (PowerShell)
```powershell
# Muhammed's PC
powershell -ExecutionPolicy Bypass -File scripts/run_windows.ps1 -Threads 4 -Iterations 1000000 -Repetitions 5 -Machine muhammed_windows

# Zeynep's PC
powershell -ExecutionPolicy Bypass -File scripts/run_windows.ps1 -Threads 4 -Iterations 1000000 -Repetitions 5 -Machine zeynep_windows
```

### macOS (Terminal — Apple Silicon M1/M2/M3/M4 or Intel)
```bash
chmod +x scripts/run_macos.sh
./scripts/run_macos.sh 4 1000000 5 macbook_m1
```

Both commands generate:
- `raw.csv` — All warm-up (`rep = -1`) and measured (`rep >= 0`) runs with correctness verification.
- `addresses.csv` — Verified runtime memory addresses, `sizeof`, `alignof`, and 64B/128B cache-line indices.

## Cross-Architecture Validation Summary (4 Threads, 1M Iterations, 5 Measured Reps + 1 Warm-up)

| Mode & Batch | Windows x86-64 (16 logical CPUs, MSVC) | Apple M1 ARM64 (8 logical CPUs, `hw.cachelinesize=128`, clang++) |
| :--- | :--- | :--- |
| `store`, `B=1` | `0.95 → 0.94 ms` (`1.01x`, 128B: `0.93 ms`) | `1.40–1.41 → 1.03 ms` (`1.36x`, 128B: `1.03–1.04 ms`) |
| `store`, `B=16` | `0.92 → 0.92 ms` (`1.00x`) | `1.03–1.04 → 1.02–1.04 ms` (`1.00x`) |
| `atomic`, `B=1` | `41.32 → 4.01 ms` (**`10.30x`**, 128B: `3.92 ms`) | `55.07–64.46 → 1.04 ms` (**`53.03x–61.96x`**, 128B: `1.04–1.05 ms`) |
| `atomic`, `B=16` | `1.64 → 0.95 ms` (**`1.72x`**, 128B: `0.92 ms`) | `3.96–4.01 → 1.03–1.04 ms` (**`3.82x–3.89x`**) |
| `atomic`, `B=256` | `0.93 → 0.93 ms` (`1.00x`) | `1.03 → 1.03 ms` (`1.00x`) |
| `atomic`, `Local (end)` | `0.92 → 0.94 ms` (`0.97x`) | `1.03 → 1.03–1.04 ms` (`0.99x–1.00x`) |

### Key Takeaways
1. **Consistent across ISAs, OSes, and compilers:** On both Windows (x86-64, MSVC) and macOS (Apple M1 ARM64, clang++), padding delivers large speedups only under frequent atomic updates (`B=1`, `B=16`) and vanishes when updates become infrequent (`B=256`, `Local`).
2. **64B vs. 128B on Apple M1:** Even though Apple M1 reports `hw.cachelinesize = 128` bytes, `alignas(64)` already matched `alignas(128)` (`1.04 ms` vs. `1.04–1.05 ms`) on this 4-thread workload, demonstrating the importance of empirical measurement over assuming hardware padding constants.

