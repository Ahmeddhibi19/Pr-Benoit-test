"""Split generated test classes that hold too many tests into several classes, without changing any test.

usage: split_test_classes.py <tests_dir> <max_tests_per_class>

pankti-generate writes all the tests of a target class into one class; for GlyfSimpleDescript.getFlags this is
11,730 tests in a 90 MB source file, beyond what javac and the class-file format handle comfortably. A class with
more than <max_tests_per_class> tests is replaced by Test<Class>PanktiGenPart1, Part2, ... Each part keeps the
class header (imports, the XStream field, the deserializeObject helpers) and the class footer (setUpXStream) and
receives a consecutive slice of the @Test methods, unchanged.
"""
import re
import sys
from pathlib import Path

TEST = re.compile(r"    @Test\n    public void test\w+\(\) throws Exception \{\n.*?\n    \}\n", re.S)


def split(path, limit):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    tests = list(TEST.finditer(text))
    if len(tests) <= limit:
        return 0
    head, tail = text[:tests[0].start()], text[tests[-1].end():]
    name = path.stem
    parts = 0
    for start in range(0, len(tests), limit):
        parts += 1
        part = f"{name}Part{parts}"
        body = "\n".join(m.group(0) for m in tests[start:start + limit])
        new_head = head.replace(f"public class {name} {{", f"public class {part} {{", 1)
        assert new_head != head, f"class declaration not found in {path}"
        (path.parent / f"{part}.java").write_text(new_head + body + tail, encoding="utf-8", newline="\n")
    path.unlink()
    print(f"{path.name}: {len(tests)} tests -> {parts} classes of at most {limit}")
    return parts


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    root, limit = Path(argv[1]), int(argv[2])
    for path in sorted(root.rglob("Test*PanktiGen.java")):
        split(path, limit)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
