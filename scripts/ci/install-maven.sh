#!/usr/bin/env bash
# Install Maven 3.6.3 from the Apache archive.
# Usage: install-maven.sh [dest_dir]   (default: $RUNNER_TEMP, or /tmp)
set -euo pipefail

dest="${1:-${RUNNER_TEMP:-/tmp}}"
base="https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries"
file="apache-maven-3.6.3-bin.tar.gz"

mkdir -p "$dest"
cd "$dest"
curl -fsSL --retry 3 -o "$file" "$base/$file"
curl -fsSL --retry 3 -o "$file.sha512" "$base/$file.sha512"
echo "$(awk '{print $1}' "$file.sha512")  $file" | sha512sum -c -
tar xzf "$file"

home="$dest/apache-maven-3.6.3"
"$home/bin/mvn" -v

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "MAVEN_HOME=$home" >> "$GITHUB_ENV"
  echo "$home/bin" >> "$GITHUB_PATH"
fi
