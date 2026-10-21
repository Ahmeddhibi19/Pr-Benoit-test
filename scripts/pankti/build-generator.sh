#!/usr/bin/env bash
# Build pankti-generate as the authors used it for the tests they published (Zenodo, pankti-generated-junit-tests):
#   - PANKTI commit 7afc584 (2020-11-12), the first generator version after the workload run of 2020-11-03; its
#     output has the deserializeObject() helpers found in every published test class (0fddf27 does not);
#   - with the @Before method setUpXStream() enabled (one line, commented out in the sources): it registers the
#     XStream converters for Inflater and Cleaner objects, and 18 of the 22 published classes contain it.
# The profile parser is the same as in 0fddf27 (the commit of the instrumentation), so #UNIQUE is unchanged.
# Usage: build-generator.sh <pankti_checkout_at_7afc584> <out_dir>      (MAVEN_EXTRA_ARGS: extra Maven arguments)
set -euo pipefail

pankti=$(cd "$1" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"

work="$out/src"
rm -rf "$work"
mkdir -p "$work"
cp "$pankti/pom.xml" "$work/"
cp -r "$pankti/pankti-generate" "$work/"
echo "pankti $(git -C "$pankti" rev-parse HEAD)" > "$out/versions.txt"

gen="$work/pankti-generate/src/main/java/se/kth/castor/pankti/generate/generators/TestGenerator.java"
line='            // generatedClass.addMethod(generateSetupMethod());'
n=$(grep -cxF "$line" "$gen" || true)
if [ "$n" -ne 1 ]; then
  echo "expected 1 line '$line' in TestGenerator.java, found $n" >&2
  exit 1
fi
cp "$gen" "$out/TestGenerator.java.orig"
sed -i 's#^            // generatedClass.addMethod(generateSetupMethod());#            generatedClass.addMethod(generateSetupMethod());#' "$gen"
diff "$out/TestGenerator.java.orig" "$gen" > "$out/generator.diff" || true
rm "$out/TestGenerator.java.orig"

(cd "$work" && mvn -B -q "${extra[@]}" -N install && cd pankti-generate && mvn -B -q "${extra[@]}" package -DskipTests)
cp "$work"/pankti-generate/target/pankti-generate-*-jar-with-dependencies.jar "$out/pankti-generate.jar"
rm -rf "$work"
(cd "$out" && sha256sum pankti-generate.jar >> versions.txt)
cat "$out/generator.diff" "$out/versions.txt"
