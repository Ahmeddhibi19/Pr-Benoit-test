"""Figure 5 of the paper: distribution of the sizes of the collected object profiles.

usage: figure5.py <out_prefix> <label>=<profile_dir> [<label>=<profile_dir> ...]

Each <profile_dir> holds the <method>-object-profile-sizes.txt files written by PANKTI (one size in bytes per
collected profile). The paper bins the sizes by 10 MB from 0 to 60 MB on a logarithmic count axis; the sizes are
binary units (the largest profile, 57,385,679 bytes, is the paper's "nearly 55 MB"), so the bins are 10 MiB wide.
Writes <out_prefix>.csv (counts per bin and data set) and <out_prefix>.png.
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MIB = 2 ** 20
BIN_MIB = 10
N_BINS = 6
COLORS = ["#2a78d6", "#eb6834"]  # categorical slots 1 and 2 (validated for colour-vision deficiencies)
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"


def sizes(profile_dir):
    values = []
    for f in sorted(Path(profile_dir).glob("*-object-profile-sizes.txt")):
        values += [int(x) for x in f.read_text().split()]
    return values


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    out = Path(argv[1])
    series = []
    for arg in argv[2:]:
        label, path = arg.split("=", 1)
        values = sizes(path)
        bins = [0] * N_BINS
        for s in values:
            bins[min(int(s / (BIN_MIB * MIB)), N_BINS - 1)] += 1
        series.append((label, values, bins))

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["bin_mib"] + [label for label, _, _ in series])
        for i in range(N_BINS):
            w.writerow([f"{i * BIN_MIB}-{(i + 1) * BIN_MIB}"] + [b[i] for _, _, b in series])
        w.writerow(["profiles"] + [len(v) for _, v, _ in series])
        w.writerow(["min_bytes"] + [min(v) for _, v, _ in series])
        w.writerow(["max_bytes"] + [max(v) for _, v, _ in series])

    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    width = 0.8 / len(series)
    for k, (label, values, bins) in enumerate(series):
        xs = [i + (k - (len(series) - 1) / 2) * width for i in range(N_BINS)]
        ax.bar(xs, bins, width=width, color=COLORS[k % len(COLORS)], edgecolor=SURFACE, linewidth=2,
               label=f"{label} ({len(values):,} profiles)", zorder=3)
    ax.set_yscale("log")
    ax.set_xticks(range(N_BINS))
    ax.set_xticklabels([f"{i * BIN_MIB}-{(i + 1) * BIN_MIB}" for i in range(N_BINS)], color=MUTED)
    ax.set_xlabel("Object profile size (MiB)", color=MUTED)
    ax.set_ylabel("Number of profiles (log scale)", color=MUTED)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="y", color="#e4e3df", linewidth=0.8, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.set_title("Sizes of the collected object profiles, PDFBox (paper, Figure 5)", color=INK, loc="left", fontsize=11)
    ax.legend(frameon=False, labelcolor=INK, fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{out}.png", facecolor=SURFACE)
    with open(f"{out}.csv", encoding="utf-8") as f:
        print(f.read(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
