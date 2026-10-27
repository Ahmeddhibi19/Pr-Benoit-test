# Pseudo-tested methods (Descartes)

The paper selects its target methods with Descartes (Section III.D): a method is *pseudo-tested* when it is covered by
the test suite but no test fails when its whole body is replaced by a default return value. The targets (#TARGET) are
the pseudo-tested methods that PANKTI can instrument (public, non-static, non-void, ...). After the generated tests
are added, Descartes runs again; a target that is no longer pseudo-tested is "well-tested" (PANKTI_STATUS).

This page describes how Descartes is run in this reproduction, and how the result compares with the authors' reports.

## Extreme mutation in short

Descartes is a mutation engine for PIT. For every method it creates *extreme mutants*: the body is replaced by
`return <value>` for each default value of the return type (`void` methods get an empty body). With the 21 operators
used here:

| Return type | Mutants |
|---|---|
| void | empty body |
| reference types | `null` (plus `""`/`"A"` for `String`, an empty array for arrays) |
| boolean | `true`, `false` |
| int, long, short, byte | 0 and 1 |
| float, double | 0.0 and 1.0 |
| char | `' '` (`'\40'`) and `'A'` |

A mutant is *detected* when at least one test fails. A covered method is *tested* if all its mutants are detected,
*partially-tested* if some are, *pseudo-tested* if none is. Methods that no test reaches are *not-covered*.

Descartes skips "stop methods" by default (simple getters and setters, empty methods, `toString`, `hashCode`,
deprecated, synthetic, methods that only return a constant or delegate). They do not appear in the reports.

## Configuration

| Setting | Value | Source / reason |
|---|---|---|
| PIT | pitest-maven 1.4.10 | Descartes 1.2.6 is built against it |
| Descartes | 1.2.6 | last release before the authors' runs (2020-09-21); 1.3 came out in December 2020 |
| Mutation operators | the 21 listed above | read from the `analysis.mutators` field of every methods.json of the authors |
| Stop methods, timeouts | PIT and Descartes defaults | nothing else is documented |
| Output | `METHODS` (methods.json) and `JSON` (mutations.json) | the authors published methods.json |
| Modules | examples, fontbox, pdfbox, preflight, tools, xmpbox, one run each | the authors' "before" reports |
| Classes | `org.apache.fontbox.*`, `org.apache.xmpbox.*`, `org.apache.pdfbox.*` for the other modules | PIT's default (`<groupId>*`) would select nothing in fontbox and xmpbox (assumption A4) |
| Excluded tests | `TestCreateSignature`, `CreatePDFATest` (examples) | expired test keystore (assumption A2) |
| Threads | 1 (PIT's default) | with 4 threads the pdfbox module gives a different result, see below |
| JDK / OS | AdoptOpenJDK 11.0.8+10, Ubuntu 22.04 runner | assumption A5 |

The configuration lives outside the PDFBox sources: `scripts/pdfbox/add-descartes-profile.sh` adds a `descartes`
profile to the PDFBox parent POM, and `scripts/pdfbox/run-descartes.sh` installs the module and runs
`org.pitest:pitest-maven:mutationCoverage` with it. The workflow `.github/workflows/descartes-before.yml` runs every
module in its own job and uploads `methods.json`, `mutations.json.gz`, the timing and the environment report.

## "Before" run: comparison with the authors' reports

Reports of the reproduction: runs [39409510406](https://github.com/Ahmeddhibi19/Pr-Benoit-test/actions/runs/39409510406)
(all modules, 4 threads) and [39415980930](https://github.com/Ahmeddhibi19/Pr-Benoit-test/actions/runs/39415980930)
(pdfbox, 1 thread), 2026-10-20. They are compared with the authors' reports of 2020-09-21 by
`analysis/compare_descartes_runs.py` (methods matched by class, name and parameter descriptor). The reports used
below are stored in `results/02-descartes-before/descartes_before/`, and the comparison in `results/02-descartes-before/descartes_before_vs_authors/`.

| Module | Methods | Tested | Partially | Pseudo-tested | Not covered | Same classification as the authors | Jaccard (pseudo-tested) | Descartes time |
|---|---|---|---|---|---|---|---|---|
| fontbox | 550 | 168 | 6 | 61 | 315 | 550 / 550 | 1.00 | 43 s |
| xmpbox | 550 | 358 | 31 | 18 | 143 | 550 / 550 | 1.00 | 54 s |
| preflight | 398 | 263 | 21 | 63 | 51 | 398 / 398 | 1.00 | 217 s |
| tools | 126 | 28 | 6 | 5 | 87 | 126 / 126 | 1.00 | 17 s |
| pdfbox (1 thread) | 4,438 | 1,580 | 97 | 463 | 2,298 | 4,421 / 4,438 | 0.97 | 68 min |
| examples | 311 | 0 | 0 | 3 | 308 | 231 / 311 | 0.08 | 14 s |
| **all** | 6,373 | 2,397 | 161 | 613 | 3,202 | 6,276 / 6,373 (98.5%) | 0.92 | |
| *authors, all* | 6,373 | 2,439 | 164 | 644 | 3,126 | | | *pdfbox: 83 min* |

**All 46 effective targets of Table III are pseudo-tested in the reproduction's "before" run**, as in the authors'
reports (the exact-agreement criterion of the plan).

- fontbox, xmpbox, preflight, tools: identical to the authors, method by method.
- pdfbox: 17 methods differ (out of 4,438). The extra detected mutants are killed by `TestTextStripper`,
  `ControlCharacterTest` and `MultilineFieldsTest`, the missing ones by `PDAcroFormFlattenTest`,
  `TestSymmetricKeyEncryption` and `TestTextStripper`. These tests read and write files under `target/test-output`
  and some download their input from the Apache JIRA during the test, so a few outcomes are not deterministic. None of
  the 17 is an effective target.
- examples: all 80 differences are methods covered only by the excluded test classes (assumption A2). No target comes
  from this module.

### Parallel mutation analysis changes the result for pdfbox

The first run used 4 threads (the runner's vCPUs). For fontbox, xmpbox, preflight and tools this gives exactly the
authors' result. For pdfbox it does not:

| pdfbox | Tested | Partially | Pseudo-tested | Not covered | Timed-out mutants | Same as the authors | Effective targets still pseudo-tested |
|---|---|---|---|---|---|---|---|
| authors | 1,580 | 98 | 458 | 2,302 | 62 | | 40 / 40 |
| reproduction, 1 thread | 1,580 | 97 | 463 | 2,298 | 64 | 4,421 / 4,438 | 40 / 40 |
| reproduction, 4 threads | 1,799 | 40 | 301 | 2,298 | 310 | 4,202 / 4,438 | 15 / 40 |

With 4 threads, 280 mutants are detected that the authors' run did not detect: 215 because the run *timed out*
(PIT counts a timeout as a detection) and 65 because a test failed. The failing tests are almost all tests that use
fixed file names under `target/test-output` (`PDAcroFormFlattenTest` alone accounts for 38). With several PIT
worker JVMs running in the same module directory, these tests overwrite and delete each other's files, and the
tests that download PDFs from the Apache JIRA slow down; the failures and timeouts have nothing to do with the
mutant. For example, `RenderingMode.isFill` becomes "tested": its `return false` mutant is "killed" by
`PDAcroFormFlattenTest.testFlattenPDFBOX2586`, and its `return true` mutant "times out" before any test runs.
With 1 thread the timeouts fall back to 64 and the result matches the authors'. The authors' pdfbox run took 83
minutes, consistent with a single thread. The configuration therefore uses 1 thread for every module (assumption A3).
The effect on the case study would be large: with the 4-thread pdfbox report, pankti-extract and
`find-pseudo-tested.py` select 91 targets instead of 138, and only 21 of the 46 effective targets of Table III.
The 4-thread reports are kept in `results/02-descartes-before/descartes_before_pdfbox_4_threads/` with their comparison.

A local run of fontbox on Windows differs from the authors' report on 4 methods, all OS-specific font-directory
finders (discrepancies.md §15); on Linux the four methods match.

## Targets

`scripts/pankti/extract-targets.sh` applies the authors' tools to PDFBox 2.0.21: pankti-extract (commit `0fddf27`)
keeps 3,588 public, non-static, non-abstract, non-void, non-deprecated, non-empty methods of classes (3,587 distinct:
one row, `PlainTextFormatter$Builder.textAlign(int)`, appears twice; `count_targets.py` reports 3,587), and the authors'
`find-pseudo-tested.py` keeps those that a Descartes report classifies as pseudo-tested.

| Descartes reports used | #TARGET | Effective targets included | Output |
|---|---|---|---|
| authors' "before" reports | **138** (paper: 138) | 46 / 46 | `results/02-descartes-before/targets_authors_reports.{csv,txt}` |
| reproduction's "before" reports | **138** | 46 / 46 | `results/02-descartes-before/targets_own_reports.{csv,txt}` |

The two lists share 137 methods (Jaccard index 0.986): `PDFontDescriptor.getFontFile()` is a target only with the
authors' reports, `PDAnnotation.isNoRotate()` only with the reproduction's. The list instrumented from the instrumentation stage on is
the one from the authors' reports (`results/02-descartes-before/instrumentation-candidates-pdfbox.csv`, assumption A8).

## "After" run: PANKTI_STATUS

Workflow `.github/workflows/descartes-after.yml`, run [39747040848](https://github.com/Ahmeddhibi19/Pr-Benoit-test/actions/runs/39747040848) (2026-10-22). Same configuration as "before" (PIT 1.4.10,
Descartes 1.2.6, 21 operators, 1 thread). Three sources of tests, each on fontbox and pdfbox:

| Source | Tests added | fontbox: tested / partially / pseudo / not covered | pdfbox: tested / partially / pseudo / not covered | pdfbox time |
|---|---|---|---|---|
| none (control) | 0 | 34 / 1 / 9 / 18 | 150 / 23 / 98 / 132 | 21 min |
| reproduction | 14,314 passing tests of 14,679 (test execution) | 40 / 1 / 3 / 18 | 162 / 34 / 75 / 132 | 18 min |
| authors | 13,614 passing published tests of 13,851 | 40 / 1 / 3 / 18 | 162 / 34 / 75 / 132 | 16 min |

Only the tests that passed in all five runs of the test execution are added (`scripts/pankti/keep_passing_tests.py`, assumption
A22): PIT needs a green suite. Mutation is restricted to the 22 classes that declare the effective targets (5 in
fontbox, 17 in pdfbox; 465 methods), with all the tests of the module (A21).

**Restriction check.** The control run (no generated test) is compared with the full "before" run on the 465
methods (`results/07-descartes-after/restriction_check/`): fontbox 62 / 62 identical, pdfbox 398 / 403. The 5 differences are not
caused by the restriction but by unstable tests of PDFBox (discrepancies.md §23): 4 come from mutants killed by
`TestOptionalContentGroups.testOCGConsumption` in the control run and not in the full run, 1 from a mutant that timed
out in the full run. One of the five is an effective target: `XrefTrailerResolver.getXrefType`.

**PANKTI_STATUS** (`analysis/pankti_status.py`, `analysis/table3_status.py`, outputs `results/07-descartes-after/`):

| | Well-tested (tested + partially tested) | Same status as Table III |
|---|---|---|
| Paper, Table III | 28 / 46 (17 + 11) | |
| Authors' passing tests, run here | **28 / 46 (17 + 11)** | 46 / 46 |
| Reproduction's passing tests | **28 / 46 (17 + 11)** | 46 / 46 |
| Control run, no generated test | 1 / 46 (`getXrefType`) | 19 / 46 |

The 47th target of the reproduction, `TrueTypeFont.getOS2Windows`, has no passing test and stays pseudo-tested.
With our tests and with the authors', the Descartes classification is the same for all 465 analysed methods
(`results/07-descartes-after/reproduction_vs_authors/`). The authors' own "after" reports (Zenodo) analyse the whole modules; on the
465 methods analysed here they agree on 460, including all 46 targets. The 5 other methods are not targets and differ
through the same unstable tests (`TestOptionalContentGroups`, `TestPublicKeyEncryption`, `TestTextStripper`;
`results/07-descartes-after/reproduction_vs_authors_published/`).

**Examples of the paper** (`analysis/mutant_tests.py`, `results/07-descartes-after/examples_mutants.txt`):
- `RenderingMode.isFill` is partially tested: the single observed value is `true`, so the generated test kills the
  `false` mutant and not the `true` mutant. This is the paper's example (Section IV.C).
- `NamingTable.getName` is tested: the mutants `null`, `"A"` and `""` are all killed (Section II.C). Most observed
  calls return `null`: the first test that kills the `null` mutant is the 112th that PIT runs (91st with the authors'
  tests).
- `XrefTrailerResolver.getXrefType`: the `null` mutant survived all 183 covering tests in the full "before" run and
  was killed by the 53rd of them (`testOCGConsumption`) in the control run. With the generated tests, the first
  test PIT runs (a generated one) kills it. The target is well-tested after in every run, but its "before" status is
  not stable, so it should not be counted as an improvement due to PANKTI without this caveat: the robust count is
  27 / 46 targets that are pseudo-tested in both runs without generated tests and well-tested with them.
