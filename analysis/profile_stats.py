"""Statistics of the object profiles collected by PANKTI (paper, Section IV.C and Table III).

usage: profile_stats.py <profile_dir> <out_prefix> [--listing <zip_listing.csv> <prefix_in_zip>]

<profile_dir> holds, per target method, the files written by the PANKTI instrumentation (commit 0fddf27):
  <method>-count.txt                  "Invocation count for <method>: N" (cumulative over all JVM launches)
  <method>-object-profile-sizes.txt   one line per collected profile: its size in bytes
  <method>-receiving.xml, -params.xml, -returned.xml   the serialised objects
#INVOCATIONS is read from the count file and #COLLECTED is the number of lines of the sizes file.

The total on-disk size and the largest XML file of each method are computed from the XML files. When only a
listing of the replication archive is available (the raw XML of the authors is 5.9 GB), pass --listing with the
CSV written by setup/extract_zip.py and the folder of the profiles inside the archive.

Writes <out_prefix>.csv (one row per method) and <out_prefix>.txt (totals compared with the paper).
"""
import csv
import re
import sys
from pathlib import Path

MIB = 2 ** 20
THRESHOLD_MIB = 200          # PANKTI stops collecting once one XML file of a method reaches 200 MiB
BIN_MIB = 10                 # bin width of Figure 5
XML_PARTS = ("-receiving.xml", "-params.xml", "-returned.xml")
PAPER = {"methods": 46, "invocations": 121175, "collected": 57563, "min_bytes": 158,
         "max": "nearly 55 MB", "total": "5.5 GB", "threshold_methods": 19}


def split_method(stem):
    """'org.apache.fontbox.ttf.NamingTable.getName_int,int,int,int' -> (class FQN, method, 'int,int,int,int')."""
    name, _, params = stem.partition("_")
    fqn, method = name.rsplit(".", 1)
    return fqn, method, params


def xml_sizes(profile_dir, listing, prefix):
    """{(method stem, part): bytes} for the XML files, from the directory or from the archive listing."""
    sizes = {}
    if listing:
        with open(listing, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                name = r["name"]
                if name.startswith(prefix):
                    sizes[name[len(prefix):]] = int(r["size"])
    else:
        for p in Path(profile_dir).glob("*.xml"):
            sizes[p.name] = p.stat().st_size
    result = {}
    for name, size in sizes.items():
        for part in XML_PARTS:
            if name.endswith(part):
                result[(name[:-len(part)], part)] = size
    return result


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    profile_dir, out_prefix = Path(argv[1]), Path(argv[2])
    listing = prefix = None
    if "--listing" in argv:
        i = argv.index("--listing")
        listing, prefix = argv[i + 1], argv[i + 2]

    xml = xml_sizes(profile_dir, listing, prefix)
    rows = []
    all_sizes = []
    for count_file in sorted(profile_dir.glob("*-count.txt")):
        stem = count_file.name[:-len("-count.txt")]
        text = count_file.read_text(encoding="utf-8", errors="replace")
        invocations = int(re.search(r"(\d+)\s*$", text).group(1))
        sizes_file = profile_dir / f"{stem}-object-profile-sizes.txt"
        sizes = [int(x) for x in sizes_file.read_text().split()] if sizes_file.exists() else []
        all_sizes += sizes
        parts = [xml.get((stem, part)) for part in XML_PARTS]
        largest_part = max((p for p in parts if p is not None), default=None)
        fqn, method, params = split_method(stem)
        rows.append({
            "class": fqn, "method": method, "params": params,
            "invocations": invocations, "collected": len(sizes),
            "threshold_hit": len(sizes) < invocations,
            "largest_xml_mib": round(largest_part / MIB, 1) if largest_part is not None else "",
            "xml_bytes": sum(p for p in parts if p is not None) if any(p is not None for p in parts) else "",
            "min_profile_bytes": min(sizes) if sizes else "",
            "max_profile_bytes": max(sizes) if sizes else "",
        })

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out_prefix}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: -r["invocations"]))

    total_xml = sum(xml.values())
    capped = [r for r in rows if r["threshold_hit"]]
    bins = [0] * 6
    for s in all_sizes:
        bins[min(int(s / (BIN_MIB * MIB)), len(bins) - 1)] += 1
    lines = [
        f"methods with a count file : {len(rows)} (paper: {PAPER['methods']})",
        f"#INVOCATIONS total        : {sum(r['invocations'] for r in rows):,} (paper: {PAPER['invocations']:,})",
        f"#COLLECTED total          : {len(all_sizes):,} (paper: {PAPER['collected']:,})",
        f"smallest profile          : {min(all_sizes):,} bytes (paper: {PAPER['min_bytes']} bytes)",
        f"largest profile           : {max(all_sizes):,} bytes = {max(all_sizes) / 1e6:.1f} MB = "
        f"{max(all_sizes) / MIB:.1f} MiB (paper: {PAPER['max']})",
        f"XML files on disk         : {total_xml:,} bytes = {total_xml / 1e9:.2f} GB = {total_xml / 2 ** 30:.2f} GiB "
        f"(paper: {PAPER['total']})",
        f"collected < invocations   : {len(capped)} methods (paper: {PAPER['threshold_methods']} hit the "
        f"{THRESHOLD_MIB} MB threshold)",
        f"  of which with an XML file >= {THRESHOLD_MIB} MiB: "
        f"{sum(1 for r in capped if r['largest_xml_mib'] != '' and r['largest_xml_mib'] >= THRESHOLD_MIB)}",
        f"profile sizes per {BIN_MIB} MiB bin (Figure 5): "
        + ", ".join(f"[{i * BIN_MIB}-{(i + 1) * BIN_MIB}) {n}" for i, n in enumerate(bins[:-1]))
        + f", >= {(len(bins) - 1) * BIN_MIB}: {bins[-1]}",
    ]
    text = "\n".join(lines) + "\n"
    Path(f"{out_prefix}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
