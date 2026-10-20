"""Compare two jar files entry by entry (content CRC), ignoring archive-level differences such as timestamps.

usage: compare_jars.py <jar_A> <jar_B> [output.txt]

Used to check that pdfbox-app-2.0.21.jar built from the sources has the same content as the jar the authors ran.
"""
import sys
import zipfile
from pathlib import Path


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    a, b = zipfile.ZipFile(argv[1]), zipfile.ZipFile(argv[2])
    ea = {i.filename: i for i in a.infolist() if not i.is_dir()}
    eb = {i.filename: i for i in b.infolist() if not i.is_dir()}
    common = sorted(set(ea) & set(eb))
    different = [n for n in common if ea[n].CRC != eb[n].CRC]
    classes = [n for n in common if n.endswith(".class")]
    lines = [f"A: {Path(argv[1]).name}, {Path(argv[1]).stat().st_size:,} bytes, {len(ea)} entries",
             f"B: {Path(argv[2]).name}, {Path(argv[2]).stat().st_size:,} bytes, {len(eb)} entries",
             f"only in A: {len(set(ea) - set(eb))}, only in B: {len(set(eb) - set(ea))}",
             f"identical entries: {len(common) - len(different)} / {len(common)} "
             f"(class files: {sum(1 for n in classes if ea[n].CRC == eb[n].CRC)} / {len(classes)})",
             "different entries:"] + [f"  {n}" for n in different]
    text = "\n".join(lines) + "\n"
    if len(argv) > 3:
        Path(argv[3]).write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
