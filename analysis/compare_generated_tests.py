"""Compare generated test classes with reference ones (e.g. the tests the authors published), test by test.

usage: compare_generated_tests.py <generated_tests_dir> <reference_tests_dir> <out_prefix>

Both directories hold Test*PanktiGen.java files in package directories. For every class, each @Test method of the
reference is looked up by name in the generated class and its body is compared (line endings ignored). Class-level
differences (imports, the position of the @Before method) are not counted: the authors edited those by hand.
Writes <out_prefix>.csv (one row per class) and <out_prefix>.txt (summary).
"""
import csv
import re
import sys
from pathlib import Path

TEST = re.compile(r"    @Test\n    public void (test\w+)\(\) throws Exception \{\n(.*?)\n    \}\n", re.S)


def tests(path):
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return dict(TEST.findall(text))


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    gen_root, ref_root, out = Path(argv[1]), Path(argv[2]), Path(argv[3])
    rows = []
    for ref in sorted(ref_root.rglob("Test*PanktiGen.java")):
        rel = ref.relative_to(ref_root)
        gen = gen_root / rel
        r_tests = tests(ref)
        g_tests = tests(gen) if gen.exists() else {}
        same = sum(1 for n, body in r_tests.items() if g_tests.get(n) == body)
        rows.append({"class": rel.as_posix(), "reference_tests": len(r_tests), "generated_tests": len(g_tests),
                     "identical": same, "different": sum(1 for n in r_tests if n in g_tests and g_tests[n] != r_tests[n]),
                     "missing": sum(1 for n in r_tests if n not in g_tests),
                     "extra": sum(1 for n in g_tests if n not in r_tests)})
    extra_classes = sorted(p.relative_to(gen_root).as_posix() for p in gen_root.rglob("Test*PanktiGen.java")
                           if not (ref_root / p.relative_to(gen_root)).exists())
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    total = lambda k: sum(r[k] for r in rows)
    lines = [f"reference classes: {len(rows)}; generated classes not in the reference: {len(extra_classes)}",
             f"reference tests: {total('reference_tests'):,}; generated: {total('generated_tests'):,}",
             f"identical test methods: {total('identical'):,}; different: {total('different'):,}; "
             f"missing: {total('missing'):,}; extra: {total('extra'):,}"]
    lines += [f"  {r['class']}: {r['identical']}/{r['reference_tests']} identical, {r['different']} different, "
              f"{r['missing']} missing, {r['extra']} extra" for r in rows if r["identical"] != r["reference_tests"] or r["extra"]]
    lines += [f"  extra class: {c}" for c in extra_classes]
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
