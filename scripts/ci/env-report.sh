#!/usr/bin/env bash
# Print the execution environment, so every run records where it ran.
set -uo pipefail

section() { printf '\n== %s\n' "$1"; }

section "date (UTC)"; date -u +%Y-%m-%dT%H:%M:%SZ
section "runner image"; echo "${ImageOS:-unknown} ${ImageVersion:-unknown}"
section "os"; uname -a; cat /etc/os-release 2>/dev/null | grep -E '^(NAME|VERSION)='
section "cpu"; nproc; grep -m1 'model name' /proc/cpuinfo
section "memory"; free -h
section "disk"; df -h / "${RUNNER_TEMP:-/tmp}"
section "java"; java -version 2>&1; echo "JAVA_HOME=${JAVA_HOME:-}"
section "maven"; mvn -v 2>&1
section "python"; python3 --version
section "locale"; locale 2>/dev/null | head -3
section "fonts ($(fc-list | wc -l))"; fc-list --format '%{family[0]}|%{style[0]}|%{file}\n' | sort
