#!/usr/bin/env bash
# Publish the outcome of a Maven build as workflow annotations and in the job summary.
# Usage: annotate-build.sh <out_dir>   (expects build.log, and test-summary.csv / failing-tests.txt if present)
set -uo pipefail

out="${1:-out}"
log="$out/build.log"
summary="${GITHUB_STEP_SUMMARY:-/dev/null}"

escape() { sed -e 's/%/%25/g' -e 's/\r/%0D/g'; }

if [ -f "$out/test-summary.csv" ]; then
  total=$(grep '^TOTAL,' "$out/test-summary.csv" || true)
  echo "::notice title=Test summary::module,suites,tests,failures,errors,skipped,time_s -> ${total:-no surefire reports}"
  { echo "### Test summary"; echo; echo '```'; cat "$out/test-summary.csv"; echo '```'; } >> "$summary"
fi

if [ -f "$log" ]; then
  sed -n '/Reactor Summary/,/BUILD /p' "$log" | sed 's/^\[INFO\] //' > "$out/reactor.txt"
  { echo "### Reactor"; echo; echo '```'; cat "$out/reactor.txt"; echo '```'; } >> "$summary"
  failed_modules=$(grep -E 'FAILURE|SKIPPED' "$out/reactor.txt" | tr -s ' ' | paste -sd ';' -)
  [ -n "$failed_modules" ] && echo "::error title=Reactor::$(echo "$failed_modules" | escape)"
  { grep -E '^\[ERROR\] Failed to execute goal' "$log"; grep -E '^\[ERROR\] ' "$log" | grep -v 'Failed to execute goal'; } \
    | grep -vE '^\[ERROR\] *$|^\[ERROR\] -> \[Help|Re-run Maven|full stack trace|For more information|To see the full|After correcting|mvn <args>' \
    | awk '!seen[$0]++' | head -8 | while IFS= read -r line; do
      echo "::error title=Maven::$(echo "${line#\[ERROR\] }" | cut -c1-400 | escape)"
    done
fi

if [ -s "$out/failing-tests.txt" ]; then
  echo "::warning title=Failing tests::$(wc -l < "$out/failing-tests.txt") failing or erroring test cases (see failing-tests.txt)"
  head -9 "$out/failing-tests.txt" | while IFS= read -r line; do
    echo "::warning title=Failing test::$(echo "$line" | cut -c1-400 | escape)"
  done
  { echo "### Failing tests"; echo; echo '```'; cat "$out/failing-tests.txt"; echo '```'; } >> "$summary"
fi
exit 0
