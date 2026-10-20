"""Compare the profile metrics of a workload run with Table III (columns #INVOCATIONS, #COLLECTED, #UNIQUE).

usage: compare_table3.py <ours.csv> <authors.csv> <authors_invoked-methods.csv> <out_prefix>

<ours.csv> and <authors.csv> are outputs of profile_stats.py --fragments (this reproduction's profiles and the
authors' replication data). The authors' invoked-methods.csv gives the parameter types of the 46 methods of
Table III, so that overloaded methods are matched exactly. Writes <out_prefix>.csv (one row per method invoked in
either run, with the paper's values when the method is in Table III) and <out_prefix>.txt (summary).
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLUMNS = ["invocations", "collected", "unique"]


def norm(params):
    return params.replace(" ", "")


def load_stats(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["class"], r["method"], norm(r["params"])): r for r in csv.DictReader(f)}


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    ours, authors = load_stats(argv[1]), load_stats(argv[2])
    out = Path(argv[4])
    with open(HERE / "paper" / "table3_pdfbox.csv", newline="") as f:
        paper = {r["class_method"]: r for r in csv.DictReader(f)}
    names = {}
    with open(argv[3], newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["parent-FQN"], r["method-name"], norm(r["param-list"]))
            names[key] = r["parent-FQN"].rsplit(".", 1)[1] + "_" + r["method-name"]
    assert sorted(names.values()) == sorted(paper), "invoked-methods.csv does not match Table III"

    rows = []
    for key in sorted(set(ours) | set(names), key=lambda k: -int(ours[k]["invocations"]) if k in ours else 0):
        p = paper.get(names.get(key, ""), {})
        o, a = ours.get(key, {}), authors.get(key, {})
        row = {"row": p.get("row", ""), "class": key[0], "method": key[1], "params": key[2],
               "in_table3": bool(p), "invoked_here": bool(o)}
        for c in COLUMNS:
            row[f"paper_{c}"] = p.get(c, "")
            row[f"authors_{c}"] = a.get(c, "")
            row[f"ours_{c}"] = o.get(c, "")
        row["ours_threshold_hit"] = o.get("threshold_hit", "")
        row["ours_max_depth"] = o.get("max_depth", "")
        rows.append(row)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    eff_paper = set(names)
    eff_ours = set(ours)
    both = eff_paper & eff_ours
    total = lambda src, c, keys: sum(int(src[k][c]) for k in keys if k in src)
    lines = [f"#EFF_TARGET: ours {len(eff_ours)}, paper 46; in both {len(both)}, "
             f"Jaccard {len(both) / len(eff_paper | eff_ours):.3f}"]
    for label, keys in (("only in the paper", eff_paper - eff_ours), ("only in this run", eff_ours - eff_paper)):
        lines.append(f"  {label}: {len(keys)}")
        lines += [f"    {k[0]}.{k[1]}({k[2]})" + (f"  [{ours[k]['invocations']} invocations]" if k in ours else "")
                  for k in sorted(keys)]
    lines.append("")
    lines.append(f"{'totals':<34}{'paper':>10}{'ours':>10}")
    for c in COLUMNS:
        lines.append(f"  {c:<32}{sum(int(p[c]) for p in paper.values()):>10,}{total(ours, c, eff_ours):>10,}")
    inv, col, uni = (total(ours, c, eff_ours) for c in COLUMNS)
    lines.append(f"  {'collected / invocations':<32}{'47.5%':>10}{col / inv:>10.1%}")
    lines.append(f"  {'unique / collected':<32}{'24.0%':>10}{uni / col:>10.1%}")
    capped = [k for k in eff_ours if ours[k]["threshold_hit"] == "True"]
    lines.append(f"  {'methods with collected < inv.':<32}{19:>10}{len(capped):>10}")
    lines.append("")
    same = {c: sum(1 for k in both if int(ours[k][c]) == int(paper[names[k]][c])) for c in COLUMNS}
    lines.append(f"Table III methods invoked here: {len(both)} / 46; identical values: "
                 + ", ".join(f"{c} {same[c]}" for c in COLUMNS))
    isfill = ("org.apache.pdfbox.pdmodel.graphics.state.RenderingMode", "isFill", "")
    if isfill in ours:
        r = ours[isfill]
        ok = (r["invocations"], r["collected"], r["unique"], r["min_profile_bytes"], r["max_profile_bytes"]) == \
             ("30944", "30944", "1", "158", "158")
        lines.append(f"isFill: {r['invocations']} invocations, {r['collected']} collected, {r['unique']} unique, "
                     f"profiles of {r['min_profile_bytes']}-{r['max_profile_bytes']} bytes "
                     f"(paper: 30,944 / 30,944 / 1 / 158 bytes) -> {'EXACT MATCH' if ok else 'differs'}")
    text = "\n".join(lines) + "\n"
    Path(f"{out}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
