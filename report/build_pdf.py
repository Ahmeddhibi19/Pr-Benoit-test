"""Build report/rapport.pdf from report/rapport.md: Markdown -> HTML (python-markdown) -> PDF (headless Chrome or
Chromium, which renders the tables and the figures as on GitHub).

usage: python report/build_pdf.py [chrome_executable]

The browser is taken from the argument, the CHROME environment variable, or the usual install locations.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CANDIDATES = [
    "google-chrome", "chromium", "chromium-browser", "chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #202124; }
h1 { font-size: 17pt; margin: 0 0 6pt; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; border-bottom: 1px solid #dadce0; padding-bottom: 2pt; break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; break-after: avoid; }
table { border-collapse: collapse; margin: 6pt 0; font-size: 8.5pt; width: 100%; break-inside: auto; }
th, td { border: 1px solid #dadce0; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f1f3f4; }
tr { break-inside: avoid; }
code { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 8.5pt; background: #f1f3f4; padding: 0 2pt; }
pre code { display: block; padding: 4pt; white-space: pre-wrap; }
img { max-width: 100%; }
blockquote { margin: 6pt 0; padding-left: 8pt; border-left: 3px solid #dadce0; color: #5f6368; }
"""


LIST_ITEM = re.compile(r"^(\s*)(?:[-*] |\d+\. )")


def prepare(src):
    """Adapt GitHub-flavoured lists to python-markdown, which needs a blank line before a list and four spaces of
    indentation for a nested item. The Markdown file itself is not changed (GitHub renders it as written)."""
    out, fenced = [], False
    for line in src.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        m = None if fenced else LIST_ITEM.match(line)
        if m:
            indent = len(m.group(1))
            if 0 < indent < 4:
                line = "    " + line[indent:]
            prev = out[-1] if out else ""
            if prev.strip() and not LIST_ITEM.match(prev) and not prev.startswith("    "):
                out.append("")
        out.append(line)
    return "\n".join(out) + "\n"


def browser(argv):
    for c in ([argv[1]] if len(argv) > 1 else []) + ([os.environ["CHROME"]] if "CHROME" in os.environ else []) + CANDIDATES:
        path = shutil.which(c) or (c if Path(c).is_file() else None)
        if path:
            return path
    raise SystemExit("no Chrome / Chromium / Edge found; pass its path as argument")


def main(argv):
    source = HERE / "rapport.md"
    html = markdown.markdown(prepare(source.read_text(encoding="utf-8")),
                             extensions=["tables", "fenced_code", "sane_lists"])
    page = (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Rapport de reproduction</title>"
            f"<style>{CSS}</style></head><body>{html}</body></html>")
    # the HTML is written next to the Markdown so that the relative image paths (../results/...) resolve
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=HERE, delete=False, encoding="utf-8") as f:
        f.write(page)
        tmp = Path(f.name)
    out = HERE / "rapport.pdf"
    try:
        subprocess.run([browser(argv), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", tmp.as_uri()], check=True, capture_output=True, timeout=120)
    finally:
        tmp.unlink()
    print(f"{out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
