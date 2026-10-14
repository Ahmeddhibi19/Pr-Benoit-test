# External artifacts

Everything the reproduction downloads, with the exact version and a checksum. `setup/fetch-artifacts.sh` fetches the
authors' artifacts. The CI scripts fetch the toolchain and PDFBox.

## Subject

| Artifact | Version | Identifier |
|---|---|---|
| Apache PDFBox sources | tag `2.0.21` | commit `fa8029d80e39ff4febd1ce0d6ecc628bf2970ca0` (tag object `159cb7f5`) on github.com/apache/pdfbox |

Build-only change: the two IPA font URLs of `pdfbox/pom.xml` (PDFBOX-5005), see `scripts/pdfbox/patch-build.sh`.

## Authors' tool and experiment repositories

The `castor-software` organisation was renamed; both repositories now live under `ASSERT-KTH`.

| Repository | Commit | Date | Role |
|---|---|---|---|
| ASSERT-KTH/pankti | `0fddf273a8a6acbaba51a318fcc7fc6e5b84058f` | 2020-10-26 | tool version used for the PDFBox run (last master commit before 2020-11-03) |
| ASSERT-KTH/pankti | `326a7533e6dd9600f7ed0ce5d2d6c6b2a26ebf71` | 2021-03-14 | last commit before paper v4 (fallback, sensitivity check) |
| ASSERT-KTH/pankti-experiments | `7bc7791e8cfbdee2268e077e9d289137541dc3a6` | 2020-11-03 | "Update PDFBox numbers": state of the PDFBox results |
| ASSERT-KTH/pankti-experiments | `1d8f9aa150d9bfd99e3a38c987025cd6159494da` | 2021-06-08 | last commit before paper v4; adds the 2020-11-19 Descartes runs |

Only `README.md` and `pdfbox/` of pankti-experiments are checked out (about 2.8 GB per snapshot).

Content of `pdfbox/` used here:

| Path | Content |
|---|---|
| `README.md` | summary counts (129 instrumented, 46 invoked, test outcome 17 / 11 / 18) |
| `execution/run.sh` | the workload: 10 pdfbox-app commands on 5 PDFs |
| `execution/execution.log` | console output of the workload run (2020-11-03) |
| `execution/report.csv` | per-method counts, executed tests and Descartes classification |
| `execution/pdfbox-app-2.0.21.jar` | self-built app jar, 9,890,400 bytes, sha256 `a9327e88ca1a98f0...` |
| `descartes/before/<module>/.../methods.json` | Descartes runs of 2020-09-21 on 6 modules |
| `descartes/after/{fontbox,pdfbox}/.../methods.json` | Descartes runs with the generated tests (2020-10-04/05, 10-15, 11-19) |
| `org/**/Test*PanktiGen.java`, `resources/` | 15 generated test classes and 1,533 resource files |
| `data/report-file-sizes.csv`, `data/find-file-sizes.py` | profile sizes |
| `time-coverage-version.md` (2021 snapshot only) | test-suite time and coverage, 2.0.22 note |

A summary of all Descartes reports is in `results/day1/authors_descartes_reports.csv`.

## Workload documents

GovDocs1 files, as shipped in `pdfbox/execution/workload/` of the experiments repository.

| File | Bytes | sha256 (first 16 hex digits) | Role |
|---|---|---|---|
| 000752.pdf | 496,878 | `19fff50000cdb8af` | input |
| 000753.pdf | 160,991 | `cc47261dc72cfa43` | input |
| 000809.pdf | 32,034 | `13552b69646b840a` | input (already encrypted) |
| 000810.pdf | 30,055 | `b156e9a6c16d7228` | input |
| 000817.pdf | 1,471,951 | `f4d66338663f5b17` | input |
| 000142.pdf | 445,338 | `bdd62b32cf5211cd` | overlay page for `OverlayPDF` |

## Replication data (Zenodo)

| Record | DOI | File | Bytes | md5 |
|---|---|---|---|---|
| 4298605 (version 1, 2020-11-30) | 10.5281/zenodo.4298605 | `pankti-data.zip` | 1,374,537,485 | `9c902f3e2342338192197034413d70c0` |

The archive holds 5,064 files, 11.2 GB uncompressed, under `pankti-data/` (README, `broadleaf/`, `jitsi-jicofo/`,
`pdfbox/`). The `pdfbox/` part:

| Folder | Files | Size | Content |
|---|---|---|---|
| `descartes-pseudo-tested-method-reports/` | 8 | 79.5 MB | Descartes `methods.json`, before (6 modules) and after (fontbox, pdfbox) |
| `execution-workload-reproduction/` | 7 | 2.6 MB | `run.sh` and the 6 workload PDFs |
| `pankti-collected-object-profiles/` | 231 | 5,898.8 MB | `invoked-methods.csv` and, per method, count, sizes, receiving, params, returned |
| `pankti-generated-junit-tests/` | 4,492 | 5,205.7 MB | generated test classes and resource files |

`setup/extract_zip.py` extracts `pdfbox/` without the raw `-receiving/-params/-returned.xml` files (136 files,
177 MB). Info-ZIP's `unzip` can list this Zip64 archive but does not match file patterns in it.

The paper cites the concept DOI 10.5281/zenodo.4298604, which now resolves to version 2 (record 4700393,
4.09 GB). Version 1 is used here because it is the one contemporary with the PDFBox run. The archive is listed
before extraction, and only `pdfbox/` is extracted, without the raw `-receiving/-params/-returned.xml` profiles
(they are extracted later, when needed).

## Tools

| Tool | Version | Use |
|---|---|---|
| Glowroot | 0.13.6 (`glowroot-0.13.6-dist.zip`) | agent hosting the PANKTI instrumentation plugin (plugin API 0.13.6) |
| PIT + Descartes | 1.4.x + 1.2.x (set up on Day 2) | pseudo-tested methods, 21 mutation operators as in the authors' reports |
| JaCoCo | 0.8.5 | coverage (optional, Table II) |
