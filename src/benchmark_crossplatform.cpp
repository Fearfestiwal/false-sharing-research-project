#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <string>
#include <thread>
#include <tuple>
#include <vector>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

constexpr std::uint64_t LCG_A = 6364136223846793005ULL;
constexpr std::uint64_t LCG_C = 1442695040888963407ULL;

// Normal store layouts (volatile prevents dead-store elimination)
struct AdjacentStore { volatile std::uint64_t value = 0; };
struct alignas(64) Padded64Store { volatile std::uint64_t value = 0; };
struct alignas(128) Padded128Store { volatile std::uint64_t value = 0; };

// Atomic exchange layouts
struct AdjacentAtomic { std::atomic<std::uint64_t> value{0}; };
struct alignas(64) Padded64Atomic { std::atomic<std::uint64_t> value{0}; };
struct alignas(128) Padded128Atomic { std::atomic<std::uint64_t> value{0}; };

std::uint64_t expected_lcg(std::uint64_t seed, std::uint64_t iterations) {
    std::uint64_t x = seed;
    for (std::uint64_t i = 0; i < iterations; ++i) {
        x = x * LCG_A + LCG_C;
    }
    return x;
}

double compute_median(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    const std::size_t n = values.size();
    return (n % 2 == 1) ? values[n / 2] : 0.5 * (values[n / 2 - 1] + values[n / 2]);
}

template <typename CounterType, bool IsAtomic>
std::pair<double, bool> run_trial(
    int num_threads,
    std::uint64_t iterations,
    std::uint64_t batch,
    const std::string& layout_name,
    std::ofstream* addr_csv) {
    std::vector<CounterType> counters(num_threads);

    if (addr_csv != nullptr) {
        for (int id = 0; id < num_threads; ++id) {
            const auto addr = reinterpret_cast<std::uintptr_t>(&counters[id].value);
            (*addr_csv) << layout_name << "," << sizeof(CounterType) << "," << alignof(CounterType)
                        << "," << id << ",0x" << std::hex << addr << std::dec
                        << "," << (addr % 64) << "," << (addr / 64)
                        << "," << (addr % 128) << "," << (addr / 128) << "\n";
        }
    }

    std::atomic<int> ready{0};
    std::atomic<bool> go{false};
    std::vector<std::thread> workers;
    workers.reserve(num_threads);

    for (int id = 0; id < num_threads; ++id) {
        workers.emplace_back([&, id]() {
            std::uint64_t x = 1000ULL + static_cast<std::uint64_t>(id);
            ready.fetch_add(1, std::memory_order_release);
            while (!go.load(std::memory_order_acquire)) {
            }

            for (std::uint64_t s = 0; s < iterations; s += batch) {
                const std::uint64_t e = std::min(iterations, s + batch);
                for (std::uint64_t i = s; i < e; ++i) {
                    x = x * LCG_A + LCG_C;
                }
                if constexpr (IsAtomic) {
                    counters[id].value.exchange(x, std::memory_order_relaxed);
                } else {
                    counters[id].value = x;
                }
            }
        });
    }

    while (ready.load(std::memory_order_acquire) < num_threads) {
    }

    const auto t0 = std::chrono::steady_clock::now();
    go.store(true, std::memory_order_release);
    for (auto& w : workers) {
        w.join();
    }
    const auto t1 = std::chrono::steady_clock::now();

    bool ok = true;
    for (int id = 0; id < num_threads; ++id) {
        const std::uint64_t exp = expected_lcg(1000ULL + static_cast<std::uint64_t>(id), iterations);
        std::uint64_t got = 0;
        if constexpr (IsAtomic) {
            got = counters[id].value.load(std::memory_order_relaxed);
        } else {
            got = counters[id].value;
        }
        if (got != exp) {
            ok = false;
        }
    }

    const double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return {ms, ok};
}

struct Config {
    std::string mode;
    std::string layout;
    std::uint64_t batch;
};

int main(int argc, char* argv[]) {
    int num_threads = 4;
    std::uint64_t iterations = 1'000'000;
    int reps = 5;

    if (argc >= 2) num_threads = std::max(1, std::stoi(argv[1]));
    if (argc >= 3) iterations = std::stoull(argv[2]);
    if (argc >= 4) reps = std::max(1, std::stoi(argv[3]));

    const unsigned hw = std::thread::hardware_concurrency();
    std::cout << "=== False Sharing Cross-Platform Benchmark (8B vs 64B vs 128B) ===\n";
    std::cout << "Logical CPUs : " << hw << "\n";
    std::cout << "Threads      : " << num_threads << "\n";
    std::cout << "Iterations   : " << iterations << " per thread (weak scaling)\n";
    std::cout << "Repetitions  : " << reps << " (+1 warmup)\n\n";

    std::vector<Config> configs;
    const std::vector<std::uint64_t> batches = {1ULL, 16ULL, 256ULL, iterations};
    for (const std::string& mode : {"store", "atomic"}) {
        for (const std::string& layout : {"adjacent_8B", "padded_64B", "padded_128B"}) {
            for (std::uint64_t b : batches) {
                configs.push_back({mode, layout, b});
            }
        }
    }

    std::mt19937 rng(42);
    std::shuffle(configs.begin(), configs.end(), rng);

    std::ofstream raw_csv("raw.csv");
    raw_csv << "rep,is_warmup,threads,iterations,mode,layout,batch,ms,correct\n";

    std::ofstream addr_csv("addresses.csv");
    addr_csv << "layout,sizeof_bytes,alignof_bytes,thread_id,address,mod64,line64,mod128,line128\n";

    std::map<std::tuple<std::string, std::string, std::uint64_t>, std::vector<double>> results;
    bool recorded_addresses[3] = {false, false, false};

    for (int rep = -1; rep < reps; ++rep) {
        const bool warmup = (rep == -1);
        for (const auto& c : configs) {
            std::pair<double, bool> res{0.0, false};
            std::ofstream* addr_ptr = nullptr;

            if (c.mode == "store") {
                if (c.layout == "adjacent_8B") {
                    if (!recorded_addresses[0]) { addr_ptr = &addr_csv; recorded_addresses[0] = true; }
                    res = run_trial<AdjacentStore, false>(num_threads, iterations, c.batch, c.layout, addr_ptr);
                } else if (c.layout == "padded_64B") {
                    if (!recorded_addresses[1]) { addr_ptr = &addr_csv; recorded_addresses[1] = true; }
                    res = run_trial<Padded64Store, false>(num_threads, iterations, c.batch, c.layout, addr_ptr);
                } else {
                    if (!recorded_addresses[2]) { addr_ptr = &addr_csv; recorded_addresses[2] = true; }
                    res = run_trial<Padded128Store, false>(num_threads, iterations, c.batch, c.layout, addr_ptr);
                }
            } else {
                if (c.layout == "adjacent_8B") {
                    res = run_trial<AdjacentAtomic, true>(num_threads, iterations, c.batch, c.layout, nullptr);
                } else if (c.layout == "padded_64B") {
                    res = run_trial<Padded64Atomic, true>(num_threads, iterations, c.batch, c.layout, nullptr);
                } else {
                    res = run_trial<Padded128Atomic, true>(num_threads, iterations, c.batch, c.layout, nullptr);
                }
            }

            raw_csv << rep << "," << (warmup ? 1 : 0) << "," << num_threads << ","
                    << iterations << "," << c.mode << "," << c.layout << "," << c.batch << ","
                    << std::fixed << std::setprecision(4) << res.first << ","
                    << (res.second ? "OK" : "FAIL") << "\n";

            if (!warmup) {
                results[{c.mode, c.layout, c.batch}].push_back(res.first);
            }
        }
    }

    raw_csv.close();
    addr_csv.close();

    for (const std::string& mode : {"store", "atomic"}) {
        std::cout << "[" << mode << "] Median completion time (ms)\n";
        std::cout << "  Batch        | Adj 8B (ms) | Pad 64B (ms) | Pad 128B (ms) | 8B/64B | 8B/128B\n";
        std::cout << "  -------------+-------------+--------------+---------------+--------+--------\n";
        for (std::uint64_t b : batches) {
            const double m8   = compute_median(results[{mode, "adjacent_8B", b}]);
            const double m64  = compute_median(results[{mode, "padded_64B", b}]);
            const double m128 = compute_median(results[{mode, "padded_128B", b}]);
            const std::string blabel = (b == iterations) ? "Local (end)" : ("B=" + std::to_string(b));
            std::cout << "  " << std::left << std::setw(12) << blabel
                      << " | " << std::right << std::setw(11) << std::fixed << std::setprecision(2) << m8
                      << " | " << std::setw(12) << m64
                      << " | " << std::setw(13) << m128
                      << " | " << std::setw(5) << (m8 / m64) << "x"
                      << " | " << std::setw(6) << (m8 / m128) << "x\n";
        }
        std::cout << "\n";
    }

    std::cout << "Saved raw measurements to raw.csv and memory alignment proof to addresses.csv\n";
    return 0;
}
