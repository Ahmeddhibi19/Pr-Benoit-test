#!/usr/bin/env bash
# Run PIT + Descartes on one PDFBox module and collect the reports.
# Requires the "descartes" profile (add-descartes-profile.sh) and the build-only patches (patch-build.sh).
# Usage: run-descartes.sh <pdfbox_dir> <module> <out_dir> [threads]
# Extra Maven arguments can be passed in MAVEN_EXTRA_ARGS (e.g. -Dmaven.repo.local=...).
set -euo pipefail

root=$1
module=$2
out=$3
threads="${4:-1}"

# PIT defaults targetClasses to "<groupId>*", i.e. org.apache.pdfbox*, which would select no class in fontbox and
# xmpbox (their packages are org.apache.fontbox and org.apache.xmpbox). The authors' reports contain exactly these
# packages per module.
case "$module" in
  fontbox) target="org.apache.fontbox.*" ;;
  xmpbox) target="org.apache.xmpbox.*" ;;
  pdfbox|preflight|tools|examples) target="org.apache.pdfbox.*" ;;
  *) echo "unknown module: $module" >&2; exit 2 ;;
esac

mkdir -p "$out"
out=$(cd "$out" && pwd)
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"
cd "$root"

# Install the module and the modules it depends on (this also fetches the test resources), without running tests.
SECONDS=0
mvn -B -e "${extra[@]}" install -DskipTests -pl "$module" -am 2>&1 | tee "$out/install.log" | tail -5
echo "install_seconds=$SECONDS" > "$out/timing.txt"

SECONDS=0
set +e
mvn -B -e "${extra[@]}" -Pdescartes -Ddescartes.threads="$threads" -DtargetClasses="$target" -pl "$module" \
  test-compile org.pitest:pitest-maven:mutationCoverage 2>&1 | tee "$out/descartes.log" | grep -E 'BUILD|ERROR|Generated|Ran|>> ' | tail -20
rc=${PIPESTATUS[0]}
set -e
{
  echo "descartes_seconds=$SECONDS"
  echo "descartes_exit_code=$rc"
  echo "module=$module"
  echo "target_classes=$target"
  echo "threads=$threads"
} >> "$out/timing.txt"

report=$(ls -d "$module"/target/pit-reports/*/ 2>/dev/null | sort | tail -1)
if [ -n "$report" ] && [ -f "$report/methods.json" ]; then
  cp "$report/methods.json" "$out/methods.json"
  [ -f "$report/mutations.json" ] && gzip -c "$report/mutations.json" > "$out/mutations.json.gz"
  echo "report_dir=$(basename "$report")" >> "$out/timing.txt"
  echo "methods.json copied from $report"
fi
cat "$out/timing.txt"
exit $rc
