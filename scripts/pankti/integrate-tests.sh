#!/usr/bin/env bash
# Add the generated tests to the PDFBox modules, following the authors' notes (experiments README) with smaller
# build changes:
#   - each test class goes to src/test/java of its module (fontbox for org.apache.fontbox, pdfbox otherwise), each
#     resource file (profiles longer than 10,000 characters) to src/test/resources of the module of its method;
#   - classes with more than MAX_TESTS tests are split (split_test_classes.py; default 500 tests per class);
#   - PANKTI's three XStream converters (used by the generated setUpXStream()) are copied into every test package,
#     with only the package line changed; the authors copied them into two packages and added imports by hand;
#   - XStream 1.4.12 becomes a test dependency of fontbox and pdfbox;
#   - the tests are compiled with release 9 (the converters use java.lang.ref.Cleaner); the library itself is still
#     compiled with release 6, so animal-sniffer (which checks the library classes) stays enabled. The authors set
#     the whole build to Java 9 and disabled animal-sniffer.
# Usage: integrate-tests.sh <pdfbox_dir> <generated_dir> <converters_dir>
#   <generated_dir>/tests and /resources come from generate-tests.sh; <converters_dir> is
#   pankti-instrument/src/main/java/se/kth/castor/pankti/instrument/converters of a PANKTI checkout.
set -euo pipefail

root=$(cd "$1" && pwd)
gen=$(cd "$2" && pwd)
conv=$(cd "$3" && pwd)
here=$(cd "$(dirname "$0")" && pwd)
max="${MAX_TESTS:-500}"
python="${PYTHON:-python3}"

# 1. Build changes (guarded: each anchor must occur exactly once; indentation and line endings are tolerated).
count_lines() {   # file regex (on the line without its end-of-line)
  awk -v re="$2" '{ l = $0; sub(/\r$/, "", l) } l ~ re { n++ } END { print n + 0 }' "$1"
}
test_release_9() {
  # On JDK 9+, PDFBox's profile jdkGte9 compiles with <release>6</release>, for the tests too. Only the test
  # compilation (execution default-testCompile) gets release 9; the library is still compiled for Java 6.
  local pom=$1
  [ "$(count_lines "$pom" '^ *<release>6</release>$')" -eq 1 ] || { echo "expected one <release>6</release> in $pom" >&2; exit 1; }
  awk '{ l = $0; sub(/$/, "", l); print l }
       l ~ /^ *<release>6<\/release>$/ { seen = 1; next }
       seen && l ~ /^ *<\/configuration>$/ {
         ind = l; sub(/<.*/, "", ind)
         print ind "<executions>"
         print ind "    <execution>"
         print ind "        <id>default-testCompile</id>"
         print ind "        <configuration>"
         print ind "            <release>9</release>"
         print ind "        </configuration>"
         print ind "    </execution>"
         print ind "</executions>"
         seen = 0 }' "$pom" > "$pom.tmp" && mv "$pom.tmp" "$pom"
}
test_release_9 "$root/parent/pom.xml"
for module in fontbox pdfbox; do
  pom="$root/$module/pom.xml"
  grep -q '<artifactId>xstream</artifactId>' "$pom" && continue
  [ "$(count_lines "$pom" '^ *</dependencies>$')" -eq 1 ] || { echo "expected one </dependencies> in $pom" >&2; exit 1; }
  awk '{ l = $0; sub(/\r$/, "", l) } l ~ /^ *<\/dependencies>$/ {
    ind = l; sub(/<.*/, "", ind); i = ind ind
    print i "<dependency>"; print i "    <groupId>com.thoughtworks.xstream</groupId>"
    print i "    <artifactId>xstream</artifactId>"; print i "    <version>1.4.12</version>"
    print i "    <scope>test</scope>"; print i "</dependency>" } { print l }' "$pom" > "$pom.tmp" && mv "$pom.tmp" "$pom"
done

# 2. Tests, split if needed, with the converters in each test package.
work=$(mktemp -d)
cp -r "$gen/tests" "$work/tests"
"$python" "$here/split_test_classes.py" "$work/tests" "$max"
(cd "$work/tests" && find . -name '*.java') | while read -r f; do
  case "$f" in ./org/apache/fontbox/*) module=fontbox ;; *) module=pdfbox ;; esac
  dest="$root/$module/src/test/java/$(dirname "$f")"
  mkdir -p "$dest"
  cp "$work/tests/$f" "$dest/"
  # The classes the authors published use @Before without importing it (they do not compile as published); the
  # import is added to such classes only. Classes written by pankti-generate have it already.
  target="$dest/$(basename "$f")"
  if grep -q '@Before' "$target" && ! grep -q -E '^import org\.junit\.(Before|\*);' "$target"; then
    sed -i '0,/^package .*;/s//&\nimport org.junit.Before;/' "$target"
    echo "added the missing import org.junit.Before to $(basename "$f")"
  fi
  package=$(dirname "${f#./}" | tr / .)
  for c in CleanerImplConverter FileCleanableConverter InflaterConverter; do
    [ -f "$dest/$c.java" ] || sed "1s/^package .*;/package $package;/" "$conv/$c.java" > "$dest/$c.java"
  done
done

# 3. Resource files, by the module of the method they belong to.
for module in fontbox pdfbox; do mkdir -p "$root/$module/src/test/resources"; done
find "$gen/resources" -type f -name '*.xml' | while read -r f; do
  case "$(basename "$f")" in org.apache.fontbox.*) module=fontbox ;; *) module=pdfbox ;; esac
  cp "$f" "$root/$module/src/test/resources/"
done
rm -rf "$work"

for module in fontbox pdfbox; do
  echo "$module: $(find "$root/$module/src/test/java" -name 'Test*PanktiGen*.java' | wc -l) generated test classes," \
       "$(grep -rh '@Test' --include='Test*PanktiGen*.java' "$root/$module/src/test/java" | wc -l) tests," \
       "$(find "$root/$module/src/test/resources" -maxdepth 1 -name 'org.apache.*.xml' | wc -l) resource files"
done
