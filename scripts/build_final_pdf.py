from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, HRFlowable
)
from PIL import Image as PILImage

ROOT = Path(r"C:\Users\muham\.gemini\antigravity\scratch\false-sharing-research-project")
FIGS = ROOT / "paper_build" / "figures"
PRES = ROOT / "presentation_assets"
OUT_PDF = ROOT / "research_paper_FINAL_Group4.pdf"

NAVY = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#475569")
BLUE = colors.HexColor("#1D4ED8")
LIGHT_BG = colors.HexColor("#F1F5F9")
BORDER = colors.HexColor("#CBD5E1")


def make_figure1_schematic():
    """Create crisp Figure 1: 4-worker memory layout schematic (8B vs 64B vs Local)."""
    fig, axes = plt.subplots(3, 1, figsize=(7.6, 3.3), dpi=300)
    plt.subplots_adjust(hspace=0.55)

    # Row 1: Adjacent (8B)
    ax = axes[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.3)
    ax.axis("off")
    ax.set_title("A. Adjacent counters (8-byte stride): multiple workers share one 64-byte cache line",
                 loc="left", fontsize=9.2, fontweight="bold", color="#991B1B", pad=3)
    ax.add_patch(patches.FancyBboxPatch((0.1, 0.15), 9.7, 0.85, boxstyle="round,pad=0.05",
                                        fc="#FEF2F2", ec="#DC2626", lw=1.4))
    for i in range(4):
        ax.add_patch(patches.Rectangle((0.3 + i * 1.45, 0.28), 1.32, 0.58,
                                       fc="#FCA5A5", ec="#991B1B", lw=1.0))
        ax.text(0.3 + i * 1.45 + 0.66, 0.57, f"W{i} (8B)", ha="center", va="center",
                fontsize=8.2, fontweight="bold", color="#7F1D1D")
    ax.text(7.9, 0.57, "Remaining 32B of same 64B line", ha="center", va="center",
            fontsize=8, color="#7F1D1D", style="italic")

    # Row 2: Separated (64B)
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.3)
    ax.axis("off")
    ax.set_title("B. Separated / padded (64-byte stride, alignas(64)): each worker owns a separate 64-byte line",
                 loc="left", fontsize=9.2, fontweight="bold", color="#0F766E", pad=3)
    for i in range(4):
        x0 = 0.1 + i * 2.45
        ax.add_patch(patches.FancyBboxPatch((x0, 0.15), 2.30, 0.85, boxstyle="round,pad=0.04",
                                            fc="#F0FDFA", ec="#0D9488", lw=1.2))
        ax.add_patch(patches.Rectangle((x0 + 0.1, 0.28), 0.78, 0.58,
                                       fc="#5EEAD4", ec="#0F766E", lw=0.9))
        ax.text(x0 + 0.49, 0.57, f"W{i}", ha="center", va="center",
                fontsize=8.2, fontweight="bold", color="#134E4A")
        ax.text(x0 + 1.56, 0.57, "56B pad", ha="center", va="center",
                fontsize=7.6, color="#115E59", style="italic")

    # Row 3: Local accumulation
    ax = axes[2]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.3)
    ax.axis("off")
    ax.set_title("C. Local accumulation / batching (B = 16, 256, or N): compute in register, publish less often",
                 loc="left", fontsize=9.2, fontweight="bold", color="#1D4ED8", pad=3)
    ax.add_patch(patches.FancyBboxPatch((0.1, 0.15), 4.6, 0.85, boxstyle="round,pad=0.05",
                                        fc="#EFF6FF", ec="#2563EB", lw=1.2))
    ax.text(2.4, 0.57, "CPU Register: x = x * A + C  (B steps)", ha="center", va="center",
            fontsize=8.4, fontweight="bold", color="#1E3A8A")
    ax.annotate("", xy=(6.2, 0.57), xytext=(4.85, 0.57),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.8))
    ax.text(5.52, 0.83, "1 write", ha="center", fontsize=7.6, fontweight="bold", color="#1D4ED8")
    ax.add_patch(patches.FancyBboxPatch((6.3, 0.15), 3.5, 0.85, boxstyle="round,pad=0.05",
                                        fc="#F8FAFC", ec="#475569", lw=1.2))
    ax.text(8.05, 0.57, "Worker Memory Slot (8B or 64B)", ha="center", va="center",
            fontsize=8.2, fontweight="bold", color="#1E293B")

    out = FIGS / "figure1_layout.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def scaled_image(path: Path, max_w_mm=164, max_h_mm=92):
    with PILImage.open(path) as im:
        w, h = im.size
    aspect = h / float(w)
    target_w = max_w_mm * mm
    target_h = target_w * aspect
    if target_h > max_h_mm * mm:
        target_h = max_h_mm * mm
        target_w = target_h / aspect
    img = Image(str(path), width=target_w, height=target_h)
    img.hAlign = "CENTER"
    return img


def make_table(data, col_widths_mm):
    t = Table(data, colWidths=[w * mm for w in col_widths_mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.4),
        ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont("Helvetica", 7.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, A4[1] - 12 * mm,
                          "When More Threads Become Slower: False Sharing and Mitigation | Uyan & Aksoy (Group-4)")
        canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 12 * mm, "Vistula University | Architecture of Computers")
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(18 * mm, A4[1] - 14 * mm, A4[0] - 18 * mm, A4[1] - 14 * mm)
    canvas.setFont("Helvetica", 8.2)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2.0, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    fig1_path = make_figure1_schematic()

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title="When More Threads Become Slower: Investigating False Sharing and Its Mitigation",
        author="Zeynep Uyan (75616) and Muhammed Enes Aksoy (75569)"
    )

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold",
                             fontSize=19, leading=23, textColor=NAVY, alignment=TA_CENTER, spaceAfter=4)
    s_sub = ParagraphStyle("SubCustom", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=11, leading=14, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8)
    s_author = ParagraphStyle("AuthorCustom", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=10, leading=13, textColor=SLATE, alignment=TA_CENTER, spaceAfter=2)
    s_affil = ParagraphStyle("AffilCustom", parent=styles["Normal"], fontName="Helvetica",
                             fontSize=9, leading=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10)
    s_h1 = ParagraphStyle("H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold",
                          fontSize=12.2, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=4, keepWithNext=True)
    s_h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold",
                          fontSize=10.4, leading=13, textColor=BLUE, spaceBefore=7, spaceAfter=3, keepWithNext=True)
    s_body = ParagraphStyle("BodyCustom", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=9.4, leading=13.2, textColor=SLATE, alignment=TA_JUSTIFY, spaceAfter=5)
    s_abs = ParagraphStyle("AbsCustom", parent=s_body, fontSize=9.0, leading=12.6,
                           leftIndent=6, rightIndent=6)
    s_cap = ParagraphStyle("CapCustom", parent=styles["Normal"], fontName="Helvetica-Oblique",
                           fontSize=8.3, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=7)
    s_ref = ParagraphStyle("RefCustom", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=8.4, leading=11.5, textColor=SLATE, leftIndent=14, firstLineIndent=-14, spaceAfter=3)

    story = []

    # Header Block
    story.append(Paragraph("When More Threads Become Slower", s_title))
    story.append(Paragraph("Separating memory layout and publication frequency in a hybrid-CPU microbenchmark", s_sub))
    story.append(Paragraph("Zeynep Uyan (75616) and Muhammed Enes Aksoy (75569)", s_author))
    story.append(Paragraph("Architecture of Computers &nbsp;|&nbsp; Group-4 &nbsp;|&nbsp; Vistula University &nbsp;|&nbsp; November 2026", s_affil))
    story.append(HRFlowable(width="100%", thickness=1.0, color=BLUE, spaceAfter=8))

    # Abstract Box (Humanized + numerically aligned + atomic stress-condition disclaimer)
    abs_text = (
        "<b>Abstract:</b> False sharing and frequent memory writes slow down multithreaded programs in different ways. "
        "We test both effects with a state-publication microbenchmark on an Intel Core i7-13620H running Windows 11, "
        "followed by cross-architecture runs on a second x86-64 Windows laptop and an Apple M1 ARM64 MacBook Air. "
        "The primary study compares 8-byte adjacent and 64-byte separated layouts across worker counts, publication intervals, "
        "and hybrid-core placements. An initial ordinary-store run collected 792 measurements, and a workload-matched extension "
        "compared ordinary stores against relaxed atomic exchanges across 1,232 more measurements. Every correctness, affinity, "
        "and alignment check passed. With six physical performance-core workers publishing on every step, the matched ordinary-store "
        "layout ratio was 1.04 (95% bootstrap interval spanning one). Under an experimental atomic-exchange stress condition, the "
        "ratio rose to 8.50 and fell back to 0.93 when workers published every 256 steps. The same frequency-dependent pattern "
        "appeared on both x86-64 Windows laptops (MSVC, 9.68x to 10.30x at B=1; about 1.00x at B=256) and in the archived Apple M1 "
        "ARM64 run (clang++, 41.61x for 64-byte padding and 58.11x for 128-byte padding at B=1; 1.00x at B=256). Because atomic "
        "exchange was used strictly as an experimental stress condition, these large speedups should not be generalized to all "
        "multithreaded applications. We did not collect hardware coherence counters, so these measurements establish conditional "
        "timing differences for the tested workloads without directly counting cache-coherence traffic. Code, raw CSV data, and "
        "reproduction instructions are publicly available at "
        '<link href="https://github.com/Fearfestiwal/false-sharing-research-project" color="#1D4ED8">'
        "https://github.com/Fearfestiwal/false-sharing-research-project</link>."
    )
    abs_tbl = Table([[Paragraph(abs_text, s_abs)]], colWidths=[174 * mm])
    abs_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(abs_tbl)
    story.append(Spacer(1, 4))

    # Section 1
    story.append(Paragraph("1. Motivation and research question", s_h1))
    story.append(Paragraph(
        "Padding changes <i>where</i> each worker writes in memory, while local accumulation changes <i>how often</i> it writes. "
        "Comparing the two without holding write frequency constant mixes two separate mechanisms. We ask: How do core placement, "
        "worker count, and publication interval change the speedup from cache-line separation, and what timing difference remains "
        "when writes are batched inside an already separated layout?", s_body))
    story.append(KeepTogether([
        scaled_image(fig1_path, max_w_mm=166, max_h_mm=74),
        Paragraph("Figure 1. Four-worker layout and publication schematic. All runs verify actual runtime addresses; twelve adjacent 8-byte states span two 64-byte cache lines.", s_cap)
    ]))

    # Section 2
    story.append(Paragraph("2. Background and experimental design", s_h1))
    story.append(Paragraph(
        "Bolosky and Scott defined false sharing as accesses to separate variables inside the same coherence block that trigger "
        "extra coherence traffic, and noted how hard it is to quantify cleanly [1]. Intel outlines a profiling-first workflow for "
        "locating contended fields and testing alignment fixes [2]. False sharing is well established, so this paper focuses on "
        "measuring when each mitigation pays off on a hybrid laptop CPU and checking whether the same behavior holds across two "
        "additional machines (x86-64 and ARM64). Sections 2 through 4 report the initial ordinary-store experiment. Section 5 "
        "presents the matched atomic extension and three-machine validation; timings from separate protocols are kept separate.", s_body))
    story.append(Paragraph(
        "On a hybrid processor, a single logical-CPU count hides the difference between performance and efficiency cores [3]. "
        "We enumerate physical cores through Windows <i>GetLogicalProcessorInformationEx</i> [4] and read per-CPU CPUID leaf 0x1A "
        "to separate P cores (type 0x40) from E cores (type 0x20). On the primary Intel Core i7-13620H host, this gives six P cores "
        "(two SMT siblings each, 12 logical CPUs) and four E cores (4 logical CPUs).", s_body))

    t1_data = [
        ["Factor", "Levels and experimental control"],
        ["Layout", "8-byte stride (adjacent) and 64-byte stride (separated). Base allocation aligned to 64 bytes."],
        ["Publication interval B", "1, 16, 256, and N=16,000,000 iterations (final level writes only once at the end)."],
        ["P physical", "1, 2, 4, and 6 workers pinned to logical CPUs [0, 2, 4, 6, 8, 10]."],
        ["P SMT", "2, 4, 8, and 12 workers pinned to prefixes of [0, 1, ..., 11], filling sibling pairs first."],
        ["E physical", "1, 2, and 4 workers pinned to prefixes of [12, 13, 14, 15]."],
        ["Replication", "1 warm-up plus 9 measured runs per condition (88 conditions = 792 measured runs)."],
    ]
    story.append(KeepTogether([
        make_table(t1_data, [38, 136]),
        Paragraph("Table 1. Primary experimental factors and thread-placement controls.", s_cap)
    ]))

    story.append(Paragraph("2.1 Workload and controlled comparisons", s_h2))
    story.append(Paragraph(
        "Each worker owns a uint64_t state seeded with its worker index plus one and runs the recurrence "
        "x = 6364136223846793005*x + 1442695040888963407 (mod 2<super>64</super>) for N iterations, writing its state every B steps. "
        "After every run, the program checks every worker's final value against the expected deterministic output. Holding B and core "
        "placement fixed while changing the stride from 8 to 64 bytes isolates memory layout, since arithmetic work and write counts "
        "stay identical. Changing B inside the 64-byte layout tests batching with inter-worker line sharing removed, although it also "
        "changes how many times the outer loop executes.", s_body))

    # Section 3
    story.append(Paragraph("3. Measurement protocol and primary results", s_h1))
    story.append(Paragraph(
        "We compiled the primary benchmark with Zig 0.13.0 (bundled Clang, C++17, -O2) and disabled loop unrolling and vectorization "
        "so the dependent arithmetic loop stays comparable across builds. Volatile stores keep intermediate writes from being "
        "optimized away without acting as synchronization [5]. Atomic flags and a Win32 event form the start and completion gate, "
        "and each worker sets its single-CPU affinity mask before timing starts. Elapsed time is recorded with "
        "<i>std::chrono::steady_clock</i>. Condition order is shuffled using seed 20261112, warm-ups run before measured trials, "
        "and all outliers remain in the dataset. We report medians, interquartile ranges (IQR), and descriptive 95% bootstrap "
        "intervals from 5,000 resamples.", s_body))

    story.append(KeepTogether([
        scaled_image(FIGS / "scaling.png", max_w_mm=160, max_h_mm=82),
        Paragraph("Figure 2. Per-iteration ordinary-store publication (B=1). Error bars show IQR. Each worker runs the same N iterations (weak scaling).", s_cap)
    ]))

    story.append(Paragraph("3.1 Layout effects at equal write frequency", s_h2))
    story.append(Paragraph(
        "With six physical P-core workers at B=1, median times were 38.79 ms for adjacent slots and 36.67 ms for separated slots, "
        "a ratio of 1.06 [0.83, 1.27]. Four E-core workers gave 0.97 [0.42, 1.22]. Both intervals span one, so ordinary stores in "
        "this setup show no reliable padding speedup. Two SMT workers on one P core gave 0.86 [0.71, 1.04]. Across all multiworker "
        "cells that published during the loop, the highest ratio was 1.34 [0.80, 1.43] (P_physical, 2 workers, B=256), an exploratory "
        "maximum across 88 cells.", s_body))

    # Section 4
    story.append(KeepTogether([
        Paragraph("4. Publication frequency and layout interaction", s_h1),
        scaled_image(FIGS / "batching.png", max_w_mm=160, max_h_mm=78),
        Paragraph("Figure 3. Publication interval at the largest worker count in each placement family (medians of nine runs).", s_cap)
    ]))

    t2_data = [
        ["Six physical P workers (N=16M)", "Adjacent (ms)", "Separated (ms)", "Layout ratio [95% bootstrap]"],
        ["B = 1", "38.79", "36.67", "1.06 [0.83, 1.27]"],
        ["B = 16", "28.38", "27.51", "1.03 [0.93, 1.52]"],
        ["B = 256", "26.97", "29.48", "0.91 [0.86, 1.51]"],
        ["Final only (local)", "29.79", "30.79", "0.97 [0.74, 1.49]"],
    ]
    story.append(KeepTogether([
        make_table(t2_data, [58, 34, 34, 48]),
        Paragraph("Table 2. Initial ordinary-store medians and layout ratios on six physical P cores.", s_cap)
    ]))

    story.append(Paragraph(
        "Inside the 64-byte separated layout on six physical P cores, B=1 took 36.67 ms and final-only publication took 30.79 ms, "
        "a ratio of 1.19. Because line separation stayed fixed, that speedup comes from fewer writes and fewer outer-loop boundaries.", s_body))

    story.append(KeepTogether([
        scaled_image(FIGS / "effects.png", max_w_mm=160, max_h_mm=80),
        Paragraph("Figure 4. Layout ratios across the full ordinary-store grid (values above 1 favor separation).", s_cap)
    ]))

    # Section 5
    story.append(Paragraph("5. Exploratory extension: atomic writes and cross-architecture validation", s_h1))
    story.append(Paragraph(
        "Because the initial ordinary-store runs showed no clear six-P-core padding gain, we added a workload-matched extension "
        "(N=1,000,000 iterations/worker, 7 measured runs plus 1 warm-up per cell across 88 conditions, 616 runs per mode) comparing "
        "ordinary stores against relaxed atomic exchange (<i>memory_order_relaxed</i>). Atomic exchange was introduced strictly as "
        "an experimental stress condition to probe sensitivity to write-primitive strength; ordinary worker-owned counters do not "
        "require atomic exchange, and the large speedups observed under this stress condition must not be generalized to typical "
        "multithreaded applications. The atomic and store blocks ran one after the other without interleaving, so absolute times "
        "across the two blocks reflect session state as well as instruction cost.", s_body))

    story.append(KeepTogether([
        scaled_image(FIGS / "atomic_scaling.png", max_w_mm=160, max_h_mm=80),
        Paragraph("Figure 5. Atomic-exchange extension at B=1 (medians and IQR from seven runs per cell).", s_cap)
    ]))

    t3_data = [
        ["Placement / workers / interval", "Ordinary-store ratio", "Atomic-exchange ratio"],
        ["P physical / 6 / B=1", "1.04 [0.74, 1.25]", "8.50 [7.61, 11.46]"],
        ["P physical / 6 / B=16", "1.06 [0.81, 1.27]", "6.85 [5.31, 7.47]"],
        ["P physical / 6 / B=256", "0.84 [0.77, 1.15]", "0.93 [0.60, 1.25]"],
        ["P physical / 6 / final", "1.14 [0.81, 1.35]", "1.32 [0.91, 1.49]"],
        ["P SMT / 2 / B=1", "1.33 [0.77, 1.44]", "1.11 [0.84, 1.34]"],
        ["P SMT / 12 / B=1", "1.14 [0.81, 1.39]", "7.35 [6.93, 8.41]"],
        ["E physical / 4 / B=1", "1.08 [0.91, 4.94]", "7.53 [6.49, 8.54]"],
    ]
    story.append(KeepTogether([
        make_table(t3_data, [66, 54, 54]),
        Paragraph("Table 3. Matched ordinary-store and atomic-exchange layout ratios (1,232 measured runs).", s_cap)
    ]))

    story.append(Paragraph(
        "On six physical P cores at B=1, atomic-exchange medians fell from 122.98 ms (adjacent) to 14.47 ms (separated), an 8.50x "
        "speedup, then dropped to 0.93x at B=256. Disassembly verified a memory <i>xchg</i> instruction inside the atomic loop. "
        "Two SMT siblings sharing one P core reached only 1.11x [0.84, 1.34] even under atomic B=1.", s_body))

    story.append(Paragraph("5.1 Cross-machine and cross-architecture validation (x86-64 and Apple M1 ARM64)", s_h2))
    story.append(Paragraph(
        "To check whether the same behavior holds on other hardware and compilers, we ran a cross-platform C++17 benchmark "
        "(4 threads, 1,000,000 iterations/thread, 5 measured runs plus 1 warm-up, testing 8B adjacent, 64B padded, and 128B padded "
        "slots) on three machines: two Windows 11 x86-64 laptops (MSVC /O2) and an Apple M1 ARM64 MacBook Air (macOS, clang++ -O2, "
        "where <i>sysctl hw.cachelinesize</i> reports 128 bytes).", s_body))

    t4_data = [
        ["Mode / batch (4T, 1M)", "Windows PC #1 (x86-64)", "Windows PC #2 (x86-64)", "Apple M1 Air (ARM64, 128B)"],
        ["Ordinary store, B=1", "0.95 -> 0.94 ms (1.01x)", "1.10 -> 1.02 ms (1.09x)", "1.04 -> 1.04 ms (1.00x)"],
        ["Atomic exchange, B=1", "41.32 -> 4.01 ms (10.30x)", "50.52 -> 5.22 ms (9.68x)", "60.87 -> 1.46 / 1.05 ms (41.6x / 58.1x)"],
        ["Atomic exchange, B=16", "1.64 -> 0.95 ms (1.72x)", "3.26 -> 1.12 ms (2.91x)", "4.01 -> 1.03 ms (3.90x)"],
        ["Atomic exchange, B=256", "0.93 -> 0.93 ms (1.00x)", "1.11 -> 1.07 ms (1.04x)", "1.03 -> 1.03 ms (1.00x)"],
        ["Atomic exchange, local", "0.92 -> 0.94 ms (0.97x)", "1.10 -> 1.07 ms (1.03x)", "1.03 -> 1.03 ms (1.00x)"],
    ]
    story.append(KeepTogether([
        make_table(t4_data, [37, 40, 40, 57]),
        Paragraph("Table 4. Three-machine archived CSV medians (Adjacent 8B -> Padded 64B, plus 128B on Apple M1 at B=1).", s_cap)
    ]))

    story.append(KeepTogether([
        scaled_image(PRES / "chart_3machines.png", max_w_mm=160, max_h_mm=78),
        Paragraph("Figure 6. Atomic padding speedup across update intervals on two x86-64 Windows laptops and Apple M1 ARM64.", s_cap)
    ]))

    story.append(Paragraph(
        "All three systems showed the same trend: large atomic padding gains at B=1, smaller gains at B=16, and no gain at B=256 "
        "or local accumulation (about 1.00x). On Apple M1, verified addresses in results/macbook_m1/addresses.csv confirm that "
        "64-byte padded slots still pair up inside shared 128-byte cache lines (lines 4145414528 and 4145414529), whereas 128-byte "
        "padded slots occupy four separate 128-byte lines. In the archived M1 run, atomic B=1 dropped from 60.87 ms (8B) to 1.46 ms "
        "(64B, 41.61x) and further to 1.05 ms (128B, 58.11x). A separate 2-thread affinity check on Windows PC #1 showed the same "
        "hardware split: pinning two atomic workers to SMT siblings on one P core (CPU 0 and CPU 1) gave 1.02x (19.18 vs. 18.77 ms), "
        "whereas pinning them to two separate physical P cores (CPU 0 and CPU 2) gave 3.20x (40.53 vs. 12.65 ms).", s_body))

    # Section 6
    story.append(Paragraph("6. Interpretation, costs, and limitations", s_h1))
    story.append(Paragraph("6.1 Answer to the research question and memory cost", s_h2))
    story.append(Paragraph(
        "Cache-line separation and write batching solve different problems. Padding produced large speedups only under our "
        "experimental atomic-exchange stress condition when separate physical cores wrote frequently (8.50x on 6 P cores; "
        "9.68x to 41.61x for 64-byte padding across the three validation machines at B=1, reaching 58.11x with 128-byte padding "
        "on Apple M1). Those stress-condition numbers do not generalize to all multithreaded applications: when writes dropped to "
        "once per 256 steps, ran only at the end, used ordinary stores, or shared an SMT core, padding gave little or no benefit. "
        "Reserving 64 bytes per worker instead of 8 bytes increases counter storage by 8x (384 bytes vs. 48 bytes for six workers; "
        "16x for 128-byte padding). Measuring the actual write rate, synchronization primitive, and core placement first avoids "
        "paying that memory cost where it brings no speedup.", s_body))

    story.append(Paragraph("6.2 Evidence boundary and threats to validity", s_h2))
    story.append(Paragraph(
        "Runtime address logs confirm when slots share or avoid a 64-byte line, but we did not record hardware PMU events such as "
        "HITM or cache invalidations [2]. Our results therefore document timing contrasts consistent with false sharing without "
        "directly counting coherence bus messages. The primary 2,024-run dataset was gathered on an active Windows 11 laptop "
        "(Balanced power plan, starting at 85% battery) without continuous frequency or temperature logs, so background activity "
        "and power state remain confounders.", s_body))
    story.append(Paragraph(
        "Because the benchmark uses weak scaling, total arithmetic work grows with worker count; rising elapsed time indicates "
        "contention and synchronization overhead, not negative strong-scaling speedup. Batching changes both store count and loop "
        "boundaries at the same time. Raw CSV files and runtime address logs are archived for all three machines in the public repository.", s_body))

    story.append(Paragraph("6.3 Conclusion", s_h2))
    story.append(Paragraph(
        "Memory layout, publication interval, and write primitive should be measured separately. Across two x86-64 Windows laptops "
        "and an Apple M1 ARM64 MacBook Air, padding gave large speedups only under the experimental atomic-exchange stress condition "
        "with frequent cross-core writes, and lost its advantage once writes were batched or performed with ordinary stores. These "
        "stress-test gains should not be generalized to all multithreaded software. Direct quantification of coherence traffic "
        "remains future work with hardware event counters.", s_body))

    # Section 7
    story.append(Paragraph("7. Reproducibility, AI declaration, and references", s_h1))
    story.append(Paragraph("7.1 Public reproducibility package", s_h2))
    story.append(Paragraph(
        'Source code, build and run scripts, raw CSV measurements, verified address logs (<font face="Courier" size="8.6">addresses.csv</font> '
        'with <font face="Courier" size="8.6">address / 64</font> and <font face="Courier" size="8.6">address % 64</font>), '
        'and documentation are publicly archived at:<br/>'
        '<link href="https://github.com/Fearfestiwal/false-sharing-research-project" color="#1D4ED8">'
        "https://github.com/Fearfestiwal/false-sharing-research-project</link><br/>"
        "The archive covers the 2,288-run primary study (264 warm-ups, 2,024 measured runs, and 9,568 verified address records) "
        "alongside the cross-platform Windows and macOS benchmark suite. All correctness, affinity, and alignment checks passed, "
        "and no synthetic values were substituted.", s_body))

    story.append(Paragraph("7.2 Declaration of Generative AI and AI-Assisted Technologies", s_h2))
    story.append(Paragraph(
        "We used OpenAI Codex and Google Gemini (Antigravity) to assist with benchmark scaffolding, automation and analysis "
        "scripts, figure generation, and manuscript editing. Both authors (Zeynep Uyan and Muhammed Enes Aksoy) shaped the "
        "experimental design around coordinator feedback, compiled and ran benchmarks on three physical machines (two x86-64 "
        "Windows laptops and an Apple M1 MacBook Air), checked runtime memory alignment, correctness checksums, and thread "
        "affinity logs, and verified every number, citation, and limitation in this report.", s_body))

    story.append(Paragraph("7.3 References", s_h2))
    refs = [
        '[1] W. J. Bolosky and M. L. Scott, "False Sharing and its Effect on Shared Memory Performance," USENIX Symposium on Experiences with Distributed and Multiprocessor Systems (SEDMS IV), 1993. <link href="https://www.usenix.org/legacy/publications/library/proceedings/sedms4/bolosky.html" color="#1D4ED8">https://www.usenix.org/legacy/publications/library/proceedings/sedms4/bolosky.html</link>',
        '[2] Intel, "False Sharing," Intel VTune Profiler Performance Analysis Cookbook, version 2024.2, 2024. <link href="https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2024-2/false-sharing.html" color="#1D4ED8">https://www.intel.com/content/www/us/en/docs/vtune-profiler/cookbook/2024-2/false-sharing.html</link>',
        '[3] Intel, "Game Dev Guide for 12th Gen Intel Core Processor," updated June 13, 2022 (used for hybrid-topology principles). <link href="https://www.intel.com/content/www/us/en/developer/articles/guide/12th-gen-intel-core-processor-gamedev-guide.html" color="#1D4ED8">https://www.intel.com/content/www/us/en/developer/articles/guide/12th-gen-intel-core-processor-gamedev-guide.html</link>',
        '[4] Microsoft, "GetLogicalProcessorInformationEx function (sysinfoapi.h)," Microsoft Learn. <link href="https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex" color="#1D4ED8">https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformationex</link>',
        '[5] LLVM Project, "LLVM Atomic Instructions and Concurrency Guide," section on atomic and volatile operations. <link href="https://llvm.org/docs/Atomics.html" color="#1D4ED8">https://llvm.org/docs/Atomics.html</link>',
    ]
    for r in refs:
        story.append(Paragraph(r, s_ref))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Keywords:</b> false sharing; memory layout; publication batching; hybrid processors; multithreading; cross-architecture validation; reproducibility.", s_cap))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Generated humanized final PDF: {OUT_PDF}")


if __name__ == "__main__":
    build_pdf()
