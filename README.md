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

**In short.** Reproduced exactly: #TARGET (138), the 46 effective targets (with the authors' font-cache state),
#PASSING / #FAILING of the authors' tests, PANKTI_STATUS (28 / 46, all 46 statuses), the `isFill` example and
Section V.B. Reproduced in shape: the workload columns of Table III (38 of 46 rows identical; the others are font
methods, whose values depend on the installed fonts). Not reproduced: the nesting depth of 36, which the paper does
not define. Section V.A is reproduced on every failing test, with a different mechanism for 9 rows.

The full comparison, one line per published number with its source file, is in
[`results/comparison/comparison.txt`](results/comparison/comparison.txt); row by row in
[`results/comparison/table3_rows.csv`](results/comparison/table3_rows.csv) and
[`results/comparison/table3_rows.png`](results/comparison/table3_rows.png).

The reproduction follows two tracks:
- **Track A** checks the paper against the authors' published artifacts (tool repository, experiment repository,
  replication data on Zenodo).
- **Track B** re-runs the pipeline from scratch on GitHub Actions (Linux).

## Status

| Step | State | Evidence |
|---|---|---|
| PDFBox 2.0.21 builds and its test suite runs on CI | done | [`results/01-paper-vs-artifacts/env-check/`](results/01-paper-vs-artifacts/env-check/) |
| Authors' artifacts downloaded and checked against the paper | done | [`docs/discrepancies.md`](docs/discrepancies.md), [`results/01-paper-vs-artifacts/`](results/01-paper-vs-artifacts/) |
| Profile facts of Section IV.C recomputed from the authors' data | done | [`results/01-paper-vs-artifacts/authors_profile_stats.txt`](results/01-paper-vs-artifacts/authors_profile_stats.txt) |
| #TARGET recomputed with the authors' tools (138, as in the paper) | done | [`results/02-descartes-before/targets_authors_reports.txt`](results/02-descartes-before/targets_authors_reports.txt) |
| Descartes "before" run of the reproduction, compared with the authors' | done | [`docs/descartes.md`](docs/descartes.md), [`results/02-descartes-before/`](results/02-descartes-before/) |
| Target list frozen (138 methods) | done | [`results/targets.csv`](results/targets.csv) |
| Instrumentation built and installed in Glowroot (dry run, no workload) | done | [`docs/instrumentation.md`](docs/instrumentation.md), [`results/03-instrumentation/`](results/03-instrumentation/) |
| Workload under the instrumentation, profile metrics (Table III columns 1-3) | done | [`results/04-workload/`](results/04-workload/), [`docs/instrumentation.md`](docs/instrumentation.md) |
| Test generation (and regeneration of the authors' tests from their profiles) | done | [`docs/generation.md`](docs/generation.md), [`results/05-test-generation/`](results/05-test-generation/) |
| Test execution (5 separate runs, our tests and the authors') | done | [`docs/execution.md`](docs/execution.md), [`results/06-test-execution/`](results/06-test-execution/) |
| Descartes "after" (PANKTI_STATUS), our tests and the authors' | done | [`docs/descartes.md`](docs/descartes.md), [`results/07-descartes-after/`](results/07-descartes-after/) |
| Why tests fail (V.A), null-only check (V.B), prediction check | done | [`docs/failures.md`](docs/failures.md), [`results/08-failure-analysis/`](results/08-failure-analysis/) |
| Three-way comparison: paper, authors' artifacts, reproduction | done | [`results/comparison/`](results/comparison/) |

## Results

| Quantity | Paper | Authors' artifacts | This reproduction |
|---|---|---|---|
| #TARGET | 138 | 129 (README of 2020-10-06); 138 with the authors' tools on their reports | **138** with the reproduction's own Descartes run (137 in common with the authors' list) |
| Targets invoked by the workload (#EFF_TARGET) | 46 | 46 | 47: all 46, plus one font method |
| Pseudo-tested methods found by Descartes | not given | 644 (6 modules) | 613; same classification as the authors for 6,276 of 6,373 methods (fontbox, xmpbox, preflight, tools: all; pdfbox: 4,421 / 4,438; examples differs by design, A2). All 46 effective targets pseudo-tested. Requires 1 PIT thread: with 4, #TARGET drops to 91 ([`docs/descartes.md`](docs/descartes.md)) |
| pdfbox-app jar used for the workload | not given | self-built, 9,890,400 bytes | built from tag 2.0.21: same content as the authors' jar (all 5,644 class files identical) |
| #INVOCATIONS / #COLLECTED / #UNIQUE | 121,175 / 57,563 / 13,851 | identical | 122,384 / 58,672 / 14,679; 41 / 40 / 38 of the 46 rows identical, the others are font methods. With the PDFBox font cache built before the workload, as the authors' log shows they had: 121,300 / 57,677 / 13,852 and exactly the 46 targets ([`docs/instrumentation.md`](docs/instrumentation.md)) |
| `RenderingMode.isFill` | 30,944 invocations, 1 unique, 158 B; partially tested after (mutant `false` detected, `true` not) | identical | identical |
| Methods hitting the 200 MB threshold | 19 | 19 | 19 |
| Profile sizes | 158 B to about 55 MB, 5.5 GB | 158 B to 54.7 MiB, 5.49 GiB | 158 B to 54.7 MiB, 5.30 GiB |
| Maximum nesting depth | 36 (undefined) | 73 (XML element depth) | 73 (same measure) |
| Figure 5 (profile sizes, 10 MiB bins) | histogram | 57,458 / 71 / 3 / 23 / 5 / 3 | 58,563 / 75 / 3 / 23 / 5 / 3 ([`results/05-test-generation/fig5.png`](results/05-test-generation/fig5.png)) |
| #PANKTI_TESTS | 13,851 | 13,851; regenerated from their profiles: all 13,851 identical to the published tests | 14,679 (= #UNIQUE for each of the 47 methods) |
| #PASSING / #FAILING (5 runs, 0 flaky) | 13,614 / 237 | their 13,851 tests run here: 13,614 / 237, all 46 rows identical | 14,314 / 365 of 14,679 (38 of 46 rows identical; differences follow #UNIQUE) |
| Why generated tests fail (V.A) | 4 causes from a sample | their 237 failing tests run here: 151 `equals` by identity, 86 cache lookups returning `null` | 365: 265 / 98 / 2 exceptions. A test passes exactly when production returned `null`; the caches are not missing but keyed by identity ([`docs/failures.md`](docs/failures.md)) |
| Targets with passing tests that stay pseudo-tested (V.B) | 15 (12 in PDFBox), null-only | 12, all null-only | 12, all null-only |
| Well-tested after the generated tests (PANKTI_STATUS) | 28 / 46 | 28 / 46 in their reports; their passing tests run here: 28 / 46, all 46 statuses identical | **28 / 46** (17 tested, 11 partially tested), all 46 statuses identical to Table III. One of the 28 (`getXrefType`) is already tested in a run without generated tests: its "before" status is unstable ([`docs/descartes.md`](docs/descartes.md)) |

## Repository layout

```
.github/workflows/   CI workflows (Linux runners)
  env-check.yml        toolchain + PDFBox 2.0.21 build and test suite
  descartes-before.yml PIT + Descartes on the original test suite, one job per module
  production-run.yml   PANKTI plugin for the frozen targets, Glowroot, pdfbox-app; the workload (modes dry-run, smoke, full)
  generate-tests.yml   pankti-generate on the reproduction's profiles, and on the authors' (compared with their tests)
  assess-tests.yml     the generated tests integrated into PDFBox and run 5 times (ours and the authors')
  descartes-after.yml  Descartes with the passing generated tests added (ours, the authors', none as a control)
scripts/ci/          runner setup: JDK, Maven, disk, environment report, annotations
scripts/pdfbox/      PDFBox checkout, build-only patch, Descartes profile and run, test summary
scripts/pankti/      target extraction, plugin build, workload, test generation and integration (authors' tools)
scripts/glowroot/    Glowroot installation and agent check
setup/               local setup (portable toolchain, download of the authors' artifacts)
analysis/            analysis scripts; analysis/paper/ holds Table III as printed in the paper
results/             outputs of the runs and of the analyses, one folder per stage (index: results/README.md)
tests/               unit tests of the analysis scripts (python -m unittest discover -s tests)
requirements.txt     Python packages (Python 3.11)
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
| Python (analysis) | 3.11; `requirements.txt` (pandas 1.5.3, numpy 1.26.4, matplotlib 3.8.4) | the authors' scripts need pandas < 2 |
| GitHub Actions | `ubuntu-22.04` runners; actions pinned by major version (`checkout@v7`, `cache@v6`, `upload-artifact@v7`, `download-artifact@v7`) | the runner image is recorded by every run (`env-report.txt`) |

## Reproducing the results

There are three levels, from minutes on a laptop to the full pipeline on GitHub Actions. All local commands run from
the repository root, in bash (Linux, macOS, or Git Bash on Windows), with Python 3.11:

```bash
git clone https://github.com/Ahmeddhibi19/Pr-Benoit-test.git && cd Pr-Benoit-test
#   on Windows: git clone -c core.longpaths=true ...   (some result file names exceed 260 characters with the path)
python3.11 -m venv .venv && . .venv/bin/activate      # Windows: .venv/Scripts/activate
pip install -r requirements.txt
python -m unittest discover -s tests                  # 16 tests of the analysis scripts
```

### 1. From the committed results (no download, a few minutes)

The raw outputs of every CI run used in the report are committed under `results/` (index:
[`results/README.md`](results/README.md)). These commands recompute the derived tables from them; each output can be
compared with the committed file (`git diff` shows no change):

```bash
I=results/04-workload/full/profiles/invoked-methods.csv; T=results/01-paper-vs-artifacts/authors_report_vs_paper.csv
# PANKTI_STATUS (Table III, last column): "before" reports, "after" runs, control run without generated tests
python analysis/pankti_status.py results/02-descartes-before/descartes_before results/07-descartes-after/reproduction $I \
       results/07-descartes-after/pankti_status_reproduction --table3 $T --control results/07-descartes-after/none
python analysis/compare_descartes_runs.py results/07-descartes-after/reproduction results/07-descartes-after/authors \
       results/07-descartes-after/reproduction_vs_authors --labels reproduction authors --table3 $I
# the restriction to the target classes checked against the full "before" run (assumption A21)
python analysis/compare_descartes_runs.py results/02-descartes-before/descartes_before results/07-descartes-after/none \
       results/07-descartes-after/restriction_check --labels full-before restricted-none --table3 $I --only-b
python analysis/mutant_tests.py org.apache.pdfbox.pdmodel.graphics.state.RenderingMode isFill \
       results/07-descartes-after/reproduction/pdfbox.mutations.json.gz          # the isFill example: mutant false killed, true not
# font sensitivity (experiment E22)
R=results/08-failure-analysis/sensitivity
python analysis/sensitivity_table.py $R/font_methods main=results/04-workload/table3_comparison.csv \
       warm-cache=$R/warm-cache/table3_comparison.csv dejavu-only=$R/dejavu-only/table3_comparison.csv
# the three-way comparison and its figure
python analysis/comparison.py results results/comparison
python analysis/figure_table3.py results/comparison/table3_rows.csv results/comparison/table3_rows.png
```

### 2. With the authors' artifacts (about 7.4 GB)

`setup/fetch-artifacts.sh <root>` downloads the Zenodo replication data (md5 checked) and checks out the authors'
repositories at the commits of the study ([`docs/artifacts.md`](docs/artifacts.md)). The #TARGET step builds
pankti-extract and needs JDK 11 and Maven 3.6.3 on the `PATH` (`MAVEN_EXTRA_ARGS` passes extra Maven arguments, e.g.
a local repository). With `W` the chosen root:

```bash
W=$HOME/pankti-work; bash setup/fetch-artifacts.sh $W
P=$W/data/pankti-data-v1/pankti-data/pdfbox/pankti-collected-object-profiles   # the authors' profiles
G=$W/data/pankti-data-v1/pankti-data/pdfbox/pankti-generated-junit-tests/tests # the authors' generated tests
E=$W/src/pankti-experiments-2021/pdfbox                                       # their Descartes reports and run.sh
I=results/04-workload/full/profiles/invoked-methods.csv; T=results/01-paper-vs-artifacts/authors_report_vs_paper.csv
T3=analysis/paper/table3_pdfbox.csv

# Track A: the paper against the authors' artifacts
python analysis/check_paper_table3.py $T3 results/01-paper-vs-artifacts/paper_table3_checks.txt
python analysis/compare_authors_report.py $E $P/invoked-methods.csv $T
python analysis/profile_stats.py $P results/01-paper-vs-artifacts/authors_profile_stats \
       --listing $W/data/pankti-data-v1.listing.csv pankti-data/pdfbox/pankti-collected-object-profiles/
# #TARGET with the authors' tools (needs a PDFBox checkout and pankti-extract, see scripts/pankti/extract-targets.sh)
bash scripts/pdfbox/checkout.sh $W/work/pdfbox
bash scripts/pankti/extract-targets.sh $W/src/pankti $W/work/pdfbox $E/descartes/before $W/work/targets
python analysis/count_targets.py $W/work/targets $E/descartes/before $P/invoked-methods.csv results/02-descartes-before/targets_authors_reports
python analysis/compare_descartes_runs.py results/02-descartes-before/descartes_before $E/descartes/before \
       results/02-descartes-before/descartes_before_vs_authors --labels reproduction authors --table3 $P/invoked-methods.csv
# our Descartes "after" run against the authors' published one (whole modules)
python analysis/compare_descartes_runs.py $W/data/pankti-data-v1/pankti-data/pdfbox/descartes-pseudo-tested-method-reports/after \
       results/07-descartes-after/reproduction results/07-descartes-after/reproduction_vs_authors_published \
       --labels authors-published reproduction --table3 $I --only-b
# Sections V.A and V.B, prediction check, on the authors' published tests
python analysis/pankti_status.py results/02-descartes-before/descartes_before results/07-descartes-after/authors $P/invoked-methods.csv \
       results/07-descartes-after/pankti_status_authors --table3 $T --control results/07-descartes-after/none
python analysis/failure_analysis.py $G results/06-test-execution/authors/test_outcomes_tests.csv.gz $I \
       results/08-failure-analysis/failure_analysis_authors --table3 $T3
python analysis/prediction_check.py $G results/06-test-execution/authors/test_outcomes_tests.csv.gz results/07-descartes-after/authors $I \
       results/08-failure-analysis/prediction_check_authors --table3 $T3 --sources $W/work/pdfbox
```

The same two analyses on this reproduction's tests take, instead of `$G`, the `generated-tests` artifact of a
generate-tests run, unpacked (`zstd -dc generated-tests.tar.zst | tar -x`), with `results/06-test-execution/reproduction` and
`results/07-descartes-after/reproduction`. The run-time check of the cache lookups (`analysis/java/CacheLookupCheck.java`) gives its
command in its header.

### 3. The full pipeline on GitHub Actions

Each stage is one workflow, started from the Actions tab or with `gh workflow run <workflow> -f <input>=<value>`;
every input has a description and a default. Each job records its runner image, CPU, memory and fonts
(`env-report.txt`) and uploads its outputs as artifacts.

| Workflow | Stage | Main inputs (default) | Duration | Run used in the report |
|---|---|---|---|---|
| `env-check.yml` | toolchain, PDFBox 2.0.21 build and test suite | - | 8 min | 38548431201 |
| `descartes-before.yml` | Descartes on the original test suite, one job per module | `modules`, `threads` (1) | 71 min (pdfbox) | 39409510406, 39415980930 |
| `production-run.yml` | PANKTI plugin, Glowroot, pdfbox-app, the authors' workload | `mode` (dry-run / smoke / full), `font_set`, `font_cache` | 18 min (full) | 39444526027; sensitivity 39756523874, 39756528629 |
| `generate-tests.yml` | pankti-generate on our profiles and on the authors' | `profiles_run_id`, `generator_commit` (`7afc584`) | 12-22 min | 39581267651 (authors' profiles; its reproduction job failed), 39588027907 (reproduction) |
| `assess-tests.yml` | generated tests integrated into PDFBox, 5 separate runs | `tests_run_id`, `runs` (5) | 22 min | 39644913295 |
| `descartes-after.yml` | Descartes with the passing generated tests (ours, the authors', none) | `tests_run_id`, `sources` | 28 min | 39747040848 |

Notes:
- A stage that reads the output of an earlier one takes its run ID as input. Artifacts are kept 3 to 14 days
  (`retention-days`), so the default run IDs stop working after that: rerun the earlier stage first. The outputs used
  in the report are committed under `results/`.
- Every job fits in the 6-hour limit of GitHub-hosted runners (timeouts set to 350 minutes); the longest is the
  pdfbox job of `descartes-before`. A full pass of the pipeline takes about 3 hours of runner time.

### Windows laptop (development only)

The measurements were all made on the Linux runners (assumption A5). For local development on Windows without
administrator rights, `setup/windows/install-tools.ps1 -Dest <dir>` installs a portable toolchain (JDK 11.0.8,
Maven 3.6.3, gh, uv, Python 3.11 with the pinned packages) and `setup/windows/env.ps1` / `source setup/env.sh <dir>`
(Git Bash) set the session environment. Descartes on one module and the instrumentation can also be run locally:

```bash
bash scripts/pdfbox/checkout.sh pdfbox && bash scripts/pdfbox/patch-build.sh pdfbox
bash scripts/pdfbox/add-descartes-profile.sh pdfbox
bash scripts/pdfbox/run-descartes.sh pdfbox fontbox out/fontbox            # about one minute
python analysis/compare_descartes_runs.py out/fontbox/methods.json $E/descartes/before/fontbox out/cmp --labels mine authors

bash scripts/pankti/build-plugin.sh $W/src/pankti results/targets.csv out/plugin   # needs pandas + numpy
bash scripts/glowroot/install-glowroot.sh out/glowroot out/plugin/pankti-plugin.jar
bash scripts/pdfbox/build-app.sh pdfbox out/app
bash scripts/glowroot/check-agent.sh out/glowroot/glowroot out/app/pdfbox-app-2.0.21.jar out/agent
python analysis/compare_jars.py out/app/pdfbox-app-2.0.21.jar $W/src/pankti-experiments/pdfbox/execution/pdfbox-app-2.0.21.jar
```

## Documentation

- [docs/descartes.md](docs/descartes.md): how pseudo-tested methods are computed, and how the results compare with
  the authors'.
- [docs/instrumentation.md](docs/instrumentation.md): what PANKTI's instrumentation records, how it is built and
  installed, and its known limitations.
- [docs/generation.md](docs/generation.md): which pankti-generate version and why, how the tests are counted, how they
  are added to PDFBox.
- [docs/execution.md](docs/execution.md): how the generated tests are run and their outcomes counted.
- [docs/failures.md](docs/failures.md): why generated tests fail, when they improve the test suite, and how the
  final status follows from the observed values.
- [docs/experiments.md](docs/experiments.md): research log of every experiment (objective, method, configuration,
  outcome, interpretation, limitations).
- [docs/deviations.md](docs/deviations.md): one-page overview of every deviation from the paper's protocol, with links
  to the assumptions and discrepancies.
- [docs/assumptions.md](docs/assumptions.md): every simplifying assumption, with its justification, expected impact and
  validation.
- [docs/discrepancies.md](docs/discrepancies.md): differences between the paper, the authors' artifacts and this
  reproduction.
- [docs/environment.md](docs/environment.md) and [docs/artifacts.md](docs/artifacts.md): toolchains, external inputs,
  versions and checksums.
- [docs/journal.md](docs/journal.md): dated work log.
- [results/README.md](results/README.md): what each results folder holds and which run or script produced it.

## Deviations from the original setup (summary)

- The PDFBox 2.0.21 test build needs four build-only adjustments today (dead download URLs, one test that depends on
  execution order). No library or test code is changed (A1).
- The test keystore shipped with PDFBox 2.0.21 expired in June 2026. The two test classes that use it are excluded
  from the Descartes runs. This only affects the `examples` module, which contains no target (A2).
- All measured runs execute on Linux (GitHub Actions) with the authors' JDK; the Windows laptop is used for development
  only (A5).
- The Descartes "after" runs mutate only the 22 classes that declare the effective targets, with all the tests of
  the module (A21); a control run without generated tests gives the full run's classification for 460 of the 465
  methods of these classes.

See [docs/deviations.md](docs/deviations.md) for the full list.

## Attribution

This repository runs, without modifying them, the tools and data of the original study: PANKTI and its experiment
repository (ASSERT-KTH), the replication data on Zenodo (record 4298605), Apache PDFBox 2.0.21, PIT and Descartes,
Glowroot and XStream, each under its own license. The paper is cited at the top of this page.
