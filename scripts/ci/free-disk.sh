#!/usr/bin/env bash
# Remove preinstalled toolchains that the experiments do not use.
set -euo pipefail

df -h /
sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /usr/local/.ghcup /opt/hostedtoolcache/CodeQL || true
df -h /
