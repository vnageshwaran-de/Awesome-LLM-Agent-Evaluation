#!/usr/bin/env python3
"""Regenerate Figure 2 (evidence_trends.pdf).
Round-4 revision: solid trend lines over 2023-2025 (densely sampled, robust);
2026 H1 shown as de-emphasized provisional markers because it is a
citation-selected partial window whose multi-agent / open-source movements
reverse under the year-stratified sensitivity check (Section 4.1)."""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)                      # Awesome-LLM-Agent-Evaluation
WS = os.path.dirname(ROOT)                         # q1_springer_v2 (manuscript workspace)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(WS, "AIR_submission", "figures", "evidence_trends.pdf")
OUT2 = os.path.join(WS, "figures_evidence_trends.pdf")  # top-level mirror

rows = list(csv.DictReader(open(os.path.join(DATA, "benchmark_evolution_timeline.csv"))))
years = [int(r["year"]) for r in rows]
series = {
    "Real-world environment": ([float(r["realworld_share"]) for r in rows], "#1b6ca8", "o"),
    "Interactive environment": ([float(r["interactive_share"]) for r in rows], "#5aa469", "s"),
    "Multi-agent evaluation":  ([float(r["multiagent_share"]) for r in rows], "#d1813f", "^"),
    "Open-source release":     ([float(r["opensource_share"]) for r in rows], "#9b5fb0", "D"),
}
# split robust window (<=2025) from provisional 2026
ROBUST = [i for i, y in enumerate(years) if y <= 2025]
PROV = [i for i, y in enumerate(years) if y == 2026]

fig, ax = plt.subplots(figsize=(7.4, 4.3))
for label, (vals, color, mk) in series.items():
    xr = [years[i] for i in ROBUST]
    yr = [vals[i] for i in ROBUST]
    ax.plot(xr, yr, color=color, marker=mk, lw=2.2, ms=7, label=label, zorder=3)
    # provisional 2026: faint dotted continuation + hollow marker
    if PROV:
        i = PROV[0]
        ax.plot([years[ROBUST[-1]], years[i]], [vals[ROBUST[-1]], vals[i]],
                color=color, lw=1.2, ls=":", alpha=0.5, zorder=2)
        ax.plot(years[i], vals[i], marker=mk, mfc="white", mec=color,
                ms=7, mew=1.6, alpha=0.7, zorder=2)

# shade the provisional region
ax.axvspan(2025.5, 2026.5, color="0.85", alpha=0.45, zorder=0)
ax.text(2026, 0.02, "2026 H1\nprovisional\n(citation-selected)", ha="center",
        va="bottom", fontsize=7.5, color="0.35", style="italic")

ax.set_xticks(years)
ax.set_xticklabels([str(y) if y != 2026 else "2026 H1" for y in years])
ax.set_ylim(0, 0.62)
ax.set_ylabel("Within-corpus share")
ax.set_xlabel("Publication year")
ax.grid(True, axis="y", ls="--", lw=0.5, alpha=0.5)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9, ncol=2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
for path in (OUT, OUT2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    print("wrote", path)
