#!/usr/bin/env bash
# Install AdoptOpenJDK 11.0.8+10, the JDK recorded in the authors' execution log.
set -euo pipefail

dest="${1:-${RUNNER_TEMP:-/tmp}}"
base="https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.8%2B10"
file="OpenJDK11U-jdk_x64_linux_hotspot_11.0.8_10.tar.gz"

mkdir -p "$dest"
cd "$dest"
curl -fsSL --retry 3 -o "$file" "$base/$file"
curl -fsSL --retry 3 -o "$file.sha256.txt" "$base/$file.sha256.txt"
sha256sum -c "$file.sha256.txt"
tar xzf "$file"

home="$dest/jdk-11.0.8+10"
"$home/bin/java" -version

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "JAVA_HOME=$home" >> "$GITHUB_ENV"
  echo "$home/bin" >> "$GITHUB_PATH"
fi
