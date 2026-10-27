Run 39641425498 of assess-tests (2026-10-21), kept as evidence of two problems found by it:
- reproduction: split_test_classes.py dropped the setUpXStream() method that pankti-generate writes between the
  tests of a class with two target methods; the split HorizontalMetricsTable classes therefore had no converter
  for java.io.FileCleanable and 301 of their tests failed with ConversionException. Fixed; see docs/execution.md.
- authors: the published test classes use @Before without importing it and do not compile (authors-compile.log).
These numbers are NOT the results of the reproduction.
