"""List or selectively extract a (Zip64) archive.

usage:
  extract_zip.py list <zip> <listing.csv>
  extract_zip.py extract <zip> <dest> <prefix> [--exclude-suffix SUFFIX ...]

Info-ZIP's unzip lists the replication archive but does not match file patterns in it, hence this script.
"""
import csv
import sys
import zipfile
from pathlib import Path


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    mode, archive = argv[1], argv[2]
    with zipfile.ZipFile(archive) as z:
        if mode == "list":
            with open(argv[3], "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["name", "size", "compressed_size", "date"])
                for i in z.infolist():
                    w.writerow([i.filename, i.file_size, i.compress_size, "%04d-%02d-%02d" % i.date_time[:3]])
            print(f"{len(z.infolist())} entries listed")
            return 0
        dest, prefix = Path(argv[3]), argv[4]
        excluded = argv[argv.index("--exclude-suffix") + 1:] if "--exclude-suffix" in argv else []
        count = size = 0
        for i in z.infolist():
            if i.is_dir() or not i.filename.startswith(prefix) or i.filename.endswith(tuple(excluded)):
                continue
            z.extract(i, dest)
            count += 1
            size += i.file_size
        print(f"{count} files extracted ({size / 1e6:.1f} MB) under {dest / prefix}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
