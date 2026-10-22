"""Keep only the generated tests that passed in every run (paper, Section II.F: a test is kept if it passes and is
not flaky), before the "after" Descartes run, which needs a green test suite.

usage: keep_passing_tests.py <tests_dir> <test_outcomes_tests.csv[.gz]>

<test_outcomes_tests.csv> is written by analysis/test_outcomes.py. Test classes may have been split into
...PanktiGenPartN classes when they were run; test method names are unique within a generated class, so a test is
identified by its original class and its name. Every @Test method whose verdict is not "passing" is removed, other
members are kept; a class left without tests is removed (JUnit 4 rejects a class without tests).
"""
import csv
import gzip
import re
import sys
from pathlib import Path

TEST = re.compile(r"    @Test\n    public void (test\w+)\(\) throws Exception \{\n.*?\n    \}\n\n?", re.S)
PART = re.compile(r"Part\d+$")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    root, outcomes = Path(argv[1]), argv[2]
    opener = gzip.open if outcomes.endswith(".gz") else open
    verdicts = {}
    with opener(outcomes, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            verdicts[(PART.sub("", r["test_class"]), r["test"])] = r["verdict"]

    kept = removed = classes_removed = 0
    unknown = []
    for path in sorted(root.rglob("Test*PanktiGen.java")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        package = re.search(r"^package ([\w.]+);", text, re.M).group(1)
        cls = f"{package}.{path.stem}"

        def keep(m):
            nonlocal kept, removed
            v = verdicts.get((cls, m.group(1)))
            if v is None:
                unknown.append(f"{cls}.{m.group(1)}")
            if v == "passing":
                kept += 1
                return m.group(0)
            removed += 1
            return ""

        new = TEST.sub(keep, text)
        if not TEST.search(new):
            path.unlink()
            classes_removed += 1
        else:
            path.write_text(new, encoding="utf-8", newline="\n")
    print(f"kept {kept} passing tests, removed {removed} (failing, flaky, not run or without outcome), "
          f"removed {classes_removed} classes left without tests; tests without an outcome: {len(unknown)}")
    for u in unknown[:10]:
        print(f"  no outcome: {u}")
    return 0 if not unknown else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
