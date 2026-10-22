"""Table III, this reproduction against the paper, row by row (one panel per column).

usage: figure_table3.py <table3_rows.csv> <out.png>

Reads the output of comparison.py. A point on the diagonal is a row with the paper's value; the rows that differ are
drawn in a second colour and labelled. Symmetric log axes, so that zero counts (#FAILING) stay visible.
"""
import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PANELS = ["#INVOCATIONS", "#UNIQUE", "#PASSING", "#FAILING"]
SAME, DIFFERENT, INK, MUTED = "#9aa0a6", "#1a73e8", "#202124", "#5f6368"


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[1], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    for ax, col in zip(axes.flat, PANELS):
        data = [(int(r["paper"]), int(r["ours"]), r["method"]) for r in rows if r["column"] == col]
        same = [(p, o) for p, o, _ in data if p == o]
        diff = [(p, o, m) for p, o, m in data if p != o]
        top = max(max(p, o) for p, o, _ in data) * 2
        ax.plot([0, top], [0, top], color=MUTED, linewidth=1, zorder=1)
        ax.scatter([p for p, _ in same], [o for _, o in same], s=36, color=SAME, edgecolor="white", linewidth=1,
                   zorder=2, label=f"same as the paper ({len(same)})")
        ax.scatter([p for p, _, _ in diff], [o for _, o, _ in diff], s=44, color=DIFFERENT, edgecolor="white",
                   linewidth=1, zorder=3, label=f"different ({len(diff)})")
        # one label per point (methods with the same values share it), alternately above and below
        groups = {}
        for p, o, m in diff:
            cls, name = m.split(".", 1)
            groups.setdefault((p, o), {}).setdefault(cls, []).append(name)
        for i, ((p, o), by_cls) in enumerate(sorted(groups.items(), key=lambda g: g[0][1])):
            label = "; ".join(f"{c}.{', '.join(ns)}" for c, ns in by_cls.items())
            left = i % 2 == 1
            ax.annotate(label, (p, o), textcoords="offset points", xytext=(-7 if left else 7, 3 if left else -9),
                        ha="right" if left else "left", fontsize=7, color=INK)
        ax.set_xscale("symlog", linthresh=1)
        ax.set_yscale("symlog", linthresh=1)
        ax.set_xlim(-0.5, top)
        ax.set_ylim(-0.5, top)
        ax.set_title(f"{col} per row", fontsize=11, color=INK, loc="left")
        ax.set_xlabel("paper (Table III)", fontsize=9, color=MUTED)
        ax.set_ylabel("this reproduction", fontsize=9, color=MUTED)
        ax.grid(color="#e8eaed", linewidth=0.6)
        ax.tick_params(labelsize=8, colors=MUTED)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.suptitle("Table III (PDFBox, 46 rows): this reproduction against the paper", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(argv[2], dpi=150)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
