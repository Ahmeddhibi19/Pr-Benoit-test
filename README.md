# Reproducing Case Study 2 (PDFBox) of "Production Monitoring to Improve Test Suites"

This repository reproduces the results of **Case Study 2 (Section IV.C)** of

> D. Tiwari, L. Zhang, M. Monperrus, B. Baudry. *Production Monitoring to Improve Test Suites.*
> IEEE Transactions on Reliability, 2021. [arXiv:2012.01198](https://arxiv.org/abs/2012.01198) (v4).

The case study applies PANKTI to Apache PDFBox 2.0.21:
1. Descartes finds the *pseudo-tested* methods of PDFBox: methods covered by the test suite where no test fails when
   the whole body is replaced by a default return value.
2. PANKTI instruments the public, non-static, non-void ones (the *targets*) and records their receiver, arguments and
   return value (*object profiles*) while PDFBox runs a workload of 50 command-line calls on 5 PDF files.
3. Each unique profile becomes a differential unit test (deserialise the receiver and arguments, call the method,
   assert the observed return value).
4. Descartes runs again with the new tests: a target that is no longer pseudo-tested is *well-tested*.

The numbers to reproduce are #TARGET = 138, #EFF_TARGET = 46, the PDFBox rows of Table III (rows 30-75), the facts
about the collected profiles (5.5 GB, 158 B to about 55 MB, 19 methods hitting the 200 MB threshold, nesting depth 36),
Figure 5 and the `isFill` example.

The reproduction follows two tracks:
- **Track A** checks the paper against the authors' published artifacts (tool repository, experiment repository,
  replication data on Zenodo).
- **Track B** re-runs the pipeline from scratch on GitHub Actions (Linux).

## Status

| Step | State | Evidence |
|---|---|---|
| PDFBox 2.0.21 builds and its test suite runs on CI | done | [`results/day1/env-check/`](results/day1/env-check/) |
| Authors' artifacts downloaded and checked against the paper | done | [`docs/discrepancies.md`](docs/discrepancies.md), [`results/day1/`](results/day1/) |
| Profile facts of Section IV.C recomputed from the authors' data | done | [`results/day1/authors_profile_stats.txt`](results/day1/authors_profile_stats.txt) |
| #TARGET recomputed with the authors' tools (138, as in the paper) | done | [`results/day2/targets_authors_reports.txt`](results/day2/targets_authors_reports.txt) |
| Descartes "before" run of the reproduction, compared with the authors' | done | [`docs/descartes.md`](docs/descartes.md), [`results/day2/`](results/day2/) |
| Target list frozen (138 methods) | done | [`results/targets.csv`](results/targets.csv) |
| Instrumentation built and installed in Glowroot (dry run, no workload) | done | [`docs/instrumentation.md`](docs/instrumentation.md), [`results/day3/`](results/day3/) |
| Workload under the instrumentation | to do | |
| Test generation and execution | to do | |
| Descartes "after", comparison with the paper | to do | |

## Results so far

| Quantity | Paper | Authors' artifacts | This reproduction |
|---|---|---|---|
| #TARGET | 138 | 129 (README of 2020-10-06); 138 with the authors' tools on their reports | **138** with the reproduction's own Descartes run (137 in common with the authors' list) |
| Targets among them invoked by the workload (#EFF_TARGET) | 46 | 46 | all 46 are among the 138; workload not yet run |
| Pseudo-tested methods found by Descartes | not given | 644 (6 modules) | 613; same classification as the authors for 6,276 of 6,373 methods (fontbox, xmpbox, preflight, tools: all; pdfbox: 4,421 / 4,438; examples differs by design, A2). All 46 effective targets pseudo-tested. Requires 1 PIT thread: with 4, #TARGET drops to 91 ([`docs/descartes.md`](docs/descartes.md)) |
| pdfbox-app jar used for the workload | not given | self-built, 9,890,400 bytes | built from tag 2.0.21: same content as the authors' jar (all 5,644 class files identical) |
| #INVOCATIONS / #COLLECTED | 121,175 / 57,563 | 121,175 / 57,563 | workload not yet run |
| Profile sizes | 158 B to about 55 MB, 5.5 GB | 158 B to 54.7 MiB, 5.49 GiB | workload not yet run |
| #PASSING / #FAILING | 13,614 / 237 | 2,001 / 237 executed (11,613 tests counted as passing were not executed) | not yet run |
| Well-tested | 28 / 46 | 28 / 46 | not yet run |

## Repository layout

```
.github/workflows/   CI workflows (Linux runners)
  env-check.yml        toolchain + PDFBox 2.0.21 build and test suite
  descartes-before.yml PIT + Descartes on the original test suite, one job per module
  production-run.yml   PANKTI plugin for the frozen targets, Glowroot, pdfbox-app; workload (from Day 4)
scripts/ci/          runner setup: JDK, Maven, disk, environment report, annotations
scripts/pdfbox/      PDFBox checkout, build-only patch, Descartes profile and run, test summary
scripts/pankti/      target extraction and plugin build with the authors' tools
scripts/glowroot/    Glowroot installation and agent check
setup/               local setup (portable toolchain, download of the authors' artifacts)
analysis/            analysis scripts; analysis/paper/ holds Table III as printed in the paper
results/             outputs of the runs and of the analyses, one folder per stage
docs/                methodology notes, assumptions, discrepancies, environment, artifacts, work journal
```

## Pinned versions

| Component | Version | Why |
|---|---|---|
| JDK | AdoptOpenJDK 11.0.8+10 | version recorded in the authors' execution log |
| Maven | 3.6.3 | contemporary with the experiment (2020) |
| PDFBox | 2.0.21 (git tag, commit `fa8029d8`) | version studied in the paper |
| PIT / Descartes | pitest-maven 1.4.10 / Descartes 1.2.6, 21 operators | operators read from the authors' reports; latest Descartes release at the time of their runs |
| PANKTI | `0fddf27` (2020-10-26) | last commit before the PDFBox run of 2020-11-03 |
| Glowroot | 0.13.6 | version used by PANKTI's instrumentation plugin |
| Python (analysis) | 3.11 with pandas 1.5.3 | the authors' scripts need pandas < 2 |

## Running

### On GitHub Actions

Both workflows are started from the Actions tab or with the GitHub CLI:

```bash
gh workflow run env-check.yml          # about 10 min
gh workflow run descartes-before.yml   # one job per module, 1 PIT thread; pdfbox is the longest (about 70 min)
gh workflow run production-run.yml -f mode=dry-run   # plugin + Glowroot + pdfbox-app, agent check (about 5 min)
gh run download <run-id>               # outputs of a run (methods.json, checks, logs, environment report)
```

### Locally (Windows, no administrator rights)

```powershell
./setup/windows/install-tools.ps1 -Dest C:\w\tools   # JDK 11.0.8, Maven 3.6.3, gh, uv, Python 3.11 + pandas 1.5.3
. ./setup/windows/env.ps1 -Tools C:\w\tools          # in a new window: Set-ExecutionPolicy -Scope Process Bypass first
```
```bash
source setup/env.sh /c/w/tools        # Git Bash
bash setup/fetch-artifacts.sh /c/w    # authors' repositories and replication data (about 7.4 GB, see docs/artifacts.md)
```

Track A analyses (paths as created by `fetch-artifacts.sh`):

```bash
P=/c/w/data/pankti-data-v1/pankti-data/pdfbox/pankti-collected-object-profiles
E=/c/w/src/pankti-experiments-2021/pdfbox
python analysis/check_paper_table3.py analysis/paper/table3_pdfbox.csv results/day1/paper_table3_checks.txt
python analysis/compare_authors_report.py $E $P/invoked-methods.csv results/day1/authors_report_vs_paper.csv
python analysis/profile_stats.py $P results/day1/authors_profile_stats \
       --listing /c/w/data/pankti-data-v1.listing.csv pankti-data/pdfbox/pankti-collected-object-profiles/

bash scripts/pdfbox/checkout.sh /c/w/work/pdfbox
bash scripts/pankti/extract-targets.sh /c/w/src/pankti /c/w/work/pdfbox $E/descartes/before /c/w/work/targets
python analysis/count_targets.py /c/w/work/targets $E/descartes/before $P/invoked-methods.csv results/day2/targets_authors_reports

# the same comparison with the reproduction's own reports, stored compressed in results/day2/descartes_before/
python analysis/compare_descartes_runs.py results/day2/descartes_before $E/descartes/before results/day2/descartes_before_vs_authors \n       --labels reproduction authors --table3 $P/invoked-methods.csv
```

Descartes on one module, locally (the fontbox module takes about one minute):

```bash
bash scripts/pdfbox/checkout.sh pdfbox && bash scripts/pdfbox/patch-build.sh pdfbox
bash scripts/pdfbox/add-descartes-profile.sh pdfbox
bash scripts/pdfbox/run-descartes.sh pdfbox fontbox out/fontbox
python analysis/compare_descartes_runs.py out/fontbox/methods.json $E/descartes/before/fontbox out/cmp --labels mine authors
```

Instrumentation, locally (the agent check starts pdfbox-app without a command, so no profile is written):

```bash
bash scripts/pankti/build-plugin.sh /c/w/src/pankti results/targets.csv out/plugin   # needs pandas + numpy
bash scripts/glowroot/install-glowroot.sh out/glowroot out/plugin/pankti-plugin.jar
bash scripts/pdfbox/build-app.sh pdfbox out/app
bash scripts/glowroot/check-agent.sh out/glowroot/glowroot out/app/pdfbox-app-2.0.21.jar out/agent
python analysis/compare_jars.py out/app/pdfbox-app-2.0.21.jar /c/w/src/pankti-experiments/pdfbox/execution/pdfbox-app-2.0.21.jar
```

## Documentation

- [docs/descartes.md](docs/descartes.md): how pseudo-tested methods are computed, and how the results compare with
  the authors'.
- [docs/instrumentation.md](docs/instrumentation.md): what PANKTI's instrumentation records, how it is built and
  installed, and its known limitations.
- [docs/experiments.md](docs/experiments.md): log of every experiment (question, method, result, interpretation).
- [docs/assumptions.md](docs/assumptions.md): every simplifying assumption, with its justification, expected impact and
  validation.
- [docs/discrepancies.md](docs/discrepancies.md): differences between the paper, the authors' artifacts and this
  reproduction.
- [docs/environment.md](docs/environment.md) and [docs/artifacts.md](docs/artifacts.md): toolchains, external inputs,
  versions and checksums.
- [docs/journal.md](docs/journal.md): day-by-day work log.

## Deviations from the original setup (summary)

- The PDFBox 2.0.21 test build needs four build-only adjustments today (dead download URLs, one test that depends on
  execution order). No library or test code is changed (A1).
- The test keystore shipped with PDFBox 2.0.21 expired in June 2026. The two test classes that use it are excluded
  from the Descartes runs. This only affects the `examples` module, which contains no target (A2).
- All measured runs execute on Linux (GitHub Actions) with the authors' JDK; the Windows laptop is used for development
  only (A5).

See [docs/assumptions.md](docs/assumptions.md) for the full list.
