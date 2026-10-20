# Work journal

## Day 1 - 2026-10-14: repository, toolchain, CI baseline, authors' artifacts

**Goal of the day:** working toolchains (CI and laptop), all external inputs downloaded and checked, a first
comparison between the paper and the authors' artifacts.

### Done

- Repository skeleton: README, license, line-ending rules (`.gitattributes` forces LF so that the shell scripts
  run on the Linux runners even though the laptop uses `core.autocrlf=true`).
- CI workflow `env-check` (`ubuntu-22.04`): AdoptOpenJDK 11.0.8+10 and Maven 3.6.3 with checksum checks,
  Liberation fonts, environment report, PDFBox 2.0.21 checkout with the build-only PDFBOX-5005 fix, full build
  with tests, per-module test summary.
- Laptop toolchain without administrator rights (`setup/windows/install-tools.ps1`): JDK 11.0.8, Maven 3.6.3, gh,
  uv, Python 3.11.17 with pandas 1.5.3. Three problems had to be solved on the way (see `environment.md`):
  truncated downloads with `Invoke-WebRequest`, PowerShell 5.1 turning stderr output into errors, and file names
  longer than the Windows path limit in the experiments repository.
- Authors' artifacts: pankti at `0fddf27` and `326a753`, pankti-experiments at `7bc7791` and `1d8f9aa`
  (sparse checkout of `pdfbox/`). The Zenodo archive (1.37 GB) downloads at 50-450 KB/s and is still running.
- Table III transcribed (`analysis/paper/table3_pdfbox.csv`) and checked: every sum matches the printed totals
  (`results/day1/paper_table3_checks.txt`).
- Paper vs authors' artifacts, method by method (`results/day1/authors_report_vs_paper.csv`), and summary of
  the 14 Descartes reports of the authors (`results/day1/authors_descartes_reports.csv`).
- PANKTI's instrumentation code (`MethodAspect0.java`) read to understand how invocations are counted and how
  profiles are written.

### Findings (details in `discrepancies.md`)

1. The paper counts 13,614 passing tests, but only 2,001 passing tests were executed: for
   `GlyfSimpleDescript.getFlags` only 117 of the 11,730 generated tests were run, and the 11,613 others are
   counted as passing.
2. The difference between 28 (paper) and 29 (`report.csv`) well-tested methods is
   `DefaultResourceCache.getColorSpace`, mislabelled `tested` in `report.csv`. All Descartes reports say
   pseudo-tested, so the paper is right.
3. "Well-tested" in the paper means tested or partially-tested. With that reading, the authors' last Descartes
   run gives exactly the 46 statuses of Table III.
4. The authors' Descartes runs use 21 mutation operators (Descartes 1.2.x default), not a reduced set.
5. In PANKTI `0fddf27`, invocation counts and the 200 MB threshold are cumulative over the 50 JVM launches of the
   workload. Profile parts are written at method entry and exit and paired by position later, so a call that
   throws can shift the pairing.
6. The "after" Descartes runs of the authors report fewer tested methods than the "before" run in the pdfbox
   module, so they were not run on the same test population. To keep in mind when running Descartes again.

### Problems and decisions

- Getting the PDFBox 2.0.21 test suite to run on the CI runner took four iterations:
  1. Run 1: build step failed after about 2 minutes. The job log needs authentication even for a public
     repository, so the workflow now publishes the Maven errors, the reactor summary and the test summary as
     annotations, which can be read without logging in.
  2. Run 2: 3 errors in `PDAcroFormTest` (writes into a directory it never creates; passes only when another test
     ran first) and the preflight module failed to download the Isartor suite (HTTP 403 at pdfa.org).
  3. Run 3: everything up to preflight passed (1,654 tests, 0 failures); the examples module failed to download a
     certificate policy PDF.
  4. Run 4: full build, **1,678 tests** (the authors report 1,675), 0 failures, 13 errors, all in the examples
     module and all `CertificateExpiredException`: the test keystore shipped with PDFBox 2.0.21 expired on
     2026-06-05. This is a time bomb in the test data, unrelated to the methods studied (fontbox and pdfbox).
  The download fixes reuse byte-identical files (the build checks their sha512). The expired certificate is
  listed in `scripts/pdfbox/known-failures.txt`, so env-check only fails on unexpected failures.
- Decision for Descartes, which needs a green suite: exclude the two test classes that contain the 13 errors
  (`scripts/pdfbox/descartes-excluded-tests.txt`). PIT excludes by class, so 10 passing tests go too
  (23 of 1,678 tests). Setting the clock back was the alternative and was not retained.
- The Maven cache was not saved when the job failed. It is now restored and saved in separate steps.
- Decision: all generated tests will be executed; non-executed tests will never be counted as passing.

### Baseline on the CI runner (run 38542374578, results in `results/day1/env-check/`)

Runner image ubuntu22 20261004.315.1, 4 vCPU (AMD EPYC 7763), 15 GiB RAM, AdoptOpenJDK 11.0.8+10, 57 fonts
(16 Liberation entries). PDFBox commit `fa8029d8` (tag 2.0.21). Build and tests: 143 s.

| module | tests | errors |
|---|---|---|
| fontbox | 27 | 0 |
| pdfbox | 531 | 0 |
| xmpbox | 810 | 0 |
| preflight | 281 | 0 |
| tools | 5 | 0 |
| examples | 24 | 13 (expired test keystore) |
| total | 1,678 | 13 |

### Next (Day 2)

Fix the baseline build if needed. Set up PIT 1.4.x + Descartes 1.2.x with the 21 operators and start the "before"
runs for the 6 modules. Recompute #TARGET from the authors' "before" reports with pankti-extract.

## 15-19 Oct: no progress

No work was done on these days. On 20 Oct the work moved to another computer. The local toolchain and the authors'
artifacts were rebuilt with the repository's own scripts (`setup/windows/install-tools.ps1`,
`setup/fetch-artifacts.sh`; about 30 minutes, 7.4 GB). On the new machine, the Day-1 analyses give byte-identical
results, and a local build of the PDFBox fontbox and pdfbox modules passes its 558 tests.

## Day 2 - 2026-10-20: pseudo-tested methods and targets

**Goal of the day (plan):** Descartes "before" runs on CI for the six modules, the target count from the authors'
reports, and a script that compares two sets of Descartes reports.

### Done

- Two Day-1 fixes:
  - `analysis/descartes.py` identifies methods by class, name and parameter descriptor. The previous comparison
    merged overloads, which gave wrong "before" statuses for Table III rows 31 and 35. With the fix, all 46 targets
    are pseudo-tested in the authors' "before" reports and all 46 "after" statuses match the paper.
  - `analysis/profile_stats.py` recomputes the profile facts of Section IV.C from the replication data
    (121,175 / 57,563 / 158 B / 54.7 MiB / 5.49 GiB / 19 methods). It also shows that each of the 19 capped methods
    has an XML file of at least 200 MiB.
- Descartes configuration (`scripts/pdfbox/add-descartes-profile.sh`, `run-descartes.sh`): PIT 1.4.10, Descartes
  1.2.6, the 21 operators of the authors' reports, `targetClasses` per module. A local smoke run on fontbox gave the
  authors' counts (550 / 168 / 6 / 61 / 315).
- Workflow `descartes-before` (one job per module) and two runs: 39409510406 (all modules, 4 threads) and
  39415980930 (pdfbox, 1 thread).
- Targets: `scripts/pankti/extract-targets.sh` builds pankti-extract at `0fddf27` and runs the authors'
  `find-pseudo-tested.py`.
  - With the authors' reports: **138 targets**, exactly the paper's #TARGET.
  - With the reproduction's own reports: also 138, 137 of them in common with the authors' list.
  - Both lists contain the 46 effective targets.
- `analysis/compare_descartes_runs.py`: per-method comparison of two sets of reports (classification matrix, Jaccard
  index, mutant statuses, killing tests, Table III targets). It was checked on the authors' reports compared with
  themselves (100% agreement) and on their before/after reports (which shows the known 1,580 -> 1,488 drop in pdfbox).
- Documentation:
  - new `docs/descartes.md` (method, configuration, results);
  - new `docs/assumptions.md` (11 assumptions in a fixed format);
  - `docs/discrepancies.md` items 1b, 5 and 8 updated, items 14-16 added;
  - README.

### Results

| Module | Same classification as the authors | Note |
|---|---|---|
| fontbox, xmpbox, preflight, tools | 1,624 / 1,624 | identical |
| pdfbox (1 thread) | 4,421 / 4,438 | differences come from tests with shared files and network downloads |
| examples | 231 / 311 | excluded test classes (expired keystore), no target in this module |

All 46 effective targets of Table III are pseudo-tested in the reproduction's "before" run.

### Problems and decisions

- **4 threads change the result for pdfbox.** The first run used the runner's 4 vCPUs. pdfbox then had 310 timed-out
  mutants (authors: 62), 1,799 tested methods (authors: 1,580), and 25 of the 40 pdfbox targets became "tested",
  `isFill` among them. The extra detections come from timeouts and from tests that write fixed files under
  `target/test-output` and download PDFs during the test (mostly `PDAcroFormFlattenTest`): parallel PIT workers
  interfere with each other. A re-run with 1 thread matches the authors (the authors' 83-minute run time is
  consistent with one thread). Decision: 1 thread for every module. With the 4-thread report, the pipeline would
  have selected 91 targets instead of 138, and only 21 of the 46 effective targets.
- **examples:** excluding the two test classes with the expired keystore removes 23 of the module's 24 tests. 80
  methods lose their coverage. This has no effect on the targets.
- **pankti-extract (2020) still builds and runs**, with two fragilities:
  - Spoon declares a snapshot repository that no longer exists (warnings only).
  - JDT's open version ranges now resolve Eclipse platform jars compiled for Java 17. They are never loaded on the
    code path used, so the Java 11 tool still works.

  Its full method list is written in hash-map order, so two runs differ in row order only.
- **OS sensitivity:** a local Windows run of fontbox differs from the authors on 4 font-directory-finder methods,
  which match on Linux. This confirms that every measurement must run on the Linux runner.
- **Target list for Day 3:** frozen from the authors' reports, as decided (assumption A8). The reproduction's own
  list differs by one method in each direction.

### Next (Day 3)

Freeze `results/targets.csv` from `results/day2/instrumentation-candidates-pdfbox.csv`. Then start the production
run as a dry run: download Glowroot 0.13.6, build pankti-instrument at `0fddf27`, generate the aspects with
`instrument.py`, build the plugin jar, and install it into Glowroot on CI.
