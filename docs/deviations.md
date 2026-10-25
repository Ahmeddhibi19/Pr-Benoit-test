# Deviations from the original study

One line per point where this reproduction does something other than, or more precisely than, the paper describes.
Each line links to the full entry: the assumption (A-number in [assumptions.md](assumptions.md): original
requirement, problem, simplification, justification, expected impact, validation) and, where the deviation explains
a difference in the results, the discrepancy item (§ in [discrepancies.md](discrepancies.md)).

## Environment and tools

| Paper / original setup | This reproduction | Effect on the results | See |
|---|---|---|---|
| PDFBox 2.0.21 builds and its tests pass (2020) | four build-only adjustments (dead download URLs, one order-dependent test); no library or test code changed | none on the code studied; 1,678 tests run | A1, §12 |
| Descartes runs on the whole test suite | the two test classes that use the test keystore (expired in June 2026) are excluded | `examples` loses its coverage; it holds no target | A2 |
| Descartes configuration not given | PIT 1.4.10, Descartes 1.2.6, the 21 operators of the authors' reports, **1 thread**, classes per module | same classification as the authors for 6,276 of 6,373 methods; with 4 threads, pdfbox results are wrong (#TARGET 91) | A3, A4, §6, §14, §16 |
| Machine not described | GitHub-hosted Linux runners, AdoptOpenJDK 11.0.8 (the authors' log), Maven 3.6.3, `fonts-liberation`; environment recorded by every run | the OS changes 4 fontbox methods; the fonts and the font cache change the font methods of Table III | A5, §15, §27 |
| PANKTI version not given | `0fddf27` for extraction and instrumentation; `7afc584` with `setUpXStream()` enabled for generation (the version of the published tests) | generation reproduces the 13,851 published tests exactly | A6, A9, A17 |
| pdfbox-app jar not given | rebuilt from the 2.0.21 tag | same 5,644 class files as the authors' jar | A12 |

## Protocol

| Paper / original setup | This reproduction | Effect on the results | See |
|---|---|---|---|
| 138 targets from Descartes | target list frozen from the authors' "before" reports | our own reports also give 138 (137 in common) | A8, §5 |
| Workload: 10 commands on 5 PDFs | the authors' `run.sh`, only its two jar paths changed; 50 / 50 command outcomes as in their log | none on the commands; 11 of the 50 calls fail in both runs | A14, §10, §19 |
| Font cache not mentioned | the main run deletes the PDFBox font cache first; the authors' log shows they had one | one extra target and more `getName` profiles; with a pre-built cache, the paper's 46 targets exactly | A24, §20, §27 |
| #UNIQUE: unique profiles | computed on the exact text of the XML fragments, as pankti-generate does | validated on the authors' data (46 / 46 rows) | A15, §9 |
| Nesting depth 36 (not defined) | maximum XML element depth | 73 in the authors' data and in ours; 36 not reproduced | A16, §17 |
| "Tests run 5 times" | 5 separate JVM runs; passing = passes in all 5; a test that did not run is never counted as passing | 0 flaky tests; the paper's #PASSING counted 11,613 tests that were not executed (they do pass) | A11, A19, §2, §21 |
| The authors' published tests | run here after adding a missing `import` in 18 classes | their #PASSING / #FAILING reproduced for all 46 rows | A18, A20, §22 |
| "Well-tested": no longer pseudo-tested | tested or partially tested (Descartes) | gives the 46 statuses of Table III from the authors' reports | A10, §3, §4 |
| Descartes "after" on the test suite with the new tests | passing tests only; mutation of the 22 classes of the targets, all tests of the module; a control run without generated tests | 460 / 465 methods as the full run; one target (`getXrefType`) has an unstable "before" status | A21, A22, §7, §23, §24 |
| Failing tests analysed by hand on a sample | every failing test classified from its message and observed value, checked in the code and at run time | different mechanism than the paper for 9 rows | A23, §25, §26 |

Every result in the report is labelled as published (paper), artifact (the authors' data) or measured (this
reproduction); [`results/comparison/comparison.txt`](../results/comparison/comparison.txt) gives, for each published
number, the three values side by side.
