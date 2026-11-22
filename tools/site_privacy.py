"""privacy.html follows the suggestion box: the hand-written page (Pages repo) must describe exactly what is live.

build_site.py calls update(site_dir, box) on every build. The texts live in privacy_box_section.html (next to this file; shipped
to the Pages repo's tools/ by install_pages.py). Each named block there has a «form» variant (today's text, byte-exact) and a
«box» variant (the text for SUGGEST_WORKER_URL set).

How the swap works (idempotent, marker-based):
- box on: each block is found between its markers <!--asl:NAME--> ... <!--/asl:NAME--> and set to the «box» text. The first
  time (no markers yet) the «form» text is found once in the page and wrapped in markers. A block found neither way stops the
  build: the box never goes live with a privacy page that does not describe it.
- box off: blocks inside markers go back to the «form» text (a clean rollback); a page without markers is left byte-for-byte
  alone (so today's live page does not change at all).
Line endings of the page (CRLF in a Windows checkout) are kept.
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "privacy_box_section.html"
BLOCK_RE = re.compile(r"<!-- (form|box):([a-z][a-z-]*) -->\n(.*?)\n<!-- /\1:\2 -->", re.S)


def blocks(source: Path = SOURCE) -> dict[str, dict[str, str]]:
    """{name: {"form": text, "box": text}} from the source file; a block missing either variant is an error."""
    out: dict[str, dict[str, str]] = {}
    for kind, name, text in BLOCK_RE.findall(source.read_text(encoding="utf-8").replace("\r\n", "\n")):
        out.setdefault(name, {})[kind] = text
    bad = [n for n, v in out.items() if set(v) != {"form", "box"}]
    if not out or bad:
        raise SystemExit(f"{source.name}: every block needs a form and a box variant (bad: {bad or 'no blocks'})")
    return out


def apply(page: str, box: bool, texts: dict[str, dict[str, str]]) -> str:
    crlf = "\r\n" in page
    html = page.replace("\r\n", "\n")
    for name, v in texts.items():
        start, end = f"<!--asl:{name}-->", f"<!--/asl:{name}-->"
        want = v["box" if box else "form"]
        marked = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.S)
        if marked.search(html):
            html = marked.sub(lambda m: start + want + end, html, count=1)
        elif box:
            if html.count(v["form"]) != 1:
                raise SystemExit(f"privacy.html: block «{name}» not found (hand-edited?): update privacy_box_section.html first")
            html = html.replace(v["form"], start + want + end)
    return html.replace("\n", "\r\n") if crlf else html


def update(site: Path, box: bool, source: Path = SOURCE) -> bool:
    """Rewrite SITE/privacy.html when its blocks are not in the wanted state. Returns True when the file changed."""
    page_path = site / "privacy.html"
    if not page_path.is_file():
        if box:
            raise SystemExit("privacy.html is missing: the suggestion box needs the privacy page")
        return False
    old = page_path.read_bytes().decode("utf-8")
    new = apply(old, box, blocks(source))
    if new == old:
        return False
    page_path.write_bytes(new.encode("utf-8"))
    return True
