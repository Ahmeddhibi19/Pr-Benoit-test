#!/usr/bin/env bash
# Fetch the authors' PDFBox workload: run.sh, the six GovDocs1 PDFs and the console log of their run
# (pankti-experiments, pdfbox/execution/, commit 7bc7791 of 2020-11-03), into <dest>/execution/.
# The PDFs are checked against their sha256 (see docs/artifacts.md).
# Usage: get-workload.sh <dest>
set -euo pipefail

dest=$1
commit=7bc7791e8cfbdee2268e077e9d289137541dc3a6
repo=https://github.com/ASSERT-KTH/pankti-experiments.git

mkdir -p "$dest"
dest=$(cd "$dest" && pwd)
src="$dest/pankti-experiments"
rm -rf "$src" "$dest/execution"
git clone --quiet --filter=blob:none --no-checkout "$repo" "$src"
# MSYS2_ARG_CONV_EXCL keeps Git Bash (Windows) from rewriting the patterns below into Windows paths; ignored elsewhere.
(cd "$src" && MSYS2_ARG_CONV_EXCL="*" git sparse-checkout set --no-cone /pdfbox/execution/run.sh /pdfbox/execution/execution.log /pdfbox/execution/workload/ \
  && git checkout --quiet "$commit")
mkdir -p "$dest/execution"
cp -r "$src/pdfbox/execution/run.sh" "$src/pdfbox/execution/execution.log" "$src/pdfbox/execution/workload" "$dest/execution/"
rm -rf "$src"

cd "$dest/execution/workload"
sha256sum -c - <<'EOF'
bdd62b32cf5211cda13f9bdfe850456f661d0d8692c883056174fdfd289b2268  000142.pdf
19fff50000cdb8af99de1b20e13be592cddab36879cf5c5d36d88560a9325606  000752.pdf
cc47261dc72cfa43075e2b402eda8c4a204d505c3f41b55b5ad76ceaa1c9405f  000753.pdf
13552b69646b840a7c27c6454ed06164a46f30b99e609a7cc5211b4266893555  000809.pdf
b156e9a6c16d7228e798f0c0df0f2ff6c619c6da1ca39d2cb85f8cdf515d0baf  000810.pdf
f4d66338663f5b17b8a7281f8e4cda6e5ab812950f12fe54c647d891b570b07f  000817.pdf
EOF
echo "workload from pankti-experiments $commit in $dest/execution"
