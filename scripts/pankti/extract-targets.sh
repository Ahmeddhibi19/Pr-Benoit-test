#!/usr/bin/env bash
# Compute the target methods (#TARGET) with the authors' own tools:
#   1. build pankti-extract at the given PANKTI checkout (commit 0fddf27 for the paper's PDFBox run);
#   2. run it on a PDFBox 2.0.21 checkout: public, non-static, non-abstract, non-void, non-deprecated, non-empty
#      methods of classes -> extracted-methods-<name>.csv;
#   3. run find-pseudo-tested.py: keep the extracted methods that Descartes classifies as pseudo-tested
#      -> instrumentation-candidates-<name>.csv.
# find-pseudo-tested.py needs pandas < 2 (DataFrame.append), i.e. Python <= 3.11 (setup/windows/install-tools.ps1).
# Usage: extract-targets.sh <pankti_dir> <pdfbox_dir> <descartes_reports_dir> <out_dir>
# Extra Maven arguments can be passed in MAVEN_EXTRA_ARGS; PYTHON selects the interpreter (default: python).
set -euo pipefail

pankti=$(cd "$1" && pwd)
pdfbox=$(cd "$2" && pwd)
reports=$(cd "$3" && pwd)
mkdir -p "$4"
out=$(cd "$4" && pwd)
python="${PYTHON:-python}"
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"

echo "pankti $(git -C "$pankti" rev-parse HEAD)" | tee "$out/versions.txt"
echo "pdfbox $(git -C "$pdfbox" rev-parse HEAD)" | tee -a "$out/versions.txt"

# The build prints warnings about an unreachable snapshot repository declared by Spoon 8.0.0; they are harmless.
(cd "$pankti" && mvn -B -q "${extra[@]}" -pl pankti-extract -am package -DskipTests)
jar=$(ls "$pankti"/pankti-extract/target/pankti-extract-*-jar-with-dependencies.jar)

# Spoon's MavenLauncher looks for Maven through M2_HOME.
export M2_HOME="${M2_HOME:-${MAVEN_HOME:-$(dirname "$(dirname "$(command -v mvn)")")}}"
name=$(basename "$pdfbox")
(cd "$out" && java -jar "$jar" "$pdfbox" 2>&1 | grep -v '^Picked up' | tee extract.log | tail -3)

mapfile -t jsons < <(find "$reports" -name methods.json | sort)
echo "${#jsons[@]} Descartes reports" | tee -a "$out/versions.txt"
(cd "$out" && PYTHONUTF8=1 "$python" "$pankti/pankti-extract/find-pseudo-tested.py" "extracted-methods-$name.csv" "${jsons[@]}" 2>&1 \
  | grep -v -E 'FutureWarning|DataFrame.append|instrumentation_candidates_df' | tee find-pseudo-tested.log | tail -1)
