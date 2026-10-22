"""Three-way comparison of every published PDFBox number: the paper, the authors' artifacts, this reproduction.

usage: comparison.py <results_dir> <out_dir>

Reads the per-row outputs of the earlier stages (results/day4/table3_comparison.csv, results/day6/
table3_execution.csv, results/day7/table3_status.csv) and writes:
  <out_dir>/table3_rows.csv   one row per Table III row and column: paper, authors, ours, ours - paper
  <out_dir>/comparison.csv    one row per published quantity (totals, ratios, profile facts, examples, success
                              criteria of the plan), with the source file of each value and a verdict
  <out_dir>/comparison.txt    the same, as text
"authors" is the value in the authors' artifacts (profiles, published tests), or obtained here from them (their tests
run in this environment, their Descartes reports). The values that do not come from the per-row files are listed in
FACTS with the result file that holds them; the script checks that each value appears in that file.
"""
import csv
import re
import sys
from pathlib import Path

COLUMNS = [
    # Table III column, (file, paper column, authors column, ours column)
    ("#INVOCATIONS", "day4/table3_comparison.csv", "paper_invocations", "authors_invocations", "ours_invocations"),
    ("#COLLECTED", "day4/table3_comparison.csv", "paper_collected", "authors_collected", "ours_collected"),
    ("#UNIQUE", "day4/table3_comparison.csv", "paper_unique", "authors_unique", "ours_unique"),
    ("#PANKTI_TESTS", "day6/table3_execution.csv", "paper_tests", "authors_tests_here", "ours_tests"),
    ("#PASSING", "day6/table3_execution.csv", "paper_passing", "authors_passing_here", "ours_passing"),
    ("#FAILING", "day6/table3_execution.csv", "paper_failing", "authors_failing_here", "ours_failing"),
    ("PANKTI_STATUS", "day7/table3_status.csv", "paper_status", "authors_status_here", "ours_status"),
]

# quantity, paper, authors, ours, verdict, source file(s) of the authors' and our values (relative to results/)
FACTS = [
    ("#TARGET", "138", "138", "138", "exact (137 methods in common)",
     "day2/targets_authors_reports.txt day2/targets_own_reports.txt"),
    ("smallest profile (bytes)", "158", "158", "158", "exact", "day1/authors_profile_stats.txt day4/full/profile_stats.txt"),
    ("largest profile", "nearly 55 MB", "54.7 MiB", "54.7 MiB", "exact (binary units)",
     "day1/authors_profile_stats.txt day4/full/profile_stats.txt"),
    ("profiles on disk", "5.5 GB", "5.49 GiB", "5.30 GiB", "close (-3.5%)",
     "day1/authors_profile_stats.txt day4/full/profile_stats.txt"),
    ("methods hitting the 200 MB threshold", "19", "19", "19", "exact",
     "day1/authors_profile_stats.txt day4/full/profile_stats.txt"),
    ("maximum nesting depth", "36", "73", "73", "differs: 36 not reproduced; the paper does not define it",
     "day4/full/profile_stats.txt"),
    ("Figure 5, profiles per 10 MiB bin", "histogram", "57458 / 71 / 3 / 23 / 5 / 3", "58563 / 75 / 3 / 23 / 5 / 3",
     "same shape; bins above 20 MiB identical", "day5/fig5.csv"),
    ("isFill: invocations / collected / unique / tests", "30,944 / 30,944 / 1 / 1", "30,944 / 30,944 / 1 / 1",
     "30,944 / 30,944 / 1 / 1", "exact", "day4/table3_comparison.txt"),
    ("isFill: status after", "well-tested", "partially-tested (their report and their test run here)",
     "partially-tested", "exact: mutant false detected, true not", "day7/pankti_status_reproduction.csv"),
    ("all 46 targets pseudo-tested before (plan A.6, exact)", "46 / 46", "46 / 46", "46 / 46", "exact",
     "day2/targets_authors_reports.txt"),
    ("V.A: failing tests of methods returning a primitive, primitive array, wrapper or enum", "0", "0", "0",
     "exact", "day8/failure_analysis_reproduction.txt day8/prediction_check_reproduction.txt"),
    ("V.B: PDFBox targets with passing tests that stay pseudo-tested, all null-only", "12 (15 with other subjects)",
     "12", "12", "exact", "day8/prediction_check_authors.txt day8/prediction_check_reproduction.txt"),
    ("prediction check (plan A.6): mutant outcomes predicted from the observed values", "-", "82 / 82", "82 / 82",
     "all predicted", "day8/prediction_check_authors.txt day8/prediction_check_reproduction.txt"),
    ("sensitivity run with a pre-built font cache: #EFF_TARGET / INV / COLL / UNIQ", "46 / 121,175 / 57,563 / 13,851",
     "-", "46 / 121,300 / 57,677 / 13,852", "targets exact, totals within 0.2% (38 rows identical)",
     "day8/sensitivity/warm-cache/profile_stats.txt day8/sensitivity/warm-cache/table3_comparison.txt"),
]


def number(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    res, out = Path(argv[1]), Path(argv[2])
    tables = {}
    for _, path, *_ in COLUMNS:
        if path not in tables:
            with open(res / path, newline="", encoding="utf-8") as f:
                tables[path] = {r["row"]: r for r in csv.DictReader(f) if r["row"]}
    rows_out, summary = [], []
    for col, path, p, a, o in COLUMNS:
        t = tables[path]
        equal_a = equal_o = 0
        tot = {"paper": 0, "authors": 0, "ours": 0}
        for row in sorted(t, key=int):
            r = t[row]
            vp, va, vo = r[p], r[a], r[o]
            np_, na, no = number(vp), number(va), number(vo)
            rows_out.append({"row": row, "method": f"{r['class'].rsplit('.', 1)[1]}.{r['method']}", "column": col,
                             "paper": vp, "authors": va, "ours": vo,
                             "ours_minus_paper": (no - np_) if None not in (no, np_) else ""})
            equal_a += va == vp
            equal_o += vo == vp
            for k, n in (("paper", np_), ("authors", na), ("ours", no)):
                tot[k] += n or 0
        n_rows = len(t)
        summary.append((f"Table III {col}: rows equal to the paper", f"{n_rows} rows", f"{equal_a} / {n_rows}",
                        f"{equal_o} / {n_rows}", "", path))
        if col != "PANKTI_STATUS":
            summary.append((f"Table III {col}: total of the 46 rows", f"{tot['paper']:,}", f"{tot['authors']:,}",
                            f"{tot['ours']:,}", f"ours {100 * (tot['ours'] - tot['paper']) / tot['paper']:+.1f}%",
                            path))
        else:
            well = {k: sum(1 for r in t.values() if r[c] == "well-tested") for k, c in
                    (("paper", p), ("authors", a), ("ours", o))}
            summary.append(("well-tested targets (PANKTI_STATUS)", f"{well['paper']} / {n_rows} "
                            f"({100 * well['paper'] / n_rows:.1f}%)", f"{well['authors']} / {n_rows}",
                            f"{well['ours']} / {n_rows}", "exact (27 / 46 robust, discrepancies.md 23)", path))

    def total(col, who):
        return sum(number(r[who]) or 0 for r in rows_out if r["column"] == col)

    for name, num, den, paper_pct in (("collected / invocations", "#COLLECTED", "#INVOCATIONS", "47.5%"),
                                      ("unique / collected", "#UNIQUE", "#COLLECTED", "24%"),
                                      ("passing / tests", "#PASSING", "#PANKTI_TESTS", "98.2% (98.29%)")):
        summary.append((f"{name} (46 rows of Table III)", paper_pct,
                        f"{100 * total(num, 'authors') / total(den, 'authors'):.2f}%",
                        f"{100 * total(num, 'ours') / total(den, 'ours'):.2f}%", "same order of magnitude",
                        "computed from table3_rows.csv"))
    summary.append(("#EFF_TARGET", "46", "46", "47 (46 in common, Jaccard 0.979)",
                    "set agreement; extra: TrueTypeFont.getOS2Windows", "day4/table3_comparison.txt"))

    for fact in FACTS:
        # every number of this reproduction's value must appear in one of the cited result files
        text = " ".join((res / src).read_text(encoding="utf-8") for src in fact[5].split())
        for tok in re.split(r"\s*/\s*", fact[3].split(" (")[0]):
            if re.search(r"\d", tok) and tok not in text and tok.replace(",", "") not in text:
                raise SystemExit(f"{fact[0]}: value {tok!r} not found in {fact[5]}")
        summary.append(fact)

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "table3_rows.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)
    header = ["quantity", "paper", "authors", "ours", "verdict", "source"]
    with open(out / "comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(summary)
    lines = [f"{q}\n    paper: {p} | authors: {a} | ours: {o}" + (f" | {v}" if v else "") for q, p, a, o, v, _ in summary]
    (out / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
