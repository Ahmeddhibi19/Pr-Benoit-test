#!/usr/bin/env bash
# Download the authors' artifacts used as reference and as fallback:
#   - Zenodo replication data, version 1 (record 4298605, concept DOI 10.5281/zenodo.4298604)
#   - PANKTI at the commit used for the PDFBox run, plus the last commit before paper v4
#   - pankti-experiments at the commit of the PDFBox numbers, plus the last commit before paper v4
# Usage: bash setup/fetch-artifacts.sh [root]   (default root: /c/w)
set -euo pipefail

root="${1:-/c/w}"
data="$root/data"
src="$root/src"
mkdir -p "$data" "$src"

zip="$data/pankti-data-v1.zip"
md5="9c902f3e2342338192197034413d70c0"
if [ ! -f "$zip" ]; then
  curl -fL --retry 5 --retry-all-errors -C - -o "$zip.part" "https://zenodo.org/records/4298605/files/pankti-data.zip?download=1"
  mv "$zip.part" "$zip"
fi
echo "$md5  $zip" | md5sum -c -

# Some file names in pankti-experiments exceed the Windows path limit; only README.md and pdfbox/ are
# checked out. MSYS2_ARG_CONV_EXCL keeps Git Bash from rewriting the sparse patterns into Windows paths.
sparse=()
clone_at() {
  local url=$1 dir=$2 sha=$3
  [ -d "$dir/.git" ] || git -c core.longpaths=true clone --quiet --filter=blob:none --no-checkout "$url" "$dir"
  git -C "$dir" config core.longpaths true
  if [ ${#sparse[@]} -gt 0 ]; then (cd "$dir" && MSYS2_ARG_CONV_EXCL='*' git sparse-checkout set --no-cone "${sparse[@]}"); fi
  git -C "$dir" checkout --quiet --force --detach "$sha"
  echo "$(basename "$dir") $(git -C "$dir" rev-parse HEAD) $(git -C "$dir" log -1 --format=%cs)"
}
add_worktree() {
  local repo=$1 dir=$2 sha=$3
  [ -d "$dir" ] || git -C "$repo" worktree add --quiet --no-checkout --detach "$dir" "$sha"
  if [ ${#sparse[@]} -gt 0 ]; then (cd "$dir" && MSYS2_ARG_CONV_EXCL='*' git sparse-checkout set --no-cone "${sparse[@]}"); fi
  git -C "$dir" checkout --quiet --force --detach "$sha"
  echo "$(basename "$dir") $(git -C "$dir" rev-parse HEAD) $(git -C "$dir" log -1 --format=%cs)"
}

clone_at https://github.com/ASSERT-KTH/pankti.git "$src/pankti" 0fddf273a8a6acbaba51a318fcc7fc6e5b84058f
add_worktree "$src/pankti" "$src/pankti-2021" 326a7533e6dd9600f7ed0ce5d2d6c6b2a26ebf71
sparse=(/README.md /pdfbox/)
clone_at https://github.com/ASSERT-KTH/pankti-experiments.git "$src/pankti-experiments" 7bc7791e8cfbdee2268e077e9d289137541dc3a6
add_worktree "$src/pankti-experiments" "$src/pankti-experiments-2021" 1d8f9aa150d9bfd99e3a38c987025cd6159494da

listing="$data/pankti-data-v1.listing.txt"
unzip -l "$zip" > "$listing"
prefix=$(awk '$4 ~ /(^|\/)pdfbox\/$/ {print $4; exit}' "$listing")
echo "pdfbox folder in archive: ${prefix:-not found}"
if [ -n "$prefix" ]; then
  unzip -q -o "$zip" "${prefix}*" \
    -x '*-receiving.xml' '*-receiving-post.xml' '*-params.xml' '*-returned.xml' \
    -d "$data/pankti-data-v1"
fi
du -sh "$data/pankti-data-v1" 2>/dev/null || true
