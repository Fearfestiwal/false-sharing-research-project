#!/usr/bin/env bash
set -euo pipefail

THREADS="${1:-4}"
ITERATIONS="${2:-1000000}"
REPS="${3:-5}"
MACHINE="${4:-macbook_m1}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "Detected OS/Arch: $(uname -s) $(uname -m)"
if command -v sysctl >/dev/null 2>&1; then
    sysctl -n machdep.cpu.brand_string 2>/dev/null || true
    echo "Hardware cache line size (bytes): $(sysctl -n hw.cachelinesize 2>/dev/null || echo 'unknown')"
fi

clang++ -O2 -std=c++17 -pthread src/benchmark_crossplatform.cpp -o benchmark_macos
./benchmark_macos "$THREADS" "$ITERATIONS" "$REPS"

mkdir -p "results/$MACHINE"
mv -f raw.csv "results/$MACHINE/raw.csv"
mv -f addresses.csv "results/$MACHINE/addresses.csv"
echo "Results saved to: results/$MACHINE"
