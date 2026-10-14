#!/usr/bin/env bash
# Shallow clone of PDFBox at the tag studied in the paper.
set -euo pipefail

dest="${1:-pdfbox}"
tag="${PDFBOX_TAG:-2.0.21}"

git clone --quiet --depth 1 --branch "$tag" https://github.com/apache/pdfbox.git "$dest"
echo "pdfbox tag=$tag commit=$(git -C "$dest" rev-parse HEAD)"
