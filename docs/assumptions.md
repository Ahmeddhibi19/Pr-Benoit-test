# Simplifying assumptions and deviations

Each entry states what the paper (or the authors' artifacts) requires, what prevented doing exactly that, what was
done instead, and how the choice is checked. Entries are added when a decision is taken; the outcome of the check is
filled in once it is known. Related observations (differences between the paper and the authors' artifacts) are in
[discrepancies.md](discrepancies.md).

| # | Topic | Status |
|---|---|---|
| A1 | [Build-only adjustments of PDFBox 2.0.21](#a1-build-only-adjustments-of-pdfbox-2021) | validated |
| A2 | [Test classes excluded from the Descartes runs](#a2-test-classes-excluded-from-the-descartes-runs) | validated, effect measured |
| A3 | [PIT and Descartes versions, operators and threads](#a3-pit-and-descartes-versions-and-operators) | validated |
| A4 | [Classes analysed per module](#a4-classes-analysed-per-module) | validated |
| A5 | [Execution environment](#a5-execution-environment) | partly validated |
| A6 | [PANKTI version](#a6-pankti-version) | in use |
| A7 | [Replication data version](#a7-replication-data-version) | validated |
| A8 | [Source of the frozen target list](#a8-source-of-the-frozen-target-list) | decided, checked |
| A9 | [Building pankti-extract today](#a9-building-pankti-extract-today) | validated |
| A10 | [Meaning of "well-tested"](#a10-meaning-of-well-tested) | validated on the authors' data |
| A11 | [What #PASSING counts](#a11-what-passing-counts) | validated (E17, E18) |
| A12 | [The pdfbox-app jar](#a12-the-pdfbox-app-jar) | validated (identical content) |
| A13 | [Glowroot configuration](#a13-glowroot-configuration) | in use |
| A14 | [The workload script](#a14-the-workload-script) | in use |
| A15 | [How #UNIQUE is computed](#a15-how-unique-is-computed) | validated on the authors' data |
| A16 | [Nesting depth](#a16-nesting-depth) | open (the paper's value is not reproduced) |
| A17 | [Generator version](#a17-generator-version) | validated (13,851 / 13,851 tests identical) |
| A18 | [Integration of the generated tests](#a18-integration-of-the-generated-tests) | validated locally |
| A19 | [How the tests are run and counted](#a19-how-the-tests-are-run-and-counted) | in use |
| A20 | [Running the authors' published tests](#a20-running-the-authors-published-tests) | in use |
| A21 | [Descartes "after": analysed classes](#a21-descartes-after-analysed-classes) | validated (460 / 465 methods; the 5 others come from unstable tests) |
| A22 | [Which generated tests are added](#a22-which-generated-tests-are-added) | in use |
| A23 | [Failure causes classified from the evidence of every test](#a23-failure-causes-classified-from-the-evidence-of-every-test) | in use |
| A24 | [Font sensitivity runs](#a24-font-sensitivity-runs) | in use |

## A1. Build-only adjustments of PDFBox 2.0.21

| Item | Explanation |
|---|---|
| Original requirement | Build PDFBox 2.0.21 and run its test suite (1,675 tests according to the authors). |
| Problem | Six years later the unmodified build fails: two IPA font URLs return 404 (PDFBOX-5005), the Isartor archive returns HTTP 403, a certificate-policy PDF is not served to CI runners, and `PDAcroFormTest` depends on test execution order (it writes into a directory it does not create). |
| Simplification | `scripts/pdfbox/patch-build.sh`: the same files from other locations (sha512 checked by the build), and the missing directory created before the build. No library or test code is changed. |
| Justification | The downloaded files are byte-identical to the originals; creating an output directory does not change any test's logic. |
| Expected impact | None on the code under study. |
| Validation | CI run 38542374578: 1,678 tests, 0 failures, 13 errors that are all explained by A2. The same patched build passes locally (fontbox and pdfbox modules, 558 tests). |
| Reporting | Report section on the experimental setup; observation on build decay in the reflections. |

## A2. Test classes excluded from the Descartes runs

| Item | Explanation |
|---|---|
| Original requirement | Run Descartes on the original test suite (PIT requires a green suite). |
| Problem | The keystore shipped with the PDFBox 2.0.21 tests expired on 2026-06-05: 13 tests of the `examples` module fail with `CertificateExpiredException`. |
| Simplification | Exclude the two test classes that contain them, `TestCreateSignature` and `CreatePDFATest` (`scripts/pdfbox/descartes-excluded-tests.txt`). PIT excludes whole classes, so 10 passing tests go too (23 of 1,678 tests). |
| Justification | The excluded tests only exercise the `examples` module. None of the 138 targets and none of the 46 effective targets is in that module (`results/02-descartes-before/targets_authors_reports.txt`). Setting the clock back to 2020 was the alternative; it would affect every test that reads the date. |
| Expected impact | Methods of `examples` lose their coverage. No effect on fontbox, pdfbox, xmpbox, preflight and tools. |
| Validation | Measured in the "before" run: `examples` has 3 pseudo-tested methods instead of 39 and 308 not-covered instead of 228 (the module has only 24 tests, 23 of them excluded). fontbox, xmpbox, preflight and tools are identical to the authors' reports method by method, pdfbox differs on 17 of 4,438 methods for unrelated reasons (see [descartes.md](descartes.md)). |
| Reporting | Limitations; #TARGET is unaffected because pankti-extract keeps no method of `examples` that is pseudo-tested in the authors' reports. |

## A3. PIT and Descartes versions and operators

| Item | Explanation |
|---|---|
| Original requirement | Find pseudo-tested methods with Descartes. The paper gives no version or configuration. |
| Problem | The versions are not documented anywhere. |
| Simplification | pitest-maven 1.4.10 with Descartes 1.2.6, the 21 mutation operators listed in every methods.json of the authors, PIT's default timeouts and a single analysis thread (PIT's default). |
| Justification | The authors' reports are dated 2020-09-21. Descartes 1.2.6 (October 2019) was the latest release at that date (1.3 is from December 2020) and is built against PIT 1.4.10. The operator list is read from the reports. One thread: with 4 threads, pdfbox tests that share files under `target/test-output` and download test data during the test produce spurious kills and timeouts (see [descartes.md](descartes.md)); the authors' pdfbox run time (83 min) is consistent with one thread. |
| Expected impact | Small classification differences from non-deterministic tests. |
| Validation | fontbox, xmpbox, preflight, tools: the authors' classification for every method. pdfbox with 1 thread: 4,421 of 4,438 methods identical, 64 timeouts (authors: 62); with 4 threads only 4,202, 310 timeouts, and 25 of the 40 pdfbox targets wrongly "tested". All 46 effective targets are pseudo-tested in the 1-thread run. |
| Reporting | Experimental setup. |

## A4. Classes analysed per module

| Item | Explanation |
|---|---|
| Original requirement | One Descartes run per module, as in the authors' artifacts. |
| Problem | PIT's default `targetClasses` is `<groupId>*` = `org.apache.pdfbox*`, which selects no class in `fontbox` (`org.apache.fontbox`) and `xmpbox` (`org.apache.xmpbox`). |
| Simplification | `targetClasses` is set per module in `scripts/pdfbox/run-descartes.sh`. |
| Justification | The authors' reports contain exactly these packages per module. |
| Expected impact | None. |
| Validation | Same number of methods per module as the authors' reports (fontbox 550, xmpbox 550, preflight 398, tools 126, examples 311; pdfbox in [descartes.md](descartes.md)). |
| Reporting | Experimental setup. |

## A5. Execution environment

| Item | Explanation |
|---|---|
| Original requirement | The paper gives none. The authors' execution log shows Linux with AdoptOpenJDK 11.0.8 and Glowroot 0.13.6. |
| Problem | The authors' machine (fonts, font cache, CPU) is unknown. Several targets are font methods whose invocation counts depend on the installed fonts. |
| Simplification | All measured runs use a GitHub-hosted `ubuntu-22.04` runner with AdoptOpenJDK 11.0.8+10, Maven 3.6.3 and `fonts-liberation` (the font of the paper's Figure 2). Every run records the runner image, CPU, memory and font list. A Windows laptop is used for development and smoke tests only. |
| Justification | Closest available match to the authors' setup that can be re-run by anyone. |
| Expected impact | Font-dependent counts of the workload may differ from the paper (checked in the workload stage). |
| Validation | Descartes: Linux results are identical to the authors' reports, while a local Windows run of fontbox differs on 4 methods, all of them OS-specific font-directory finders (`WindowsFontDirFinder` vs `UnixFontDirFinder`). This confirms that the OS matters and that Linux is the right choice. |
| Reporting | Experimental setup; threats to validity. |

## A6. PANKTI version

| Item | Explanation |
|---|---|
| Original requirement | Use PANKTI as in the paper. The paper names no commit. |
| Problem | PANKTI evolved after the PDFBox run (void methods, profile writing, mocks). |
| Simplification | Commit `0fddf27` (2020-10-26), the last commit before the authors' PDFBox run of 2020-11-03. `326a753` (2021-03-14, last commit before paper v4) is kept as a fallback. |
| Justification | Date of the authors' `execution.log`. |
| Expected impact | Reproduces the behaviour of the tool at the time, including its known limits (profile pairing, discrepancies.md §9). |
| Validation | pankti-extract at this commit, applied to the authors' reports, gives exactly the paper's #TARGET = 138. |
| Reporting | Experimental setup. |

## A7. Replication data version

| Item | Explanation |
|---|---|
| Original requirement | The paper cites the concept DOI 10.5281/zenodo.4298604. |
| Problem | It now resolves to version 2 (4.09 GB), published after the paper's PDFBox numbers. |
| Simplification | Version 1 (record 4298605, 2020-11-30), checked against its md5. |
| Justification | Contemporary with the PDFBox run. |
| Expected impact | None found. |
| Validation | Its PDFBox profiles give exactly the totals of Section IV.C (`results/01-paper-vs-artifacts/authors_profile_stats.txt`). |
| Reporting | Experimental setup. |

## A8. Source of the frozen target list

| Item | Explanation |
|---|---|
| Original requirement | Targets = pseudo-tested methods found by Descartes, filtered by PANKTI. |
| Problem | Time: the schedule required starting the instrumentation before the reproduction's own Descartes run could be fully analysed. |
| Simplification | The target list instrumented from the instrumentation stage on is the one computed from the authors' "before" reports, frozen as `results/targets.csv` (copy of `results/02-descartes-before/instrumentation-candidates-pdfbox.csv`, sha256 in `results/targets.sha256`). The reproduction's own Descartes run is compared with it method by method. |
| Justification | The reproduction's own run gives 138 targets as well, 137 of them in common with the authors' list, and all 46 effective targets (`results/02-descartes-before/targets_own_reports.txt`). |
| Expected impact | One target differs in each direction (`PDFontDescriptor.getFontFile` is instrumented, `PDAnnotation.isNoRotate` is not); neither is an effective target in the paper. |
| Validation | `analysis/compare_descartes_runs.py` and `analysis/count_targets.py` on both sets of reports. `isNoRotate` is not in the frozen list, so whether the workload invokes it was not measured; with the frozen list the workload invokes all 46 effective targets of the paper (E11). |
| Reporting | Methodology. |

## A9. Building pankti-extract today

| Item | Explanation |
|---|---|
| Original requirement | Run pankti-extract at `0fddf27`. |
| Problem | Spoon 8.0.0 declares a snapshot repository that no longer exists, and its JDT dependency pulls Eclipse platform jars through open version ranges. Maven now resolves recent versions, some of them compiled for Java 17 (class file version 61), while the tool runs on Java 11. |
| Simplification | Built as is. The unreachable repository only produces warnings, and the Java 17 classes are never loaded on the code path used. |
| Justification | No dependency was upgraded or pinned, so the tool's own code and its Spoon/JDT versions are unchanged. |
| Expected impact | None observed. The build is not exactly reproducible over time (another resolution could pull other platform versions). |
| Validation | The tool runs on JDK 11.0.8 and gives #TARGET = 138, as in the paper. Two runs give the same candidate list; the full method list has the same content but a different row order (it is written from a hash map). |
| Reporting | Reflections on reproducibility (dependency version ranges). |

## A10. Meaning of "well-tested"

| Item | Explanation |
|---|---|
| Original requirement | Paper, Section III.E, metric 14: after adding the generated tests, a target "is either still pseudo-tested, or is not pseudo-tested anymore. In the latter case, we give it the status of well-tested." |
| Problem | Descartes has two non-pseudo-tested statuses for a covered method: `tested` and `partially-tested`. |
| Simplification | well-tested = `tested` or `partially-tested`. Strict counts (`tested` only) are reported as well. |
| Justification | Follows from the paper's definition. The authors' README splits its 28 well-tested methods into 17 tested and 11 partially tested. |
| Expected impact | None. |
| Validation | With this reading, the authors' last "after" reports give the status printed in Table III for all 46 methods (`results/01-paper-vs-artifacts/authors_report_vs_paper.csv`). |
| Reporting | Methodology. |

## A11. What #PASSING counts

| Item | Explanation |
|---|---|
| Original requirement | #PASSING: generated tests that pass when executed. |
| Problem | The authors' artifacts show that 11,613 of the 11,730 tests of `GlyfSimpleDescript.getFlags` were not executed but are counted as passing in the paper (discrepancies.md §2). |
| Simplification | None: every generated test is executed, and only tests that actually pass are counted. The paper's way of counting is reported next to it. |
| Justification | Measures what the metric claims to measure. |
| Expected impact | #PASSING may be lower than in the paper if some getFlags tests fail. |
| Validation | E17, E18: every generated test was executed in each of the 5 runs (none "not run"); the 11,613 `getFlags` tests all pass, so the authors' tests give the paper's #PASSING, 13,614, as actually measured. |
| Reporting | Results; discussion of the difference. |

## A12. The pdfbox-app jar

| Item | Explanation |
|---|---|
| Original requirement | Run the workload on `pdfbox-app-2.0.21.jar`, as the authors' `run.sh` does. |
| Problem | The authors' jar (9,890,400 bytes, in the experiments repository) is not the one published on Maven Central (9,897,381 bytes): they built it from a local checkout. |
| Simplification | Build the jar from tag 2.0.21 with the same JDK (`scripts/pdfbox/build-app.sh`). |
| Justification | Running a jar built from the documented sources is reproducible; the authors' jar is used only for comparison. |
| Expected impact | None if the contents are the same. |
| Validation | Built on the Linux runner (run 39431056888), the jar has the same 5,786 entries as the authors' jar; all 5,644 class files are byte-identical and only 3 build-metadata entries differ (`results/03-instrumentation/app_jar_vs_authors.txt`). A Windows build also differs in 118 text resources because of line endings. |
| Reporting | Experimental setup. |

## A13. Glowroot configuration

| Item | Explanation |
|---|---|
| Original requirement | Run the workload with the PANKTI plugin inside Glowroot (paper, Section II.G). |
| Problem | No Glowroot configuration file is published; only the version (0.13.6) is known from the authors' execution log. |
| Simplification | Glowroot 0.13.6 with its default configuration; the plugin jar is the only addition. |
| Justification | Nothing indicates a custom configuration; PANKTI's code does not depend on Glowroot settings (it writes its own files). |
| Expected impact | Glowroot's own data (traces, UI) may differ; the files written by PANKTI should not. |
| Validation | Agent check: Glowroot starts without warnings and registers the plugin (`scripts/glowroot/check-agent.sh`); profiles are checked in the workload stage. |
| Reporting | Experimental setup. |

## A14. The workload script

| Item | Explanation |
|---|---|
| Original requirement | The PDFBox workload: 10 command-line features on 5 GovDocs1 PDFs (paper, Section III.B), exactly as in the authors' `run.sh`. |
| Problem | `run.sh` hard-codes two paths of the authors' machine (`/home/user/glowroot/glowroot.jar`, `/home/user/dev/pdfbox/app/target/pdfbox-app-2.0.21.jar`). |
| Simplification | `scripts/pankti/run-workload.sh` copies `run.sh` and replaces only these two lines; the diff is saved with the results (`run-sh.diff`). Commands, order, inputs and the failing file `000809.pdf` are unchanged. Before the run the profile directory is emptied and `~/.pdfbox.cache` is deleted (cold font cache). |
| Justification | Fidelity to the authors' execution, including its failures. |
| Expected impact | None on the commands. The font cache state of the authors' run is unknown (cold is assumed). |
| Validation | Per-command outcomes compared with the authors' `execution.log` (`analysis/workload_log.py`). |
| Reporting | Experimental protocol. |

## A15. How #UNIQUE is computed

| Item | Explanation |
|---|---|
| Original requirement | #UNIQUE: the number of unique object profiles, i.e. the number of tests pankti-generate creates. |
| Problem | Running pankti-generate is the next stage (test generation); the metric is needed when the profiles are collected, and pankti-generate's parser loads whole files in memory. |
| Simplification | `analysis/profile_stats.py --fragments` applies pankti-generate's rule (`ObjectXMLParser`, commit `0fddf27`): top-level XML fragments of the receiving, params and returned files, paired by position, and the number of distinct triples (params only for methods with parameters). Fragments are compared on their exact text; pankti-generate compares them after a deterministic re-serialisation. |
| Justification | Equal texts give equal re-serialisations; XStream writes a given object the same way every time. |
| Expected impact | None found. |
| Validation | On the authors' raw data (5.9 GB), the script gives the #UNIQUE of Table III for all 46 methods (13,851 in total), as well as #INVOCATIONS and #COLLECTED (`results/04-workload/authors_profile_metrics.*`). Unit tests in `tests/test_analysis.py`. The number of tests pankti-generate actually produces is compared in the test-generation stage. |
| Reporting | Methodology. |

## A16. Nesting depth

| Item | Explanation |
|---|---|
| Original requirement | Paper, Section IV.C: "the maximum level of nesting we observe in a collected object profile is 36". |
| Problem | The measure is not defined. On the authors' raw data the maximum depth of XML elements in a profile is 73 (`COSParser.getEncryption`, receiving object); ignoring XStream's `entry` elements gives 72, counting typed elements only gives 51. None gives 36. The paper's other figure, "toUnicode ... nested 13 levels deep" (Section II.D.3), matches the XML depth minus one (14 - 1). |
| Simplification | Report the maximum XML element depth of a fragment (its root element has depth 1), computed the same way on the authors' data and on this reproduction's. |
| Justification | A defined measure applied identically to both data sets allows a like-for-like comparison. |
| Expected impact | The absolute value is not comparable with the paper's 36. |
| Validation | Not possible without the authors' definition. |
| Reporting | Results (as an unreproduced number) and limitations. |

## A17. Generator version

| Item | Explanation |
|---|---|
| Original requirement | Generate one differential unit test per unique object profile with pankti-generate. |
| Problem | The tests the authors published were not produced by the PANKTI commit of their workload run (`0fddf27`): they contain `deserializeObject()` helpers that pankti-generate only writes from `7afc584` (2020-11-12), and 18 of 22 classes have a `setUpXStream()` method whose call is commented out in the generator. |
| Simplification | pankti-generate at `7afc584` with the line that adds `setUpXStream()` enabled (`scripts/pankti/build-generator.sh`, one-line diff saved with each run). The instrumentation stays at `0fddf27`. |
| Justification | `7afc584` is the only change to pankti-generate between the workload run and the authors' last "after" Descartes run; its profile parser is identical to `0fddf27`'s, so the set of tests (#UNIQUE) does not depend on the choice. The setup method registers converters needed to deserialise `Inflater` and `Cleaner` fields. |
| Expected impact | Four classes get a `setUpXStream()` method that the published ones do not have; it only registers converters. |
| Validation | Generated from the authors' own profiles (generate-tests run 39581267651), the 13,851 tests are identical, method by method, to the 13,851 tests the authors published (`results/05-test-generation/authors_generation/`). |
| Reporting | Implementation; observations (the published artifacts mix two tool versions and manual edits). |

## A18. Integration of the generated tests

| Item | Explanation |
|---|---|
| Original requirement | Add the generated tests to the PDFBox test suite; the authors' README: compile with source/target 9 (because of `java.lang.ref.Cleaner`), disable animal-sniffer. |
| Problem | Compiling the whole build for Java 9 also changes the bytecode of the library under test, and PDFBox's `jdkGte9` profile forces `<release>6</release>` on every compilation. One generated class (`GlyfSimpleDescript.getFlags`) has 11,730 tests in a 90 MB source file. |
| Simplification | `scripts/pankti/integrate-tests.sh`: only the test compilation (`default-testCompile`) gets `<release>9</release>`; the library stays at release 6 and animal-sniffer stays enabled. PANKTI's three converters are copied into every test package instead of being imported by hand. Classes with more than 500 tests are split into parts without changing any test (`scripts/pankti/split_test_classes.py`). XStream 1.4.12 is a test dependency of fontbox and pdfbox. |
| Justification | The code that Descartes mutates is compiled exactly as in the original build (class file version 50), while the tests can use the Java 9 API (version 53). Splitting keeps every test and lets all of them be compiled and executed (the authors executed 117 of the 11,730 getFlags tests). |
| Expected impact | None on the library; test classes have different names (`...PanktiGenPartN`) for the split classes. |
| Validation | Local check: 3 classes generated from the authors' profiles, split into 6, compile and their 20 tests pass; library class version 50, test class version 53, animal-sniffer passes. The full test set is compiled and run in the test-execution stage. |
| Reporting | Implementation; limitations. |

## A19. How the tests are run and counted

| Item | Explanation |
|---|---|
| Original requirement | Paper, Section II.F: a generated test is kept if it passes and is not flaky; "we run it 5 times" (footnote 4, citing DeFlaker). #PASSING and #FAILING per method. |
| Problem | The paper does not say how the 5 runs are made (same JVM or not), with which test settings, or how a test that passes only sometimes is counted. The authors counted 11,613 tests that were never run as passing (A11). |
| Simplification | 5 runs, each a separate Maven invocation (new JVMs), with the modules' own surefire settings (pdfbox: `-Xmx768m`). Over the 5 runs a test is *passing* if it passes every time, *failing* if it fails every time, *flaky* otherwise; a test that did not run in every run is *not run* and never counted as passing. Failures are grouped by exception type. If `OutOfMemoryError` appears, it is reported as its own category and a larger-heap re-run of the affected classes is reported as a secondary measurement, never replacing the primary one. |
| Justification | Separate JVMs are the strongest of the rerun strategies discussed by DeFlaker; keeping PDFBox's settings is what running `mvn test` on the module does, which is how the authors describe the integration. |
| Expected impact | Memory-heavy tests (profiles up to 55 MB) may fail with 768 MB of heap. |
| Validation | Local check E16; the authors' published tests are run in the same way (E18) to separate the environment from the profiles. |
| Reporting | Results (#PASSING / #FAILING), threats to validity. |

## A20. Running the authors' published tests

| Item | Explanation |
|---|---|
| Original requirement | Plan task 6.3: check the tool against the authors' data, separating the effect of the environment from the effect of the profiles. |
| Problem | The 22 test classes the authors published (Zenodo) do not compile as published: they use the `@Before` annotation without importing `org.junit.Before` (assess-tests run 39641425498, `results/06-test-execution/run-39641425498-split-bug/authors-compile.log`). |
| Simplification | `scripts/pankti/integrate-tests.sh` adds `import org.junit.Before;` to the classes that use `@Before` without importing it, and logs each one; nothing else in the published classes is changed. They are then integrated and run exactly like the reproduction's tests. |
| Justification | A missing import cannot change the behaviour of a test that compiles; the authors must have had it when they ran the tests. |
| Expected impact | None on the outcomes. |
| Validation | The repaired classes compile; the classes generated by pankti-generate already contain the import and are untouched (the repair is logged per class). |
| Reporting | Observations (the published artifacts do not compile as published); results of the authors' tests in this environment. |

## A21. Descartes "after": analysed classes

| Item | Explanation |
|---|---|
| Original requirement | Run Descartes again with the generated tests added and read the status of the effective targets (PANKTI_STATUS). |
| Problem | With the generated tests, every mutant of a class covered by thousands of generated tests (11,730 for `GlyfSimpleDescript.getFlags`) triggers long test runs; a full run of the pdfbox module took 68 minutes without them. The paper does not say whether the authors analysed whole modules. |
| Simplification | The "after" runs analyse only the 22 classes that declare the effective targets (`TARGET_CLASSES` in `scripts/pdfbox/run-descartes.sh`), with all the tests of the module. Same Descartes configuration as "before" (1 thread). |
| Justification | Descartes classifies each method from the outcome of its own mutants, which only depends on the tests that cover it; restricting the mutated classes does not change the tests. Caveat found while preparing the run: pitest-maven defaults `targetTests` to `targetClasses`, so a restricted run would select no test at all (every method "not covered"); the tests are now always given explicitly as the module's package, which is what the "before" runs used implicitly. |
| Expected impact | None on the classification of the methods of these classes. |
| Validation | Job "none" of the descartes-after workflow (run 39747040848): the same restricted run with no generated test gives the classification of the full "before" run for 460 of the 465 methods of the 22 classes (fontbox 62 / 62, pdfbox 398 / 403; `results/07-descartes-after/restriction_check/`). The 5 differences are mutants killed by an unstable test, `TestOptionalContentGroups.testOCGConsumption`, in one run and not in the other, and one timeout (discrepancies.md §23); the restriction cannot cause them, since the tests are the same. The authors' published "after" reports, which cover whole modules, agree with our restricted "after" run on all 46 targets. |
| Reporting | Methodology. |

## A22. Which generated tests are added

| Item | Explanation |
|---|---|
| Original requirement | Paper, Section II.F: a generated test is kept if it passes, is not flaky and improves the adequacy criterion. PIT requires a green test suite. |
| Problem | The paper does not say which tests were added for its "after" Descartes run. |
| Simplification | The tests that passed in all five runs (`scripts/pankti/keep_passing_tests.py`): 14,314 of the 14,679 generated by this reproduction; for the authors' published tests, 13,614 of 13,851. Failing tests are removed; classes left without tests are removed. |
| Justification | Follows the paper's assessment step; a failing test cannot be kept in a suite that PIT accepts. |
| Expected impact | None found: removing a failing test cannot make a method better tested. |
| Validation | The filter keeps exactly the passing counts of the test-execution stage for both test sets. |
| Reporting | Methodology. |

## A23. Failure causes classified from the evidence of every test

| Item | Explanation |
|---|---|
| Original requirement | Section V.A: the authors "manually analyze a random sample" of the failing tests and give four causes, with the rows of Table III for each. |
| Problem | The sample and the analysis procedure are not published, so the manual analysis cannot be repeated. |
| Simplification | Every failing test (237 of the authors' tests, 365 of ours) is classified automatically from its JUnit message and its observed value (`analysis/failure_analysis.py`). The mechanisms found are then checked in the PDFBox sources (`equals`/`hashCode` declarations) and, for the cache lookups, by deserialising three tests at run time (`analysis/java/CacheLookupCheck.java`). |
| Justification | Covers all failures instead of a sample, and is repeatable. The categories come from the evidence (the message shows two identity hash codes, or `null`), not from the paper's list. |
| Expected impact | A category says how the assertion fails, not every reason why the objects differ: when `equals` is by identity, a field-by-field difference (e.g. transient fields) is not detected. |
| Validation | No failing test is left in "other"; the rule "a test passes exactly when it observed null" holds for every test of the 13 / 14 methods with failures. |
| Reporting | Methodology; [failures.md](failures.md). |

## A24. Font sensitivity runs

| Item | Explanation |
|---|---|
| Original requirement | Plan task 8.3 (optional): one sensitivity run on the environment. The paper does not describe the fonts or the font cache of the authors' machine. |
| Problem | 8 of the 46 rows differ in #UNIQUE, all of them font methods, and the cause is unknown. PDFBox reads the naming table of every system font (`NamingTable.getName`) when it builds its font cache, so both the installed fonts and the state of the cache (`~/.pdfbox.cache`) can change these counts. |
| Simplification | Two extra runs of the full workload, each changing one factor (inputs of `production-run.yml`): (A) font cache built beforehand by PDFToImage on copies of the five PDFs, without the agent; (B) all font files except DejaVu removed (23 fonts instead of 57). |
| Justification | One factor per run; the defaults stay those of the main run, which remains the reference. |
| Expected impact | None on the main results; these runs only test the explanation. |
| Validation | Each run records its font list (`env-report.txt`) and its variant (`variant.txt`). Runs 39756523874 (warm cache: PDFBox reports "found 57 fonts" while priming, `font-cache-priming.log`) and 39756528629 (22 DejaVu fonts); results in E22. |
| Reporting | Methodology; experiment E22. |
