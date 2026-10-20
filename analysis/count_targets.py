"""Summarise the target methods (#TARGET) obtained with pankti-extract and find-pseudo-tested.py.

usage: count_targets.py <extract_out_dir> <descartes_reports_dir> <invoked-methods.csv> <out_prefix>

<extract_out_dir> is the output of scripts/pankti/extract-targets.sh (extracted-methods-*.csv and
instrumentation-candidates-*.csv). <descartes_reports_dir> holds the "before" methods.json files, one folder per
module. invoked-methods.csv lists the 46 effective targets of Table III (replication data).

Writes <out_prefix>.csv (one row per target: module, signature, return type, effective target or not) and
<out_prefix>.txt (counts compared with the paper, plus the variants used to discuss #TARGET).
"""
import csv
import sys
from collections import Counter
from pathlib import Path

from descartes import find_reports, load_method_list, load_report

PAPER_TARGET, PAPER_EFF_TARGET, README_INSTRUMENTED = 138, 46, 129


def module_of(report_path):
    """.../before/<module>/target/pit-reports/<date>/methods.json -> <module>"""
    return Path(report_path).parents[3].name


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    extract_dir, reports_dir, invoked_csv, out_prefix = Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4])
    extracted = load_method_list(next(extract_dir.glob("extracted-methods-*.csv")))
    candidates = load_method_list(next(extract_dir.glob("instrumentation-candidates-*.csv")))
    invoked = {k for k, _ in load_method_list(invoked_csv)}

    classification, module = {}, {}
    for path in find_reports(reports_dir):
        for key, m in load_report(path).items():
            classification[key] = m["classification"]
            module[key] = module_of(path)

    rows = []
    for key, r in candidates:
        rows.append({"module": module.get(key, ""), "class": key[0], "method": key[1], "params": key[2],
                     "return_type": r["return-type"], "returns_primitive": r["returns-primitives"],
                     "effective_target": key in invoked})
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out_prefix}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["module"], r["class"], r["method"], r["params"])))

    keys = {k for k, _ in candidates}
    extracted_keys = {k for k, _ in extracted}
    per_module = Counter(r["module"] for r in rows)
    not_covered = sum(1 for k in extracted_keys if classification.get(k) == "not-covered")
    pseudo_all = Counter(module[k] for k, c in classification.items() if c == "pseudo-tested")
    pseudo_void = sum(1 for k, c in classification.items() if c == "pseudo-tested" and k not in extracted_keys
                      and k not in keys)
    lines = [
        f"methods kept by pankti-extract          : {len(extracted_keys):,}",
        f"#TARGET (extracted and pseudo-tested)   : {len(keys)} (paper: {PAPER_TARGET}; README of the experiments: "
        f"{README_INSTRUMENTED} instrumented)",
        "  per module: " + ", ".join(f"{m} {n}" for m, n in sorted(per_module.items())),
        f"effective targets among them           : {len(keys & invoked)} / {len(invoked)} "
        f"(paper #EFF_TARGET: {PAPER_EFF_TARGET})",
        "",
        "Variants (to discuss the definition of #TARGET):",
        f"  pseudo-tested methods in the reports, before any filter: {sum(pseudo_all.values())} "
        "(" + ", ".join(f"{m} {n}" for m, n in sorted(pseudo_all.items())) + ")",
        f"  of which removed by the pankti-extract filter: {pseudo_void} (void, static, private, deprecated, ...)",
        f"  extracted methods that are not covered by any test: {not_covered} "
        "(later PANKTI versions also target these)",
    ]
    text = "\n".join(lines) + "\n"
    Path(f"{out_prefix}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0 if keys >= invoked else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
