# Executing the generated tests

The paper keeps a generated test if it passes and is not flaky (Section II.F, run 5 times), and reports per target
method the tests that pass and fail (Table III, #PASSING and #FAILING). This page describes how the generated tests
are run here and how their outcomes are counted.

## Procedure

Workflow `assess-tests` (one job per test source):

1. **Tests.** `reproduction`: the tests generated from this repository's profiles (artifact of a `generate-tests`
   run). `authors`: the tests the authors published (Zenodo record 4298605, `pankti-generated-junit-tests/`), to see
   how the same tests behave in this environment.
2. **Integration** into a PDFBox 2.0.21 checkout with `scripts/pankti/integrate-tests.sh` (see
   [generation.md](generation.md)), then `mvn install -DskipTests` on fontbox and pdfbox, which compiles every test.
3. **Runs** with `scripts/pankti/run-generated-tests.sh`: 5 separate Maven invocations of
   `surefire:test -Dtest='Test*PanktiGen*'`, each in new JVMs, with the modules' own surefire settings (pdfbox:
   `-Xmx768m`). The surefire reports of every run are kept.
4. **Counting** with `analysis/test_outcomes.py` (assumption A19):

   | Verdict over the 5 runs | Rule |
   |---|---|
   | passing | passes in every run |
   | failing | fails (assertion failure or error) in every run |
   | flaky | passes in some runs, fails in others |
   | not run | absent or skipped in some run; never counted as passing |

   Tests are attributed to their target method as in `analysis/count_generated_tests.py`. Failures are grouped by
   exception type. The per-method counts are compared with Table III and with the tests the authors actually executed
   (`report.csv` of their experiments repository; discrepancies.md item 2).

Local check: [experiments.md](experiments.md), E16.

## A bug found by the first run

The first run (assess-tests 39641425498) reported 301 failing tests of `HorizontalMetricsTable` (`getAdvanceWidth`,
`getLeftSideBearing`), all with `ConversionException: No converter available` for `java.io.FileCleanable`. The
profiles of these methods contain a `TrueTypeFont` read from a font file, hence a `java.io.FileDescriptor`, which
XStream can only rebuild with PANKTI's `FileCleanableConverter`, registered by the generated `setUpXStream()` method.
pankti-generate writes that method after the tests of the first target method of a class, i.e. between tests, and the
class splitter kept only the text before the first test and after the last one: the two split parts of the class had
no `setUpXStream()`. The splitter now keeps every member found between tests in every part (unit test in
`tests/test_analysis.py`). The same run showed that the authors' published classes do not compile as published
(assumption A20). Its summary is kept in `results/06-test-execution/run-39641425498-split-bug/` as evidence; it is not a result.

## Results

Run 39644913295 (`results/06-test-execution/`, `results/06-test-execution/table3_execution.*`; details in [experiments.md](experiments.md),
E17 and E18):

| | Tests | Passing in all 5 runs | Failing in all 5 runs | Flaky | Pass rate |
|---|---|---|---|---|---|
| Paper (Table III) | 13,851 | 13,614 | 237 | | 98.29% |
| The authors' published tests, run here | 13,851 | 13,614 | 237 | 0 | 98.29% |
| This reproduction | 14,679 | 14,314 | 365 | 0 | 97.51% |

- The authors' tests give Table III's #PASSING and #FAILING for all 46 methods: the environment does not change the
  outcomes, and the 11,613 `getFlags` tests the authors had not executed do pass.
- This reproduction's tests give the paper's values in 38 of the 46 rows. In the other 8, the number of tests differs
  (more or fewer unique profiles, mostly font methods; see the workload results), and all the extra failures belong to
  4 methods: `TrueTypeFont.getOS2Windows` (not in Table III, 114 tests, all failing), `FontCache.getFont` (+8),
  `DefaultResourceCache.getColorSpace` (+4), `COSParser.getEncryption` (+2).
- No test is flaky over the 5 runs.
- Failure types: `AssertionError` (the deserialised object does not equal the returned one: `equals()` not overridden,
  transient state, missing caches; paper Section V.A), and, for `getOS2Windows`, `EOFException` and
  `IOException: Bad file descriptor`: its profiles contain an open font file, which cannot be restored.
