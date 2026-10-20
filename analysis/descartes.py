"""Shared helpers for Descartes `methods.json` reports and PANKTI method lists.

A method is identified by (class FQN, method name, parameter descriptor), e.g.
("org.apache.pdfbox.pdmodel.font.PDSimpleFont", "toUnicode", "I"). The parameter descriptor is the part between
parentheses of the JVM descriptor that Descartes writes in the `description` field; PANKTI's method lists
(`extracted-methods-*.csv`, `invoked-methods.csv`) store the same string in `param-signature`. This is also the key
used by the authors' `find-pseudo-tested.py`. Matching on the name alone merges overloads
(`PDSimpleFont.toUnicode(int)` is pseudo-tested, `toUnicode(int, GlyphList)` is tested).
"""
import csv
import json
import re
from pathlib import Path

CLASSIFICATIONS = ["tested", "partially-tested", "pseudo-tested", "not-covered"]


def param_descriptor(description):
    """'(ILjava/lang/String;)V' -> 'ILjava/lang/String;'"""
    return re.match(r"\((.*)\)", description).group(1)


def method_key(method):
    """Key of a methods.json entry."""
    fqn = method["package"].replace("/", ".") + "." + method["class"]
    return fqn, method["name"], param_descriptor(method["description"])


def load_report(path):
    """methods.json -> {key: method entry}."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    methods = {}
    for m in data["methods"]:
        key = method_key(m)
        if key in methods:
            raise ValueError(f"{path}: duplicate method {key}")
        methods[key] = m
    return methods


def load_reports(paths):
    """Merge several methods.json files (one per module). A method found in two reports is an error."""
    merged = {}
    for p in paths:
        for key, m in load_report(p).items():
            if key in merged:
                raise ValueError(f"{p}: method {key} already found in another report")
            merged[key] = m
    return merged


def find_reports(root):
    """All methods.json files below root, sorted."""
    return sorted(Path(root).glob("**/methods.json"))


def mutators(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f).get("analysis", {}).get("mutators", [])


def well_tested(classification):
    """Paper, Section III.E, metric 14: a target that is no longer pseudo-tested is "well-tested".
    After tests are added a covered method is tested, partially-tested or pseudo-tested."""
    return classification in ("tested", "partially-tested")


def load_method_list(path):
    """PANKTI CSV (extracted-methods, instrumentation-candidates, invoked-methods) -> list of (key, row)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [((r["parent-FQN"], r["method-name"], r["param-signature"] or ""), r) for r in rows]


def table3_keys(invoked_methods_csv, table3_rows):
    """Map the paper's Table III names ("Class_method") to full method keys, using the authors' invoked-methods.csv.
    Raises if a name is ambiguous or missing, so that overloads can never be merged silently."""
    by_name = {}
    for key, _ in load_method_list(invoked_methods_csv):
        simple = key[0].rsplit(".", 1)[1].split("$")[-1]
        by_name.setdefault(f"{simple}_{key[1]}", []).append(key)
    result = {}
    for name in table3_rows:
        keys = by_name.get(name, [])
        if len(keys) != 1:
            raise ValueError(f"Table III method {name}: {len(keys)} matches in {invoked_methods_csv}")
        result[name] = keys[0]
    return result
