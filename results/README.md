# Results

Outputs of the CI runs and of the analysis scripts. The folders are named after the stage of the work in which they
were produced (`day1` to `day8`, the order of the pipeline); this table says what each one holds. Experiment numbers
refer to [docs/experiments.md](../docs/experiments.md), run numbers to GitHub Actions runs of this repository.
Large raw outputs (`methods.json`, `mutations.json`, test verdicts) are stored compressed (`.gz`).

| Folder | Stage | Contents | Produced by | Experiments |
|---|---|---|---|---|
| [`day1/`](day1/) | the paper against the authors' artifacts | consistency checks of Table III; the authors' Descartes reports summarised and compared with Table III; profile facts recomputed from their raw data; PDFBox test suite on CI (`env-check/`) | `check_paper_table3.py`, `compare_authors_report.py`, `summarize_descartes_reports.py`, `profile_stats.py`; run 38548431201 | E1, E2 |
| [`day2/`](day2/) | Descartes "before", targets | Descartes reports of this reproduction (`descartes_before/`, 1 thread; `descartes_before_pdfbox_4_threads/`) and their comparison with the authors'; #TARGET with the authors' tools on their reports and on ours; the instrumented candidates | `descartes-before.yml` (runs 39409510406, 39415980930), `extract-targets.sh`, `count_targets.py`, `compare_descartes_runs.py` | E5-E7 (E3, E4: local checks, outputs not stored) |
| [`targets.csv`](targets.csv) | frozen target list | the 138 targets instrumented from Day 3 on, with its sha256 | `extract-targets.sh` | E7 |
| [`day3/`](day3/) | instrumentation | plugin, Glowroot and agent checks (`production_dry_run/`); the pdfbox-app jar compared with the authors' | `production-run.yml` dry-run (run 39431056888), `compare_jars.py` | E8 |
| [`day4/`](day4/) | workload, Table III columns 1-3 | smoke and full workload runs (per-method counts and sizes, profile statistics, command outcomes, environment); the authors' profile metrics; Table III comparison | `production-run.yml` smoke / full (runs 39442198598, 39444526027), `profile_stats.py`, `compare_table3.py`, `workload_log.py` | E9-E11 |
| [`day5/`](day5/) | test generation, Figure 5 | Figure 5; tests generated from the authors' profiles compared with their published tests; counts of our generated tests; sample generated tests | `generate-tests.yml` (runs 39581267651, 39588027907), `figure5.py`, `count_generated_tests.py`, `compare_generated_tests.py` | E12-E15 |
| [`day6/`](day6/) | test execution, Table III columns 4-6 | verdicts of every generated test over 5 runs (ours, the authors'), failure types, Table III columns; `run-39641425498-split-bug/` is a flawed run kept as evidence, not a result | `assess-tests.yml` (run 39644913295), `test_outcomes.py`, `table3_execution.py` | E16-E18 |
| [`day7/`](day7/) | Descartes "after", PANKTI_STATUS | Descartes reports after adding our tests, the authors' tests, and none (control); PANKTI_STATUS; restriction check; comparisons; mutant details of the paper's examples | `descartes-after.yml` (run 39747040848), `pankti_status.py`, `table3_status.py`, `compare_descartes_runs.py`, `mutant_tests.py` | E19, E20 |
| [`day8/`](day8/) | why tests fail, V.B, prediction check, font sensitivity | failure classification and prediction check for both test sets; run-time check of the cache lookups; `sensitivity/`: the two font sensitivity runs | `failure_analysis.py`, `prediction_check.py`, `CacheLookupCheck.java`, `production-run.yml` (runs 39756523874, 39756528629), `sensitivity_table.py` | E21-E23 |
| [`comparison/`](comparison/) | summary | one line per published number (paper / authors' artifacts / reproduction, with its source file); Table III row by row, with a figure | `comparison.py`, `figure_table3.py` | all |

Each `.txt` file is the human-readable summary of the `.csv` next to it; each run folder has the `env-report.txt` of
its runner (image, CPU, memory, JDK, Maven, fonts).
