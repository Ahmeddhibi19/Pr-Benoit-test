#!/usr/bin/env bash
# Generate the differential unit tests from a directory of object profiles with pankti-generate, then keep only
# the generated test classes (pankti-generate also re-prints the whole PDFBox source tree) and their resource files.
# Usage: generate-tests.sh <pankti-generate.jar> <pdfbox_dir> <profiles_dir> <out_dir>
#   <profiles_dir> holds invoked-methods.csv and the XML profiles; HEAP sets the JVM heap (default 12g).
# Output: <out_dir>/tests/<package>/Test<Class>PanktiGen.java, <out_dir>/resources/*.xml, generate.log, sizes.
set -uo pipefail

jar=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
pdfbox=$(cd "$2" && pwd)
profiles=$(cd "$3" && pwd)
mkdir -p "$4"
out=$(cd "$4" && pwd)
heap="${HEAP:-12g}"

work="$out/work"
rm -rf "$work" "$out/tests" "$out/resources"
mkdir -p "$work"
# Spoon's MavenLauncher looks for Maven through M2_HOME.
export M2_HOME="${M2_HOME:-${MAVEN_HOME:-$(dirname "$(dirname "$(command -v mvn)")")}}"
cd "$work"
SECONDS=0
java -Xmx"$heap" -jar "$jar" "$pdfbox" "$profiles/invoked-methods.csv" "$profiles" > "$out/generate.log" 2>&1
rc=$?
echo "generate_exit_code=$rc" > "$out/generate-info.txt"
echo "generate_seconds=$SECONDS" >> "$out/generate-info.txt"

# Keep the generated test classes (with their package directories) and the resource files.
name=$(basename "$pdfbox")
(cd "output/generated/$name" 2>/dev/null && find . -name 'Test*PanktiGen.java' -print0 | while IFS= read -r -d '' f; do
  mkdir -p "$out/tests/$(dirname "$f")"
  cp "$f" "$out/tests/$f"
done)
mkdir -p "$out/resources"
[ -d output/object-data ] && cp output/object-data/* "$out/resources/" 2>/dev/null
cd "$out"
rm -rf "$work"
{
  echo "test_classes=$(find tests -name '*.java' | wc -l)"
  echo "test_methods=$(grep -rh '@Test' tests | wc -l)"
  echo "resource_files=$(ls resources | wc -l)"
  echo "tests_bytes=$(du -sb tests | cut -f1)"
  echo "resources_bytes=$(du -sb resources | cut -f1)"
} >> generate-info.txt
grep -E "^(Number of new test cases|NO OBJECT|Exception|java\.)" generate.log | sort | uniq -c | head -20
cat generate-info.txt
exit $rc
