#!/usr/bin/env bash
# Run PDFBox under Glowroot + PANKTI and summarise the collected object profiles.
#   smoke: PDFToImage on one PDF, twice, each in a new JVM. Checks that RenderingMode.isFill is recorded, that the
#          XML parses, and that the invocation count is cumulative over JVM launches (count after run 2 = 2 x run 1).
#   full:  the authors' run.sh (50 JVM launches), with only its two machine-specific paths replaced.
# Before running: the profile directory is emptied and the PDFBox font cache (~/.pdfbox.cache) is deleted.
# Usage: run-workload.sh <smoke|full> <glowroot.jar> <pdfbox-app.jar> <workload_dir> <out_dir>
#   <workload_dir>/execution comes from get-workload.sh. PANKTI writes to /tmp/pankti-object-data (hard-coded).
set -uo pipefail

mode=$1
glowroot_jar=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
app_jar=$(cd "$(dirname "$3")" && pwd)/$(basename "$3")
exec_dir=$(cd "$4/execution" && pwd)
mkdir -p "$5"
out=$(cd "$5" && pwd)
here=$(cd "$(dirname "$0")/../.." && pwd)
profiles=/tmp/pankti-object-data
isfill=org.apache.pdfbox.pdmodel.graphics.state.RenderingMode.isFill

rm -rf "$profiles" "$HOME/.pdfbox.cache"
{ echo "== before"; date -u +%FT%TZ; df -h / | tail -1; } > "$out/run-info.txt"
cd "$exec_dir"
SECONDS=0
ok=1
check() { if [ "$1" -eq 0 ]; then echo "OK   $2"; else echo "FAIL $2"; ok=0; fi; }

if [ "$mode" = smoke ]; then
  counts=()
  for k in 1 2; do
    echo "PDFToImage ./workload/000752.pdf (run $k)" >> "$out/workload-console.log"
    java -javaagent:"$glowroot_jar" -jar "$app_jar" PDFToImage ./workload/000752.pdf >> "$out/workload-console.log" 2>&1
    counts+=("$(grep -o '[0-9]*$' "$profiles/$isfill-count.txt" 2>/dev/null || echo 0)")
  done
  {
    [ -f "$profiles/invoked-methods.csv" ]; check $? "invoked-methods.csv written"
    [ -s "$profiles/$isfill-receiving.xml" ] && [ -s "$profiles/$isfill-returned.xml" ]; check $? "isFill receiving and returned profiles written"
    [ "${counts[0]}" -gt 0 ] && [ "${counts[1]}" -eq $((2 * counts[0])) ]; check $? "isFill count cumulative over 2 JVM launches (${counts[0]} then ${counts[1]})"
  } | tee "$out/smoke-checks.txt"
elif [ "$mode" = full ]; then
  # Only the two machine-specific paths of the authors' script change; the diff is kept with the results.
  sed -e "s#^glowroot_jar_loc=.*#glowroot_jar_loc=\"$glowroot_jar\"#" -e "s#^pdfbox_jar_loc=.*#pdfbox_jar_loc=\"$app_jar\"#" run.sh > run-adapted.sh
  diff run.sh run-adapted.sh > "$out/run-sh.diff"
  bash run-adapted.sh > "$out/workload-console.log" 2>&1
  echo "run.sh exit code: $?" >> "$out/run-info.txt"
  cp execution.log "$out/authors-execution.log"
else
  echo "unknown mode: $mode" >&2
  exit 2
fi

{
  echo "== after"; date -u +%FT%TZ; df -h / | tail -1
  echo "workload_seconds=$SECONDS"
  echo "jvm_launches=$(grep -c 'Glowroot version' "$out/workload-console.log")"
  echo "profile_dir_bytes=$(du -sb "$profiles" 2>/dev/null | cut -f1)"
  echo "profile_files=$(ls "$profiles" 2>/dev/null | wc -l)"
} >> "$out/run-info.txt"

# Small per-method files are kept with the results; the XML profiles are archived separately by the caller.
mkdir -p "$out/profiles"
cp "$profiles"/invoked-methods.csv "$profiles"/*-count.txt "$profiles"/*-object-profile-sizes.txt "$out/profiles/" 2>/dev/null
python3 "$here/analysis/profile_stats.py" "$profiles" "$out/profile_stats" --fragments > /dev/null
check $? "profiles parsed (profile_stats.py --fragments)" | tee -a "$out/smoke-checks.txt"
python3 "$here/analysis/workload_log.py" "$out/workload-console.log" "$exec_dir/execution.log" "$out/workload_commands.csv" \
  | tee "$out/workload_commands.txt"
cat "$out/run-info.txt"
[ "$ok" -eq 1 ] || exit 1
