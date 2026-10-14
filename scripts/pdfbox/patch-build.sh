#!/usr/bin/env bash
# Build-only adjustments so that the PDFBox 2.0.21 test suite runs today. No library or test code is changed.
#  1. PDFBOX-5005: the IPA fonts used by the tests moved (same files and sha512, the URLs used from 2.0.22 on).
#  2. The Isartor test suite of the preflight module is no longer served by pdfa.org (HTTP 403). The same file
#     is taken from the Internet Archive; the download plugin still checks the sha512 given in the pom.
#  3. The certificate policy PDF used by the examples tests is not served to the CI runners any more; the same
#     file (sha512 checked by the plugin) is taken from the Internet Archive.
#  4. PDAcroFormTest writes into pdfbox/target/test-output but never creates it; it only passes when another
#     test created the directory before. The directory is created up front.
set -euo pipefail

root="${1:-pdfbox}"

replace() {
  local file=$1 old=$2 new=$3 expected=$4
  local n
  n=$(grep -cF "$old" "$file" || true)
  if [ "$n" -ne "$expected" ]; then
    echo "expected $expected occurrence(s) of $old in $file, found $n" >&2
    exit 1
  fi
  sed -i "s#${old}#${new}#g" "$file"
  grep -nF "$new" "$file"
}

replace "$root/pdfbox/pom.xml" \
  "https://ipafont.ipa.go.jp/IPAfont/" \
  "https://moji.or.jp/wp-content/ipafont/IPAfont/" 2

replace "$root/preflight/pom.xml" \
  "https://www.pdfa.org/wp-content/until2016_uploads/2011/08/isartor-pdfa-2008-08-13.zip" \
  "https://web.archive.org/web/2020id_/https://www.pdfa.org/wp-content/until2016_uploads/2011/08/isartor-pdfa-2008-08-13.zip" 1

replace "$root/examples/pom.xml" \
  "https://www.quovadisglobal.com/wp-content/uploads/2020/01/QV_RCA1_RCA3_CPCPS_V4_11.pdf" \
  "https://web.archive.org/web/2020id_/https://www.quovadisglobal.com/wp-content/uploads/2020/01/QV_RCA1_RCA3_CPCPS_V4_11.pdf" 1

mkdir -p "$root/pdfbox/target/test-output"
