"""Compare two sets of Descartes reports method by method (e.g. this reproduction vs the authors' reports).

usage: compare_descartes_runs.py <reports_A> <reports_B> <out_dir> [--labels A B] [--table3 <invoked-methods.csv>]

<reports_A> and <reports_B> are methods.json files or directories searched recursively for methods.json (one
report per module). Methods are matched on (class, name, parameter descriptor), see descartes.py.

Writes to <out_dir>:
  methods.csv   one row per method: classification in A and in B ("absent" if the method is not in a report)
  matrix.csv    counts of (classification in A, classification in B)
  summary.txt   per-classification totals, agreement, Jaccard index of the pseudo-tested sets, and, with --table3,
                the classification of the 46 effective targets of Table III in both runs
"""
import csv
import sys
from collections import Counter
from pathlib import Path

from descartes import CLASSIFICATIONS, find_reports, load_reports, mutators, table3_keys

HERE = Path(__file__).resolve().parent
STATES = CLASSIFICATIONS + ["absent"]


def reports(path):
    path = Path(path)
    return [path] if path.is_file() else find_reports(path)


def main(argv):
    args = list(argv[1:])
    labels = ["A", "B"]
    table3 = None
    if "--labels" in args:
        i = args.index("--labels")
        labels = args[i + 1:i + 3]
        del args[i:i + 3]
    if "--table3" in args:
        i = args.index("--table3")
        table3 = args[i + 1]
        del args[i:i + 2]
    if len(args) < 3:
        print(__doc__)
        return 2
    files_a, files_b, out = reports(args[0]), reports(args[1]), Path(args[2])
    a, b = load_reports(files_a), load_reports(files_b)
    keys = sorted(set(a) | set(b))
    cls_a = {k: a[k]["classification"] if k in a else "absent" for k in keys}
    cls_b = {k: b[k]["classification"] if k in b else "absent" for k in keys}

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "methods.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["class", "method", "params", labels[0], labels[1], "same"])
        for k in keys:
            w.writerow([k[0], k[1], k[2], cls_a[k], cls_b[k], cls_a[k] == cls_b[k]])

    pairs = Counter((cls_a[k], cls_b[k]) for k in keys)
    with open(out / "matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([f"{labels[0]} \\ {labels[1]}"] + STATES)
        for s in STATES:
            w.writerow([s] + [pairs[(s, t)] for t in STATES])

    pseudo_a = {k for k in keys if cls_a[k] == "pseudo-tested"}
    pseudo_b = {k for k in keys if cls_b[k] == "pseudo-tested"}
    union = pseudo_a | pseudo_b
    same = sum(1 for k in keys if cls_a[k] == cls_b[k])
    lines = [f"{labels[0]}: {len(files_a)} report(s), {len(a)} methods, mutators per report: "
             f"{sorted({len(mutators(p)) for p in files_a})}",
             f"{labels[1]}: {len(files_b)} report(s), {len(b)} methods, mutators per report: "
             f"{sorted({len(mutators(p)) for p in files_b})}",
             "",
             f"{'classification':<18}{labels[0]:>10}{labels[1]:>10}"]
    for s in STATES:
        lines.append(f"{s:<18}{sum(1 for k in keys if cls_a[k] == s):>10}{sum(1 for k in keys if cls_b[k] == s):>10}")
    lines += ["",
              f"same classification: {same} / {len(keys)} methods ({same / len(keys):.2%})",
              f"pseudo-tested: {len(pseudo_a & pseudo_b)} in both, {len(pseudo_a - pseudo_b)} only in {labels[0]}, "
              f"{len(pseudo_b - pseudo_a)} only in {labels[1]}; Jaccard index "
              f"{len(pseudo_a & pseudo_b) / len(union) if union else 1.0:.4f}",
              "",
              "differences (A -> B: count):"]
    for (s, t), n in sorted(pairs.items(), key=lambda x: -x[1]):
        if s != t:
            lines.append(f"  {s} -> {t}: {n}")

    # Why do classifications differ? PIT counts a mutant as detected when a test fails (KILLED) but also when the
    # run times out (TIMED_OUT) or crashes (MEMORY_ERROR, RUN_ERROR).
    lines += ["", "mutant statuses:"]
    for label, methods in ((labels[0], a), (labels[1], b)):
        st = Counter(x["status"] for m in methods.values() for x in m.get("mutations", []))
        lines.append(f"  {label}: " + ", ".join(f"{s} {n}" for s, n in st.most_common()))
    for first, second, la, lb in ((a, b, labels[0], labels[1]), (b, a, labels[1], labels[0])):
        more = [k for k in keys if k in first and k in second
                and len(first[k].get("detected", [])) > len(second[k].get("detected", []))]
        if not more:
            continue
        how = Counter()
        killers = Counter()
        for k in more:
            for x in first[k].get("mutations", []):
                if x["mutator"] in first[k].get("detected", []) and x["mutator"] not in second[k].get("detected", []):
                    how[x["status"]] += 1
                    for t in x.get("killing-tests", []):
                        killers[t.split("(")[0].rsplit(".", 1)[0]] += 1
        lines.append(f"  {len(more)} methods have more detected mutants in {la} than in {lb}; those extra mutants are "
                     + ", ".join(f"{s} {n}" for s, n in how.most_common()))
        if killers:
            lines.append("    killing test classes: "
                         + ", ".join(f"{t.rsplit('.', 1)[-1]} {n}" for t, n in killers.most_common(6)))

    if table3:
        with open(HERE / "paper" / "table3_pdfbox.csv", newline="") as f:
            paper = [r["class_method"] for r in csv.DictReader(f)]
        targets = table3_keys(table3, paper)
        in_a = sum(1 for n in paper if cls_a.get(targets[n]) == "pseudo-tested")
        in_b = sum(1 for n in paper if cls_b.get(targets[n]) == "pseudo-tested")
        lines += ["", f"Table III effective targets pseudo-tested: {labels[0]} {in_a} / 46, {labels[1]} {in_b} / 46"]
        for n in paper:
            k = targets[n]
            if cls_a.get(k) != "pseudo-tested" or cls_b.get(k) != "pseudo-tested":
                lines.append(f"  {n}({k[2]}): {labels[0]} {cls_a.get(k, 'absent')}, {labels[1]} {cls_b.get(k, 'absent')}")

    text = "\n".join(lines) + "\n"
    (out / "summary.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
