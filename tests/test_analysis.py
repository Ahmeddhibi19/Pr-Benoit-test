"""Unit tests of the analysis scripts that turn raw outputs into the paper's metrics.

Run from the repository root: python -m unittest discover -s tests
"""
import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import profile_stats  # noqa: E402
import workload_log  # noqa: E402
from descartes import param_descriptor, well_tested  # noqa: E402


def sha1(text):
    return hashlib.sha1(text).digest()


class FragmentTest(unittest.TestCase):
    """profile_stats.scan_fragments must return the exact text of each top-level element, as pankti-generate does."""

    def scan(self, data):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x-returned.xml"
            f.write_bytes(data)
            return profile_stats.scan_fragments(f)

    def test_empty_elements(self):
        frags = self.scan(b"<null/>\n<null/>\n")
        self.assertEqual([h for h, _ in frags], [sha1(b"<null/>")] * 2)
        self.assertEqual([d for _, d in frags], [1, 1])

    def test_nested_elements_and_depth(self):
        frag = b"<a>\n  <b>x</b>\n  <c/>\n</a>"
        frags = self.scan(frag + b"\n" + frag + b"\n<a><b><c>y</c></b></a>\n")
        self.assertEqual([h for h, _ in frags], [sha1(frag), sha1(frag), sha1(b"<a><b><c>y</c></b></a>")])
        self.assertEqual([d for _, d in frags], [2, 2, 3])

    def test_no_final_newline(self):
        frags = self.scan(b"<int>5</int>\n<null/>")
        self.assertEqual([h for h, _ in frags], [sha1(b"<int>5</int>"), sha1(b"<null/>")])


class UniqueTest(unittest.TestCase):
    """#UNIQUE: distinct (receiving, params, returned) triples of fragments paired by position."""

    def write(self, d, stem, receiving, params, returned):
        for part, data in (("-receiving.xml", receiving), ("-params.xml", params), ("-returned.xml", returned)):
            (Path(d) / f"{stem}{part}").write_bytes(data)

    def test_unique_and_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            # 3 calls, two of them identical; a fourth call threw (receiving and params written, no returned value)
            self.write(d, "p.C.m_int",
                       b"<C/>\n<C/>\n<C/>\n<C/>\n",
                       b"<object-array><int>1</int></object-array>\n" * 2
                       + b"<object-array><int>2</int></object-array>\n" * 2,
                       b"<boolean>true</boolean>\n<boolean>true</boolean>\n<boolean>false</boolean>\n")
            stats = profile_stats.fragment_stats(d, "p.C.m_int", has_params=True)
        self.assertEqual((stats["receiving_fragments"], stats["params_fragments"], stats["returned_fragments"]),
                         (4, 4, 3))
        self.assertEqual(stats["paired"], 3)
        self.assertEqual(stats["unique"], 2)
        self.assertTrue(stats["fragment_mismatch"])

    def test_params_ignored_without_parameters(self):
        with tempfile.TemporaryDirectory() as d:
            self.write(d, "p.C.m", b"<C/>\n<C/>\n", b"<object-array/>\n<object-array/>\n",
                       b"<int>1</int>\n<int>1</int>\n")
            stats = profile_stats.fragment_stats(d, "p.C.m", has_params=False)
        self.assertEqual(stats["unique"], 1)
        self.assertFalse(stats["fragment_mismatch"])


class WorkloadLogTest(unittest.TestCase):
    LOG = (b"Encrypt  ./workload/000809.pdf\n"
           b"2020-11-03 13:49:45.198 INFO  org.glowroot - Glowroot version: 0.13.6\n"
           b"WARNING: An illegal reflective access operation has occurred\n"
           b"Error: Document is already encrypted.\n"
           b"PDFMerger  ./workload/000810.pdf\n"
           b"Usage: java -jar pdfbox-app-x.y.z.jar PDFMerger <inputfiles 2..n> <outputfile>\n"
           b"OverlayPDF  ./workload/000810.pdf\n"
           b"2020-11-03 13:50:10.211 WARN  o.glowroot.agent.impl.TraceCollector - not storing a trace\n")

    def test_statuses(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "console.log"
            f.write_bytes(self.LOG)
            runs = workload_log.parse(f)
        self.assertEqual([(c, f, s) for c, f, s, _ in runs],
                         [("Encrypt", "000809.pdf", "error"), ("PDFMerger", "000810.pdf", "usage"),
                          ("OverlayPDF", "000810.pdf", "ok")])


class TestOutcomesTest(unittest.TestCase):
    """test_outcomes.py: passing in every run, failing in every run, flaky, not run."""

    REPORT = ('<testsuite name="s">'
              '<testcase classname="p.TestCPanktiGen" name="testM1"/>'
              '<testcase classname="p.TestCPanktiGenPart2" name="testM2">{m2}</testcase>'
              '<testcase classname="p.TestCPanktiGen" name="testM3">'
              '<error type="java.lang.OutOfMemoryError" message="Java heap space"/></testcase>'
              '{m4}</testsuite>')

    def test_verdicts(self):
        import test_outcomes
        with tempfile.TemporaryDirectory() as d:
            runs = Path(d) / "runs"
            for k, (m2, m4) in enumerate([("", '<testcase classname="p.TestCPanktiGen" name="testM4"/>'),
                                          ('<failure type="java.lang.AssertionError"/>', "")], start=1):
                (runs / f"run-{k}").mkdir(parents=True)
                (runs / f"run-{k}" / "TEST-p.xml").write_text(self.REPORT.format(m2=m2, m4=m4), encoding="utf-8")
            invoked = Path(d) / "invoked.csv"
            invoked.write_text("parent-FQN,method-name,param-list\np.C,m,\n", encoding="utf-8")
            test_outcomes.main(["x", str(runs), str(invoked), str(Path(d) / "out")])
            with open(Path(d) / "out_tests.csv", encoding="utf-8") as f:
                verdicts = {r["test"]: r["verdict"] for r in csv.DictReader(f)}
        self.assertEqual(verdicts, {"testM1": "passing", "testM2": "flaky", "testM3": "failing", "testM4": "not-run"})


class SplitTest(unittest.TestCase):
    """split_test_classes.py keeps every test unchanged and the members found between tests in every part."""

    def test_split_keeps_setup_between_tests(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pankti"))
        import split_test_classes
        test = "    @Test\n    public void test{n}() throws Exception {{\n        Assert.assertTrue(true);\n    }}\n"
        setup = "    @Before\n    public void setUpXStream() {\n        xStream.registerConverter(null);\n    }\n"
        source = ("package p;\npublic class TestCPanktiGen {\n\n" + "\n".join(test.format(n=f"A{i}") for i in range(3))
                  + "\n" + setup + "\n" + "\n".join(test.format(n=f"B{i}") for i in range(2)) + "}\n")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "TestCPanktiGen.java"
            f.write_text(source, encoding="utf-8")
            self.assertEqual(split_test_classes.split(f, 2), 3)
            parts = sorted(Path(d).glob("TestCPanktiGenPart*.java"))
            texts = [p.read_text(encoding="utf-8") for p in parts]
        self.assertEqual(len(parts), 3)
        self.assertTrue(all("setUpXStream" in t for t in texts))
        self.assertEqual(sum(t.count("@Test") for t in texts), 5)
        self.assertTrue(all(f"public class {p.stem} {{" in t for p, t in zip(parts, texts)))


class DescartesTest(unittest.TestCase):
    def test_descriptor(self):
        self.assertEqual(param_descriptor("(ILjava/lang/String;)V"), "ILjava/lang/String;")
        self.assertEqual(param_descriptor("()Z"), "")

    def test_well_tested(self):
        self.assertTrue(well_tested("partially-tested"))
        self.assertFalse(well_tested("pseudo-tested"))


if __name__ == "__main__":
    unittest.main()
