# Instrumentation (PANKTI + Glowroot)

PANKTI observes the target methods while PDFBox runs its workload (paper, Section II.D). For every invocation of a
target it serialises the receiving object, the arguments and the returned value with XStream: this triple is an
*object profile*. This page describes how the reproduction builds and installs the instrumentation, and what the
PANKTI code of the paper's period actually records, as far as it matters for the numbers of Table III.

## Frozen target list

`results/targets.csv` is the list of methods to instrument. It is a byte-for-byte copy of
`results/day2/instrumentation-candidates-pdfbox.csv`: the 138 methods that pankti-extract and `find-pseudo-tested.py`
obtain from the authors' Descartes "before" reports (assumption A8 in [assumptions.md](assumptions.md)). Its sha256 is
in `results/targets.sha256`, and every run of the `production-run` workflow records it. The list uses PANKTI's own
column format (`visibility, parent-FQN, method-name, param-list, ...`), which is what `instrument.py` reads.

## How the instrumentation works (PANKTI commit `0fddf27`)

`pankti-instrument` is a Glowroot plugin. `instrument.py` copies the template `MethodAspect0.java` once per target
(`MethodAspect1` ... `MethodAspect138`), filling in the class, method name and parameter types of a Glowroot
`@Pointcut`, and lists the new classes in `META-INF/glowroot.plugin.json`. Glowroot weaves the advice into the target
methods when their classes are loaded.

For one target, the generated advice does the following:

| Event | What is written (directory `/tmp/pankti-object-data/`, hard-coded) |
|---|---|
| `@OnBefore` (method entry) | If the method is still under the size threshold: the receiving object, appended to `<method>-receiving.xml`, and the argument array, appended to `<method>-params.xml`. |
| `@OnReturn` (normal exit) | If still under the threshold: the returned value, appended to `<method>-returned.xml`, and the size of this profile (growth of the three files) appended to `<method>-object-profile-sizes.txt`. Then the invocation counter in `<method>-count.txt` is incremented, and on the first invocation the target's row is added to `invoked-methods.csv`. |
| `@OnThrow` (exception) | Nothing. The call is not counted, and the receiving object and arguments written at entry stay without a returned value. |

Consequences for the metrics (checked in the code, `discrepancies.md` §9):
- **#INVOCATIONS** is the value in `-count.txt`. The file is read and incremented at every return, so the count is
  cumulative over the 50 separate JVM launches of the workload. Calls that end with an exception are not counted.
- **#COLLECTED** is the number of lines of `-object-profile-sizes.txt`.
- **Size threshold:** collection for a method stops for good once one of its three XML files reaches 200 MiB
  (`file.length() / (1024 * 1024) >= 200`). The check reads the files on disk, so it is also cumulative over JVM
  launches. Invocations are still counted afterwards, which is why #COLLECTED can be lower than #INVOCATIONS. The
  authors' data confirms it: each of the 19 methods with #COLLECTED < #INVOCATIONS has an XML file of at least
  200 MiB (`results/day1/authors_profile_stats.txt`).
- XStream uses a few custom converters (Thread, ThreadGroup, Inflater, Cleaner); a serialisation error is logged and
  that part of the profile is skipped.

### Known limitations of this version (hypotheses to measure on the workload)

The receiving object and arguments are written at entry and the returned value at exit, into separate files that
pankti-generate later pairs by position. The pairing can shift when:
1. a call throws (entry written, no exit), see above;
2. a target calls itself, directly or through other methods (entries of the inner call are written between the entry
   and the exit of the outer one);
3. the threshold is crossed between the entry and the exit of a call (entry written, exit skipped);
4. the serialisation of one part fails.

In addition, the size of a profile is computed as the growth of the files between entry and exit, held in one static
field per aspect: nested calls of the same target record wrong sizes. The authors changed this design in December
2020, after the PDFBox run (PANKTI issues #39/#40). The reproduction keeps the original behaviour, as in the paper,
and measures it: for every method, the number of XML fragments in the receiving, params and returned files is
compared with #COLLECTED (Day 4).

## Build and installation

| Step | Script | Checks |
|---|---|---|
| Plugin | `scripts/pankti/build-plugin.sh <pankti> results/targets.csv <out>` | runs the authors' `instrument.py` on a copy of the sources; one aspect per target, all listed in `glowroot.plugin.json`, all present in the jar (`checks.txt`); `aspects.csv` maps each aspect to its target |
| Glowroot | `scripts/glowroot/install-glowroot.sh <dir> <plugin.jar>` | Glowroot 0.13.6 (the plugin API version of PANKTI), sha256 pinned; default configuration (assumption A13) |
| Application | `scripts/pdfbox/build-app.sh <pdfbox> <out>` | `pdfbox-app-2.0.21.jar` built from the tag (assumption A12); size and sha256 in `app-jar.txt` |
| Agent check | `scripts/glowroot/check-agent.sh <glowroot> <app.jar> <out>` | pdfbox-app started under the agent without a command: Glowroot starts without warnings, registers the plugin `panktiplugin`, and no profile is written. The check fails if the plugin is missing (tested). |

The `production-run` workflow runs these steps on the Linux runner (mode `dry-run`); the workload modes are added on
Day 4.

## Results of the dry run

Run [39431056888](https://github.com/Ahmeddhibi19/Pr-Benoit-test/actions/runs/39431056888) (2026-10-20), outputs in
`results/day3/production_dry_run/`:

| Check | Result |
|---|---|
| Target list used | sha256 `5ee6736d...`, the frozen `results/targets.csv` |
| Plugin (PANKTI `0fddf27`) | 138 aspects generated, 138 listed in `glowroot.plugin.json`, 138 aspect classes in the jar (`checks.txt`, `aspects.csv`) |
| Glowroot 0.13.6 | starts on Java 11.0.8 (AdoptOpenJDK / Linux) without warnings or errors, registers the plugin `panktiplugin` |
| pdfbox-app | built from tag 2.0.21: 9,890,413 bytes (the authors' jar: 9,890,400) |
| Agent check | 5 / 5 (`agent-checks.txt`); no profile written, as expected without a command |

**The app jar is the same as the authors'.** `analysis/compare_jars.py` (`results/day3/app_jar_vs_authors.txt`): the two
jars have the same 5,786 entries, all 5,644 class files are byte-identical, and the only differences are the build
metadata (`MANIFEST.MF`, the copyright year in `NOTICE`, the build date in `pom.properties`). The authors' jar was
therefore built from tag 2.0.21 with the same JDK, on 2020-09-21. A build on the Windows laptop differs in 118 text
resources (CMap and AFM files): Git checks text files out with Windows line endings there, which is one more reason
to run the workload on Linux only.

The first dry run (39428845392) failed in the Glowroot installation step: the script resolved the plugin path after
changing directory. Fixed in `install-glowroot.sh` and checked by replaying the remaining steps with the workflow's
relative paths.

## Workload

`production-run` mode `full` fetches the authors' workload (`scripts/pankti/get-workload.sh`: `run.sh`, the six PDFs
with their sha256, the authors' `execution.log`, from `pankti-experiments` at `7bc7791`) and runs it with
`scripts/pankti/run-workload.sh`: empty profile directory, deleted font cache, `run.sh` with only its two jar paths
replaced (assumption A14), 50 JVM launches. The job then computes the metrics (`analysis/profile_stats.py
--fragments`), compares each command's outcome with the authors' log (`analysis/workload_log.py`), uploads the
summaries and archives the raw profiles (about 5.7 GB, 326 MB compressed, kept 3 days) for test generation.
Mode `smoke` runs `PDFToImage` on one PDF twice and checks that isFill is recorded and that counts accumulate.

Results (run 39444526027, `results/day4/full/`): see [experiments.md](experiments.md) (E11) and
[discrepancies.md](discrepancies.md) (item 20). Summary against Table III:

| | Paper | Reproduction |
|---|---|---|
| Commands with the same outcome as the authors' log | | 50 / 50 (39 ok, 9 errors on `000809.pdf`, 2 usage) |
| #EFF_TARGET | 46 | 47 (the 46 + `TrueTypeFont.getOS2Windows`) |
| #INVOCATIONS / #COLLECTED / #UNIQUE | 121,175 / 57,563 / 13,851 | 122,384 / 58,672 / 14,679 |
| Methods hitting the 200 MB threshold | 19 | 19 |
| Smallest / largest profile, total | 158 B / about 55 MB / 5.5 GB | 158 B / 54.7 MiB / 5.30 GiB |
| isFill | 30,944 / 30,944 / 1, 158 B | identical |
| Rows identical to Table III (INV / COLL / UNIQ) | | 41 / 40 / 38 of 46; the others are font methods |
