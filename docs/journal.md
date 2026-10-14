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
