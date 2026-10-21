# Experiment log

One entry per experiment that produced evidence used in the reproduction, including the runs that failed or were
discarded. Every number points to a CI run or a file under `results/`. No experiment uses randomness, so there are no
seeds. CI runs use the GitHub-hosted `ubuntu-22.04` runner (4 vCPU AMD EPYC 7763, 15 GiB RAM) with AdoptOpenJDK
11.0.8+10 and Maven 3.6.3, unless stated otherwise. The runner image and font list of each run are in its
`env-report.txt`.

| Id | Date | Question | Outcome |
|---|---|---|---|
| [E1](#e1-pdfbox-2021-test-suite-on-ci) | 2026-10-14 | Does the PDFBox 2.0.21 test suite run today? | yes, after 4 build-only adjustments |
| [E2](#e2-checks-of-the-authors-artifacts) | 2026-10-14, 10-20 | Do the authors' artifacts match the paper? | yes, with explained exceptions |
| [E3](#e3-local-build-on-a-second-machine) | 2026-10-20 | Does the setup rebuild on another machine? | yes, identical results |
| [E4](#e4-descartes-on-fontbox-windows) | 2026-10-20 | Does the Descartes configuration reproduce the authors' report? | yes for counts; 4 OS-specific methods differ |
| [E5](#e5-descartes-before-6-modules-4-threads) | 2026-10-20 | Same, on CI for the 6 modules | 4 modules identical; pdfbox differs (discarded, see E6) |
| [E6](#e6-descartes-before-pdfbox-1-thread) | 2026-10-20 | Is the pdfbox difference caused by parallelism? | yes: with 1 thread pdfbox matches |
| [E7](#e7-target-extraction) | 2026-10-20 | Does the authors' pipeline give #TARGET = 138? | yes, with both sets of reports |
| [E8](#e8-production-run-dry-run) | 2026-10-20 | Do the plugin, Glowroot and pdfbox-app build and start together on CI? | yes (second run); app jar identical to the authors' |
| [E9](#e9-profile-metrics-on-the-authors-data) | 2026-10-20 | Do the metric scripts reproduce Table III from the authors' raw profiles? | yes for all 46 methods; depth 36 not reproduced |
| [E10](#e10-smoke-test-of-the-instrumentation) | 2026-10-20 | Does the instrumentation record profiles on CI? | yes; isFill as in the paper; counts cumulative |
| [E11](#e11-full-workload) | 2026-10-20 | Columns 1-3 of Table III with our own run | 46/46 effective targets, isFill exact, totals within 1-6%; differences on font methods |
| [E12](#e12-figure-5) | 2026-10-21 | Figure 5 | same shape; bins from 20 MiB identical |
| [E13](#e13-regenerating-the-authors-tests) | 2026-10-21 | Does the generator reproduce the authors' published tests? | yes: 13,851 / 13,851 identical (with PANKTI 7afc584) |
| [E14](#e14-generating-the-tests-from-the-reproductions-profiles) | 2026-10-21 | Tests generated from our own profiles | 14,679 tests for 47 methods, = #UNIQUE for every method |
| [E15](#e15-integration-check) | 2026-10-21 | Do the generated tests compile and run inside PDFBox? | yes on a sample (20 / 20 pass) |

## E1. PDFBox 2.0.21 test suite on CI

| | |
|---|---|
| Objective | Baseline: build PDFBox 2.0.21 and run its tests with the authors' JDK. |
| Method | Workflow `env-check`: checkout of tag 2.0.21 (`fa8029d8`), `mvn install` with tests. |
| Runs | 38535865735, 38538739999, 38539831127 and 38540837977 (all failed), then 38542374578 and 38548431201 (green). |
| Reference | The authors report 1,675 tests for the original suite. |
| Result | 1,678 tests, 0 failures, 13 errors (all `CertificateExpiredException` in `examples`), 143 s (`results/day1/env-check/`). |
| Failures | Dead download URLs (IPA fonts 404, Isartor 403, a certificate-policy PDF not served to CI), one order-dependent test (`PDAcroFormTest`), the expired test keystore. |
| Interpretation | The suite runs with build-only adjustments (assumption A1); the keystore has to be handled for Descartes (A2). |

## E2. Checks of the authors' artifacts

| | |
|---|---|
| Objective | Separate the paper from its artifacts before reproducing anything (Track A). |
| Data | `pankti-experiments` at `7bc7791` and `1d8f9aa`; Zenodo record 4298605 (md5 `9c902f3e...`). |
| Method | `analysis/check_paper_table3.py`, `compare_authors_report.py`, `summarize_descartes_reports.py`, `profile_stats.py`. |
| Result | Table III is internally consistent. The authors' raw data gives exactly the paper's 121,175 invocations, 57,563 profiles, 158 B minimum, 54.7 MiB maximum and 5.49 GiB total. The authors' last "after" reports give all 46 statuses of Table III (well-tested = tested or partially tested). 11,613 of the 13,614 "passing" tests were never executed. (`results/day1/`, `docs/discrepancies.md`) |
| Failures | The first comparison merged overloaded methods (rows 31 and 35); fixed by matching on the parameter descriptor (2026-10-20). |
| Interpretation | The paper's numbers are traceable to the artifacts; the reproduction executes every generated test (A11). |

## E3. Local build on a second machine

| | |
|---|---|
| Objective | Check that the setup scripts rebuild the environment (the work moved to another PC on 2026-10-20). |
| Environment | Windows 10 LTSC, Intel i7-1185G7, 16 GB RAM, no administrator rights. |
| Method | `setup/windows/install-tools.ps1`, `setup/fetch-artifacts.sh`; local build of the fontbox and pdfbox modules with tests. |
| Result | Toolchain and artifacts rebuilt with all checksums matching (about 30 min, 7.4 GB). 558 / 558 tests pass (fontbox 27, pdfbox 531), 6.5 min. The Day-1 analyses give byte-identical outputs. |
| Interpretation | The scripts are sufficient to recreate the environment. |

## E4. Descartes on fontbox (Windows)

| | |
|---|---|
| Objective | Smoke test of the Descartes configuration (`docs/descartes.md`) before using CI. |
| Method | `scripts/pdfbox/run-descartes.sh` on fontbox, 4 threads, local machine of E3. |
| Reference | The authors' fontbox report: 550 methods, 168 tested, 6 partially, 61 pseudo-tested, 315 not covered. |
| Result | The same counts, 21 operators, 55 s. Per method 546 / 550 agree. The 4 differences are font-directory finders: `WindowsFontDirFinder` is exercised on Windows, `UnixFontDirFinder` and `NativeFontDirFinder` are not. |
| Interpretation | The configuration is right; the OS changes which code the tests reach, so measured runs use Linux (A5). |

## E5. Descartes "before", 6 modules, 4 threads

| | |
|---|---|
| Objective | The reproduction's own pseudo-tested methods (plan task 2.2). |
| Method | Workflow `descartes-before`, run 39409510406, one job per module, 4 PIT threads. |
| Result | fontbox, xmpbox, preflight, tools: identical to the authors' reports for every method. examples: 231 / 311 (excluded test classes, A2). pdfbox: 4,202 / 4,438, with 1,799 tested methods instead of 1,580, 310 timed-out mutants instead of 62, and 25 of the 40 pdfbox targets "tested". pdfbox took 49 min. |
| Failures | `RenderingMode.isFill`, which the paper uses as its example of a pseudo-tested method, came out "tested", which contradicts the paper's account. Of the 280 extra detections, 215 are timeouts and 65 are failures of tests that use fixed files under `target/test-output` or download PDFs during the test (`PDAcroFormFlattenTest` mostly). |
| Interpretation | Hypothesis: parallel PIT workers interfere with these tests. The pdfbox report of this run is not used (kept in `results/day2/descartes_before_pdfbox_4_threads/`). With it, the pipeline would select 91 targets instead of 138. |

## E6. Descartes "before", pdfbox, 1 thread

| | |
|---|---|
| Objective | Test the hypothesis of E5. |
| Method | Run 39415980930, pdfbox only, 1 PIT thread (PIT's default). |
| Expected | If parallelism caused E5's differences, the result should match the authors'. |
| Result | 1,580 tested, 97 partially, 463 pseudo-tested, 2,298 not covered; 64 timed-out mutants. 4,421 / 4,438 methods agree with the authors (Jaccard 0.97 on the pseudo-tested sets). All 40 pdfbox targets are pseudo-tested. 68 min (the authors: 83 min). |
| Interpretation | Hypothesis confirmed. One thread is now the default. The 17 remaining differences involve tests with shared files or network access; none is an effective target. |

## E7. Target extraction

| | |
|---|---|
| Objective | #TARGET (paper: 138; README of the experiments: 129). |
| Method | `scripts/pankti/extract-targets.sh` (pankti-extract `0fddf27`, the authors' `find-pseudo-tested.py`), `analysis/count_targets.py`. |
| Result | 3,588 methods kept out of 9,021. With the authors' reports: 138 targets. With the reproduction's reports (E5 without pdfbox, plus E6): 138, of which 137 are in common. Both lists contain the 46 effective targets. A second run gives the same candidate list. (`results/day2/targets_*`) |
| Failures | Spoon's snapshot repository no longer exists (warnings only). JDT's version ranges now resolve Java 17 jars, which are never loaded. The extractor writes its full list in hash-map order. |
| Interpretation | #TARGET is reproduced exactly. The README's 129 predates the paper's run. |

## E8. Production run, dry run

| | |
|---|---|
| Objective | Plan task 3.4: catch build and installation problems of the instrumentation before running the workload. |
| Method | Workflow `production-run`, mode `dry-run`: PANKTI `0fddf27` `instrument.py` on the frozen `results/targets.csv`, plugin build, Glowroot 0.13.6, pdfbox-app built from the tag, pdfbox-app started under the agent without a command. |
| Runs | 39428845392 (failed), 39431056888 (green). |
| Expected | One aspect per target; Glowroot starts and registers the plugin; no profile written (no target runs). |
| Result | 138 / 138 aspects; Glowroot starts without warnings and registers `panktiplugin`; no profile written. pdfbox-app built on the runner: all 5,644 class files and all other entries identical to the authors' jar except 3 build-metadata files. (`results/day3/`) |
| Failures | Run 39428845392: `install-glowroot.sh` lost the relative plugin path after `cd` (the local test had used an absolute path). Fixed and replayed locally with relative paths before re-running. |
| Interpretation | The instrumentation is ready for the workload (Day 4). The authors ran plain PDFBox 2.0.21 (open question T11 answered). Whether the aspects actually capture profiles is only visible once a target runs (Day 4 smoke test). |

## E9. Profile metrics on the authors' data

| | |
|---|---|
| Objective | Validate the metric script before applying it to the reproduction's profiles. |
| Data | Zenodo record 4298605, `pdfbox/pankti-collected-object-profiles/`: 231 files, 5.9 GB of XML. |
| Method | `analysis/profile_stats.py --fragments` (pankti-generate's pairing and uniqueness rule, maximum element depth). |
| Reference | Table III and the text of Section IV.C. |
| Result | #INVOCATIONS, #COLLECTED and #UNIQUE equal to Table III for all 46 methods (121,175 / 57,563 / 13,851). No method has different numbers of receiving, params and returned fragments. Maximum XML element depth: 73 (`COSParser.getEncryption`). 167 s on the laptop. (`results/day4/authors_profile_metrics.*`) |
| Failures | First run crashed: for an empty element (`<null/>`) expat reports the position after the tag, not a closing tag. Fixed, with unit tests. |
| Interpretation | The uniqueness rule is validated. The pairing problem possible in PANKTI `0fddf27` (a call that throws leaves a receiving object without a returned value) did not occur in the authors' run. The paper's depth of 36 has an undocumented definition (A16). |

## E10. Smoke test of the instrumentation

| | |
|---|---|
| Objective | Plan task 4.1: does the plugin record profiles, does the XML parse, is the count cumulative over JVM launches? |
| Method | `production-run` mode `smoke`, run 39442198598: `PDFToImage` on `000752.pdf`, twice, each in a new JVM, cold font cache. |
| Expected | isFill files present; count after the second launch = 2 x first; isFill profiles of 158 bytes, 1 unique (paper). |
| Result | All checks pass. isFill: 4,349 then 8,698 invocations, every profile 158 bytes, 1 unique. 27 targets invoked, 3.4 GB of profiles, 11 methods already at the 200 MB threshold, no fragment mismatch, maximum depth 39. 237 s. (`results/day4/smoke/`) |
| Interpretation | The instrumentation works as described in the paper; counts accumulate across JVM launches (T7). The threshold is reached very quickly. |

## E11. Full workload

| | |
|---|---|
| Objective | Plan tasks 4.2-4.5: run the authors' workload under PANKTI and compare columns #INVOCATIONS, #COLLECTED, #UNIQUE of Table III. |
| Method | `production-run` mode `full`, run 39444526027: the authors' `run.sh` (only its two jar paths replaced, `run-sh.diff`), 50 JVM launches, cold font cache, frozen 138 targets. Metrics: `profile_stats.py --fragments`, `compare_table3.py`, `workload_log.py`. |
| Environment | `ubuntu-22.04` runner (image 20261012), 57 fonts installed (DejaVu, Lato, Liberation, Noto Color Emoji; list in `env-report.txt`). |
| Reference | Table III rows 30-75 and Section IV.C; the authors' `execution.log`. |
| Result | Workload: 50 / 50 commands with the same outcome as the authors' (39 ok, 9 errors on `000809.pdf`, 2 PDFMerger usage messages); 687 s (the authors' log spans about 16 min). Profiles: 47 methods invoked, all 46 of Table III plus `TrueTypeFont.getOS2Windows` (342 invocations). Totals: 122,384 invocations (paper 121,175), 58,672 collected (57,563), 14,679 unique (13,851); collected/invocations 47.9% (47.5%), unique/collected 25.0% (24.0%). 19 methods hit the threshold (19). Smallest profile 158 B, largest 54.7 MiB, 5.30 GiB in total (paper 5.5 GB). Maximum XML depth 73, the same as the authors' data. **isFill: 30,944 / 30,944 / 1 unique, 158 B each: exact match.** Per method, 41 of 46 invocation counts, 40 collected counts and 38 unique counts are identical to Table III. (`results/day4/full/`, `results/day4/table3_comparison.*`) |
| Differences | `NamingTable.getName` (650 -> 1,457 invocations, 273 -> 976 unique), `PDFontDescriptor.getFlags` (227 -> 257), `isSerif`/`isItalic`/`isFixedPitch` (21 -> 31), `FontCache.getFont` (106 -> 103 unique), `DefaultResourceCache.getColorSpace` (25 -> 29 collected), `COSParser.getEncryption` (33 -> 35 unique), and the extra `TrueTypeFont.getOS2Windows`. |
| Interpretation | The workload behaves exactly as the authors' did. All non-font methods match and the font methods do not, which points to the fonts installed on the machine (PDFBox matches and caches system fonts); the authors' font set is unknown (risk R3, assumption A5). This cause is probable, not verified. |

## E12. Figure 5

| | |
|---|---|
| Objective | Plan task 5.1: the distribution of profile sizes (paper, Figure 5: 10 MB bins, logarithmic count axis). |
| Method | `analysis/figure5.py` on the size files of the authors' data (the data behind the paper's figure) and of run 39444526027. 10 MiB bins, since the paper uses binary units (discrepancies.md, item 1b). |
| Result | Authors / reproduction: 57,458 / 58,563 profiles below 10 MiB, 71 / 75 in 10-20 MiB, then 3, 23, 5, 3 in both for 20-30, 30-40, 40-50 and 50-60 MiB. Smallest 158 B in both, largest 57,385,679 B / 57,385,628 B. (`results/day5/fig5.png`, `fig5.csv`) |
| Interpretation | Same shape as the paper's figure; the large profiles (above 20 MiB, all from methods capped by the threshold) are identical in number, the small ones differ with the font methods (E11). |

## E13. Regenerating the authors' tests

| | |
|---|---|
| Objective | Validate the generation step on its own: from the authors' profiles, does pankti-generate produce the tests they published? |
| Method | Workflow `generate-tests` (run 39581267651, job "authors"): Zenodo profiles, pankti-generate at `7afc584` with `setUpXStream()` enabled (A17), 12 GB heap; `analysis/count_generated_tests.py`, `analysis/compare_generated_tests.py` against the 22 published classes. |
| Hypothesis | The published tests come from `7afc584` (their `deserializeObject()` helpers); a 3-class local run already matched. |
| Result | 22 classes, 13,851 tests, 4,464 resource files (as published), 564 s. #PANKTI_TESTS = #UNIQUE for all 46 methods. Test by test: 13,851 identical, 0 different, 0 missing, 0 extra. (`results/day5/authors_generation/`) |
| Failures | The other job of the same run (reproduction) failed: the profile archive was looked for in a sub-folder (single artifacts are downloaded directly into the path). Fixed. |
| Interpretation | The generation step is reproduced exactly. The published tests were made with a later generator than the instrumentation and edited by hand (imports, converter classes). |

## E14. Generating the tests from the reproduction's profiles

| | |
|---|---|
| Objective | Plan task 5.2: generate the differential unit tests from this reproduction's profiles (production-run 39444526027). |
| Method | Workflow `generate-tests`, run 39588027907 (job "reproduction"): the profile archive of run 39444526027, pankti-generate `7afc584` with `setUpXStream()` (A17), 12 GB heap. |
| Expected | #PANKTI_TESTS = #UNIQUE for every method (14,679 from E11); paper: 13,851. |
| Result | 22 test classes, 14,679 tests for 47 methods, #PANKTI_TESTS = #UNIQUE for all 47; 5,414 resource files (4.9 GB); no method skipped, no exception in the log; 455 s. The tests and resources are archived as artifact `generated-tests-2` (391 MB compressed, kept 5 days) and copied locally. (`results/day5/reproduction_generation/`, `results/day5/table3_partial.csv`) |
| Interpretation | Column #PANKTI_TESTS of Table III follows #UNIQUE exactly, as in the authors' run; the differences with the paper are those of #UNIQUE (E11). |

## E15. Integration check

| | |
|---|---|
| Objective | Plan task 5.3: prepare and test the integration of the generated tests into PDFBox before running the whole set (Day 6). |
| Method | `scripts/pankti/integrate-tests.sh` on a fresh PDFBox 2.0.21 checkout with 3 classes generated locally from the authors' profiles (RenderingMode, PDCIDSystemInfo, XrefTrailerResolver), split with at most 5 tests per class; `mvn -pl pdfbox -am test -Dtest='Test*PanktiGen*'`. Laptop (Windows), JDK 11.0.8. |
| Result | First attempt: compilation error, `java.lang.ref.Cleaner` not found: PDFBox's `jdkGte9` profile compiles everything with `<release>6</release>`, which overrides `testSource`/`testTarget`. Second attempt, with `<release>9</release>` on the `default-testCompile` execution only: 6 classes compile, 20 / 20 tests pass (Table III: all pass for these methods). Library classes keep version 50 (Java 6), test classes 53 (Java 9); animal-sniffer passes. |
| Interpretation | The integration works with smaller build changes than the authors' (A18). |

