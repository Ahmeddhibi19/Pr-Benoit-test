"""Compare the PDFBox rows of Table III with the authors' own artifacts.

usage: compare_authors_report.py <pankti-experiments/pdfbox> <output.csv>

Use the experiments repository at commit 1d8f9aa (2021-06-08): the 2020-11-19 Descartes reports are not in
earlier snapshots. Its report.csv holds the same values as the one of 2020-11-03, in a different order.

Sources compared, method by method:
  - the paper (analysis/paper/table3_pdfbox.csv)
  - execution/report.csv of the experiments repository
  - the Descartes reports: before (2020-09-21) and the last "after" run (2020-11-19)
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COUNTS = ["invocations", "collected", "unique", "passing", "failing"]
REPORT_COLUMNS = {"invocations": "invocations", "collected": "collected-profiles", "unique": "unique-profiles",
                  "passing": "passing-tests", "failing": "failing-tests"}
BEFORE = ["before/fontbox/target/pit-reports/202009211456", "before/pdfbox/target/pit-reports/202009211459"]
AFTER = ["after/fontbox/target/pit-reports/202011191911", "after/pdfbox/target/pit-reports/202011191939"]


def classifications(pdfbox_dir, report_dirs):
    result = {}
    for d in report_dirs:
        with open(pdfbox_dir / "descartes" / d / "methods.json", encoding="utf-8-sig") as f:
            for m in json.load(f)["methods"]:
                result.setdefault((m["class"], m["name"]), []).append(m["classification"])
    return result


def status(classes):
    if not classes:
        return "absent"
    return "/".join(sorted(set(classes)))


def well_tested(classes):
    return "well-tested" if classes and all(c in ("tested", "partially-tested") for c in classes) else "pseudo-tested"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    pdfbox_dir, out = Path(argv[1]), Path(argv[2])

    with open(HERE / "paper" / "table3_pdfbox.csv", newline="") as f:
        paper = {r["class_method"]: r for r in csv.DictReader(f)}
    with open(pdfbox_dir / "execution" / "report.csv", newline="") as f:
        report = {}
        for r in csv.DictReader(f):
            if r["#"] == "*":
                continue
            fqn, method = r["method"].rsplit(".", 1)
            report[fqn.rsplit(".", 1)[1] + "_" + method] = dict(r, fqn=fqn, method_name=method)
    before = classifications(pdfbox_dir, BEFORE)
    after = classifications(pdfbox_dir, AFTER)

    header = ["row", "class_method", "fqn"]
    for c in COUNTS:
        header += [f"paper_{c}", f"report_{c}"]
    header += ["report_executed", "paper_status", "report_classification", "descartes_before", "descartes_after",
               "after_as_paper_status", "differences"]
    rows = []
    for name, p in paper.items():
        r = report.get(name)
        key = (r["fqn"].rsplit(".", 1)[1], r["method_name"]) if r else None
        b, a = before.get(key, []), after.get(key, [])
        diffs = []
        line = [p["row"], name, r["fqn"] if r else ""]
        for c in COUNTS:
            rv = r[REPORT_COLUMNS[c]] if r else ""
            line += [p[c], rv]
            if r and int(rv) != int(p[c]):
                diffs.append(f"{c} {p[c]} vs {rv}")
        derived = well_tested(a)
        if not r:
            diffs.append("missing in report.csv")
        else:
            rep_status = "well-tested" if r["descartes-classification"] in ("tested", "partially-tested") else "pseudo-tested"
            if rep_status != p["status"]:
                diffs.append(f"status paper {p['status']} vs report {r['descartes-classification']}")
        if derived != p["status"]:
            diffs.append(f"status paper {p['status']} vs Descartes after {status(a)}")
        if status(b) != "pseudo-tested":
            diffs.append(f"before = {status(b)}")
        line += [r["executed-tests"] if r else "", p["status"], r["descartes-classification"] if r else "",
                 status(b), status(a), derived, "; ".join(diffs)]
        rows.append(line)

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    n_diff = sum(1 for r in rows if r[-1])
    print(f"{len(rows)} methods compared, {n_diff} with at least one difference")
    for r in rows:
        if r[-1]:
            print(f"  row {r[0]} {r[1]}: {r[-1]}")
    exec_total = sum(int(r[header.index("report_executed")] or 0) for r in rows)
    print(f"executed tests in report.csv: {exec_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
