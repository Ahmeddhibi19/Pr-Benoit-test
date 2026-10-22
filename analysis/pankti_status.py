"""PANKTI_STATUS of the effective targets: Descartes classification before and after adding the generated tests.

usage: pankti_status.py <before_reports> <after_reports> <invoked-methods.csv> <out_prefix>
                        [--table3 <authors_report_vs_paper.csv>] [--control <control_reports>]

<before_reports> and <after_reports> are methods.json files (or directories holding them, possibly compressed as in
results/). invoked-methods.csv lists the effective targets. Paper, Section III.E (metric 14): after the generated tests
are added, a target is either still pseudo-tested or "well-tested"; for Descartes, a covered method that is not
pseudo-tested is tested or partially-tested (assumption A10). The strict count (tested only) is reported as well.
With --table3, the status printed in Table III is compared row by row.
With --control, the reports of the same Descartes run without the generated tests are read as well: a target that is
already well-tested there is not counted as improved by the generated tests (docs/descartes.md, "after" run).
Writes <out_prefix>.csv (one row per target) and <out_prefix>.txt (summary).
"""
import csv
import sys
from pathlib import Path

from descartes import find_reports, load_method_list, load_reports, well_tested


def reports(path):
    path = Path(path)
    return [path] if path.is_file() else find_reports(path)


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    before, after = load_reports(reports(argv[1])), load_reports(reports(argv[2]))
    targets = load_method_list(argv[3])
    out = Path(argv[4])
    control = load_reports(reports(argv[argv.index("--control") + 1])) if "--control" in argv else None
    paper = {}
    if "--table3" in argv:
        with open(argv[argv.index("--table3") + 1], newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                paper[(r["fqn"], r["class_method"].split("_", 1)[1], r["param_signature"])] = r

    rows = []
    for key, r in targets:
        # invoked-methods.csv gives the parameter descriptor in param-signature, as Descartes' description does
        b, a = before.get(key), after.get(key)
        cls_b = b["classification"] if b else "absent"
        cls_a = a["classification"] if a else "absent"
        c = control.get(key) if control is not None else None
        cls_c = (c["classification"] if c else "absent") if control is not None else ""
        p = paper.get(key)
        rows.append({
            "row": p["row"] if p else "", "class": key[0], "method": key[1], "params": key[2],
            "before": cls_b, "control": cls_c, "after": cls_a,
            "detected_after": " ".join(a.get("detected", [])) if a else "",
            "not_detected_after": " ".join(a.get("not-detected", [])) if a else "",
            "pankti_status": "well-tested" if well_tested(cls_a) else "pseudo-tested",
            "paper_status": p["paper_status"] if p else "",
        })
    rows.sort(key=lambda r: (int(r["row"]) if r["row"] else 999, r["class"], r["method"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    in_paper = [r for r in rows if r["paper_status"]]
    well = [r for r in in_paper if r["pankti_status"] == "well-tested"]
    strict = [r for r in in_paper if r["after"] == "tested"]
    agree = [r for r in in_paper if r["pankti_status"] == r["paper_status"]]
    lines = [
        f"effective targets: {len(rows)} (of which in Table III: {len(in_paper)})",
        f"pseudo-tested before: {sum(1 for r in rows if r['before'] == 'pseudo-tested')} / {len(rows)}",
        f"well-tested after (tested or partially-tested), Table III methods: {len(well)} / {len(in_paper)} "
        f"(paper: 28 / 46); strictly tested: {len(strict)}; partially tested: {len(well) - len(strict)}",
        f"same status as Table III: {len(agree)} / {len(in_paper)}",
    ]
    if control is not None:
        already = [r for r in in_paper if well_tested(r["control"])]
        lines.append(f"well-tested in the control run without generated tests: {len(already)}; "
                     f"well-tested after and not in the control run: {len(well) - sum(1 for r in already if r in well)}")
        lines += [f"  row {r['row']:>2} {r['class'].rsplit('.', 1)[1]}.{r['method']}: before {r['before']}, "
                  f"control {r['control']}, after {r['after']}" for r in already]
    lines += [f"  row {r['row']:>2} {r['class'].rsplit('.', 1)[1]}.{r['method']}: paper {r['paper_status']}, here {r['after']}"
              for r in in_paper if r["pankti_status"] != r["paper_status"]]
    lines += [f"  not in Table III: {r['class'].rsplit('.', 1)[1]}.{r['method']}: before {r['before']}, after {r['after']}"
              for r in rows if not r["paper_status"]]
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
