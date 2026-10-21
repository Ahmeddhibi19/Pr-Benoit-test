#!/usr/bin/env bash
# Run the generated tests (Test*PanktiGen*) of the fontbox and pdfbox modules several times, each time in a
# separate Maven invocation, hence in new JVMs (paper, Section II.F: a test is run 5 times to detect flakiness).
# The modules' own surefire settings are kept (pdfbox: -Xmx768m). The tests must already be compiled
# (integrate-tests.sh, then mvn install -DskipTests). Failing tests do not stop a run.
# Usage: run-generated-tests.sh <pdfbox_dir> <runs> <out_dir>       (MAVEN_EXTRA_ARGS: extra Maven arguments)
#   -> <out_dir>/run-<k>/<module>/TEST-*.xml, <out_dir>/runs.txt
set -uo pipefail

root=$(cd "$1" && pwd)
runs=$2
mkdir -p "$3"
out=$(cd "$3" && pwd)
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"
: > "$out/runs.txt"

for k in $(seq 1 "$runs"); do
  for module in fontbox pdfbox; do rm -rf "$root/$module/target/surefire-reports"; done
  SECONDS=0
  (cd "$root" && mvn -B "${extra[@]}" -pl fontbox,pdfbox surefire:test -Dtest='Test*PanktiGen*' \
     -DfailIfNoTests=false -Dmaven.test.failure.ignore=true > "$out/run-$k.log" 2>&1)
  rc=$?
  for module in fontbox pdfbox; do
    mkdir -p "$out/run-$k/$module"
    [ -d "$root/$module/target/surefire-reports" ] && cp "$root/$module/target/surefire-reports"/TEST-*.xml "$out/run-$k/$module/" 2>/dev/null
  done
  summary=$(grep -E "^\[(INFO|WARNING|ERROR)\] Tests run: [0-9]+, Failures" "$out/run-$k.log" | tail -2 | tr '\n' ' ')
  echo "run $k: maven exit $rc, ${SECONDS} s; $summary" | tee -a "$out/runs.txt"
done
