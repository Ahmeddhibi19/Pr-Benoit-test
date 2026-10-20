#!/usr/bin/env bash
# Build the PANKTI Glowroot plugin for a list of target methods, with the authors' own generator.
#   1. copy the PANKTI sources (parent POM + pankti-instrument) to a work directory, so the checkout stays clean;
#   2. run instrument.py: one aspect class per target (MethodAspect1..N, copied from MethodAspect0) and their names
#      in META-INF/glowroot.plugin.json;
#   3. build the jar-with-dependencies (Glowroot plugin API 0.13.6, XStream 1.4.12);
#   4. check that the jar holds exactly one aspect per target, and write a manifest (aspect -> target method).
# instrument.py needs pandas and numpy. Usage: build-plugin.sh <pankti_dir> <targets.csv> <out_dir>
# Extra Maven arguments can be passed in MAVEN_EXTRA_ARGS; PYTHON selects the interpreter (default: python).
set -euo pipefail

pankti=$(cd "$1" && pwd)
targets=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
mkdir -p "$3"
out=$(cd "$3" && pwd)
python="${PYTHON:-python}"
read -r -a extra <<< "${MAVEN_EXTRA_ARGS:-}"

work="$out/src"
rm -rf "$work"
mkdir -p "$work"
cp "$pankti/pom.xml" "$work/"
cp -r "$pankti/pankti-instrument" "$work/"
echo "pankti $(git -C "$pankti" rev-parse HEAD)" > "$out/versions.txt"

(cd "$work/pankti-instrument" && PYTHONUTF8=1 "$python" instrument.py "$targets" 2>&1 \
  | grep -v -E 'FutureWarning|DeprecationWarning' | tee "$out/instrument.log")

# The parent POM lists three modules; only pankti-instrument is copied, so it is built on its own.
(cd "$work" && mvn -B -q "${extra[@]}" -N install && cd pankti-instrument && mvn -B -q "${extra[@]}" package -DskipTests)
cp "$work"/pankti-instrument/target/pankti-instrument-*-jar-with-dependencies.jar "$out/pankti-plugin.jar"
cp "$work/pankti-instrument/src/main/resources/META-INF/glowroot.plugin.json" "$out/"

# Manifest: aspect class -> target method, read back from the generated sources.
"$python" - "$work/pankti-instrument/src/main/java/se/kth/castor/pankti/instrument/plugins" "$out" "$targets" <<'EOF'
import csv, json, re, sys, zipfile
from pathlib import Path
src, out, targets = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
rows = []
for f in sorted(src.glob("MethodAspect*.java"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))):
    n = int(re.search(r"(\d+)", f.stem).group(1))
    if n == 0:
        continue
    text = f.read_text(encoding="utf-8")
    cls = re.search(r'className = "([^"]+)"', text).group(1)
    name = re.search(r'methodName = "([^"]+)"', text).group(1)
    params = re.search(r"methodParameterTypes = \{([^}]*)\}", text).group(1).replace('"', "").replace(" ", "")
    rows.append({"aspect": f"MethodAspect{n}", "class": cls, "method": name, "params": params})
with open(out / "aspects.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["aspect", "class", "method", "params"], lineterminator="\n")
    w.writeheader(); w.writerows(rows)

with open(targets, newline="", encoding="utf-8") as fh:
    expected = sorted((r["parent-FQN"], r["method-name"], r["param-list"].replace(" ", "")) for r in csv.DictReader(fh))
generated = sorted((r["class"], r["method"], r["params"]) for r in rows)
listed = json.loads((out / "glowroot.plugin.json").read_text(encoding="utf-8"))["aspects"]
with zipfile.ZipFile(out / "pankti-plugin.jar") as z:
    in_jar = {n for n in z.namelist() if re.fullmatch(r"se/kth/castor/pankti/instrument/plugins/MethodAspect[1-9]\d*\.class", n)}
checks = {
    "one aspect per target": generated == expected,
    "aspects listed in glowroot.plugin.json": sorted(listed) == sorted(f"se.kth.castor.pankti.instrument.plugins.{r['aspect']}" for r in rows),
    "aspect classes in the jar": len(in_jar) == len(rows),
}
lines = [f"targets: {len(expected)}, generated aspects: {len(rows)}, listed: {len(listed)}, classes in jar: {len(in_jar)}"]
lines += [("OK   " if ok else "FAIL ") + name for name, ok in checks.items()]
(out / "checks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
sys.exit(0 if all(checks.values()) else 1)
EOF
(cd "$out" && sha256sum pankti-plugin.jar >> versions.txt)
rm -rf "$work"
cat "$out/versions.txt"
