"""Summarise Maven surefire reports per module.

usage: test_summary.py <project_dir> <out_dir> [--check]

Writes <out_dir>/test-summary.csv and <out_dir>/failing-tests.txt.
With --check, exits with 1 when no test ran or when a test failed or errored.
"""
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def collect(project):
    per_module = defaultdict(lambda: {"suites": 0, "tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time_s": 0.0})
    failing = []
    for report in sorted(project.glob("**/target/surefire-reports/TEST-*.xml")):
        module = report.relative_to(project).parts[0]
        if module == "target":
            module = "."
        root = ET.parse(report).getroot()
        m = per_module[module]
        m["suites"] += 1
        for key in ("tests", "failures", "errors", "skipped"):
            m[key] += int(root.get(key, 0))
        m["time_s"] += float(root.get("time", 0) or 0)
        for case in root.iter("testcase"):
            for kind in ("failure", "error"):
                node = case.find(kind)
                if node is not None:
                    message = (node.get("message") or "").strip().splitlines()
                    failing.append((module, case.get("classname"), case.get("name"), kind,
                                    node.get("type", ""), message[0][:200] if message else ""))
    return per_module, failing


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    project, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    per_module, failing = collect(project)

    total = {"suites": 0, "tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time_s": 0.0}
    with open(out / "test-summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module", "suites", "tests", "failures", "errors", "skipped", "time_s"])
        for module in sorted(per_module):
            m = per_module[module]
            w.writerow([module] + [m[k] for k in ("suites", "tests", "failures", "errors", "skipped")] + [round(m["time_s"], 1)])
            for k in total:
                total[k] += m[k]
        w.writerow(["TOTAL"] + [total[k] for k in ("suites", "tests", "failures", "errors", "skipped")] + [round(total["time_s"], 1)])

    with open(out / "failing-tests.txt", "w") as f:
        for row in failing:
            f.write(" | ".join(str(x) for x in row) + "\n")

    print(f"tests={total['tests']} failures={total['failures']} errors={total['errors']} skipped={total['skipped']}")
    for row in failing:
        print("FAILED", " | ".join(str(x) for x in row))

    if "--check" in argv:
        known = load_known(Path(__file__).with_name("known-failures.txt"))
        unexpected = [row for row in failing if (row[0], row[4]) not in known]
        expected = len(failing) - len(unexpected)
        print(f"known failures: {expected}, unexpected: {len(unexpected)}")
        for row in unexpected:
            print("UNEXPECTED", " | ".join(str(x) for x in row))
        return 1 if total["tests"] == 0 or unexpected else 0
    return 0


def load_known(path):
    """Lines 'module | exception type | reason': failures with a documented cause outside the code under study."""
    known = set()
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                module, exception = [p.strip() for p in line.split("|")[:2]]
                known.add((module, exception))
    return known


if __name__ == "__main__":
    sys.exit(main(sys.argv))
