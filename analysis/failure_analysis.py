"""Why generated tests fail (paper, Section V.A): every failing test classified from its outcome and its oracle.

usage: failure_analysis.py <generated_tests_dir> <test_outcomes_tests.csv[.gz]> <invoked-methods.csv> <out_prefix>
                           [--table3 <analysis/paper/table3_pdfbox.csv>]

The verdicts are those of test_outcomes.py (5 runs). Each failing test is put in one category, from the failure
message of JUnit's assertEquals (expected:<...> but was:<...>) and the observed value of the test
(generated_tests.py):
  identity-equals     both values are non-null and print differently only by their identity hash code
                      (Class@1a2b3c), or print identically: the returned class does not override equals()
  returns-null        the method returns null on the deserialised receiver, although it returned an object in
                      production
  exception           the call throws (not an assertion failure)
  other               anything else
Per method, the passing and failing tests are also split by observed value (null or not), to check whether a test
passes exactly when it observed null. The paper's causes for PDFBox (rows of Table III, Section V.A) are added for
comparison. Writes <out_prefix>.csv (one row per method with failing tests), <out_prefix>_tests.csv (one row per
failing test) and <out_prefix>.txt (summary).
"""
import csv
import gzip
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from generated_tests import observed_values

# Section V.A: rows of Table III given for each cause
PAPER_CAUSES = {
    "equals not overridden": {51, 72, 73},
    "SoftReference cache not available": {37, 44, 45, 46, 50},
    "transient fields": {33, 34, 35, 53, 73},
}
MESSAGE = re.compile(r"expected: ?<?(.*?)>? but was: ?<?(.*?)>?$", re.S)
IDENTITY = re.compile(r"[\w.$]+@[0-9a-f]+")


def category(failure_type, message):
    if failure_type != "java.lang.AssertionError":
        return "exception"
    m = MESSAGE.match(message or "")
    if not m:
        return "other"
    expected, actual = m.group(1), m.group(2)
    if actual == "null" and expected != "null":
        return "returns-null"
    if expected == actual or (IDENTITY.fullmatch(expected) and IDENTITY.fullmatch(actual)
                              and expected.split("@")[0] == actual.split("@")[0]):
        return "identity-equals"
    return "other"


def open_text(path):
    return gzip.open(path, "rt", encoding="utf-8", newline="") if str(path).endswith(".gz") else \
        open(path, encoding="utf-8", newline="")


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    values = observed_values(argv[1])
    with open(argv[3], newline="", encoding="utf-8") as f:
        signature = {(r["parent-FQN"], r["method-name"], r["param-list"].replace(" ", "")): r["param-signature"]
                     for r in csv.DictReader(f)}
    rows_by_key = {}
    if "--table3" in argv:
        with open(argv[argv.index("--table3") + 1], newline="", encoding="utf-8") as f:
            paper = {r["class_method"]: r["row"] for r in csv.DictReader(f)}
        for (cls, name, params) in signature:
            simple = cls.rsplit(".", 1)[1]
            rows_by_key[(cls, name, params)] = paper.get(f"{simple}_{name}", "")

    per_method = defaultdict(Counter)
    tests_out = []
    with open_text(argv[2]) as f:
        for r in csv.DictReader(f):
            key = (r["class"], r["method"], r["params"].replace(" ", "").replace(",", ","))
            obs = values[(re.sub(r"Part\d+$", "", r["test_class"]), r["test"])]
            null = "null" if obs[0] == "null" else "non-null"
            c = per_method[key]
            c["tests"] += 1
            c[f"{r['verdict']}_{null}"] += 1
            if r["verdict"] == "failing":
                cat = category(r["failure_type"], r["failure_message"])
                c[cat] += 1
                tests_out.append({"class": r["class"], "method": r["method"], "params": r["params"],
                                  "test_class": r["test_class"], "test": r["test"], "observed": obs[0],
                                  "declared_type": obs[2], "failure_type": r["failure_type"], "category": cat,
                                  "failure_message": (r["failure_message"] or "")[:200]})

    cats = ["identity-equals", "returns-null", "exception", "other"]
    rows = []
    for key, c in per_method.items():
        failing = sum(v for k, v in c.items() if k.startswith("failing_"))
        if not failing:
            continue
        row = rows_by_key.get((key[0], key[1], key[2].replace(" ", "")), "")
        paper = [cause for cause, rs in PAPER_CAUSES.items() if row and int(row) in rs]
        types = Counter(t["declared_type"] for t in tests_out if (t["class"], t["method"], t["params"]) == key)
        rows.append({
            "row": row, "class": key[0], "method": key[1], "params": key[2], "tests": c["tests"],
            "passing": c["passing_null"] + c["passing_non-null"], "failing": failing,
            "passing_observed_null": c["passing_null"], "passing_observed_non_null": c["passing_non-null"],
            "failing_observed_null": c["failing_null"], "failing_observed_non_null": c["failing_non-null"],
            **{cat: c[cat] for cat in cats},
            "returned_type": " ".join(t for t, _ in types.most_common()),
            "paper_cause": "; ".join(paper),
        })
    rows.sort(key=lambda r: (int(r["row"]) if r["row"] else 999, r["class"], r["method"]))
    out = Path(argv[4])
    out.parent.mkdir(parents=True, exist_ok=True)
    for path, data in ((f"{out}.csv", rows), (f"{out}_tests.csv", tests_out)):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)

    total = Counter()
    for r in rows:
        for k in ["tests", "passing", "failing", "passing_observed_null", "passing_observed_non_null",
                  "failing_observed_null", "failing_observed_non_null"] + cats:
            total[k] += r[k]
    lines = [
        f"methods with failing tests: {len(rows)}; their tests: {total['tests']}, passing {total['passing']}, "
        f"failing {total['failing']}",
        "failing tests by category: " + ", ".join(f"{k} {total[k]}" for k in cats),
        f"in these methods, passing tests that observed null: {total['passing_observed_null']}, non-null: "
        f"{total['passing_observed_non_null']}; failing tests that observed null: {total['failing_observed_null']}, "
        f"non-null: {total['failing_observed_non_null']}",
        "",
        "row  method                                   tests pass fail  pass(null/non-null) fail(null/non-null)  "
        "categories  | returned type | paper's cause",
    ]
    for r in rows:
        catstr = " ".join(f"{k}={r[k]}" for k in cats if r[k])
        lines.append(f"{r['row']:>3}  {r['class'].rsplit('.', 1)[1] + '.' + r['method']:<40} {r['tests']:>5} "
                     f"{r['passing']:>4} {r['failing']:>4}  {r['passing_observed_null']:>4}/{r['passing_observed_non_null']:<4}"
                     f"            {r['failing_observed_null']:>4}/{r['failing_observed_non_null']:<4}           {catstr}"
                     f" | {r['returned_type']} | {r['paper_cause'] or '-'}")
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
