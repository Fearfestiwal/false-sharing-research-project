# When More Threads Become Slower

Separating memory layout and publication frequency in a hybrid-CPU microbenchmark

**Zeynep Uyan (75616) and Muhammed Enes Aksoy (75569)**  
Architecture of Computers | Group-4 | Vistula University  
November 2026

### Abstract

False sharing and frequent publication are distinct sources of multithreaded overhead. This study investigates their interaction using a state-publication microbenchmark on an Intel Core i7-13620H running Windows 11, supplemented by cross-architecture validation on a second x86-64 Windows laptop and an Apple M1 ARM64 MacBook Air. Aligned 8-byte and 64-byte layouts are compared across worker counts, publication intervals and hybrid-core placements. An initial ordinary-store experiment collected 792 measurements. A subsequent workload-matched extension compared ordinary stores and relaxed atomic exchanges, collecting another 1,232 measurements. All correctness, affinity and alignment checks passed. For six physical performance-core workers publishing every iteration, the matched ordinary-store layout ratio was 1.04, with a descriptive bootstrap interval spanning one. The atomic-exchange ratio was 8.50; at 256 iterations per publication it fell to 0.93, with an interval spanning one. Cross-machine validation confirmed the same frequency-dependent pattern across both x86-64 (MSVC, 9.68x–10.30x at B=1; ~1.00x at B=256) and Apple M1 ARM64 (clang++, 53.03x–61.96x at B=1; 1.00x at B=256). The extension was motivated by the initial findings and is explicitly exploratory. These results show why publication primitive, placement and update interval must be reported alongside a padding benchmark. Batching also changes loop overhead, so its benefit cannot be attributed solely to fewer memory instructions. No coherence-event counters were collected, and the primary study used one active laptop session. The findings establish conditional timing contrasts rather than a universal speedup or direct measurement of coherence traffic. Code, raw measurements and reproduction instructions are publicly archived at https://github.com/Fearfestiwal/false-sharing-research-project.

### 1  Motivation and question

Padding changes where workers publish; local accumulation changes how often they publish. Comparing these strategies without holding publication frequency constant confounds two interventions. We ask: **How do placement, worker count and publication interval change the benefit of cache-line separation, and what additional timing change remains when publication is batched in an already separated layout?**

Figure 1. Four-worker layout schematic. Measurements use verified addresses; twelve adjacent states occupy two lines, not one.

## 2  Background and experimental design

Bolosky and Scott describe false sharing as accesses to distinct objects within a coherence block that induce unnecessary coherence activity, while emphasizing the difficulty of quantifying it [1]. Intel demonstrates a profiling-led workflow for identifying contended data and evaluating alignment changes [2]. These sources establish the phenomenon; this study does not claim to discover it. Its contribution is a documented comparison of layout and publication interventions on a hybrid laptop CPU, verified across two additional systems spanning x86-64 and ARM64. Sections 2–4 report the initial ordinary-store experiment; Section 5 describes the subsequent matched extension and cross-architecture validation without pooling timings across separate protocols.

Hybrid-core topology must be enumerated rather than inferred from a single logical-processor count [3]. Windows exposes physical-core relationships through GetLogicalProcessorInformationEx [4]. We combine those relationships with per-logical-CPU CPUID leaf 0x1A to distinguish P cores (type 0x40) and E cores (type 0x20). The measured mapping contains six P cores with two SMT siblings each and four E cores.

| Factor | Levels and control |
| --- | --- |
| Layout | 8-byte stride (adjacent); 64-byte stride (separated). Allocation base aligned to 64 bytes. |
| Publication interval B | 1, 16, 256, N=16,000,000 iterations; last level publishes only the final state. |
| P physical | 1, 2, 4, 6 workers; CPUs selected from [0,2,4,6,8,10]. |
| P SMT | 2, 4, 8, 12 workers; prefixes of CPUs [0,1,...,11], filling sibling pairs first. |
| E physical | 1, 2, 4 workers; prefixes of CPUs [12,13,14,15]. |
| Replication | One warm-up and nine measured executions per condition; 88 conditions total. |

### 2.1  Workload and equal-work control

Each worker owns a separate uint64_t state seeded with its worker index plus one. Each logical iteration computes x = 6364136223846793005*x + 1442695040888963407 modulo 2^64. The dependent recurrence prevents trivial constant-counter substitution and provides a deterministic final state. Every B iterations, the worker writes its current state to its assigned slot. All configurations use the same recurrence and N iterations per worker; the arithmetic result is checked independently after completion.

This is a synthetic state-publication workload, not an atomic fetch-add counter. It operationalizes the proposal using reproducible checkpoint stores. The final-only case represents local accumulation; joining and any final reduction are outside the timed interval. No claim about a complete application reduction follows from these measurements.

### 2.2  What the interventions isolate

At a fixed B and placement, changing stride modifies the address calculation before the worker loop but leaves publication count and arithmetic work unchanged. This is the primary layout contrast. Changing B in the separated layout evaluates batching when inter-worker line sharing has been removed. That contrast changes both publication count and outer-loop overhead; it cannot identify the cost of stores alone.

## 3  Measurement and primary results

### 3.1  Execution protocol

The compiler is Zig 0.13.0 with its bundled Clang toolchain, C++17 and -O2. Loop unrolling and loop/SLP vectorization are disabled to retain a comparable dependent arithmetic loop. Volatile stores preserve publications; volatile is not used for synchronization, consistent with LLVM guidance [5]. Atomics implement the start and completion gate, and a Win32 event wakes the controller. Each worker sets a single-CPU affinity mask before the start gate; failure aborts the run.

Timing uses std::chrono::steady_clock from immediately before start release until the completion event wakes the controller. It excludes thread construction, joins and correctness checks, but includes start-release and completion/event overhead. Configurations are shuffled with seed 20261112, then partitioned so all warm-ups precede measurements. No outliers are removed. Each condition is summarized by its median and interquartile range (IQR). Ratios use independent bootstrap resampling of the nine observations per cell (5,000 resamples; fixed seed). Intervals are descriptive, assume exchangeability and do not account for session-level dependence or multiple comparisons.

![Figure 2. Per-iteration publication (B=1). Error bars show IQR, not confidence intervals. Work is fixed per worker; increasing thread count increases total work.](figures/scaling.png)

### 3.2  Layout effects at equal publication frequency

For six physical P-core workers at B=1, adjacent and separated medians were 38.79 ms and 36.67 ms, respectively. Their ratio was 1.06 [0.83, 1.27] (descriptive 95% bootstrap interval). For four E-core workers, the corresponding ratio was 0.97 [0.42, 1.22]. Both intervals span one: these cells do not establish a clear padding benefit. Two SMT workers occupy siblings on one P core, giving a ratio of 0.86 [0.71, 1.04]; this placement must not be treated as two independent physical cores.

The largest observed layout ratio among multiworker, non-final-only cells was 1.34 [0.80, 1.43] for P_physical, 2 workers and B=256. This is an exploratory maximum across many conditions, not an unbiased estimate of an optimal configuration. Single-worker cells provide a control where inter-worker false sharing is absent; remaining layout differences there reflect noise or other effects.

## 4  Publication frequency and interaction

![Figure 3. Publication interval at the largest worker count in each placement family. Final-only publication is the local-accumulation analogue; medians of nine executions.](figures/batching.png)

| Six physical P workers | Adjacent (ms) | Separated (ms) | Layout ratio [95% interval] |
| --- | --- | --- | --- |
| B = 1 | 38.79 | 36.67 | 1.06 [0.83, 1.27] |
| B = 16 | 28.38 | 27.51 | 1.03 [0.93, 1.52] |
| B = 256 | 26.97 | 29.48 | 0.91 [0.86, 1.51] |
| Final only | 29.79 | 30.79 | 0.97 [0.74, 1.49] |

Within the separated six-P-core layout, B=1 versus final-only publication gave a median-time ratio of 1.19 (36.67 ms vs. 30.79 ms). This timing change occurs without changing line separation and therefore cannot be credited to padding. It combines reduced stores with fewer publication-loop boundaries. Intermediate intervals show whether most of the benefit appears before final-only publication; no monotonic benefit is assumed.

![Figure 4. Layout ratios across the full grid. Values above 1 favor separation; values below 1 favor adjacency. Color is capped for legibility; annotations show actual ratios.](figures/effects.png)

The grid is a conditional map, not a universal ranking. Layout and publication interval may interact, and SMT placement changes what is shared within a physical core. At final-only publication, the main body performs no repeated output stores, so sustained ownership bouncing on those output lines is not a sufficient explanation for a large residual timing difference. Such differences require caution about noise, frequency, scheduling or common overhead.

## 5  Exploratory extension: publication primitive and cross-architecture validation

The initial ordinary-store results did not show a clear six-P-core padding benefit. Rather than relabeling this as success, we added an exploratory control: relaxed atomic exchange of the same state. This tests sensitivity to the publication primitive; it is not a correction that erases the initial negative result. Atomic exchange is deliberately used as a stress variant, not recommended as necessary synchronization for worker-owned outputs.

Both extension blocks use the same updated binary, 1,000,000 recurrence iterations per worker, B in {1,16,256,N}, the same layouts and placement groups, and seven measured repetitions after one warm-up per cell. The atomic block was executed first and the matched ordinary-store block second; modes were not interleaved. Each block has 88 conditions and 616 measured runs. Within each block, condition order is randomized. Absolute times across blocks are not a clean causal estimate of the primitive cost because order and power state remain confounded.

![Figure 5. Atomic-exchange extension at B=1. Medians and IQR from seven executions per cell. Its N differs from Figures 2-4; compare layout ratios, not absolute times across those figures.](figures/atomic_scaling.png)

| Placement / interval | Ordinary-store ratio | Atomic-exchange ratio |
| --- | --- | --- |
| P physical / 6 / B=1 | 1.04 [0.74, 1.25] | 8.50 [7.61, 11.46] |
| P physical / 6 / B=16 | 1.06 [0.81, 1.27] | 6.85 [5.31, 7.47] |
| P physical / 6 / B=256 | 0.84 [0.77, 1.15] | 0.93 [0.60, 1.25] |
| P physical / 6 / final | 1.14 [0.81, 1.35] | 1.32 [0.91, 1.49] |
| P SMT / 2 / B=1 | 1.33 [0.77, 1.44] | 1.11 [0.84, 1.34] |
| P SMT / 12 / B=1 | 1.14 [0.81, 1.39] | 7.35 [6.93, 8.41] |
| E physical / 4 / B=1 | 1.08 [0.91, 4.94] | 7.53 [6.49, 8.54] |

For six physical P workers, atomic B=1 medians were 122.98 ms adjacent and 14.47 ms separated. Their 8.50-fold ratio contracts to 0.93 at B=256, whose interval spans one. The generated assembly contains a memory xchg for the atomic variant. The same-cell store result does not reproduce this large separation benefit. These observations are consistent with sensitivity to atomic publication and topology; they still do not count coherence events. Small final-only timings and residual layout ratios caution against reading every ratio as false sharing.

### 5.1  Cross-machine and cross-architecture validation (x86-64 and Apple M1 ARM64)

To check whether the frequency- and primitive-dependent pattern generalizes beyond a single laptop and compiler, we executed a cross-platform C++17 benchmark (4 threads, 1,000,000 iterations/thread, 5 measured repetitions plus 1 warm-up, comparing 8-byte adjacent, 64-byte padded, and 128-byte padded layouts) across three independent systems: two x86-64 Windows 11 laptops (MSVC `/O2`) and an Apple M1 ARM64 MacBook Air (macOS, `clang++ -O2`, OS-reported `hw.cachelinesize = 128` bytes).

| Mode / Batch (4 threads, 1M ops) | Windows PC #1 (x86-64, 16 CPU) | Windows PC #2 (x86-64, 16 CPU) | Apple M1 MacBook Air (ARM64, 8 CPU, 128B line) |
| --- | --- | --- | --- |
| Ordinary store, B=1 | 0.95 → 0.94 ms (1.01x) | 1.10 → 1.02 ms (1.09x) | 1.40–1.41 → 1.03 ms (1.36x) |
| Atomic exchange, B=1 | 41.32 → 4.01 ms (10.30x) | 50.52 → 5.22 ms (9.68x) | 55.07–64.46 → 1.04 ms (53.03x–61.96x) |
| Atomic exchange, B=16 | 1.64 → 0.95 ms (1.72x) | 3.26 → 1.12 ms (2.91x) | 3.96–4.01 → 1.03–1.04 ms (3.82x–3.89x) |
| Atomic exchange, B=256 | 0.93 → 0.93 ms (1.00x) | 1.11 → 1.07 ms (1.04x) | 1.03 → 1.03 ms (1.00x) |
| Atomic exchange, Local (end) | 0.92 → 0.94 ms (0.97x) | 1.10 → 1.07 ms (1.03x) | 1.03 → 1.03–1.04 ms (0.99x–1.00x) |

All three machines reproduced the same qualitative pattern: padding produced large speedups under frequent atomic publication (`B=1`), moderated under `B=16`, and vanished at `B=256` and local accumulation (~1.00x). Notably, although Apple M1 reports a 128-byte cache line via `sysctl`, `alignas(64)` (1.04 ms) already matched `alignas(128)` (1.04–1.05 ms) on this 4-thread workload; doubling counter storage from 64B to 128B yielded no additional speedup. Additionally, an explicit 2-thread affinity control on Windows PC #1 confirmed that pinning two atomic workers to SMT siblings on the same P core (`CPU 0` & `CPU 1`) yielded no padding benefit (19.18 ms vs. 18.77 ms, 1.02x), whereas pinning them to two separate physical P cores (`CPU 0` & `CPU 2`) produced a 3.20x speedup (40.53 ms vs. 12.65 ms).

## 6  Interpretation, costs and limitations

### 6.1  Answer to the research question

The equal-frequency layout contrast and the separated-layout batching contrast produce different quantities. On six physical P workers in the initial ordinary-store study, the measured layout ratio changed only modestly from 1.06 [0.83, 1.27] at B=1 to 0.97 [0.74, 1.49] with final-only publication, whereas in the atomic-exchange extension it dropped sharply from 8.50 [7.61, 11.46] at B=1 to 0.93 [0.60, 1.25] at B=256. The observed benefit therefore depends on publication regime and memory primitive rather than on padding alone. The practical interpretation is to measure the intended update pattern and placement before expanding every per-thread object.

The adjacent allocation uses 8 bytes per worker, while the separated allocation reserves 64 bytes per worker: an eightfold storage increase (or sixteenfold for 128-byte padding). For six workers this is 48 versus 384 allocated bytes; for twelve workers, 96 versus 768 bytes. These are allocation sizes, not measured resident-set or whole-program memory costs. Larger footprints may matter in real data structures, but this tiny experiment cannot quantify cache-capacity or TLB penalties.

### 6.2  Mechanism and evidence boundary

Addresses confirm when output states share a 64-byte line. The same worker loop and publication count are used in each fixed-B stride contrast. These controls make false sharing a plausible interpretation of suitable timing differences. They do not measure coherence messages. No HITM, cache-to-cache, invalidation or other PMU events were collected. Intel recommends profiling contended structures [2]; a follow-up should correlate timing with appropriate hardware events before claiming a quantified coherence mechanism.

### 6.3  Threats to validity

**Environment.** The primary 2,024-run study was collected in one session on an active Windows 11 desktop (build 26200), with Balanced power policy; a pre-run power snapshot reported battery operation and 85% charge. Power, temperature and frequency were not continuously logged, and background processes were not eliminated. Random ordering and robust summaries reduce some sensitivity but cannot remove these confounders.

**Timing and synchronization.** Common completion atomics and event wake-up add overhead, and the controller is not explicitly pinned. Physical P workers leave their SMT siblings available to other processes. Short runs and scheduling noise can influence ratios. Warm-ups occur in a separate phase; this does not guarantee a stationary thermal state throughout measurements.

**Workload and scaling.** A serial multiply-add recurrence is intentionally simple. The added exchange variant does not implement a full concurrent application or consumer protocol. Publication batching changes loop overhead as well as stores. Scaling is weak: total work grows with worker count. Rising elapsed time is not proof that fixed-work parallel speedup is negative. Initial, extension and cross-platform workloads use different N and binaries; their absolute times are not pooled.

**Statistics and generalization.** Nine initial, seven extension and five cross-platform executions per cell are insufficient for strong tail-latency conclusions. Bootstrap intervals are descriptive, not confirmatory tests. The atomic extension followed inspection of the initial results; mode blocks in the primary study were sequential. While Section 5.1 adds two independent machines and alternate compilers (MSVC and Apple clang++), raw CSV logs are archived for both Windows systems while the Apple M1 runs are documented from two independent terminal sessions. P/E differences include shared-resource and placement differences, not a single isolated cause.

### 6.4  Conclusion

Separation, publication reduction and publication primitive should be reported distinctly. A large atomic-exchange layout contrast coexists with an inconclusive ordinary-store contrast on the same machine, and batching substantially reduces or eliminates the padding advantage across both x86-64 and Apple M1 ARM64 systems. This supports conditional engineering decisions grounded in empirical measurement, while stronger causal and application-level claims require hardware-event profiling.

## 7  Reproducibility, declarations and references

### 7.1  Evidence package and public repository

All source code, build/run scripts, raw measurements, verified address logs and documentation are publicly available at:  
**https://github.com/Fearfestiwal/false-sharing-research-project**

The primary study archive (`main_study/` and accompanying `research_package.zip`) contains the Zig/Clang benchmark source, scripts, raw measurements (`data/`, `runs/atomic/data/`, `runs/matched_store/data/`), topology, environment metadata, compiler-produced assembly and analysis scripts covering 2,288 executions (264 warm-ups and 2,024 measured runs). The cross-platform validation suite (`src/benchmark_crossplatform.cpp`, `scripts/run_windows.ps1`, `scripts/run_macos.sh`, and machine-specific CSV folders under `results/`) provides single-command reproduction on Windows and macOS. All recorded correctness, affinity and base-alignment flags are true; no synthetic result values were substituted.

For each record, `addresses.csv` supplies the assigned CPU (in the pinned study), runtime address, cache-line index (`address / 64` and `address / 128`), and line offset (`address % 64` and `address % 128`). Independent validation confirms that separated outputs occupy distinct cache-line indices with zero offsets, whereas adjacent outputs occupy consecutive 8-byte offsets.

### 7.2  Declaration of Generative AI and AI-Assisted Technologies

Generative AI tools (OpenAI Codex and Google Gemini / Antigravity) were used to assist with benchmark scaffolding, experiment automation scripts, statistical analysis scripts, figure generation, and manuscript editing/formatting. Both student authors (Zeynep Uyan and Muhammed Enes Aksoy) actively designed the experimental direction in response to coordinator feedback, independently compiled and executed benchmarks across three physical machines (two Windows x86-64 laptops and an Apple M1 MacBook Air), verified memory alignment logs, correctness checksums, and thread-affinity behavior, and reviewed all claims, citations, numbers, and limitations presented in this manuscript.

### 7.3  References

- [1] W. J. Bolosky and M. L. Scott, "False Sharing and its Effect on Shared Memory Performance," USENIX SEDMS IV, 1993. https://www.usenix.org/legacy/publications/library/proceedings/sedms4/bolosky.html
- [2] Intel, "False Sharing," Intel VTune Profiler Cookbook, version 2024.2, 2024. https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2024-2/false-sharing.html
- [3] Intel, "Game Dev Guide for 12th Gen Intel Core Processor," updated June 13, 2022. Used for topology principles, not as a specification of the tested 13th Gen CPU. https://www.intel.com/content/www/us/en/developer/articles/guide/12th-gen-intel-core-processor-gamedev-guide.html
- [4] Microsoft, "GetLogicalProcessorInformationEx function (sysinfoapi.h)," Microsoft Learn. https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex
- [5] LLVM Project, "LLVM Atomic Instructions and Concurrency Guide," section on atomic and volatile operations. https://llvm.org/docs/Atomics.html

Keywords: false sharing; memory layout; publication batching; hybrid processors; multithreading; cross-architecture validation; reproducibility.
