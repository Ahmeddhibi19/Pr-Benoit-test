# Reproducing Case Study 2 (PDFBox) of "Production Monitoring to Improve Test Suites"

This repository reproduces the results of **Case Study 2 (Section IV.C)** of

> D. Tiwari, L. Zhang, M. Monperrus, B. Baudry. *Production Monitoring to Improve Test Suites.*
> IEEE Transactions on Reliability, 2021. [arXiv:2012.01198](https://arxiv.org/abs/2012.01198) (v4).

The case study applies PANKTI to Apache PDFBox 2.0.21. It selects the pseudo-tested methods found by
Descartes, monitors them while PDFBox runs a PDF workload, turns the collected object profiles into
differential unit tests, and checks which methods are no longer pseudo-tested.

The numbers to reproduce are the PDFBox rows of Table III (rows 30-75), #TARGET = 138, #EFF_TARGET = 46,
the size facts about the collected profiles, and Figure 5.

## Status

| Step | State |
|---|---|
| Environment and PDFBox 2.0.21 baseline build on CI | in progress |
| Authors' artifacts downloaded and inventoried | in progress |
| Pseudo-tested methods (Descartes, before) | to do |
| Instrumentation and workload | to do |
| Test generation and execution | to do |
| Descartes after, comparison with the paper | to do |

## Layout

```
.github/workflows/   CI workflows (Linux runners)
scripts/ci/          runner setup: JDK, Maven, disk, environment report
scripts/pdfbox/      PDFBox checkout, build-only patch, test summary
setup/               local setup (portable toolchain, artifact download)
analysis/            analysis scripts and data transcribed from the paper
docs/                environment, artifacts, discrepancies, work journal
results/             summaries produced by the runs
```

## Pinned versions

| Component | Version | Why |
|---|---|---|
| JDK | AdoptOpenJDK 11.0.8+10 | version recorded in the authors' execution log |
| Maven | 3.6.3 | contemporary with the experiment (2020) |
| PDFBox | 2.0.21 (git tag) | version studied in the paper |
| Glowroot | 0.13.6 | version used by PANKTI's instrumentation plugin |
| PANKTI | `0fddf27` (2020-10-26) | last commit before the PDFBox run of 2020-11-03 |

## Running

**CI.** The `env-check` workflow installs the toolchain, builds PDFBox 2.0.21 and runs its test suite. It starts
on pushes that touch its scripts, or manually from the Actions tab.

**Locally (Windows, no admin rights needed).**
```powershell
./setup/windows/install-tools.ps1 -Dest C:\w\tools
. ./setup/windows/env.ps1 -Tools C:\w\tools
```
```bash
bash setup/fetch-artifacts.sh /c/w
```

## Deviations from the original setup

The PDFBox 2.0.21 test build needs three adjustments today (`scripts/pdfbox/patch-build.sh`). The library code and
the tests are unchanged:
- two IPA fonts moved to another host (PDFBOX-5005), so the URLs used from PDFBox 2.0.22 onwards are used;
- the Isartor test suite of the preflight module is no longer served by pdfa.org, so the identical file (same
  sha512, checked during the build) is taken from the Internet Archive;
- `PDAcroFormTest` writes into `pdfbox/target/test-output` without creating it, so the directory is created first.

All deviations and simplifying assumptions are listed in [docs/discrepancies.md](docs/discrepancies.md).
