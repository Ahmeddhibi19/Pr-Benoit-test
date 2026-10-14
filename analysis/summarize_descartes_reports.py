"""Summarise Descartes methods.json reports found under a directory.

usage: summarize_descartes_reports.py <dir> [output.csv] [--method Class.method ...]

For every report: number of methods, count per classification and number of mutation operators.
With --method, also prints the classification of the given methods in every report.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

CLASSES = ["tested", "partially-tested", "pseudo-tested", "not-covered"]


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root = Path(argv[1])
    out = None
    watch = []
    rest = argv[2:]
    if "--method" in rest:
        i = rest.index("--method")
        watch = rest[i + 1:]
        rest = rest[:i]
    if rest:
        out = Path(rest[0])

    rows = []
    for report in sorted(root.glob("**/methods.json")):
        data = load(report)
        methods = data["methods"]
        counts = Counter(m["classification"] for m in methods)
        mutators = data.get("analysis", {}).get("mutators", [])
        rel = report.relative_to(root).as_posix()
        rows.append([rel, len(methods)] + [counts.get(c, 0) for c in CLASSES] + [len(mutators), " ".join(mutators)])
        for w in watch:
            cls, name = w.rsplit(".", 1)
            for m in methods:
                if m["class"] == cls and m["name"] == name:
                    print(f"{rel}: {w}{m.get('description', '')} -> {m['classification']} "
                          f"(detected {m.get('detected')}, not detected {m.get('not-detected')})")

    header = ["report", "methods"] + CLASSES + ["n_mutators", "mutators"]
    w = csv.writer(sys.stdout)
    w.writerow(header[:-1])
    for r in rows:
        w.writerow(r[:-1])
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            csv.writer(f).writerows([header] + rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
