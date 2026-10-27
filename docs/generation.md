# Test generation and integration (pankti-generate)

PANKTI turns every unique object profile into a differential unit test (paper, Section II.E): deserialise the
receiving object and the arguments, call the target method, and assert that the result equals the returned value
observed in production. This page describes which generator is used and why, how the generated tests are counted and
checked, and how they are added to PDFBox.

## Which generator version

The instrumentation runs PANKTI `0fddf27`, the last commit before the authors' workload run of 2020-11-03 (assumption
A6). The tests the authors published (Zenodo, `pdfbox/pankti-generated-junit-tests/`, 22 test classes) were not
produced by that commit:

- every published class has two `deserializeObject(...)` helper methods. pankti-generate writes them only from commit
  `7afc584` (2020-11-12, "Abstract away XStream call with deserializeMethod()"); `0fddf27` writes direct casts;
- 18 of the 22 classes have a `setUpXStream()` method that registers three XStream converters (for `Inflater` and
  `Cleaner` objects). The generator contains this method, but the line that adds it is commented out;
- the 13 classes outside the packages `org.apache.fontbox.ttf` and `org.apache.pdfbox.pdfparser` import the converters
  from `org.apache.pdfbox.pdfparser`, after a blank line that the generator never writes, and the converter classes
  were copied into those two packages: edits made by hand.

`7afc584` is the only commit between the workload run and the authors' last "after" Descartes run (2020-11-19) that
changes pankti-generate. Its profile parser (`ObjectXMLParser`) is identical to the one of `0fddf27`, so #UNIQUE is
unchanged. The reproduction therefore builds pankti-generate at `7afc584` with the `setUpXStream()` line enabled
(`scripts/pankti/build-generator.sh`, assumption A17).

Check on 4 methods (local run on the authors' profiles): `TestRenderingModePanktiGen` and
`TestXrefTrailerResolverPanktiGen` are identical to the published files apart from the `setUpXStream()` method, and in
`TestPDCIDSystemInfoPanktiGen` the only differences are the hand-added imports and the position of `setUpXStream()`;
all 20 test methods are identical.

## Counting the generated tests

`analysis/count_generated_tests.py` counts the `@Test` methods per target method (test names are `test` + method
name + an optional parameter suffix for overloaded methods + a counter). On the authors' published tests it finds
13,851 tests in 22 classes, and #PANKTI_TESTS = #UNIQUE for all 46 methods, which confirms that #UNIQUE as computed by
`analysis/profile_stats.py --fragments` is the number of tests pankti-generate writes.

`analysis/compare_generated_tests.py` compares two sets of generated classes test by test (method bodies, line endings
ignored); class-level differences such as imports are ignored, since the authors edited them by hand.

## Generation runs

`scripts/pankti/generate-tests.sh` runs pankti-generate (12 GB heap on the CI runner) on a profile directory and the
PDFBox 2.0.21 sources. pankti-generate re-prints the whole Spoon model of PDFBox; the script keeps only the
`Test*PanktiGen.java` classes and the resource files (profiles longer than 10,000 characters, which the tests read
with `getClass().getClassLoader().getResource(...)`).

The `generate-tests` workflow runs it twice, in parallel:
- on the profiles of production-run 39444526027 (this reproduction): the test set used from the test-execution stage on;
- on the authors' profiles from Zenodo, and compares the result with the 13,851 tests they published.

Results: see [experiments.md](experiments.md).

## Integration into PDFBox

`scripts/pankti/integrate-tests.sh` follows the authors' notes (experiments README) with smaller build changes:

| Step | Authors (README and published files) | This reproduction |
|---|---|---|
| Test classes | into the module's `src/test/java` | same; fontbox for `org.apache.fontbox`, pdfbox otherwise |
| Resource files | into `src/test/resources` | same, by the module of the method they belong to |
| XStream | test dependency | XStream 1.4.12 test dependency of fontbox and pdfbox |
| Converters | copied into 2 packages, imports added by hand | copied into every test package (package line changed); generated classes are not edited |
| Java level | source/target 9 for the whole build, animal-sniffer disabled | only the test compilation (`default-testCompile`) gets `<release>9</release>`; the library is still compiled with release 6 by PDFBox's `jdkGte9` profile, and animal-sniffer stays enabled |
| Large classes | (11,730 tests in one 90 MB class; only 117 of them were executed) | classes with more than 500 tests are split into parts, tests unchanged (`scripts/pankti/split_test_classes.py`) |

The library code that Descartes mutates is therefore compiled exactly as without the generated tests (class file
version 50, Java 6), while the tests are compiled for Java 9 (version 53).

Local check (Windows, 3 classes generated from the authors' profiles, split with at most 5 tests per class): the
tests compile and the 20 tests pass (`mvn -pl pdfbox -am test -Dtest='Test*PanktiGen*'`), as in Table III for these
methods.
