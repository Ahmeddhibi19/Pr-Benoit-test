#!/usr/bin/env bash
# Add a "descartes" Maven profile to the PDFBox parent POM, so that PIT + Descartes can run on any module without
# touching the library or test code. The configuration mirrors the authors' reports (pankti-experiments, 2020-09-21):
#   - PIT 1.4.10 with Descartes 1.2.6 (the last Descartes release before the authors' runs; built against PIT 1.4.10)
#   - the 21 extreme-mutation operators listed in every report of the authors (Descartes 1.2.x default set)
#   - METHODS output (methods.json, the file the authors published) and JSON output (mutations.json)
# Test classes listed in descartes-excluded-tests.txt are excluded (PIT needs a green suite, see that file).
# targetClasses is set per module by run-descartes.sh; threads come from -Ddescartes.threads (default 1: with more
# threads, PDFBox tests that share files and download test data make PIT report spurious kills and timeouts).
# Usage: add-descartes-profile.sh <pdfbox_dir>
set -euo pipefail

root="${1:-pdfbox}"
pom="$root/parent/pom.xml"
here=$(cd "$(dirname "$0")" && pwd)
pitest_version="${PITEST_VERSION:-1.4.10}"
descartes_version="${DESCARTES_VERSION:-1.2.6}"

anchor='    </profiles>'
n=$(grep -cxF "$anchor" "$pom" || true)
if [ "$n" -ne 1 ]; then
  echo "expected 1 line '$anchor' in $pom, found $n" >&2
  exit 1
fi
if grep -q '<id>descartes</id>' "$pom"; then
  echo "profile descartes already present in $pom" >&2
  exit 1
fi

excluded=""
while IFS= read -r line; do
  line="${line%%#*}"
  line="$(echo "$line" | tr -d '[:space:]')"
  [ -n "$line" ] && excluded="$excluded                                <param>$line</param>"$'\n'
done < "$here/descartes-excluded-tests.txt"

mutators=""
for m in void null empty true false 0 1 '(short)0' '(short)1' '(byte)0' '(byte)1' 0L 1L 0.0 1.0 0.0f 1.0f "'\\40'" "'A'" '""' '"A"'; do
  mutators="$mutators                                <mutator>$m</mutator>"$'\n'
done

profile=$(cat <<EOF
        <profile>
            <id>descartes</id>
            <properties>
                <descartes.threads>1</descartes.threads>
            </properties>
            <build>
                <plugins>
                    <plugin>
                        <groupId>org.pitest</groupId>
                        <artifactId>pitest-maven</artifactId>
                        <version>$pitest_version</version>
                        <configuration>
                            <mutationEngine>descartes</mutationEngine>
                            <mutators>
$mutators                            </mutators>
                            <outputFormats>
                                <format>METHODS</format>
                                <format>JSON</format>
                            </outputFormats>
                            <excludedTestClasses>
$excluded                            </excludedTestClasses>
                            <threads>\${descartes.threads}</threads>
                            <timestampedReports>true</timestampedReports>
                        </configuration>
                        <dependencies>
                            <dependency>
                                <groupId>eu.stamp-project</groupId>
                                <artifactId>descartes</artifactId>
                                <version>$descartes_version</version>
                            </dependency>
                        </dependencies>
                    </plugin>
                </plugins>
            </build>
        </profile>
EOF
)

tmp=$(mktemp)
# The block goes through the environment: awk -v would expand the backslash in the '\40' mutator.
ANCHOR="$anchor" BLOCK="$profile" awk '$0 == ENVIRON["ANCHOR"] { print ENVIRON["BLOCK"] } { print }' "$pom" > "$tmp"
mv "$tmp" "$pom"
echo "descartes profile added to $pom (pitest-maven $pitest_version, descartes $descartes_version, $(echo -n "$mutators" | grep -c '<mutator>') mutators)"
