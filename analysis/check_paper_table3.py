"""Consistency checks on the PDFBox rows of Table III as printed in the paper.

usage: check_paper_table3.py [table3_pdfbox.csv] [output.txt]
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRINTED_TOTALS = {"invocations": 121175, "collected": 57563, "unique": 13851, "tests": 13851,
                  "passing": 13614, "failing": 237}
PRINTED_STATUS = {"well-tested": 28, "pseudo-tested": 18}
COLUMNS = ["invocations", "collected", "unique", "tests", "passing", "failing"]


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in COLUMNS + ["row"]:
            r[c] = int(r[c])
    return rows


def check(rows):
    out = []
    ok = True

    def line(cond, text):
        nonlocal ok
        ok &= cond
        out.append(("OK   " if cond else "FAIL ") + text)

    line(len(rows) == 46, f"number of methods = {len(rows)} (expected 46, rows 30-75)")
    for c in COLUMNS:
        s = sum(r[c] for r in rows)
        line(s == PRINTED_TOTALS[c], f"sum of {c} = {s:,} (printed total {PRINTED_TOTALS[c]:,})")
    for status, expected in PRINTED_STATUS.items():
        n = sum(r["status"] == status for r in rows)
        line(n == expected, f"{status} = {n} (printed {expected})")

    bad = [r["row"] for r in rows if r["passing"] + r["failing"] != r["tests"]]
    line(not bad, f"passing + failing = tests in every row {bad or ''}")
    bad = [r["row"] for r in rows if r["tests"] != r["unique"]]
    line(not bad, f"tests = unique in every row {bad or ''}")

    capped = [r["row"] for r in rows if r["collected"] < r["invocations"]]
    line(len(capped) == 19, f"rows with collected < invocations (200 MB threshold hit) = {len(capped)} "
                            f"(text says 19): {capped}")
    single = [r["row"] for r in rows if r["tests"] == 1]
    line(len(single) == 7, f"methods with a single test = {len(single)} (text says 7): {single}")
    biggest = max(rows, key=lambda r: r["tests"])
    line(biggest["tests"] == 11730, f"max tests = {biggest['tests']} for {biggest['class_method']} (text says 11,730)")

    t = {c: sum(r[c] for r in rows) for c in COLUMNS}
    well = sum(r["status"] == "well-tested" for r in rows)
    out.append("")
    out.append("Ratios recomputed from the counts:")
    out.append(f"  collected / invocations = {t['collected'] / t['invocations']:.2%} (printed 47.5%)")
    out.append(f"  unique / collected      = {t['unique'] / t['collected']:.2%} (printed 24%)")
    out.append(f"  passing / tests         = {t['passing'] / t['tests']:.2%} (printed 98.2% in Table III, 98.3% in the text)")
    out.append(f"  well-tested / methods   = {well / len(rows):.2%} (printed 60.9%)")

    still = [r for r in rows if r["status"] == "pseudo-tested" and r["passing"] > 0]
    out.append("")
    out.append(f"Still pseudo-tested although at least one generated test passes: {len(still)} PDFBox methods")
    out.append("  (Section V.B counts 15 such methods over the three projects)")
    for r in still:
        out.append(f"  row {r['row']:>2} {r['class_method']} (passing {r['passing']}/{r['tests']})")
    return ok, out


def main(argv):
    src = Path(argv[1]) if len(argv) > 1 else HERE / "paper" / "table3_pdfbox.csv"
    ok, out = check(load(src))
    text = "\n".join(out) + "\n"
    print(text, end="")
    if len(argv) > 2:
        Path(argv[2]).parent.mkdir(parents=True, exist_ok=True)
        Path(argv[2]).write_text(text, encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
