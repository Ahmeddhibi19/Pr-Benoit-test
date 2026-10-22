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


class KeepPassingTest(unittest.TestCase):
    """keep_passing_tests.py removes every test that did not pass in all runs, and classes left without tests."""

    def test_keep_passing(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pankti"))
        import keep_passing_tests
        test = "    @Test\n    public void {n}() throws Exception {{\n        Assert.assertTrue(true);\n    }}\n\n"
        with tempfile.TemporaryDirectory() as d:
            pkg = Path(d) / "tests" / "p"
            pkg.mkdir(parents=True)
            (pkg / "TestCPanktiGen.java").write_text(
                "package p;\npublic class TestCPanktiGen {\n\n" + test.format(n="testM1") + test.format(n="testM2")
                + "    @Before\n    public void setUpXStream() {\n    }\n}\n", encoding="utf-8")
            (pkg / "TestDPanktiGen.java").write_text(
                "package p;\npublic class TestDPanktiGen {\n\n" + test.format(n="testN1") + "}\n", encoding="utf-8")
            outcomes = Path(d) / "outcomes.csv"
            outcomes.write_text("test_class,test,class,method,params,verdict\n"
                                "p.TestCPanktiGenPart1,testM1,p.C,m,,passing\n"
                                "p.TestCPanktiGenPart2,testM2,p.C,m,,failing\n"
                                "p.TestDPanktiGen,testN1,p.D,n,,flaky\n", encoding="utf-8")
            self.assertEqual(keep_passing_tests.main(["x", str(Path(d) / "tests"), str(outcomes)]), 0)
            kept = (pkg / "TestCPanktiGen.java").read_text(encoding="utf-8")
            self.assertIn("testM1", kept)
            self.assertNotIn("testM2", kept)
            self.assertIn("setUpXStream", kept)
            self.assertFalse((pkg / "TestDPanktiGen.java").exists())


class PanktiStatusTest(unittest.TestCase):
    """pankti_status.py: status after the generated tests, and targets already well-tested in the control run."""

    @staticmethod
    def report(path, classes):
        methods = [{"name": m, "description": "()Z", "class": "C", "package": "p", "classification": c,
                    "detected": [], "not-detected": [], "mutations": ["true", "false"]} for m, c in classes.items()]
        path.write_text('{"methods": %s}' % __import__("json").dumps(methods), encoding="utf-8")
        return str(path)

    def test_control(self):
        import pankti_status
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            before = self.report(d / "before.json", {"a": "pseudo-tested", "b": "pseudo-tested", "c": "pseudo-tested"})
            after = self.report(d / "after.json", {"a": "partially-tested", "b": "tested", "c": "pseudo-tested"})
            control = self.report(d / "control.json", {"a": "pseudo-tested", "b": "tested", "c": "pseudo-tested"})
            invoked = d / "invoked.csv"
            invoked.write_text("parent-FQN,method-name,param-list,param-signature\np.C,a,,\np.C,b,,\np.C,c,,\n",
                               encoding="utf-8")
            table3 = d / "table3.csv"
            table3.write_text("row,fqn,class_method,param_signature,paper_status\n1,p.C,C_a,,well-tested\n"
                              "2,p.C,C_b,,well-tested\n3,p.C,C_c,,pseudo-tested\n", encoding="utf-8")
            pankti_status.main(["x", before, after, str(invoked), str(d / "out"), "--table3", str(table3),
                                "--control", control])
            with open(d / "out.csv", encoding="utf-8") as f:
                rows = {r["method"]: r for r in csv.DictReader(f)}
            text = (d / "out.txt").read_text(encoding="utf-8")
        self.assertEqual([rows[m]["pankti_status"] for m in "abc"], ["well-tested", "well-tested", "pseudo-tested"])
        self.assertEqual(rows["b"]["control"], "tested")
        self.assertIn("28 / 46", text)
        self.assertIn("2 / 3 (paper", text)
        self.assertIn("same status as Table III: 3 / 3", text)
        self.assertIn("well-tested in the control run without generated tests: 1; "
                      "well-tested after and not in the control run: 1", text)


class GeneratedTestsTest(unittest.TestCase):
    """generated_tests.py reads the observed value of each generated test; mutant_killed applies the equals rule."""

    BODY = ('        {decl}\n        Assert.assertEquals({expected}, receivingObject.m());\n')

    def value(self, expected, decl=""):
        import generated_tests
        return generated_tests.test_value(self.BODY.format(expected=expected, decl=decl))

    def test_literals(self):
        self.assertEqual(self.value("null"), ("null", None))
        self.assertEqual(self.value("true"), ("bool", True))
        self.assertEqual(self.value("32"), ("num", 32.0))
        self.assertEqual(self.value("(byte) 1"), ("num", 1.0))

    def test_xml_values(self):
        decl = ('String returnedObjectStr = \n        "<string>A\\"b</string>";\n'
                '        java.lang.String expectedObject = deserializeObject(returnedObjectStr);')
        self.assertEqual(self.value("expectedObject", decl), ("str", 'A"b'))
        enum = ('String returnedObjectStr = \n        "<p.C_-E>TABLE</p.C_-E>";\n'
                '        p.C.E expectedObject = deserializeObject(returnedObjectStr);')
        self.assertEqual(self.value("expectedObject", enum), ("enum", "TABLE"))
        big = ('File fileReturned = new File("x");\n'
               '        java.awt.geom.GeneralPath expectedObject = deserializeObject(fileReturned);')
        self.assertEqual(self.value("expectedObject", big), ("object", "java.awt.geom.GeneralPath"))

    def test_mutant_killed(self):
        from generated_tests import mutant_killed
        self.assertTrue(mutant_killed(("bool", True), "false"))
        self.assertFalse(mutant_killed(("bool", True), "true"))       # isFill: partially tested
        self.assertFalse(mutant_killed(("null", None), "null"))       # Section V.B
        self.assertTrue(mutant_killed(("null", None), '""'))
        self.assertTrue(mutant_killed(("str", "Italic"), '"A"'))
        self.assertFalse(mutant_killed(("num", 0.0), "(byte)0"))
        self.assertTrue(mutant_killed(("object", "p.C"), "null"))
        self.assertTrue(mutant_killed(("array", None), "empty"))
        self.assertFalse(mutant_killed(("array", 0), "empty"))


class FailureCategoryTest(unittest.TestCase):
    def test_categories(self):
        from failure_analysis import category
        a = "java.lang.AssertionError"
        self.assertEqual(category(a, "expected:<p.C@1a2b> but was:<p.C@3c4d>"), "identity-equals")
        self.assertEqual(category(a, "expected: p.C<X-0> but was: p.C<X-0>"), "identity-equals")
        self.assertEqual(category(a, "expected:<PDTrueTypeFont Arial> but was:<null>"), "returns-null")
        self.assertEqual(category("java.io.EOFException", ""), "exception")
        self.assertEqual(category(a, "expected:<1> but was:<2>"), "other")


class DescartesTest(unittest.TestCase):
    def test_descriptor(self):
        self.assertEqual(param_descriptor("(ILjava/lang/String;)V"), "ILjava/lang/String;")
        self.assertEqual(param_descriptor("()Z"), "")

    def test_well_tested(self):
        self.assertTrue(well_tested("partially-tested"))
        self.assertFalse(well_tested("pseudo-tested"))


if __name__ == "__main__":
    unittest.main()
