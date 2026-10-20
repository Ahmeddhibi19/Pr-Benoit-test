"""Outcome of each command of the PDFBox workload, from the console output of run.sh.

usage: workload_log.py <console.log> [<reference_console.log>] [output.csv]

run.sh prints "<Command>  <file>" before each of its 50 JVM launches. For each command, the lines up to the next
command are classified: "error" if PDFBox prints an error or an exception, "usage" if it prints its usage message
(wrong arguments, e.g. PDFMerger with a single input file), otherwise "ok". Glowroot and JVM warnings are ignored.
With a reference log (the authors' execution.log), both outcomes are put side by side.
"""
import csv
import re
import sys
from pathlib import Path

COMMANDS = ("Encrypt", "Decrypt", "ExtractText", "ExtractImages", "PDFToImage", "TextToPDF", "PDFSplit", "PDFMerger",
            "WriteDecodedDoc", "OverlayPDF")
HEADER = re.compile(r"^(%s)\s+(\S+)\s*$" % "|".join(COMMANDS))
IGNORED = re.compile(r"org\.glowroot|^WARNING: |TraceCollector|^\s*$")


def parse(path):
    """[(command, file, status, first message)] in order."""
    runs = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = HEADER.match(line)
        if m:
            runs.append([m.group(1), m.group(2).rsplit("/", 1)[-1], "ok", ""])
        elif runs and not IGNORED.search(line):
            if runs[-1][2] == "ok":
                text = line.strip()
                if text.startswith("Usage:"):
                    runs[-1][2:] = ["usage", text[:120]]
                elif re.search(r"Error|Exception|error:", text):
                    runs[-1][2:] = ["error", text[:120]]
    return runs


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    ours = parse(argv[1])
    ref = parse(argv[2]) if len(argv) > 2 else []
    out = Path(argv[3]) if len(argv) > 3 else None
    ref_by_key = {(c, f): (s, msg) for c, f, s, msg in ref}
    rows = []
    for c, f, s, msg in ours:
        rs, rmsg = ref_by_key.get((c, f), ("", ""))
        rows.append({"command": c, "file": f, "status": s, "message": msg, "reference_status": rs,
                     "reference_message": rmsg, "same": (s == rs) if ref else ""})
    if out:
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["command"], lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    count = lambda runs, st: sum(1 for r in runs if r[2] == st)
    print(f"commands: {len(ours)} (ok {count(ours, 'ok')}, error {count(ours, 'error')}, usage {count(ours, 'usage')})")
    if ref:
        print(f"reference: {len(ref)} (ok {count(ref, 'ok')}, error {count(ref, 'error')}, usage {count(ref, 'usage')})")
        print(f"same outcome: {sum(1 for r in rows if r['same'])} / {len(rows)}")
    for r in rows:
        if r["status"] != "ok" or (ref and not r["same"]):
            print(f"  {r['command']:<16}{r['file']:<14}{r['status']:<7}{r['message'][:60]:<62}"
                  + (f"| reference: {r['reference_status']} {r['reference_message'][:50]}" if ref else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
