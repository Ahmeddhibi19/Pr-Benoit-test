#!/usr/bin/env bash
# Install the Glowroot 0.13.6 agent (the version of PANKTI's plugin API) and, optionally, the PANKTI plugin.
# Glowroot keeps its default configuration, as nothing else is documented for the authors' run.
# The release publishes no checksum; the sha256 below was computed on the first download (2026-10-20).
# Usage: install-glowroot.sh <dest_dir> [plugin.jar]   -> <dest_dir>/glowroot/glowroot.jar
set -euo pipefail

dest=$1
plugin="${2:-}"
# Resolve the plugin path before changing directory.
[ -z "$plugin" ] || plugin="$(cd "$(dirname "$plugin")" && pwd)/$(basename "$plugin")"
version=0.13.6
file="glowroot-$version-dist.zip"
sha256=f1e76f3ac1b08587a5694fe9fd0b852313177643347e3fd2ec811588129a4968

mkdir -p "$dest"
cd "$dest"
[ -f "$file" ] || curl -fsSL --retry 3 -o "$file" "https://github.com/glowroot/glowroot/releases/download/v$version/$file"
echo "$sha256  $file" | sha256sum -c -
rm -rf glowroot
unzip -q "$file"
mkdir -p glowroot/plugins
if [ -n "$plugin" ]; then
  cp "$plugin" glowroot/plugins/
  echo "plugin installed: glowroot/plugins/$(basename "$plugin")"
fi
ls -l glowroot glowroot/plugins
