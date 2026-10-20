#!/usr/bin/env bash
# Check that the Glowroot agent starts with the PANKTI plugin, without running any target method:
# pdfbox-app is started without a command, so it only prints its usage.
# Passes when Glowroot logs its start without WARN/ERROR lines, registers the plugin "panktiplugin" in its
# config.json, and no object profile is written.
# Usage: check-agent.sh <glowroot_dir> <pdfbox-app.jar> <out_dir> [profile_dir]   (profile_dir: /tmp/pankti-object-data)
set -uo pipefail

glowroot=$(cd "$1" && pwd)
app=$2
mkdir -p "$3"
out=$(cd "$3" && pwd)
profiles="${4:-/tmp/pankti-object-data}"

java -javaagent:"$glowroot/glowroot.jar" -jar "$app" > "$out/agent-run.txt" 2>&1
echo "pdfbox-app exit code (usage only): $?" >> "$out/agent-run.txt"
cat "$glowroot"/logs/*.log > "$out/glowroot.log" 2>/dev/null || true

ok=1
check() { if [ "$1" -eq 0 ]; then echo "OK   $2"; else echo "FAIL $2"; ok=0; fi; }
{
  grep -q "Glowroot version: 0.13.6" "$out/glowroot.log"; check $? "Glowroot 0.13.6 started"
  ! grep -E " (WARN|ERROR) " "$out/glowroot.log"; check $? "no WARN or ERROR in the Glowroot log"
  grep -q '"id": "panktiplugin"' "$glowroot/config.json"; check $? "plugin panktiplugin registered in config.json"
  grep -q "^Usage: java -jar pdfbox-app" "$out/agent-run.txt"; check $? "pdfbox-app ran under the agent"
  [ ! -d "$profiles" ] || [ -z "$(ls -A "$profiles")" ]; check $? "no object profile written (no target invoked)"
} | tee "$out/agent-checks.txt"
grep -q "^FAIL" "$out/agent-checks.txt" && exit 1
exit 0
