"""Outcome of the generated tests over several runs: #PASSING, #FAILING and flaky tests per target method.

usage: test_outcomes.py <runs_dir> <invoked-methods.csv> <out_prefix>
                        [--generated <generated_tests.csv>] [--table3 <authors_report_vs_paper.csv>]

<runs_dir> holds run-1/, run-2/, ... with the surefire reports (TEST-*.xml) of each run (run-generated-tests.sh).
A test passes in a run if its <testcase> has no <failure>, <error> or <skipped>. Over all runs, a test is
  passing  if it passes in every run,
  failing  if it fails (failure or error) in every run,
  flaky    if it passes in some runs and fails in others,
  not run  otherwise (absent or skipped in some run) - never counted as passing.
Tests are attributed to target methods as in count_generated_tests.py; split classes (...PanktiGenPartN) belong to
their target class. With --generated, the number of generated tests per method is shown next to the executed ones;
with --table3 (results/01-paper-vs-artifacts/authors_report_vs_paper.csv), the paper's #PASSING / #FAILING and the authors' executed
counts are added.
Writes <out_prefix>.csv (per method), <out_prefix>_tests.csv (per test and run), <out_prefix>_failures.csv
(failure types) and <out_prefix>.txt (summary).
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from count_generated_tests import attribute, targets_by_class  # noqa: E402

CLASS = re.compile(r"^(?P<package>.*)\.Test(?P<simple>\w+?)PanktiGen(Part\d+)?$")


def read_run(run_dir):
    """{(test class, test name): (status, exception type, message)} for one run."""
    results = {}
    for report in sorted(Path(run_dir).rglob("TEST-*.xml")):
        for case in ET.parse(report).getroot().iter("testcase"):
            status, kind, message = "pass", "", ""
            for tag in ("failure", "error", "skipped"):
                node = case.find(tag)
                if node is not None:
                    status = tag
                    kind = node.get("type", "") or ""
                    message = (node.get("message") or "").strip().splitlines()[0][:200] if node.get("message") else ""
                    break
            results[(case.get("classname"), case.get("name"))] = (status, kind, message)
    return results


def classify(statuses):
    if all(s == "pass" for s in statuses):
        return "passing"
    if all(s in ("failure", "error") for s in statuses):
        return "failing"
    if any(s == "pass" for s in statuses) and all(s in ("pass", "failure", "error") for s in statuses):
        return "flaky"
    return "not-run"


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    runs_dir, invoked, out = Path(argv[1]), argv[2], Path(argv[3])
    run_dirs = sorted((d for d in runs_dir.iterdir() if d.is_dir() and re.fullmatch(r"run-\d+", d.name)),
                      key=lambda d: int(d.name.split("-")[1]))
    runs = [read_run(d) for d in run_dirs]
    by_class = targets_by_class(invoked)
    tests = sorted(set().union(*runs)) if runs else []

    per_method = defaultdict(Counter)
    failures = Counter()
    test_rows = []
    unattributed = 0
    for test in tests:
        m = CLASS.match(test[0] or "")
        target = None
        if m:
            cls = m.group("package") + "." + m.group("simple")
            hit = attribute(test[1], by_class.get(cls, []))
            target = (cls, hit[0], hit[1]) if hit else None
        if target is None:
            unattributed += 1
            continue
        outcomes = [r.get(test, ("absent", "", "")) for r in runs]
        verdict = classify([o[0] for o in outcomes])
        per_method[target][verdict] += 1
        per_method[target]["executed"] += 1
        for status, kind, _ in outcomes:
            if status in ("failure", "error"):
                failures[(target, status, kind)] += 1
        first_fail = next((o for o in outcomes if o[0] in ("failure", "error")), ("", "", ""))
        test_rows.append([test[0], test[1], target[0], target[1], target[2], verdict]
                         + [o[0] for o in outcomes] + [first_fail[1], first_fail[2]])

    generated = {}
    if "--generated" in argv:
        with open(argv[argv.index("--generated") + 1], newline="", encoding="utf-8") as f:
            generated = {(r["class"], r["method"], r["params"]): int(r["pankti_tests"]) for r in csv.DictReader(f)}
    paper = {}
    if "--table3" in argv:
        with open(argv[argv.index("--table3") + 1], newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                paper[(r["fqn"], r["class_method"].split("_", 1)[1])] = r

    keys = sorted(set(per_method) | set(generated))
    rows = []
    for k in keys:
        c = per_method.get(k, Counter())
        p = next((v for (fqn, name), v in paper.items() if fqn == k[0] and name == k[1]), None)
        rows.append({
            "row": p["row"] if p else "", "class": k[0], "method": k[1], "params": k[2],
            "generated": generated.get(k, ""), "executed": c["executed"], "passing": c["passing"],
            "failing": c["failing"], "flaky": c["flaky"], "not_run": c["not-run"],
            "paper_passing": p["paper_passing"] if p else "", "paper_failing": p["paper_failing"] if p else "",
            "authors_executed": p["report_executed"] if p else "", "authors_passing": p["report_passing"] if p else "",
            "authors_failing": p["report_failing"] if p else ""})

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(f"{out}_tests.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["test_class", "test", "class", "method", "params", "verdict"]
                   + [f"run{i + 1}" for i in range(len(runs))] + ["failure_type", "failure_message"])
        w.writerows(test_rows)
    with open(f"{out}_failures.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["class", "method", "params", "status", "exception_type", "occurrences_over_runs"])
        for (k, status, kind), n in sorted(failures.items()):
            w.writerow([k[0], k[1], k[2], status, kind, n])

    tot = Counter()
    for c in per_method.values():
        tot.update(c)
    kinds = Counter()
    for (_, _, kind), n in failures.items():
        kinds[kind] += n
    lines = [f"runs: {len(runs)}; tests seen: {len(tests):,}; not attributed to a target: {unattributed}",
             f"generated: {sum(generated.values()):,}" if generated else "generated: (not given)",
             f"executed: {tot['executed']:,}; passing in every run: {tot['passing']:,}; failing in every run: "
             f"{tot['failing']:,}; flaky: {tot['flaky']:,}; not run in some run: {tot['not-run']:,}"]
    if tot["executed"]:
        lines.append(f"passing / executed: {tot['passing'] / tot['executed']:.2%}")
    lines.append("failure types (occurrences over all runs): "
                 + (", ".join(f"{k or '?'} {n}" for k, n in kinds.most_common(8)) or "none"))
    if paper:
        lines.append("")
        lines.append("methods whose #PASSING / #FAILING differ from the paper:")
        for r in rows:
            if r["paper_passing"] != "" and (int(r["paper_passing"]) != r["passing"] or int(r["paper_failing"]) != r["failing"]):
                lines.append(f"  row {r['row']} {r['class'].rsplit('.', 1)[1]}.{r['method']}: paper {r['paper_passing']} / "
                             f"{r['paper_failing']}, here {r['passing']} / {r['failing']} (flaky {r['flaky']}), "
                             f"authors executed {r['authors_executed']}: {r['authors_passing']} / {r['authors_failing']}")
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
