"""Predict the Descartes status of each target from the values its passing tests observed, and compare with the
"after" run (plan A.6, "prediction check"); list the targets that keep passing tests but stay pseudo-tested
(paper, Section V.B, "null-only" check).

usage: prediction_check.py <generated_tests_dir> <test_outcomes_tests.csv[.gz]> <after_reports> <invoked-methods.csv>
                           <out_prefix> [--table3 <analysis/paper/table3_pdfbox.csv>] [--sources <pdfbox_dir>]

Prediction rule (understanding of Section II.C): a passing generated test asserts the value observed in production
with equals(), so it kills every extreme mutant whose default value differs from that value
(generated_tests.mutant_killed). For each mutant Descartes created for a target, the prediction is "detected" when
at least one passing test of the target kills it; the predicted classification follows Descartes' rule (all
mutants detected: tested; none: pseudo-tested; otherwise partially-tested). Only the target's own tests are used, so
a mutant killed by another test (an existing PDFBox test, or a generated test of another target that calls the
method) shows up as a disagreement.
Each target's return type is classified as primitive, wrapper or String, array, enum (XStream writes an enum
constant as an element with text only) or object; with --sources (a PDFBox source tree), the summary also says
whether the returned class declares equals(). Writes <out_prefix>.csv (one row per target), <out_prefix>.txt (summary).
"""
import csv
import gzip
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from descartes import find_reports, load_method_list, load_reports
from generated_tests import mutant_killed, observed_values

PRIMITIVES = {"boolean", "byte", "char", "short", "int", "long", "float", "double"}


def return_kind(return_type, values):
    if return_type in PRIMITIVES:
        return "primitive"
    if return_type.startswith("java.lang.") and return_type.count(".") == 2:
        return "wrapper or String"
    if return_type.endswith("[]"):
        return "array"
    return "enum" if any(v[0] == "enum" for v in values) else "object"


def declares_equals(sources, return_type):
    """yes / no from the class's source file in the PDFBox tree, or "not in PDFBox" (JDK classes)."""
    simple = return_type.rsplit(".", 1)[1].split("$")[0]
    files = [f for f in Path(sources).rglob(f"{simple}.java") if "src" + "/main" in f.as_posix()]
    if not files:
        return "not in PDFBox"
    return "yes" if "public boolean equals(Object" in files[0].read_text(encoding="utf-8", errors="replace") else "no"


def open_text(path):
    return gzip.open(path, "rt", encoding="utf-8", newline="") if str(path).endswith(".gz") else \
        open(path, encoding="utf-8", newline="")


def classify(detected, mutators):
    if not mutators:
        return "not-covered"
    if len(detected) == len(mutators):
        return "tested"
    return "partially-tested" if detected else "pseudo-tested"


def describe(values):
    """Short description of the observed values: kinds, and the values themselves when there are few."""
    kinds = Counter(v[0] for v in values)
    distinct = sorted({repr(v[1]) for v in values if v[0] not in ("object", "null")})
    text = ", ".join(f"{k} {n}" for k, n in kinds.most_common())
    return text + (f" [{'; '.join(distinct)}]" if 0 < len(distinct) <= 4 else "")


def main(argv):
    if len(argv) < 6:
        print(__doc__)
        return 2
    values = observed_values(argv[1])
    targets = load_method_list(argv[4])
    by_params = {(k[0], k[1], r["param-list"].replace(" ", "")): k for k, r in targets}
    returns = {k: r["return-type"] for k, r in targets}
    passing, every = defaultdict(list), defaultdict(list)
    with open_text(argv[2]) as f:
        for r in csv.DictReader(f):
            key = by_params[(r["class"], r["method"], r["params"].replace(" ", ""))]
            value = values[(re.sub(r"Part\d+$", "", r["test_class"]), r["test"])]
            every[key].append(value)
            if r["verdict"] == "passing":
                passing[key].append(value)
    sources = argv[argv.index("--sources") + 1] if "--sources" in argv else None
    after_path = Path(argv[3])
    after = load_reports([after_path] if after_path.is_file() else find_reports(after_path))
    paper = {}
    if "--table3" in argv:
        with open(argv[argv.index("--table3") + 1], newline="", encoding="utf-8") as f:
            paper = {r["class_method"]: r["row"] for r in csv.DictReader(f)}

    rows = []
    for key, _ in targets:
        m = after.get(key)
        mutators = [x["mutator"] for x in m["mutations"]] if m else []
        obs = passing.get(key, [])
        predicted = [mu for mu in mutators if any(mutant_killed(v, mu) for v in obs)]
        actual = list(m.get("detected", [])) if m else []
        rows.append({
            "row": paper.get(f"{key[0].rsplit('.', 1)[1]}_{key[1]}", ""),
            "class": key[0], "method": key[1], "params": key[2],
            "return_type": returns[key], "return_kind": return_kind(returns[key], every[key]),
            "declares_equals": declares_equals(sources, returns[key]) if sources and
            return_kind(returns[key], every[key]) == "object" else "",
            "passing_tests": len(obs), "observed": describe(obs),
            "mutators": " ".join(mutators),
            "predicted_detected": " ".join(predicted), "actual_detected": " ".join(actual),
            "predicted": classify(predicted, mutators), "actual": m["classification"] if m else "absent",
            "agree": sorted(predicted) == sorted(actual),
        })
    rows.sort(key=lambda r: (int(r["row"]) if r["row"] else 999, r["class"], r["method"]))
    out = Path(argv[5])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def name(r):
        return f"row {r['row'] or '-':>2} {r['class'].rsplit('.', 1)[1]}.{r['method']}"

    n_mut = sum(len(r["mutators"].split()) for r in rows)
    n_mut_agree = sum(len(set(r["mutators"].split()) - (set(r["predicted_detected"].split()) ^
                                                        set(r["actual_detected"].split()))) for r in rows)
    lines = [
        f"targets: {len(rows)}; mutants: {n_mut}; mutant outcome predicted correctly: {n_mut_agree} / {n_mut}",
        f"targets whose detected mutants are predicted exactly: {sum(r['agree'] for r in rows)} / {len(rows)}; "
        f"same classification: {sum(r['predicted'] == r['actual'] for r in rows)} / {len(rows)}",
    ]
    lines += [f"  {name(r)}: predicted {r['predicted']} ({r['predicted_detected'] or '-'}), "
              f"Descartes {r['actual']} ({r['actual_detected'] or '-'}); passing tests observed: {r['observed'] or '-'}"
              for r in rows if not r["agree"]]
    stay = [r for r in rows if r["passing_tests"] and r["actual"] == "pseudo-tested"]
    null_only = [r for r in stay if r["mutators"] == "null" and r["observed"].startswith("null ")
                 and "," not in r["observed"]]
    lines += ["", f"Section V.B: targets with passing tests that stay pseudo-tested: {len(stay)}; "
                  f"of which only the null mutant and only null observed: {len(null_only)}"]
    lines += [f"  {name(r)}: {r['passing_tests']} passing tests ({r['observed']}); mutants: {r['mutators']}"
              for r in stay]
    lines += ["", "status after, by return type (well-tested = tested or partially-tested):"]
    by_kind = defaultdict(Counter)
    for r in rows:
        by_kind[r["return_kind"]]["well-tested" if r["actual"] in ("tested", "partially-tested") else r["actual"]] += 1
    lines += [f"  {k}: " + ", ".join(f"{s} {n}" for s, n in sorted(c.items())) for k, c in sorted(by_kind.items())]
    if sources:
        eq = Counter(r["declares_equals"] for r in rows if r["return_kind"] == "object")
        lines.append("  object return types, the returned class declares equals(): "
                     + ", ".join(f"{k} {n}" for k, n in sorted(eq.items())))
        lines += [f"    {r['return_type']}" for r in rows if r["declares_equals"] == "yes"]
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
