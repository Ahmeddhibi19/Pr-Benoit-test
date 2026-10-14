#!/usr/bin/env bash
# Build-only fix for PDFBOX-5005: the IPA fonts used by the test suite moved.
# Same files and checksums, new host (the URLs used from PDFBox 2.0.22 on).
set -euo pipefail

pom="${1:-pdfbox}/pdfbox/pom.xml"
old="https://ipafont.ipa.go.jp/IPAfont/"
new="https://moji.or.jp/wp-content/ipafont/IPAfont/"

n=$(grep -cF "$old" "$pom" || true)
if [ "$n" -ne 2 ]; then
  echo "expected 2 IPA font URLs in $pom, found $n" >&2
  exit 1
fi
sed -i "s#${old}#${new}#g" "$pom"
grep -nF "$new" "$pom"
