#!/usr/bin/env bash
# Build the PDFBox command-line application (pdfbox-app-2.0.21.jar) from the checked-out sources, as the authors
# did (their jar was built from a local checkout, see docs/discrepancies.md, item 13). The workload runs this jar.
# Usage: build-app.sh <pdfbox_dir> <out_dir>    (MAVEN_EXTRA_ARGS: extra Maven arguments)
set -euo pipefail

root=$(cd "$1" && pwd)
mkdir -p "$2"
out=$(cd "$2" && pwd)
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"

(cd "$root" && mvn -B -q "${extra[@]}" -pl app -am package -DskipTests)
jar=$(ls "$root"/app/target/pdfbox-app-*.jar | grep -v -E 'sources|javadoc' | head -1)
cp "$jar" "$out/"
cd "$out"
name=$(basename "$jar")
{
  echo "file=$name"
  echo "bytes=$(stat -c %s "$name")"
  echo "sha256=$(sha256sum "$name" | cut -d' ' -f1)"
  echo "pdfbox_commit=$(git -C "$root" rev-parse HEAD)"
} | tee app-jar.txt
