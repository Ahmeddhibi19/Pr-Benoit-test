# Discrepancies and open points

This file tracks every difference found between the paper (arXiv:2012.01198v4, Section IV.C and Table III),
the authors' public artifacts, and this reproduction. Each item has a status: **explained**, **open** or
**assumption** (a simplifying choice made here because the information is missing).

Artifacts used (see [artifacts.md](artifacts.md)):
- `pankti-experiments` at `7bc7791` (2020-11-03, "Update PDFBox numbers") and `1d8f9aa` (2021-06-08)
- `pankti` at `0fddf27` (2020-10-26), the tool version of the PDFBox run
- Zenodo replication data, version 1 (record 4298605)

Scripts and outputs:
- `analysis/check_paper_table3.py` -> `results/day1/paper_table3_checks.txt`
- `analysis/compare_authors_report.py` -> `results/day1/authors_report_vs_paper.csv`
- `analysis/summarize_descartes_reports.py` -> `results/day1/authors_descartes_reports.csv`

## 1. Internal consistency of Table III (PDFBox rows)

**Status: explained.** All column sums match the printed totals (121,175 / 57,563 / 13,851 / 13,614 / 237),
as do 28 well-tested / 18 pseudo-tested, 19 methods where the 200 MB threshold was hit, 7 methods with a single
test, and 11,730 tests for one method. Two printing errors are corrected in the transcription:
- `PDCIDFontType2_codeToGID` is numbered 59 instead of 49.
- Row 67 prints #UNIQUE as `8 / 18` while #COLLECTED is 16.

Several percentages are 100 times too small (e.g. `1 / 18 (0.05%)`), so all ratios are recomputed from the counts.
The passing rate is 98.29%: Table III rounds it to 98.2%, the text to 98.3%.

Section V.B says that 15 target methods have passing tests but stay pseudo-tested. Table III gives 12 such PDFBox
methods; together with 2 Broadleaf methods and 1 Jicofo method this makes 15, as stated.

## 2. #PASSING: 13,614 in the paper vs 2,001 executed passing tests

**Status: explained.** `report.csv` has an `executed-tests` column. For `GlyfSimpleDescript.getFlags`, only
**117 of the 11,730** generated tests were executed (all 117 passed). Every other method had all its tests
executed. Hence:

- executed tests = 13,851 - 11,730 + 117 = **2,238** (the `report.csv` total), of which 2,001 passed and 237 failed;
- paper #PASSING = 2,001 + (11,730 - 117) = **13,614**.

The paper therefore counts the 11,613 non-executed `getFlags` tests as passing. The README of the experiments
repository at `7bc7791` gives yet another count (13,804 generated, 1,840 executed, 1,597 passing, 243 failing),
apparently from an earlier run.
`time-coverage-version.md` (2021) reports 15,526 tests in the suite (1,675 original + 13,851 generated) and, for
PDFBox 2.0.22, "Passing: 13,851 (same as before)" although "tests that failed in 2.0.21 were also ignored". These
two statements cannot both hold for the 237 failing tests; the note probably reuses the 13,851 figure of the paper.

Consequence for this reproduction: all generated tests are executed. Passing tests that were not executed are not
counted as passing, and both numbers are reported.

## 3. Well-tested: 28 (paper) vs 29 (`report.csv`)

**Status: explained.** The single difference is `DefaultResourceCache.getColorSpace` (row 45): `report.csv`
labels it `tested`, the paper `pseudo-tested`. In every Descartes report of the authors, before and after,
the method is `pseudo-tested` (only the `null` mutant, never detected). The paper is right and `report.csv`
mislabels it.

## 4. Meaning of "well-tested"

**Status: explained.** The authors' README splits the outcome into 17 `tested`, 11 `partially-tested` and
18 `pseudo-tested`. With well-tested = tested or partially-tested, the classifications of the last "after"
Descartes run (2020-11-19, fontbox and pdfbox modules) give exactly the status printed in the paper for all
46 methods. Example: `RenderingMode.isFill` is `partially-tested` (the `false` mutant is detected, `true`
is not), and the paper counts it as well-tested.

## 5. #TARGET: 138 (paper) vs 129 instrumented (README)

**Status: open.** To be recomputed on Day 2 from the authors' "before" reports with pankti-extract and
`find-pseudo-tested.py`. For reference, the six "before" reports contain 644 pseudo-tested methods in total
(fontbox 61, pdfbox 458, preflight 63, examples 39, xmpbox 18, tools 5), before the public / non-static /
non-void filter.

## 6. Descartes configuration

**Status: explained (correction of an earlier assumption).** All the authors' reports were produced with 21
mutation operators: `void null empty true false 0 1 (short)0 (short)1 (byte)0 (byte)1 0L 1L 0.0 1.0 0.0f 1.0f
'\40' 'A' "" "A"`, the Descartes 1.2.x default set. The reproduction uses the same set.

## 7. "After" Descartes runs use a different test population

**Status: open.** In the pdfbox module the "after" runs report fewer `tested` methods than the "before" run
(1,488 vs 1,580) and more `not-covered` ones (2,392 vs 2,302). Adding tests cannot remove coverage, so the
"after" runs were made with a different, smaller set of original tests (or a different configuration). This
does not affect the 46 target methods (their status is consistent with the paper), but it matters when
re-running Descartes: the reproduction runs "before" and "after" with the same configuration and the full suite.

## 8. Overloaded methods

**Status: assumption.** `PDSimpleFont.toUnicode` and `PDTrueTypeFont.getPath` are overloaded. The Descartes
reports classify each overload separately (one pseudo-tested, the other tested or not covered). The paper's
target is the pseudo-tested overload, so matching must use the full signature from `invoked-methods.csv`.

## 9. Invocation counting and profile pairing in PANKTI (`0fddf27`)

**Status: explained (from the code of `MethodAspect0.java`).**
- The `-count.txt` file is read and incremented at every return, so #INVOCATIONS is cumulative over the 50 JVM
  launches of the workload. Calls that end with an exception are not counted.
- The 200 MB threshold is checked per file (receiving, params, returned): collection stops once one of the files
  reaches 200 MiB. The check reads the file sizes on disk, so it is also cumulative over JVM launches.
- The receiving object and the parameters are appended in `@OnBefore`, the returned object in `@OnReturn`.
  Nothing is written in `@OnThrow`. A target call that throws therefore leaves receiving/params entries without
  a returned entry, and recursive calls of the same target interleave entries. The generator pairs entries by
  index, so either case shifts the pairing. The authors changed this on 2020-12-14 (issues #39/#40), after the
  PDFBox run. Whether it affected PDFBox methods is open: the reproduction checks that the three files of each
  method hold the same number of entries.

## 10. Workload execution log

**Status: explained.** `execution.log` (2020-11-03) shows that `Encrypt` fails on `000809.pdf`
("Document is already encrypted"), so every later step on `000809-locked.pdf` fails as well, and that `PDFMerger`
prints its usage for `000809` and `000810`. The workload of the paper is thus smaller than 5 x 10 successful
operations. The reproduction runs the script unchanged and reports this.

## 11. Coverage figures of Table II

**Status: open (low priority, outside Section IV.C).** Table II gives TMCov 6,049 / 11,042 and TLCov
34,653 / 64,787 (53.5%), while `time-coverage-version.md` gives 6,050 / 11,042 and 34,652 / 64,787 (53.4%).

## 12. Building PDFBox 2.0.21 today

**Status: assumption (build-only adjustments).** The unmodified 2.0.21 build fails in four places.
`scripts/pdfbox/patch-build.sh` handles them without changing library or test code:
- The IPA fonts used by the pdfbox tests return 404 (PDFBOX-5005). The 2.0.22 URLs serve the same files (same sha512).
- The Isartor archive used by the preflight tests returns HTTP 403 at pdfa.org, also in later PDFBox versions.
  The Internet Archive copy has the sha512 pinned in the pom (`66bf4ad4...`).
- The certificate policy PDF used by the examples tests (`QV_RCA1_RCA3_CPCPS_V4_11.pdf`) cannot be fetched from
  the CI runners ("Could not get content"), although it answers from other networks. The Internet Archive copy of
  2020 has the pinned sha512 (`940ab0cc...`). Later PDFBox versions use a different file for this test.
- `PDAcroFormTest.testFlatten*` (3 tests) write into `target/test-output` without creating it. They pass only when
  another test created the directory before, which depends on test execution order. In the first CI run they failed
  with `FileNotFoundException`. The directory is created before the build.

## 13. pdfbox-app jar

**Status: open.** The jar in the experiments repository (9,890,400 bytes, sha256 `a9327e88...24a1b1`) differs from
the one on Maven Central (9,897,381 bytes): the authors built it from a local checkout. The reproduction builds
the jar from the `2.0.21` tag.
