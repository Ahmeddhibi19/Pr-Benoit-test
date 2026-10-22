"""Tests that PIT ran against the mutants of one method, and which of them killed each mutant.

usage: mutant_tests.py <class FQN> <method> <mutations.json[.gz]> [<mutations.json[.gz]> ...]

Reads PIT's mutations.json (written by the descartes profile, compressed in results/). For each report and each
mutant of the method: the status, the number of tests run out of the tests that cover the method, the killing tests,
and the position of the first killing test in PIT's order. Used to explain a classification that differs between two
runs of the same tests (docs/discrepancies.md).
"""
import gzip
import json
import sys


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)["mutations"]


def short(test):
    return test.split("(")[0].rsplit(".", 2)[-2] + "." + test.split("(")[0].rsplit(".", 1)[-1]


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    cls, method = argv[1], argv[2]
    pkg, name = cls.rsplit(".", 1)
    for path in argv[3:]:
        print(path)
        for m in load(path):
            where = m["method"]
            if (where["package"], where["class"], where["name"]) != (pkg, name, method):
                continue
            tests = m["tests"]
            ordered = tests.get("ordered", [])
            killing = tests.get("killing", [])
            first = min((ordered.index(k) for k in killing if k in ordered), default=None)
            print(f"  {where['description']} mutant {m['mutator']}: {m['status']}, {tests.get('run')} of {len(ordered)} "
                  f"covering tests run; killed by: {', '.join(short(k) for k in killing) or '-'}"
                  + (f" (position {first + 1} in PIT's order)" if first is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
