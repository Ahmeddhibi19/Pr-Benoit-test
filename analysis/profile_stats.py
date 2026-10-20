"""Statistics of the object profiles collected by PANKTI (paper, Section IV.C and Table III).

usage: profile_stats.py <profile_dir> <out_prefix> [--listing <zip_listing.csv> <prefix_in_zip>] [--fragments]

<profile_dir> holds, per target method, the files written by the PANKTI instrumentation (commit 0fddf27):
  <method>-count.txt                  "Invocation count for <method>: N" (cumulative over all JVM launches)
  <method>-object-profile-sizes.txt   one line per collected profile: its size in bytes
  <method>-receiving.xml, -params.xml, -returned.xml   the serialised objects
#INVOCATIONS is read from the count file and #COLLECTED is the number of lines of the sizes file.

The total on-disk size and the largest XML file of each method are computed from the XML files. When only a
listing of the replication archive is available (the raw XML of the authors is 5.9 GB), pass --listing with the
CSV written by setup/extract_zip.py and the folder of the profiles inside the archive.

With --fragments, the XML files are parsed as pankti-generate does (ObjectXMLParser, commit 0fddf27): each file is
a sequence of top-level elements, one per recorded object; the receiving, params and returned lists are paired by
position, and #UNIQUE is the number of distinct (receiving, params, returned) triples (params only for methods that
take parameters). Fragments are compared on their exact text, which pankti-generate compares after a deterministic
re-serialisation. Also reported: the number of fragments per file (they differ when a call threw or when entries of
nested calls interleave), and the maximum element depth of a fragment (its root element has depth 1).

Writes <out_prefix>.csv (one row per method) and <out_prefix>.txt (totals compared with the paper).
"""
import csv
import hashlib
import re
import sys
from pathlib import Path
from xml.parsers import expat

MIB = 2 ** 20
THRESHOLD_MIB = 200          # PANKTI stops collecting once one XML file of a method reaches 200 MiB
BIN_MIB = 10                 # bin width of Figure 5
XML_PARTS = ("-receiving.xml", "-params.xml", "-returned.xml")
PAPER = {"methods": 46, "invocations": 121175, "collected": 57563, "min_bytes": 158,
         "max": "nearly 55 MB", "total": "5.5 GB", "threshold_methods": 19, "unique": 13851, "depth": 36}


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


def scan_fragments(path):
    """Top-level elements of a PANKTI XML file: list of (sha1 of their exact text, maximum element depth)."""
    data = Path(path).read_bytes()
    prefix = b"<root>"
    fragments = []
    state = {"depth": 0, "start": 0, "max": 0}
    parser = expat.ParserCreate()

    def start(name, attrs):
        state["depth"] += 1
        if state["depth"] == 2:
            state["start"] = parser.CurrentByteIndex - len(prefix)
            state["max"] = 1
        elif state["depth"] > 2:
            state["max"] = max(state["max"], state["depth"] - 1)

    def end(name):
        if state["depth"] == 2:
            # expat points at "</name>" for an end tag, but just after "<name/>" for an empty element
            pos = parser.CurrentByteIndex - len(prefix)
            close = data.index(b">", pos) + 1 if data[pos:pos + 2] == b"</" else pos
            fragments.append((hashlib.sha1(data[state["start"]:close]).digest(), state["max"]))
        state["depth"] -= 1

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.Parse(prefix, False)
    parser.Parse(data, False)
    parser.Parse(b"</root>", True)
    return fragments


def fragment_stats(profile_dir, stem, has_params):
    """Fragment counts, #UNIQUE (pankti-generate rule) and maximum depth for one method."""
    parts = {}
    for part in XML_PARTS:
        f = Path(profile_dir) / f"{stem}{part}"
        parts[part] = scan_fragments(f) if f.exists() else []
    rec, par, ret = (parts[p] for p in XML_PARTS)
    # pankti-generate walks the receiving list and reads the others at the same index; it stops at the first index
    # missing in one of them (an exception it catches), so only the common prefix is paired.
    n = min(len(rec), len(ret), len(par) if has_params else len(rec))
    triples = {(rec[i][0], par[i][0] if has_params else b"", ret[i][0]) for i in range(n)}
    return {
        "receiving_fragments": len(rec), "params_fragments": len(par), "returned_fragments": len(ret),
        "paired": n, "unique": len(triples),
        "max_depth": max((d for frags in parts.values() for _, d in frags), default=0),
        "fragment_mismatch": len({len(rec), len(par), len(ret)}) > 1,
    }


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    profile_dir, out_prefix = Path(argv[1]), Path(argv[2])
    listing = prefix = None
    if "--listing" in argv:
        i = argv.index("--listing")
        listing, prefix = argv[i + 1], argv[i + 2]
    fragments = "--fragments" in argv

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
        if fragments:
            rows[-1].update(fragment_stats(profile_dir, stem, params != ""))

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
    if fragments:
        mismatched = [r for r in rows if r["fragment_mismatch"]]
        lines += [
            f"#UNIQUE total (pankti-generate rule): {sum(r['unique'] for r in rows):,} (paper: {PAPER['unique']:,})",
            f"maximum element depth in a fragment: {max(r['max_depth'] for r in rows)} (paper: {PAPER['depth']})",
            f"methods whose receiving/params/returned files hold different numbers of fragments: {len(mismatched)}",
        ] + [f"  {r['class']}.{r['method']}({r['params']}): receiving {r['receiving_fragments']}, "
             f"params {r['params_fragments']}, returned {r['returned_fragments']}, collected {r['collected']}"
             for r in mismatched]
    text = "\n".join(lines) + "\n"
    Path(f"{out_prefix}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
