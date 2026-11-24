import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(r"C:\Users\muham\.gemini\antigravity\scratch\false-sharing-research-project")
ASSETS = ROOT / "presentation_assets"
ASSETS.mkdir(parents=True, exist_ok=True)
OUT_PPTX = ROOT / "False_Sharing_Presentation_Group4.pptx"

# Color palette (Clean Academic Dark-Navy + Crisp Light Canvas)
NAVY      = RGBColor(15, 23, 42)     # #0F172A
SLATE     = RGBColor(30, 41, 59)     # #1E293B
MUTED     = RGBColor(100, 116, 139)  # #64748B
LIGHT_BG  = RGBColor(248, 250, 252)  # #F8FAFC
WHITE     = RGBColor(255, 255, 255)
BLUE      = RGBColor(37, 99, 235)    # #2563EB
TEAL      = RGBColor(13, 148, 136)   # #0D9488
AMBER     = RGBColor(217, 119, 6)    # #D97706
RED       = RGBColor(220, 38, 38)    # #DC2626
BORDER    = RGBColor(226, 232, 240)  # #E2E8F0

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 0.8


def make_charts():
    # --- CHART 1: Main Study (6 Physical P-Cores, Atomic B=1) ---
    fig, ax = plt.subplots(figsize=(6.2, 3.8), dpi=300)
    labels = ["Adjacent (8B)\nAtomic B=1", "Padded (64B)\nAtomic B=1"]
    vals = [122.98, 14.47]
    colors = ["#DC2626", "#0D9488"]
    bars = ax.bar(labels, vals, color=colors, width=0.5, edgecolor="none", zorder=3)
    ax.set_ylabel("Median Completion Time (ms)", fontsize=10, color="#1E293B", fontweight="bold")
    ax.set_title("Main Study: 6 Physical P-Cores (2,024 Measured Runs)", fontsize=11, color="#0F172A", fontweight="bold", pad=12)
    ax.set_ylim(0, 145)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 3.5, f"{v:.2f} ms",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color="#0F172A")
    ax.annotate("~8.5x Speedup\n(Same write count!)", xy=(1, 18), xytext=(0.55, 78),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2),
                fontsize=10.5, fontweight="bold", color="#2563EB", ha="center",
                bbox=dict(boxstyle="round,pad=0.4", fc="#EFF6FF", ec="#2563EB", lw=1))
    fig.tight_layout()
    fig.savefig(ASSETS / "chart_main_study.png", facecolor="white")
    plt.close(fig)

    # --- CHART 2: SMT vs Physical Cores (Affinity Proof) ---
    fig, ax = plt.subplots(figsize=(5.6, 3.5), dpi=300)
    groups = ["Same P-Core\nSMT Siblings (CPU 0 & 1)", "Two Separate Physical\nP-Cores (CPU 0 & 2)"]
    adj_vals = [19.18, 40.53]
    pad_vals = [18.77, 12.65]
    x = np.arange(len(groups))
    w = 0.34
    b1 = ax.bar(x - w/2, adj_vals, w, label="Adjacent (8B)", color="#DC2626", zorder=3)
    b2 = ax.bar(x + w/2, pad_vals, w, label="Padded (64B)", color="#0D9488", zorder=3)
    ax.set_ylabel("Completion Time (ms)", fontsize=10, color="#1E293B", fontweight="bold")
    ax.set_title("Thread Placement Effect (2 Threads, 2M Atomic Ops)", fontsize=10.5, color="#0F172A", fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=9.5, color="#1E293B")
    ax.set_ylim(0, 56)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1.0, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#0F172A")
    ax.text(0, 26.0, "1.02x\n(Shared L1)", ha="center", fontsize=9, fontweight="bold", color="#64748B")
    ax.text(1, 47.5, "3.20x\n(Cross-core ping-pong)", ha="center", fontsize=9, fontweight="bold", color="#2563EB")
    fig.tight_layout()
    fig.savefig(ASSETS / "chart_affinity.png", facecolor="white")
    plt.close(fig)

    # --- CHART 3: 3-Machine Cross-Architecture Speedup Across Batch Sizes ---
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=300)
    batches = ["B=1\n(Every step)", "B=16\n(16 steps)", "B=256\n(256 steps)", "Local\n(End only)"]
    x = np.arange(len(batches))
    w = 0.25
    win_m = [10.30, 1.72, 1.00, 0.97]
    win_z = [9.68,  2.91, 1.04, 1.03]
    mac_m1 = [57.50, 3.86, 1.00, 1.00]  # midpoint of 53.03x-61.96x & 3.82x-3.89x

    b1 = ax.bar(x - w, win_m, w, label="Windows PC #1 (x86-64, MSVC)", color="#2563EB", zorder=3)
    b2 = ax.bar(x,     win_z, w, label="Windows PC #2 (x86-64, MSVC)", color="#0D9488", zorder=3)
    b3 = ax.bar(x + w, mac_m1, w, label="MacBook Air (Apple M1 ARM64, clang++)", color="#D97706", zorder=3)

    ax.axhline(1.0, color="#64748B", linestyle=":", linewidth=1.2, zorder=2)
    ax.set_ylabel("Padding Speedup (Adjacent 8B / Padded 64B)", fontsize=10, color="#1E293B", fontweight="bold")
    ax.set_title("Cross-Machine Atomic Speedup vs. Update Frequency (4 Threads, 1M Ops)", fontsize=10.5, color="#0F172A", fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(batches, fontsize=9.5, color="#1E293B")
    ax.set_ylim(0, 68)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1.1, f"{h:.1f}x",
                    ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#0F172A")
    fig.tight_layout()
    fig.savefig(ASSETS / "chart_3machines.png", facecolor="white")
    plt.close(fig)

    # --- CHART 4: Apple M1 8B vs 64B vs 128B (Empirical vs Assumption) ---
    fig, ax = plt.subplots(figsize=(5.8, 3.6), dpi=300)
    layouts = ["Adjacent\n(8B)", "Padded\n(64B)", "Padded\n(128B)"]
    times_m1 = [59.77, 1.04, 1.045]  # avg of 55.07 & 64.46
    colors = ["#DC2626", "#0D9488", "#2563EB"]
    bars = ax.bar(layouts, times_m1, color=colors, width=0.52, zorder=3)
    ax.set_ylabel("Median Time (ms) — Lower is Better", fontsize=9.5, color="#1E293B", fontweight="bold")
    ax.set_title("Apple M1 (hw.cachelinesize = 128B) — Atomic B=1", fontsize=10.5, color="#0F172A", fontweight="bold", pad=10)
    ax.set_ylim(0, 72)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, v in zip(bars, times_m1):
        ax.text(bar.get_x() + bar.get_width()/2, v + 1.8, f"{v:.2f} ms",
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#0F172A")
    ax.annotate("64B already matches 128B!\n(No extra gain from 2x memory)",
                xy=(1.5, 3.5), xytext=(1.45, 34),
                arrowprops=dict(arrowstyle="->", color="#0D9488", lw=1.8),
                fontsize=9.2, fontweight="bold", color="#0F172A", ha="center",
                bbox=dict(boxstyle="round,pad=0.4", fc="#F0FDFA", ec="#0D9488", lw=1))
    fig.tight_layout()
    fig.savefig(ASSETS / "chart_m1_64_128.png", facecolor="white")
    plt.close(fig)


def set_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, title, subtitle, slide_num):
    # Top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.65), Inches(0.28), Inches(11.3), Inches(0.65))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = NAVY

    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(13)
        p2.font.color.rgb = MUTED

    # Slide number pill
    num_box = slide.shapes.add_textbox(Inches(12.2), Inches(0.32), Inches(0.6), Inches(0.4))
    np_ = num_box.text_frame.paragraphs[0]
    np_.text = f"{slide_num}/10"
    np_.alignment = PP_ALIGN.RIGHT
    np_.font.size = Pt(11)
    np_.font.bold = True
    np_.font.color.rgb = MUTED

    # Footer
    ft = slide.shapes.add_textbox(Inches(0.65), Inches(7.1), Inches(12.0), Inches(0.3))
    fp = ft.text_frame.paragraphs[0]
    fp.text = "Architecture of Computers — Student Research Challenge 2026  |  Zeynep Uyan (75616) & Muhammed Enes Aksoy (75569)  |  Group-4"
    fp.font.size = Pt(9.5)
    fp.font.color.rgb = MUTED


def add_card(slide, left, top, width, height, title, bullets, accent=BLUE, bg_color=WHITE):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = BORDER
    shape.line.width = Pt(1.0)
    shape.adjustments[0] = 0.04

    # Accent strip on top
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left + 0.02), Inches(top), Inches(width - 0.04), Inches(0.08))
    strip.fill.solid()
    strip.fill.fore_color.rgb = accent
    strip.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.22), Inches(top + 0.18), Inches(width - 0.44), Inches(height - 0.28))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(15.5)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(6)

    for b in bullets:
        bp = tf.add_paragraph()
        bp.text = "•  " + b
        bp.font.size = Pt(12.5)
        bp.font.color.rgb = SLATE
        bp.space_after = Pt(5)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ==================== SLIDE 1: TITLE ====================
    s1 = prs.slides.add_slide(blank)
    set_bg(s1, NAVY)

    accent = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), Inches(7.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = BLUE
    accent.line.fill.background()

    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.95), Inches(1.15), Inches(4.7), Inches(0.48))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 58, 138)
    badge.line.fill.background()
    bp = badge.text_frame.paragraphs[0]
    bp.text = "STUDENT RESEARCH CHALLENGE 2026  •  VISTULA UNIVERSITY"
    bp.font.size = Pt(10.5)
    bp.font.bold = True
    bp.font.color.rgb = RGBColor(191, 219, 254)
    bp.alignment = PP_ALIGN.CENTER

    tb = s1.shapes.add_textbox(Inches(0.95), Inches(1.95), Inches(11.4), Inches(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "When More Threads Become Slower:"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.text = "Investigating False Sharing and Its Mitigation"
    p2.font.size = Pt(34)
    p2.font.bold = True
    p2.font.color.rgb = RGBColor(96, 165, 250)
    p2.space_before = Pt(8)

    sub = s1.shapes.add_textbox(Inches(0.95), Inches(4.45), Inches(10.5), Inches(0.9))
    stf = sub.text_frame
    stf.word_wrap = True
    sp = stf.paragraphs[0]
    sp.text = "Separating Memory Layout (Padding) from Update Frequency (Batching & Local Accumulation) Across x86-64 and Apple Silicon ARM64"
    sp.font.size = Pt(16)
    sp.font.color.rgb = RGBColor(203, 213, 225)

    meta = s1.shapes.add_textbox(Inches(0.95), Inches(5.75), Inches(11.0), Inches(1.1))
    mtf = meta.text_frame
    mp1 = mtf.paragraphs[0]
    mp1.text = "Zeynep Uyan (75616)   •   Muhammed Enes Aksoy (75569)   •   Group-4"
    mp1.font.size = Pt(15)
    mp1.font.bold = True
    mp1.font.color.rgb = WHITE
    mp2 = mtf.add_paragraph()
    mp2.text = "Course: Architecture of Computers   |   Lecturer: Tariq ElDakruri   |   Coordinator: Tughanbulut Kurtulush"
    mp2.font.size = Pt(12)
    mp2.font.color.rgb = RGBColor(148, 163, 184)
    mp2.space_before = Pt(6)

    add_notes(s1, "TR Konusma Notu: Merhaba, biz Zeynep Uyan ve Muhammed Enes Aksoy (Group-4). Bugun cok is parcalikli (multithreaded) programlarda daha fazla thread eklemenin neden bazen programi yavaslattigini, yani False Sharing olgusunu ve cozum yontemlerini inceledigimiz arastirmamizi sunacagiz.")

    # ==================== SLIDE 2: PROBLEM & RQ ====================
    s2 = prs.slides.add_slide(blank)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "1. The Problem: False Sharing & Research Question",
               "Independent variables can still collide inside the CPU cache hierarchy", 2)

    add_card(s2, 0.65, 1.25, 5.8, 2.75, "Why Does False Sharing Happen?", [
        "CPUs do not fetch individual 8-byte integers from RAM; they move fixed blocks called cache lines (typically 64B on x86-64, 128B reported on Apple M1).",
        "Multiple 8-byte per-thread counters placed adjacently land in the SAME cache line.",
        "When different cores modify distinct counters in that shared line, cache-coherence traffic bounces the line between cores."
    ], accent=RED)

    add_card(s2, 6.75, 1.25, 5.9, 2.75, "Visual Memory Layout Comparison", [
        "Adjacent (8B each):  [ C0 | C1 | C2 | C3 | ... ]  → 1 shared 64B line",
        "Padded (alignas(64)):  [ C0 + 56B pad ]  [ C1 + 56B pad ]  → separate lines",
        "Local Accumulation:  Compute in CPU register → write to memory once at end",
        "Key trade-off: Padding adds 8x–16x counter memory overhead; does it always pay off?"
    ], accent=TEAL)

    # Highlighted Research Question Banner
    rq = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.65), Inches(4.35), Inches(12.0), Inches(2.2))
    rq.fill.solid()
    rq.fill.fore_color.rgb = NAVY
    rq.line.fill.background()
    rq.adjustments[0] = 0.06
    rtb = s2.shapes.add_textbox(Inches(1.0), Inches(4.6), Inches(11.3), Inches(1.8))
    rtf = rtb.text_frame
    rtf.word_wrap = True
    rp1 = rtf.paragraphs[0]
    rp1.text = "APPROVED RESEARCH QUESTION"
    rp1.font.size = Pt(11.5)
    rp1.font.bold = True
    rp1.font.color.rgb = RGBColor(96, 165, 250)
    rp2 = rtf.add_paragraph()
    rp2.text = "“How do thread count and update frequency affect the performance of multithreaded counters, and under which conditions do cache-line separation and local accumulation improve performance relative to adjacent counters?”"
    rp2.font.size = Pt(18.5)
    rp2.font.italic = True
    rp2.font.color.rgb = WHITE
    rp2.space_before = Pt(10)

    add_notes(s2, "TR Konusma Notu: Islemciler bellegi 8 baytlik tek tek degiskenler degil, cache line denen 64 baytlik bloklar halinde tasir. 4 thread kendi ayri sayacina yazsa bile, bu sayaclar bellekte yan yanaysa ayni cache line'a duser ve cekirdekler arasinda surekli el degistirir. Arastirma sorumuz: Padding ve yerel biriktirme hangi kosullarda gercekten ise yariyor?")

    # ==================== SLIDE 3: METHODOLOGICAL DISTINCTION ====================
    s3 = prs.slides.add_slide(blank)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "2. Methodology: Separating Layout from Update Frequency",
               "Directly addressing the coordinator's methodological distinction", 3)

    add_card(s3, 0.65, 1.3, 3.8, 3.7, "A. Memory Layout (Padding)", [
        "Keeps update frequency FIXED.",
        "Changes only spacing between counters: 8B vs 64B (alignas(64)) vs 128B (alignas(128)).",
        "Isolates cache-line contention / false sharing effects.",
        "Runtime addresses verified: addr % 64 and addr / 64 logged."
    ], accent=BLUE)

    add_card(s3, 4.75, 1.3, 3.8, 3.7, "B. Update Frequency (Batching)", [
        "Keeps memory layout FIXED.",
        "Publishes result every B = 1, 16, 256 iterations, or only at the end (Local).",
        "Isolates the benefit of doing fewer memory writes.",
        "Same logical work (LCG math) verified for every run."
    ], accent=TEAL)

    add_card(s3, 8.85, 1.3, 3.8, 3.7, "C. Memory Operation Type", [
        "Normal Store: volatile uint64_t store (assembly checked to prevent dead-store elimination).",
        "Atomic Exchange: atomic::exchange(..., memory_order_relaxed).",
        "Tests whether padding sensitivity depends on operation strength."
    ], accent=AMBER)

    add_card(s3, 0.65, 5.25, 12.0, 1.55, "Experimental Rigor & Reproducibility Controls", [
        "Deterministic workload (x = x * A + C mod 2^64) with exact checksum verification after every trial — no skipped work allowed.",
        "Synchronized start gate (atomic ready/go), warm-up runs excluded (rep = -1), randomized execution order (fixed seed), median + IQR reporting, full CSV logging."
    ], accent=NAVY, bg_color=RGBColor(241, 245, 249))

    add_notes(s3, "TR Konusma Notu: Asistanimizin en onemli uyarisi suydu: Padding ile yerel biriktirme ayni mekanizma degil. Padding ayni siklikta yazip degiskenleri ayirir; yerel biriktirme ise daha az yazar. Biz bu iki etkiyi ayirmak icin ayni yazma sikliginda yerlesimi, ayni yerlesimde yazma sikligini (B=1, 16, 256, Local) ve ek olarak normal yazma ile atomik yazmayi ayri ayri olctuk.")

    # ==================== SLIDE 4: TOPOLOGY & AFFINITY ====================
    s4 = prs.slides.add_slide(blank)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "3. Hardware Topology & Thread Placement (Affinity)",
               "Why '2 threads' is meaningless without specifying physical vs. SMT cores", 4)

    add_card(s4, 0.65, 1.3, 5.6, 2.55, "Hybrid CPU Architecture (10 Physical / 16 Logical)", [
        "6 Performance (P) cores × 2 SMT (Hyper-Threading) = 12 logical CPUs.",
        "4 Efficiency (E) cores × 1 (no SMT) = 4 logical CPUs.",
        "Main study pins threads via Windows SetThreadAffinityMask and logs actual CPU IDs; P-cores, SMT siblings, and E-cores are never mixed blindly."
    ], accent=BLUE)

    add_card(s4, 0.65, 4.1, 5.6, 2.65, "Controlled Affinity Experiment Insight", [
        "Same P-core SMT siblings (CPU 0 & 1): 19.18 ms vs 18.77 ms → 1.02x (no padding benefit because both threads share the same L1 cache!).",
        "Two separate physical P-cores (CPU 0 & 2): 40.53 ms → 12.65 ms → 3.20x speedup from padding (cross-core cache-line bouncing)."
    ], accent=TEAL)

    s4.shapes.add_picture(str(ASSETS / "chart_affinity.png"), Inches(6.55), Inches(1.45), width=Inches(6.15))

    add_notes(s4, "TR Konusma Notu: Islemcimizde 6 P-core (SMT ile 12 mantiksal) ve 4 E-core (4 mantiksal) var. Sagdaki grafikte canli kanitini goruyorsunuz: 2 thread'i ayni fiziksel cekirdegin SMT kardeslerine (CPU 0 ve 1) koydugumuzda ayni L1 onbellegi paylastiklari icin padding hic fark yaratmadi (1.02x). Ama iki ayri fiziksel cekirdege (CPU 0 ve 2) koydugumuzda 3.20x hizlanma cikti!")

    # ==================== SLIDE 5: MAIN STUDY RESULTS ====================
    s5 = prs.slides.add_slide(blank)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "4. Main Study Results (2,024 Measured Runs)",
               "6 physical P-cores — padding's benefit depends strongly on operation type & frequency", 5)

    s5.shapes.add_picture(str(ASSETS / "chart_main_study.png"), Inches(0.65), Inches(1.4), width=Inches(6.4))

    add_card(s5, 7.3, 1.35, 5.35, 2.5, "Key Findings (2,288 Total Runs)", [
        "264 warm-up + 2,024 measured runs; 9,568 memory address records verified (100% aligned).",
        "Normal stores (volatile): ~1.04x ratio on 6 P-cores with high variance → no reliable speedup demonstrated.",
        "Atomic exchange (B=1): 122.98 ms → 14.47 ms (~8.5x speedup)."
    ], accent=BLUE)

    add_card(s5, 7.3, 4.1, 5.35, 2.65, "What Happens When Writes Slow Down?", [
        "Reducing atomic publish frequency to B=256 eliminates the padding advantage completely.",
        "Negative/null results are genuine findings: padding is NOT a universal speedup — its value depends on write intensity and memory operation type."
    ], accent=AMBER)

    add_notes(s5, "TR Konusma Notu: Ana deneyimizde 2.024 olcum ve 9.568 adres dogrulamasi yaptik. Normal bellek yazmalarinda belirgin bir padding kazanimi gosteremedik (~1.04x). Ama her adimda atomik yazmada (B=1) 6 fiziksel P cekirdeginde 122.98 ms'den 14.47 ms'ye duserek ~8.5 kat hizlanma elde ettik. Yazma sikligi 256 adimda bire dusunce bu avantaj tamamen kayboldu.")

    # ==================== SLIDE 6: 3-MACHINE VALIDATION ====================
    s6 = prs.slides.add_slide(blank)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "5. Three-Machine Cross-Architecture Validation",
               "Independent verification across two Windows x86-64 PCs and Apple M1 ARM64", 6)

    s6.shapes.add_picture(str(ASSETS / "chart_3machines.png"), Inches(0.55), Inches(1.35), width=Inches(7.5))

    add_card(s6, 8.25, 1.35, 4.45, 5.4, "Consistent Across All 3 Machines", [
        "Windows PC #1 (x86-64, 16 CPU, MSVC): B=1 → 10.30x | B=16 → 1.72x | B=256 → 1.00x.",
        "Windows PC #2 (x86-64, 16 CPU, MSVC): B=1 → 9.68x | B=16 → 2.91x | B=256 → 1.04x.",
        "MacBook Air (Apple M1 ARM64, 8 CPU, clang++): B=1 → 53x–62x | B=16 → 3.8x–3.9x | B=256 → 1.00x.",
        "Conclusion holds across ISAs (x86 vs ARM), OSes (Windows vs macOS), and compilers (MSVC vs clang++)."
    ], accent=TEAL)

    add_notes(s6, "TR Konusma Notu: Tek bilgisayarla sinirli kalmamak icin ayni testi 3 bagimsiz bilgisayarda tekrarladik: iki farkli Windows x86-64 PC ve bir Apple M1 ARM64 MacBook Air. Ucunde de birebir ayni bilimsel desen cikti: B=1'de devasa hizlanma (9.7x ile 62x arasi), B=16'da dusus, B=256 ve Local'de 1.00x!")

    # ==================== SLIDE 7: APPLE M1 64B VS 128B ====================
    s7 = prs.slides.add_slide(blank)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "6. Empirical Surprise: 64B vs. 128B on Apple M1",
               "Why empirical measurement beats blindly hardcoding OS-reported constants", 7)

    s7.shapes.add_picture(str(ASSETS / "chart_m1_64_128.png"), Inches(0.65), Inches(1.45), width=Inches(6.2))

    add_card(s7, 7.1, 1.4, 5.55, 2.55, "What We Expected vs. What We Measured", [
        "macOS sysctl hw.cachelinesize reports 128 bytes on Apple M1 (ARM64).",
        "Assumption: 64-byte padding would still suffer false sharing and require alignas(128).",
        "Measured reality (2 runs): Pad 64B (1.04 ms) already matched Pad 128B (1.04–1.05 ms)!"
    ], accent=AMBER)

    add_card(s7, 7.1, 4.2, 5.55, 2.55, "Architectural Takeaway", [
        "Doubling counter footprint from 64B to 128B gave zero additional speedup on this 4-thread workload.",
        "We report the empirical observation without over-claiming undocumented Apple microarchitecture — reinforcing the core lesson: measure, don't guess."
    ], accent=BLUE)

    add_notes(s7, "TR Konusma Notu: Apple M1'de ilginc bir bulgu yakaladik: sistem cache line boyutunu 128 bayt bildiriyor, yani normalde 64 bayt padding'in yetmeyecegini dusunebilirsiniz. Ama olctugumuzde 64B padding (1.04 ms) ile 128B padding (1.04 ms) birebir ayni hizi verdi. Yani bellegi bosuna iki katina cikarmadan once mutlaka olcum yapmak gerekiyor.")

    # ==================== SLIDE 8: PRACTICAL DECISION MATRIX ====================
    s8 = prs.slides.add_slide(blank)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "7. Performance vs. Memory Cost: When to Use What?",
               "Practical engineering guidance derived from our controlled experiments", 8)

    add_card(s8, 0.65, 1.4, 3.8, 5.2, "Adjacent Counters (8B)", [
        "Memory cost: Lowest (1x, 8 bytes/thread).",
        "Best when: Writes are infrequent (B >= 256), updates happen only at thread exit, or normal non-atomic stores dominate.",
        "Risk: Severe slowdown (8.5x–62x) under frequent cross-core atomic updates."
    ], accent=MUTED)

    add_card(s8, 4.75, 1.4, 3.8, 5.2, "Cache-Line Padding (64B)", [
        "Memory cost: 8x counter storage (64 bytes/thread).",
        "Best when: Threads MUST publish frequent atomic updates visible in real time across physical cores.",
        "Caution: Wastes memory with zero gain when updates are already batched or run on SMT siblings."
    ], accent=BLUE)

    add_card(s8, 8.85, 1.4, 3.8, 5.2, "Local Accumulation / Batching", [
        "Memory cost: Lowest (1x) + register variable.",
        "Best when: Intermediate values do not need immediate cross-thread visibility.",
        "Result: Fastest overall on every machine — eliminates both coherence traffic and atomic overhead."
    ], accent=TEAL)

    add_notes(s8, "TR Konusma Notu: Muhendislik acisindan net bir karar tablomuz var: Eger ara sonuclarin anlik gorunmesi gerekmiyorsa en iyi ve en ucuz cozum yerel biriktirme (Local / Batching). Eger gercekten sik atomik guncelleme sartsa 64B padding 8 kat bellek bedeliyle 8.5x-62x arasi hiz kazandiriyor.")

    # ==================== SLIDE 9: LIMITATIONS ====================
    s9 = prs.slides.add_slide(blank)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "8. Limitations & Threats to Validity",
               "Transparent boundaries of what our measurements do — and do not — prove", 9)

    add_card(s9, 0.65, 1.35, 5.85, 5.3, "Measurement & Hardware Boundaries", [
        "No direct hardware PMU cache-coherence counters were recorded; timing + address verification alone cannot quantify exact coherence bus messages.",
        "Main desktop runs occurred on an active Windows system (initially on battery) without continuous CPU frequency or thermal logging.",
        "In the main study, normal store and atomic exchange modes ran in separate blocks rather than interleaved."
    ], accent=RED)

    add_card(s9, 6.8, 1.35, 5.85, 5.3, "Experimental Scope & Interpretation", [
        "Weak scaling design (each thread does fixed work): longer wall-clock time at higher thread counts reflects contention + overhead, not strong-scaling speedup.",
        "Batching changes both write frequency and outer-loop structure; we report its combined practical effect.",
        "Results apply to the tested CPUs, compilers, and synthetic counter workloads — real applications with mixed memory access patterns may differ."
    ], accent=AMBER)

    add_notes(s9, "TR Konusma Notu: Bilimsel durustluk geregi sinirliliklarimizi acikca belirtiyoruz: Dogrudan donanim cache-coherence sayaclari olcmedik, bu yuzden sadece sure farkina bakip kesin su kadar onbellek mesaji azaldi demiyoruz. Ayrica ana deney aktif masaustunde yapildi ve weak scaling kullandik.")

    # ==================== SLIDE 10: CONCLUSION ====================
    s10 = prs.slides.add_slide(blank)
    set_bg(s10, NAVY)

    accent10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.28), Inches(7.5))
    accent10.fill.solid()
    accent10.fill.fore_color.rgb = TEAL
    accent10.line.fill.background()

    tb10 = s10.shapes.add_textbox(Inches(0.95), Inches(0.85), Inches(11.4), Inches(1.0))
    p10 = tb10.text_frame.paragraphs[0]
    p10.text = "9. Conclusion & Key Takeaways"
    p10.font.size = Pt(34)
    p10.font.bold = True
    p10.font.color.rgb = WHITE

    takeaways = [
        ("1. Separate the Mechanisms",
         "Padding fixes memory layout (cache-line contention); local accumulation reduces write frequency. Measuring both independently shows exactly where speedup comes from."),
        ("2. Padding Is Conditional, Not Universal",
         "Massive speedup under frequent cross-core atomic writes (8.5x on 6 P-cores; 9.7x–62x across 3 machines), but disappears at B=256, Local accumulation, SMT siblings, or normal stores."),
        ("3. Verified Across Architectures (x86-64 & ARM64)",
         "Consistent findings across two Windows x86-64 laptops and Apple M1 ARM64 — and empirical testing showed 64B already matched 128B on M1.")
    ]

    y = 2.05
    for title, desc in takeaways:
        box = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.95), Inches(y), Inches(11.4), Inches(1.25))
        box.fill.solid()
        box.fill.fore_color.rgb = SLATE
        box.line.color.rgb = RGBColor(51, 65, 85)
        box.adjustments[0] = 0.08
        btb = s10.shapes.add_textbox(Inches(1.2), Inches(y + 0.14), Inches(10.9), Inches(1.0))
        btf = btb.text_frame
        btf.word_wrap = True
        bp1 = btf.paragraphs[0]
        bp1.text = title
        bp1.font.size = Pt(16)
        bp1.font.bold = True
        bp1.font.color.rgb = RGBColor(96, 165, 250)
        bp2 = btf.add_paragraph()
        bp2.text = desc
        bp2.font.size = Pt(12.5)
        bp2.font.color.rgb = RGBColor(226, 232, 240)
        bp2.space_before = Pt(3)
        y += 1.45

    q = s10.shapes.add_textbox(Inches(0.95), Inches(6.45), Inches(11.4), Inches(0.6))
    qp = q.text_frame.paragraphs[0]
    qp.text = "Thank You!  Questions & Discussion   •   Zeynep Uyan (75616) & Muhammed Enes Aksoy (75569)  |  Group-4"
    qp.font.size = Pt(15)
    qp.font.bold = True
    qp.font.color.rgb = RGBColor(45, 212, 191)
    qp.alignment = PP_ALIGN.CENTER

    add_notes(s10, "TR Konusma Notu: Ozetle: Bellek yerlesimi ile yazma sikligini ayirdik; padding'in sadece sik atomik yazmada ve ayri fiziksel cekirdeklerde buyuk fayda sagladigini, yazma seyreklestiginde ise avantajinin kayboldugunu hem x86-64 hem Apple M1 ARM64 mimarilerinde dogruladik. Dinlediginiz icin tesekkurler, sorularinizi alabiliriz!")

    prs.save(OUT_PPTX)
    print(f"Saved presentation: {OUT_PPTX}")


if __name__ == "__main__":
    make_charts()
    build_deck()
