# Experiment log

One entry per experiment that produced evidence used in the reproduction, including the runs that failed or were
discarded. From E16 on, each entry records: objective, method, configuration, outcome, observation, interpretation,
assumptions, limitations and next step. Every number points to a CI run or a file under `results/`. No experiment uses randomness, so there are no
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
| [E16](#e16-repeated-runs-local-check) | 2026-10-21 | Do the repeated runs and the outcome counting work? | yes on a sample (20 / 20 passing in 2 runs) |
| [E17](#e17-execution-of-the-reproductions-tests) | 2026-10-21 | #PASSING / #FAILING / flaky of our 14,679 tests | 14,314 / 365 / 0; 38 of 46 rows equal to Table III |
| [E18](#e18-execution-of-the-authors-published-tests) | 2026-10-21 | The authors' 13,851 tests run in our environment | 13,614 / 237 / 0: Table III exactly, 46 / 46 rows |
| [E19](#e19-descartes-after-local-check) | 2026-10-22 | Does the "after" Descartes run work, and does isFill behave as in the paper? | yes, after a fix (no test was selected at first) |
| [E20](#e20-descartes-after-restriction-check-and-pankti_status) | 2026-10-22 | PANKTI_STATUS of the effective targets | 28 / 46 with our tests and with the authors', 46 / 46 statuses of Table III |
| [E21](#e21-why-generated-tests-fail) | 2026-10-22 | Why do generated tests fail (V.A)? | identity `equals` or identity-keyed lookup; a test passes iff it observed null |
| [E22](#e22-font-sensitivity-runs) | 2026-10-22 | Do the font methods depend on the fonts or the font cache? | yes: with a pre-built font cache, 46 / 46 targets and #UNIQUE 13,852 (paper 13,851) |
| [E23](#e23-null-only-check-and-prediction-check) | 2026-10-22 | V.B null-only check; can the final status be predicted from the observed values? | 12 null-only targets; 82 / 82 mutants predicted |
| [E24](#e24-reproduction-from-a-fresh-clone) | 2026-10-25 | Can a reader reproduce the results from the README alone? | yes, levels 1 and 2; two fixes (Windows long paths, line endings) |

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

## E16. Repeated runs: local check

| | |
|---|---|
| Objective | Check the repeated-run script and the outcome counting before running 14,679 tests on CI (plan task 6.2). |
| Method | `scripts/pankti/run-generated-tests.sh` (two separate Maven invocations of `surefire:test -Dtest='Test*PanktiGen*'`) on the sample integrated in E15; `analysis/test_outcomes.py` with the paper's and the authors' counts. |
| Configuration | Laptop (Windows), JDK 11.0.8, PDFBox surefire settings (pdfbox: `-Xmx768m`), 2 runs. |
| Outcome | 20 tests in both runs (22 s and 4 s), all passing; per method equal to Table III and to the authors' executed tests (rows 30, 54, 68, 75). Unit test of the verdict rules (passing, failing, flaky, not run) on synthetic reports passes. |
| Observation | Split classes (`...PanktiGenPartN`) are attributed to their target class correctly. |
| Interpretation | The pipeline is ready for the full set. |
| Assumptions | A19 (test-run configuration). |
| Limitations | A sample of 20 small tests: memory and duration of the full set are unknown. |
| Next step | E17 and E18 on CI. |

## E17. Execution of the reproduction's tests

| | |
|---|---|
| Objective | Plan task 6.2: #PASSING, #FAILING and flaky tests per method for the 14,679 tests generated from our profiles. |
| Method | Workflow `assess-tests`, job "reproduction"; integration (A18), compilation, 5 separate runs (A19), `analysis/test_outcomes.py`, `analysis/table3_execution.py`. |
| Configuration | Runs 39641425498 (discarded, see Outcome) and 39644913295 (result); tests of generate-tests run 39588027907; ubuntu-22.04 runner, JDK 11.0.8, PDFBox surefire settings (pdfbox `-Xmx768m`). |
| Outcome | First run: 666 failing tests, 301 of them in the split `HorizontalMetricsTable` classes (`ConversionException`), caused by the class splitter dropping `setUpXStream()` (docs/execution.md). After the fix: all 14,679 tests executed in each of the 5 runs (about 145 s per run); **14,314 passing, 365 failing, 0 flaky** (97.51%; paper 98.29%). 38 of the 46 rows have the paper's #PASSING and #FAILING; in the 8 others (font methods, and `getColorSpace` and `getEncryption`) the number of tests differs, as #UNIQUE did (E11); the extra method `TrueTypeFont.getOS2Windows` has 114 tests, all failing. Failures: `AssertionError` in all but the `getOS2Windows` tests that throw `EOFException` or `IOException: Bad file descriptor`. (`results/day6/reproduction/`, `results/day6/table3_execution.*`) |
| Observation | The extra failures (128) are exactly the extra tests of these 4 methods (114 + 8 + 4 + 2); where the profiles are the same, the outcomes are the same as in the paper. No test is flaky. |
| Interpretation | The pass/fail behaviour of the generated tests is reproduced; the differences come from the profiles collected (environment, E11), not from running the tests. `getOS2Windows` returns an `OS2WindowsMetricsTable`, which does not override `equals()`, and its profiles contain an open font file (`RandomAccessFile`): the derived oracle cannot work for such objects (paper, Section V.A). |
| Assumptions | A17-A19. |
| Limitations | Flakiness is checked by reruns only (5 JVMs); the test order inside a run is surefire's default. |
| Next step | Day 7: Descartes "after" with the passing tests. |


## E18. Execution of the authors' published tests

| | |
|---|---|
| Objective | Plan task 6.3: separate the effect of the environment from the effect of the profiles, by running the authors' own tests here. |
| Method | Same workflow, job "authors": the 22 classes the authors published (Zenodo), with the missing `@Before` import added (A20), integrated and run like ours. |
| Configuration | Run 39644913295 (run 39641425498 failed to compile them: the missing import). |
| Outcome | 13,851 tests executed in each of the 5 runs (about 120 s per run): **13,614 passing, 237 failing, 0 flaky** - Table III's totals, and the paper's #PASSING and #FAILING for **all 46 methods**. Failures: `AssertionError` only. (`results/day6/authors/`) |
| Observation | The 11,613 `getFlags` tests the authors counted as passing without executing them (discrepancies.md item 2) do pass when executed. |
| Interpretation | The environment of this reproduction does not change the outcome of the tests; columns #PASSING and #FAILING of Table III are reproduced exactly from the authors' tests, and the differences of E17 come from the profiles. |
| Assumptions | A20 (import repair), A18, A19. |
| Limitations | The published classes needed a one-line repair to compile. |
| Next step | Day 7. |

## E19. Descartes "after": local check

| | |
|---|---|
| Objective | Plan tasks 7.1-7.4, before using CI: check the "after" pipeline on a small sample. |
| Method | The sample of E15 (generated tests of `RenderingMode`, `PDCIDSystemInfo`, `XrefTrailerResolver`, all passing) in the pdfbox module, `scripts/pdfbox/run-descartes.sh` restricted to these 3 classes; `scripts/pankti/keep_passing_tests.py` on the full test sets; `analysis/pankti_status.py` on the authors' own reports. |
| Configuration | Laptop (Windows), JDK 11.0.8, PIT 1.4.10 + Descartes 1.2.6, 1 thread. |
| Outcome | First attempt: every method "not covered" after 19 s - with restricted `targetClasses`, pitest-maven also restricts `targetTests` by default and ran no test. With `targetTests` set to the module's package: 153 s; `RenderingMode.isFill` becomes partially tested (mutant `false` detected, `true` not), `getRegistry`, `getOrdering` and `getXrefType` become tested - the statuses of Table III. The filter keeps exactly 14,314 of our tests and 13,614 of the authors'. On the authors' own before/after reports, `pankti_status.py` gives 28 / 46 well-tested (17 tested, 11 partially tested), the status of Table III for all 46 methods. |
| Observation | The isFill example of the paper is reproduced: one observed value (`true`) kills only the mutant that returns the other value. |
| Interpretation | The pipeline is ready; the restriction needs the explicit test selection (A21). |
| Assumptions | A21, A22. |
| Limitations | 3 classes on Windows; the CI run validates the restriction itself. |
| Next step | E20 on CI. |

## E20. Descartes "after": restriction check and PANKTI_STATUS

| | |
|---|---|
| Objective | Plan tasks 7.2-7.4: classify the effective targets after the passing generated tests are added (Table III, PANKTI_STATUS) and check the paper's examples. |
| Method | Workflow descartes-after, run 39747040848: sources none (control), reproduction (14,314 passing tests) and authors (13,614 passing published tests), modules fontbox and pdfbox, mutation restricted to the 22 classes of the effective targets. `analysis/pankti_status.py` (with `--control`), `analysis/table3_status.py`, `analysis/compare_descartes_runs.py`, `analysis/mutant_tests.py`. |
| Configuration | GitHub Actions ubuntu-22.04, JDK 11.0.8, Maven 3.6.3, PIT 1.4.10 + Descartes 1.2.6, 21 operators, 1 thread; tests filtered with the Day 6 verdicts. 6 jobs, all successful; pdfbox 16-21 min, fontbox under 1 min. |
| Outcome | Well-tested: 28 / 46 (17 tested, 11 partially tested) with our tests and with the authors' tests, the status of Table III for all 46 methods in both cases; `getOS2Windows` stays pseudo-tested. Both test sets give the same classification for all 465 analysed methods. Control: 460 / 465 methods as in the full "before" run; `getXrefType` is tested without any generated test. `isFill`: partially tested (`false` killed, `true` not); `getName`: tested (`null`, `"A"`, `""` killed). |
| Observation | The `getXrefType` `null` mutant survived 183 tests in the full "before" run and was killed by the 53rd test, `testOCGConsumption`, in the control run: the same test passes or fails on the same mutant depending on the run. The authors' published "after" reports agree with ours on all 46 targets. |
| Interpretation | PANKTI_STATUS is reproduced exactly, with the authors' tests and with ours, although our tests differ for 8 methods: the extra tests do not change any status. One of the 28 targets (`getXrefType`) owes its "pseudo-tested before" status to an unstable test; counting only targets that are pseudo-tested in both runs without generated tests, 27 / 46 are improved by PANKTI. |
| Assumptions | A21 (restriction, validated), A22 (passing tests only), A3 (1 thread). |
| Limitations | One control run: other unstable kills may exist that this run did not reveal. Descartes "after" analyses 22 classes, not whole modules (the authors analysed whole modules). |
| Next step | Day 8: failure analysis (Section V.A categories) and the methods that stay pseudo-tested despite passing tests (Section V.B). |

## E21. Why generated tests fail

| | |
|---|---|
| Objective | Plan task 8.2: classify the failing tests into the paper's causes (Section V.A), plus any new cause. |
| Method | `analysis/failure_analysis.py` on both test sets (sources of the tests, Day 6 verdicts and failure messages); `equals`/`hashCode` declarations of the returned classes and cache keys read in the PDFBox 2.0.21 sources; `analysis/java/CacheLookupCheck.java` on three failing tests of the authors (`DefaultResourceCache.getFont1`, `getColorSpace10`, `getXObject6`). |
| Configuration | Laptop, Python 3.11; the run-time check with JDK 11.0.8, pdfbox/fontbox 2.0.21 and XStream 1.4.12 (the test dependency). |
| Outcome | Authors' tests: 237 failures = 151 identity `equals` + 86 lookups returning `null`; ours: 365 = 265 + 98 + 2 exceptions (`getOS2Windows`). In all 13 / 14 methods with failures, every passing test observed `null` and no failing test did. Run-time check: the deserialised caches hold all their entries (3, 4, 7) with live `SoftReference`s; the parameter is not one of the keys and the call returns `null`; with the cache's own key it returns the expected object. |
| Observation | The paper's "cache not available" (5 rows) and "transient fields" (4 rows) are not what makes these tests fail: the cache is present but keyed by identity, and the returned classes have no `equals`. |
| Interpretation | With PANKTI's `assertEquals` oracle, a test of a method returning such an object can only pass if production returned `null`. The failures are deterministic and environment-independent. |
| Assumptions | A23. |
| Limitations | No field-by-field comparison: transient fields may differ too. Run-time check on three tests only. |
| Next step | E23. |

## E22. Font sensitivity runs

| | |
|---|---|
| Objective | Plan task 8.3 (P2): test whether the font-method differences of Table III (#UNIQUE differs in 8 rows) depend on the environment. |
| Method | Two runs of `production-run.yml` in mode full, each changing one factor (A24): run 39756523874, font cache built before the workload (`font_cache=warm`); run 39756528629, DejaVu fonts only (`font_set=dejavu-only`). Compared with the main run 39444526027 and Table III by `analysis/compare_table3.py`. Prediction written before the runs: if the font cache build drives `NamingTable.getName`, its invocations fall in both runs, and the non-font targets do not change. |
| Configuration | As the main run (ubuntu-22.04, JDK 11.0.8, PANKTI `0fddf27`, Glowroot 0.13.6). |
| Outcome | Both runs successful, 50 / 50 command outcomes as the authors'. **Warm font cache** (57 fonts, cache built before the workload): 46 effective targets, exactly the paper's (Jaccard 1.0; `getOS2Windows` is no longer invoked); totals 121,300 / 57,677 / 13,852 (paper 121,175 / 57,563 / 13,851); `NamingTable.getName` 715 invocations and 260 unique profiles (paper 650 / 273; cold cache 1,457 / 976). **DejaVu only** (22 fonts): `getName` 741 / 403, and 13 rows differ, among them the glyph and metrics methods (e.g. `GlyfSimpleDescript.getFlags` 20,340 / 8,330 instead of 23,471 / 11,730), #UNIQUE 10,043; `FontCache.getFont` is not invoked. Rows with the paper's #INVOCATIONS and #UNIQUE: cold 38, warm 38, DejaVu 32 of 46 (`results/day8/sensitivity/`). |
| Observation | The prediction holds: `getName` invocations fall in both runs, and the non-font rows do not change (except two rows whose collected profiles depend on what was stored before the 200 MB threshold). The authors' execution log has no "Building on-disk font cache" message, which our cold-cache run prints at its first command, and the same six TrueType fallback choices as the warm-cache run (`LiberationSerif` for `TimesNewRomanPSMT`, ...). It has no fallback for the standard fonts Symbol and ZapfDingbats, which our runs replace by LiberationSans five times each. |
| Interpretation | The authors ran the workload with a PDFBox font cache already built, on a machine with the Liberation fonts and fonts for Symbol and ZapfDingbats. Building the cache during the workload explains `getOS2Windows` and most of the `getName` difference; the remaining differences (`PDFontDescriptor.getFlags`, `isSerif`, `isItalic`, `isFixedPitch`, part of `getName`) are consistent with the missing Symbol / ZapfDingbats fonts, not tested. The near-exact #UNIQUE total of the warm run comes partly from differences that cancel out (38 rows identical). |
| Assumptions | A24. |
| Limitations | One run per variant; the font set of the authors' machine is inferred from their log, not known. |
| Next step | Future work: a run with a pre-built cache and fonts for Symbol and ZapfDingbats. The main results (Days 4-7) keep the cold cache, as documented; the conclusions do not depend on it (the final status is reproduced with both test sets). |

## E23. Null-only check and prediction check

| | |
|---|---|
| Objective | Plan tasks 8.2 (null-only check of Section V.B) and 8.1 (prediction check of plan A.6): predict each target's status from the values its passing tests observed. |
| Method | `analysis/prediction_check.py`: for every mutant of every target in the "after" reports of Day 7, predicted detected if one passing test of the target observed a value different from the mutant's default value (`generated_tests.mutant_killed`); compared with Descartes. Return types from `invoked-methods.csv`, `equals` declarations from the PDFBox sources. |
| Configuration | Laptop, Python 3.11; both test sets. |
| Outcome | 82 / 82 mutants and 47 / 47 classifications predicted, for both test sets. 12 PDFBox targets keep passing tests and stay pseudo-tested; all have only `null` observations and only the `null` mutant (paper: 15 over three subjects, 12 in PDFBox). All 28 well-tested targets return a primitive, `String`, wrapper, array or enum; all 19 pseudo-tested targets return another object, with `equals` by identity. |
| Observation | Descartes' verdict after the generated tests is a function of the observed values: no other test kills a mutant that the target's own tests leave alive. |
| Interpretation | The paper's 28 / 46 is determined by the return types of the targets and the values observed for them; V.B is confirmed exactly. |
| Assumptions | A23, A10 (well-tested = tested or partially tested). |
| Limitations | The rule is checked on this case study only. |
| Next step | Report. |

## E24. Reproduction from a fresh clone

| | |
|---|---|
| Objective | Plan task 10.1: check that the README is enough to reproduce the results, without files or knowledge from the development machine. |
| Method | Fresh clone of the public repository (commit 6480ed5) in an empty directory; a new Python 3.11 environment from `requirements.txt` only; the unit tests; the code blocks of levels 1 and 2 of the README run as written, with `W` pointing to an existing copy of the authors' artifacts (fetched by `setup/fetch-artifacts.sh`, which re-checked the archive). Then `git status` in the clone: every regenerated file must equal the committed one. |
| Configuration | Windows laptop, Git Bash; JDK 11.0.8 and Maven 3.6.3 from `setup/env.sh` for the pankti-extract build (level 2). |
| Outcome | Level 1: 16 / 16 tests, all commands successful, no file changed. Level 2: all commands successful (pankti-extract rebuilt; #TARGET 138; 6,276 / 6,373 and 460 / 465 methods as the authors; PANKTI_STATUS 28 / 46; 151 + 86 failures classified; 82 / 82 mutants predicted); the only differences were the line endings of two files written by `check_paper_table3.py` and `compare_authors_report.py` (CRLF on Windows), with identical content. One transient network error (the PDFBox clone) was retried. |
| Observation | The first clone attempt failed on Windows: with the path of the clone, 30 file names under `results/day4/full/profiles/` exceed 260 characters. `git clone -c core.longpaths=true` solves it (already used for the authors' repository). |
| Interpretation | The analyses are reproducible from the repository and the authors' public artifacts. |
| Assumptions | None new. |
| Limitations | The CI workflows (level 3) were not rerun for this check; each was run when its stage was done (run IDs in the README). |
| Next step | README: Windows clone option and the JDK / Maven prerequisite of level 2; the two scripts now write LF. |
