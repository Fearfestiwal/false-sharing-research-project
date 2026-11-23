using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

Console.OutputEncoding = System.Text.Encoding.UTF8;

Console.WriteLine("=================================================================");
Console.WriteLine("   İŞLEMCİ ÇEKİRDEK, SMT VE FALSE SHARING CANLI DONANIM TESTİ");
Console.WriteLine("=================================================================\n");

// 1) GERÇEK DONANIM TOPOLOJİSİNİ OKU
var cores = CpuTopology.GetPhysicalCores();
var pCores = cores.Where(c => c.LogicalProcessors.Count > 1).ToList();
var eCores = cores.Where(c => c.LogicalProcessors.Count == 1).ToList();

// Eğer EfficiencyClass varsa ve SMT kapalıysa yine de P/E ayrımını koru
if (pCores.Count == 0 && cores.Select(c => c.EfficiencyClass).Distinct().Count() > 1)
{
    byte maxEff = cores.Max(c => c.EfficiencyClass);
    pCores = cores.Where(c => c.EfficiencyClass == maxEff).ToList();
    eCores = cores.Where(c => c.EfficiencyClass != maxEff).ToList();
}

int totalLogical = cores.Sum(c => c.LogicalProcessors.Count);

Console.WriteLine($"Toplam Fiziksel Çekirdek : {cores.Count}");
Console.WriteLine($"Toplam Mantıksal İşlemci : {totalLogical}");
Console.WriteLine($"P-Çekirdek Sayısı        : {pCores.Count} (toplam {pCores.Sum(c => c.LogicalProcessors.Count)} mantıksal işlemci)");
Console.WriteLine($"E-Çekirdek Sayısı        : {eCores.Count} (toplam {eCores.Sum(c => c.LogicalProcessors.Count)} mantıksal işlemci)\n");

Console.WriteLine("Çekirdek Haritası:");
for (int i = 0; i < cores.Count; i++)
{
    var c = cores[i];
    string tur = pCores.Contains(c) ? "P-Çekirdeği" : "E-Çekirdeği";
    string lpList = string.Join(", ", c.LogicalProcessors.Select(lp => $"CPU {lp}"));
    Console.WriteLine($"  Fiziksel #{i:D2} [{tur}] -> Mantıksal İşlemciler: {lpList}");
}

if (pCores.Count < 2 || pCores[0].LogicalProcessors.Count < 2)
{
    Console.WriteLine("\nUyarı: Beklenen en az 2 SMT'li P-çekirdeği bulunamadı, varsayılan CPU indeksleri kullanılacak.");
}

int p0_a = pCores[0].LogicalProcessors[0];
int p0_b = pCores[0].LogicalProcessors.Count > 1 ? pCores[0].LogicalProcessors[1] : pCores[1].LogicalProcessors[0];
int p1_a = pCores[1].LogicalProcessors[0];

int e0 = eCores.Count > 0 ? eCores[0].LogicalProcessors[0] : -1;
int e1 = eCores.Count > 1 ? eCores[1].LogicalProcessors[0] : -1;

// =================================================================
// TEST 1: FİZİKSEL ÇEKİRDEK vs SMT (MANTIKSAL İŞLEMCİ) vs E-ÇEKİRDEK
// =================================================================
Console.WriteLine("\n=================================================================");
Console.WriteLine(" TEST 1: ÇEKİRDEK YERLEŞİMİ (Aynı İş Yükü, Farklı Yerleşimler)");
Console.WriteLine("=================================================================");
Console.WriteLine("Her thread bağımsız olarak 80.000.000 kez matematiksel işlem yapar.\n");

const int computeIters = 80_000_000;
const int runs = 5;

// Isınma
RunCompute(new[] { p0_a }, 10_000_000);

double t1_singleP = MeasureMedian(runs, () => RunCompute(new[] { p0_a }, computeIters));
double t1_sameP_smt = MeasureMedian(runs, () => RunCompute(new[] { p0_a, p0_b }, computeIters));
double t1_twoP = MeasureMedian(runs, () => RunCompute(new[] { p0_a, p1_a }, computeIters));

Console.WriteLine($"  [Referans] 1 Thread  | 1 P-Çekirdeği (CPU {p0_a})                : {t1_singleP,7:F2} ms");
Console.WriteLine($"  [Durum A]  2 Thread  | AYNI P-Çekirdeği SMT (CPU {p0_a} & {p0_b})    : {t1_sameP_smt,7:F2} ms  (1 thread'e göre {t1_sameP_smt / t1_singleP:F2}x süre)");
Console.WriteLine($"  [Durum B]  2 Thread  | İKİ AYRI P-Çekirdeği (CPU {p0_a} & {p1_a})    : {t1_twoP,7:F2} ms  (1 thread'e göre {t1_twoP / t1_singleP:F2}x süre)");

if (e0 >= 0 && e1 >= 0)
{
    double t1_singleE = MeasureMedian(runs, () => RunCompute(new[] { e0 }, computeIters));
    double t1_twoE = MeasureMedian(runs, () => RunCompute(new[] { e0, e1 }, computeIters));
    Console.WriteLine($"  [E-Core]   1 Thread  | 1 E-Çekirdeği (CPU {e0})               : {t1_singleE,7:F2} ms  (P-çekirdeğine göre {t1_singleE / t1_singleP:F2}x süre)");
    Console.WriteLine($"  [E-Core]   2 Thread  | İKİ AYRI E-Çekirdeği (CPU {e0} & {e1})  : {t1_twoE,7:F2} ms");
}

Console.WriteLine($"\n  -> Sonuç: İki ayrı P çekirdeği, aynı P çekirdeğindeki SMT kardeşlerinden {t1_sameP_smt / t1_twoP:F2}x daha hızlı!");

// =================================================================
// TEST 2: FALSE SHARING (YAN YANA SAYAÇ vs AYRI ÖNBELLEK SATIRI)
// =================================================================
Console.WriteLine("\n=================================================================");
Console.WriteLine(" TEST 2: FALSE SHARING (Önbellek Satırı Çakışması)");
Console.WriteLine("=================================================================");
Console.WriteLine($"2 thread, İKİ AYRI P-Çekirdeğinde (CPU {p0_a} ve CPU {p1_a}) çalışır.");
Console.WriteLine("Her thread kendi sayacını 40.000.000 kez günceller.\n");

const int fsNormalIters = 40_000_000;
const int fsAtomicIters = 15_000_000;

// Isınma
RunFalseSharingNormal(p0_a, p1_a, 1_000_000, separateCacheLines: false);
RunFalseSharingNormal(p0_a, p1_a, 1_000_000, separateCacheLines: true);

double fsNormalSame = MeasureMedian(runs, () => RunFalseSharingNormal(p0_a, p1_a, fsNormalIters, separateCacheLines: false));
double fsNormalDiff = MeasureMedian(runs, () => RunFalseSharingNormal(p0_a, p1_a, fsNormalIters, separateCacheLines: true));

Console.WriteLine("  A) Normal Yazma (Volatile.Write — 40 milyon/thread):");
Console.WriteLine($"     Yan yana (Aynı 64-byte satır, offset 0 & 8)  : {fsNormalSame,7:F2} ms");
Console.WriteLine($"     Ayrı satır (64-byte boşluk, offset 0 & 64)   : {fsNormalDiff,7:F2} ms");
Console.WriteLine($"     -> Fark: Ayrı önbellek satırı {fsNormalSame / fsNormalDiff:F2}x daha hızlı!\n");

// Atomik ısınma
RunFalseSharingAtomic(p0_a, p1_a, 500_000, separateCacheLines: false);
RunFalseSharingAtomic(p0_a, p1_a, 500_000, separateCacheLines: true);

double fsAtomicSame = MeasureMedian(runs, () => RunFalseSharingAtomic(p0_a, p1_a, fsAtomicIters, separateCacheLines: false));
double fsAtomicDiff = MeasureMedian(runs, () => RunFalseSharingAtomic(p0_a, p1_a, fsAtomicIters, separateCacheLines: true));

Console.WriteLine("  B) Atomik Yazma (Interlocked.Exchange — 15 milyon/thread):");
Console.WriteLine($"     Yan yana (Aynı 64-byte satır, offset 0 & 8)  : {fsAtomicSame,7:F2} ms");
Console.WriteLine($"     Ayrı satır (64-byte boşluk, offset 0 & 64)   : {fsAtomicDiff,7:F2} ms");
Console.WriteLine($"     -> Fark: Ayrı önbellek satırı {fsAtomicSame / fsAtomicDiff:F2}x daha hızlı!\n");

// Bonus: False Sharing aynı P çekirdeğinin SMT kardeşlerinde nasıl davranır?
double fsAtomicSameCore = MeasureMedian(runs, () => RunFalseSharingAtomic(p0_a, p0_b, fsAtomicIters, separateCacheLines: false));
Console.WriteLine($"  C) Bonus — Yan Yana Sayaç (Atomik) AYNI P-Çekirdeği SMT'de (CPU {p0_a} & {p0_b}):");
Console.WriteLine($"     Süre: {fsAtomicSameCore,7:F2} ms (Aynı çekirdek L1 önbelleğini paylaştığı için çekirdekler arası satır git-geli olmaz!)");

// =================================================================
// TEST 3: 64-BYTE SINIR TARAMASI (MESAFE DENEYİ)
// =================================================================
Console.WriteLine("\n=================================================================");
Console.WriteLine(" TEST 3: 64-BYTE ÖNBELLEK SATIRI SINIRINI CANLI YAKALAMA");
Console.WriteLine("=================================================================");
Console.WriteLine($"İki ayrı P-Çekirdeği (CPU {p0_a} & CPU {p1_a}), Atomik yazma (10 milyon/thread).");
Console.WriteLine("Sayaç B'yi Sayaç A'dan adım adım uzaklaştırıyoruz:\n");

int[] offsets = { 8, 16, 32, 48, 56, 64, 128 };
const int sweepIters = 10_000_000;
var sweepResults = new List<(int offset, double ms)>();

foreach (int off in offsets)
{
    double ms = MeasureMedian(3, () => RunFalseSharingAtomicOffset(p0_a, p1_a, sweepIters, off));
    sweepResults.Add((off, ms));
}

double maxMs = sweepResults.Max(r => r.ms);
foreach (var (off, ms) in sweepResults)
{
    int barLen = Math.Max(1, (int)Math.Round((ms / maxMs) * 30));
    string bar = new string('#', barLen).PadRight(30);
    string durum = off < 64 ? "AYNI SATIR (kavga var)" : "AYRI SATIR (kavga bitti!)";
    Console.WriteLine($"  Mesafe {off,3} byte | {bar} | {ms,6:F1} ms  [{durum}]");
}

Console.WriteLine("\nTest tamamlandı.");

// =================================================================
// YARDIMCI FONKSİYONLAR
// =================================================================

static double MeasureMedian(int count, Action action)
{
    var times = new double[count];
    for (int i = 0; i < count; i++)
    {
        var sw = Stopwatch.StartNew();
        action();
        sw.Stop();
        times[i] = sw.Elapsed.TotalMilliseconds;
    }
    Array.Sort(times);
    return times[count / 2];
}

static void RunCompute(int[] cpuIds, int iterations)
{
    using var startGate = new CountdownEvent(cpuIds.Length);
    using var goSignal = new ManualResetEventSlim(false);
    var threads = new Thread[cpuIds.Length];
    long sink = 0;

    for (int i = 0; i < cpuIds.Length; i++)
    {
        int cpu = cpuIds[i];
        threads[i] = new Thread(() =>
        {
            PinCurrentThread(cpu);
            startGate.Signal();
            goSignal.Wait();

            long x = cpu + 1;
            long y = 3;
            for (int k = 0; k < iterations; k++)
            {
                x = unchecked(x * 1664525 + 1013904223);
                y ^= (x >> 7);
            }
            Interlocked.Add(ref sink, x ^ y);
        });
        threads[i].Start();
    }

    startGate.Wait();
    goSignal.Set();

    foreach (var t in threads) t.Join();
    GC.KeepAlive(sink);
}

static unsafe void RunFalseSharingNormal(int cpuA, int cpuB, int iterations, bool separateCacheLines)
{
    // 256 byte hizalanmış bellek ayır
    void* raw = NativeMemory.AlignedAlloc(256, 64);
    try
    {
        NativeMemory.Clear(raw, 256);
        long* ptrA = (long*)((byte*)raw + 0);
        long* ptrB = (long*)((byte*)raw + (separateCacheLines ? 64 : 8));

        using var startGate = new CountdownEvent(2);
        using var goSignal = new ManualResetEventSlim(false);

        var t1 = new Thread(() =>
        {
            PinCurrentThread(cpuA);
            startGate.Signal();
            goSignal.Wait();
            for (long i = 0; i < iterations; i++)
            {
                Volatile.Write(ref *ptrA, i);
            }
        });

        var t2 = new Thread(() =>
        {
            PinCurrentThread(cpuB);
            startGate.Signal();
            goSignal.Wait();
            for (long i = 0; i < iterations; i++)
            {
                Volatile.Write(ref *ptrB, i);
            }
        });

        t1.Start();
        t2.Start();
        startGate.Wait();
        goSignal.Set();
        t1.Join();
        t2.Join();
    }
    finally
    {
        NativeMemory.AlignedFree(raw);
    }
}

static unsafe void RunFalseSharingAtomic(int cpuA, int cpuB, int iterations, bool separateCacheLines)
{
    RunFalseSharingAtomicOffset(cpuA, cpuB, iterations, separateCacheLines ? 64 : 8);
}

static unsafe void RunFalseSharingAtomicOffset(int cpuA, int cpuB, int iterations, int offsetBytes)
{
    void* raw = NativeMemory.AlignedAlloc(256, 64);
    try
    {
        NativeMemory.Clear(raw, 256);
        long* ptrA = (long*)((byte*)raw + 0);
        long* ptrB = (long*)((byte*)raw + offsetBytes);

        using var startGate = new CountdownEvent(2);
        using var goSignal = new ManualResetEventSlim(false);

        var t1 = new Thread(() =>
        {
            PinCurrentThread(cpuA);
            startGate.Signal();
            goSignal.Wait();
            for (long i = 0; i < iterations; i++)
            {
                Interlocked.Exchange(ref *ptrA, i);
            }
        });

        var t2 = new Thread(() =>
        {
            PinCurrentThread(cpuB);
            startGate.Signal();
            goSignal.Wait();
            for (long i = 0; i < iterations; i++)
            {
                Interlocked.Exchange(ref *ptrB, i);
            }
        });

        t1.Start();
        t2.Start();
        startGate.Wait();
        goSignal.Set();
        t1.Join();
        t2.Join();
    }
    finally
    {
        NativeMemory.AlignedFree(raw);
    }
}

static void PinCurrentThread(int logicalProcessorIndex)
{
    IntPtr mask = (IntPtr)(1L << logicalProcessorIndex);
    IntPtr res = SetThreadAffinityMask(GetCurrentThread(), mask);
    if (res == IntPtr.Zero)
    {
        throw new InvalidOperationException($"CPU {logicalProcessorIndex} sabitlemesi başarısız.");
    }
}

[DllImport("kernel32.dll")]
static extern IntPtr GetCurrentThread();

[DllImport("kernel32.dll", SetLastError = true)]
static extern IntPtr SetThreadAffinityMask(IntPtr hThread, IntPtr dwThreadAffinityMask);

record PhysicalCoreInfo(byte EfficiencyClass, List<int> LogicalProcessors);

static class CpuTopology
{
    private const int RelationProcessorCore = 0;

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetLogicalProcessorInformationEx(
        int relationshipType,
        IntPtr buffer,
        ref int returnedLength);

    public static unsafe List<PhysicalCoreInfo> GetPhysicalCores()
    {
        int len = 0;
        GetLogicalProcessorInformationEx(RelationProcessorCore, IntPtr.Zero, ref len);
        IntPtr buf = Marshal.AllocHGlobal(len);
        try
        {
            if (!GetLogicalProcessorInformationEx(RelationProcessorCore, buf, ref len))
                throw new InvalidOperationException("CPU topolojisi okunamadı.");

            var result = new List<PhysicalCoreInfo>();
            int offset = 0;
            while (offset < len)
            {
                byte* ptr = (byte*)buf + offset;
                int relationship = *(int*)ptr;
                int size = *(int*)(ptr + 4);

                if (relationship == RelationProcessorCore)
                {
                    // PROCESSOR_RELATIONSHIP layout (64-bit Windows):
                    // offset 8:  BYTE Flags
                    // offset 9:  BYTE EfficiencyClass
                    // offset 10..29: Reserved[20]
                    // offset 30: WORD GroupCount
                    // offset 32: GROUP_AFFINITY[GroupCount] (Mask: ulong @ +0, Group: ushort @ +8)
                    byte effClass = *(ptr + 9);
                    ushort groupCount = *(ushort*)(ptr + 30);
                    var lps = new List<int>();
                    for (int g = 0; g < groupCount; g++)
                    {
                        ulong mask = *(ulong*)(ptr + 32 + g * 16);
                        for (int bit = 0; bit < 64; bit++)
                        {
                            if ((mask & (1UL << bit)) != 0)
                                lps.Add(bit);
                        }
                    }
                    result.Add(new PhysicalCoreInfo(effClass, lps));
                }

                offset += size;
            }
            return result;
        }
        finally
        {
            Marshal.FreeHGlobal(buf);
        }
    }
}
