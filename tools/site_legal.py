"""privacy.html and terms.html wear the site's look (design v3, 2026-11-22): cream paper by day, the museum teal by night, Cairo
titles and Almarai text, like the home page. The two pages are hand-written in the Pages repo (their TEXT is never touched
here); every build swaps only their look: the <style> block, the theme-color meta and the fonts link, plus the back link's
arrow (in a right-to-left page «back» points right). Idempotent: a second run changes nothing; CRLF pages keep CRLF; a page
whose head does not have the expected shape is left alone (never a broken page).

Imported by build_site.py (install_pages.py ships it as tools/site_legal.py). Pure text work, no network.
"""
from __future__ import annotations

import re
from pathlib import Path

FONTS = "https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Cairo:wght@700;800;900&display=swap"
PAGES = ("privacy.html", "terms.html")
THEME = ('<meta name="theme-color" content="#F3EEE3" media="(prefers-color-scheme: light)">'
         '<meta name="theme-color" content="#0B2E37" media="(prefers-color-scheme: dark)">')
CSS = """
    :root{color-scheme:light dark;--bg:#F3EEE3;--panel:#FBF7EE;--text:#14232B;--muted:#4D5D63;--gold:#F6C445;--teal:#0F4C5C;--line:#14232B;--focus:#1A7089}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font-family:"Almarai",Tahoma,sans-serif;line-height:1.95}
    a{color:var(--teal);text-underline-offset:3px}
    a:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
    .container{width:min(820px,100% - 32px);margin:auto}
    header{border-bottom:2px solid var(--line)}
    footer{border-top:2px solid var(--line);color:var(--muted)}
    nav,footer{padding:6px 0}
    nav{display:flex;justify-content:space-between;gap:0 16px;flex-wrap:wrap}
    nav a,footer a{display:inline-flex;align-items:center;min-height:44px;text-decoration:none;font-weight:700}
    main{padding:34px 0 56px}
    .eyebrow{display:inline-block;font-family:"Cairo","Almarai",sans-serif;font-weight:800;color:var(--teal);
      border-bottom:3px solid var(--gold);line-height:1.6}
    h1,h2{font-family:"Cairo","Almarai",sans-serif;text-wrap:balance}
    h1{font-weight:900;font-size:clamp(2rem,6vw,3rem);line-height:1.3;margin:10px 0 8px}
    h2{font-weight:800;font-size:1.25rem;line-height:1.5;margin:34px 0 6px;padding-inline-start:12px;border-inline-start:4px solid var(--gold)}
    p,li{color:var(--muted)}
    .notice{padding:16px 20px;background:var(--panel);border:2px solid var(--line);box-shadow:5px 5px 0 var(--gold)}
    @media (prefers-color-scheme:dark){
      :root{--bg:#0B2E37;--panel:#06222C;--text:#F3EEE3;--muted:#D9E3E2;--teal:#F6C445;--line:rgba(246,196,69,.55);--focus:#F6C445}
      h1{color:#F6C445}
      .eyebrow{color:#F3EEE3}
      .notice{border:1px solid rgba(246,196,69,.75);box-shadow:inset 0 0 0 4px #06222C,inset 0 0 0 5px rgba(246,196,69,.35)}
    }
  """
BACK_OLD, BACK_NEW = "← العودة إلى أصل الحكاية", "→ العودة إلى أصل الحكاية"


def apply(page: str) -> str:
    """The page with the site's look; unchanged when it lacks a <head> with one <style> block."""
    nl = "\r\n" if "\r\n" in page else "\n"
    text = page.replace("\r\n", "\n")
    head_end = text.find("</head>")
    if head_end < 0 or text.count("<style>", 0, head_end) != 1 or "</style>" not in text[:head_end]:
        return page
    head, body = text[:head_end], text[head_end:]
    head = re.sub(r"<style>.*?</style>", lambda _m: "<style>" + CSS + "</style>", head, count=1, flags=re.S)
    metas = re.findall(r"[ \t]*<meta name=\"theme-color\"[^>]*>\n?", head)
    if metas:
        head = head.replace(metas[0], "  " + THEME + "\n", 1)
        for extra in metas[1:]:
            head = head.replace(extra, "", 1)
    if FONTS not in head:
        head = head.replace("  <style>", f'  <link rel="stylesheet" href="{FONTS}">\n  <style>', 1)
    body = body.replace(BACK_OLD, BACK_NEW)
    out = head + body
    return out.replace("\n", nl)


def update(site: Path) -> list[str]:
    """Apply to the site folder's legal pages that exist; returns the names changed."""
    changed = []
    for name in PAGES:
        f = Path(site) / name
        if not f.is_file():
            continue
        old = f.read_bytes().decode("utf-8")
        new = apply(old)
        if new != old:
            f.write_bytes(new.encode("utf-8"))
            changed.append(name)
    return changed
