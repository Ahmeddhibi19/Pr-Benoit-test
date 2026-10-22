"""Table III columns #INVOCATIONS and #UNIQUE across several workload runs (sensitivity runs, experiment E22).

usage: sensitivity_table.py <out_prefix> <label>=<table3_comparison.csv> [<label>=<table3_comparison.csv> ...]

Each input is an output of compare_table3.py for one run. Writes <out_prefix>.csv with, for every method invoked in
at least one run, the paper's values and each run's values, and <out_prefix>.txt with the rows where at least one
run differs from the paper.
"""
import csv
import sys
from pathlib import Path


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    runs = [a.split("=", 1) for a in argv[2:]]
    data = {}
    for label, path in runs:
        with open(path, newline="", encoding="utf-8") as f:
            data[label] = {(r["class"], r["method"], r["params"]): r for r in csv.DictReader(f)}
    keys = set().union(*data.values())

    def any_row(k):
        return next(data[label][k] for label, _ in runs if k in data[label])

    keys = sorted(keys, key=lambda k: (int(any_row(k)["row"] or 999), k))
    rows = []
    for k in keys:
        base = any_row(k)
        row = {"row": base["row"], "class": k[0], "method": k[1], "params": k[2],
               "paper_invocations": base["paper_invocations"], "paper_unique": base["paper_unique"]}
        for label, _ in runs:
            r = data[label].get(k)
            row[f"{label}_invocations"] = r["ours_invocations"] if r else ""
            row[f"{label}_unique"] = r["ours_unique"] if r else ""
        rows.append(row)
    out = Path(argv[1])
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    head = f"{'row':>3} {'method':<44} {'paper':>13}" + "".join(f" {label:>13}" for label, _ in runs)
    lines = ["#INVOCATIONS / #UNIQUE per run; rows where a run differs from the paper", head]
    for r in rows:
        cells = [(r[f"{label}_invocations"], r[f"{label}_unique"]) for label, _ in runs]
        paper = (r["paper_invocations"], r["paper_unique"])
        if any(c != paper for c in cells):
            name = r["class"].rsplit(".", 1)[1] + "." + r["method"]
            lines.append(f"{r['row'] or '-':>3} {name:<44} {'/'.join(paper) if paper[0] else '-':>13}"
                         + "".join(f" {'/'.join(c) if c[0] else '-':>13}" for c in cells))
    for label, _ in runs:
        same = sum(1 for r in rows if r["paper_invocations"] and r[f"{label}_invocations"] == r["paper_invocations"]
                   and r[f"{label}_unique"] == r["paper_unique"])
        lines.append(f"{label}: Table III rows with the paper's #INVOCATIONS and #UNIQUE: {same} / "
                     f"{sum(1 for r in rows if r['paper_invocations'])}")
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
