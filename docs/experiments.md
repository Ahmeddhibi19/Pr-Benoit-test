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
