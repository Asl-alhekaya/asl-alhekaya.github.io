"""Everything below the home page's first screen, and the links hub (design v3, 2026-11-22, owner «نسوي تصميم خاص للموقع»):
the site's own episode card, section headings, the museum-label panels, buttons and the footer, day (cream paper) and night
(the museum: star-wall teal, gold hairlines, brass plaques), following prefers-color-scheme like the first screen.

The episode card: the art (assets/cards/<id>.webp, made by make_card_art.py: the object on the pedestal under the beam) in a
gold-lined window, the title as REAL text on a brass plaque (no text is baked into the picture), the series part as a small
label. An episode without card art shows its old cover as a framed painting in the same window (never a broken tile).

Imported by build_site.py (a sibling file; install_pages.py ships it to the Pages repo as tools/site_lower.py, a test fails when
the copy drifts). Pure functions of their arguments: no file, no network, no clock. No Pillow: the cloud build only links.
Strict-CSP rules kept: no inline script, no inline style attribute, no url() in this CSS (the links hub lives at two depths,
/links.html and /l/, so every picture is an <img> with a root-relative path given by the caller).
"""
from __future__ import annotations

import html
import re

E = html.escape
CARD_W, CARD_H = 400, 500  # the card art's pixels (4:5); the <img> carries them, so nothing shifts while it loads
CARDS_DIR = "assets/cards"


def card_file(eid: str) -> str:
    """The one naming rule of a card picture (make_card_art.py writes it, the build links it): EP-26 -> ep-26.webp."""
    return f"{eid.lower()}.webp"


def split_title(ep: dict) -> tuple[str, str]:
    """(plaque title, small label). A series part «الساعة · الجزء 2: X» shows X on the plaque and «الساعة · الجزء 2» as the
    label (a chip at the top of the picture, so every plaque keeps one height); a part without its own name shows the series
    name on the plaque."""
    title, series, part = ep.get("title", ""), ep.get("series"), ep.get("part")
    if not series:
        return title, ""
    label = f"{series}" + (f" · الجزء {part}" if part else "")
    m = re.match(rf"^\s*{re.escape(series)}\s*·\s*الجزء\s*{part}\s*:?\s*(.*)$", title) if part else None
    if m:
        return (m.group(1).strip() or series), label
    return title, label


def card(ep: dict, *, art: str | None, cover: str | None, url: str, alt_links: str = "", root: str = "",
         heading: str = "h3", lazy: bool = True) -> str:
    """One episode card. art/cover: site-relative paths of existing files (or None); url: the YouTube link."""
    title, label = split_title(ep)
    load = ' loading="lazy" decoding="async"' if lazy else ""
    if art:
        pic = f'<img src="{root}{E(art)}" alt="" width="{CARD_W}" height="{CARD_H}"{load}>'
        kind = "art"
    elif cover:
        pic = f'<img src="{root}{E(cover)}" alt="" width="540" height="960"{load}>'
        kind = "art paint"
    else:
        pic, kind = "", "art empty"
    lab = f'<span class="lab">{E(label)}</span>' if label else ""  # inside the picture window, top centre
    alt = f'<p class="also">{alt_links}</p>' if alt_links else ""
    return (f'<li class="ep"><a class="ep-a" href="{E(url)}" rel="noopener" target="_blank">'
            f'<span class="{kind}">{pic}{lab}</span>'
            f'<span class="plq"><{heading} class="ttl">{E(title)}</{heading}></span></a>{alt}</li>')


def grid(cards: list[str], cls: str = "") -> str:
    return f'<ul class="cards{(" " + cls) if cls else ""}" role="list">{"".join(cards)}</ul>'


def heading(text: str, hid: str, tag: str = "h2") -> str:
    """A section title in the brass language: the words between two rules with a gold diamond (day: ink lines)."""
    return f'<{tag} class="sec-h" id="{hid}"><i aria-hidden="true"></i><span>{E(text)}</span><i aria-hidden="true"></i></{tag}>'


# ---------------------------------------------------------------- CSS
# Scope: everything is under .low (the lower page wrapper on index.html, the <main> of the links hub), so the first screen
# (.stage, site_home.py) keeps its own rules. Day first; NIGHT rules start with N and site_home.night() writes them inside
# @media (prefers-color-scheme:dark).
DAY_CSS = r"""
.low,.low *,.low *::before,.low *::after{box-sizing:border-box}
.low{--ink:#14232B;--muted:#4D5D63;--paper:#FBF7EE;--teal:#0F4C5C;--gold:#F6C445;--goldD:#b8862b;--focus:#1A7089;
  --gold-grad:linear-gradient(135deg,#fff0a8 0%,#F6C445 28%,#b8862b 52%,#f6d77a 74%,#9a6a12 100%);
  color:var(--ink);font-family:"Almarai",Tahoma,sans-serif;line-height:1.8}
.low h2,.low h3,.low .sec-h{font-family:"Cairo","Almarai",Tahoma,sans-serif;margin:0;text-wrap:balance}
.low a{color:inherit}
.low a:focus-visible,.low summary:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
.low .sec{padding-block:30px 6px}
.low .sec-h{display:flex;align-items:center;justify-content:center;gap:12px;font-size:24px;font-weight:800;line-height:1.4;
  text-align:center;margin:0 auto 6px;max-width:520px;color:var(--ink)}
.low .sec-h i{flex:1;height:2px;background:var(--ink);position:relative;min-width:24px}
.low .sec-h i::after{content:"";position:absolute;top:50%;width:9px;height:9px;margin-top:-4.5px;background:var(--gold);
  clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}
.low .sec-h i:first-child::after{left:-2px}
.low .sec-h i:last-child::after{right:-2px}
.low .sub{color:var(--muted);text-align:center;margin:0 auto 16px;max-width:52ch;font-size:15px}

/* the episode card: equal heights, real-text titles, nothing tilted */
.low .cards{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 12px}
.low .ep{display:flex;flex-direction:column;min-width:0}
.low .ep-a{position:relative;display:flex;flex-direction:column;text-decoration:none;background:var(--paper);
  border:2px solid var(--ink);box-shadow:5px 5px 0 var(--gold);padding:6px 6px 0;transition:box-shadow .15s,transform .15s}
.low .art{position:relative;display:block;aspect-ratio:4/5;overflow:hidden;background:#124351;border:1.5px solid var(--ink)}
.low .art::after{content:"";position:absolute;inset:4px;border:1px solid rgba(246,196,69,.75);pointer-events:none}
.low .art img{display:block;width:100%;height:100%;object-fit:cover}
.low .art.paint{display:flex;align-items:center;justify-content:center;
  background:radial-gradient(ellipse 80% 55% at 50% 0,rgba(255,232,170,.35),transparent 70%),linear-gradient(180deg,#155061,#0B2E37)}
.low .art.paint img{width:auto;height:82%;aspect-ratio:9/16;object-fit:cover;outline:3px solid #c9a24a;outline-offset:0;
  box-shadow:0 8px 16px rgba(0,0,0,.5)}
.low .plq{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0;
  min-height:62px;margin:-16px 8px 10px;padding:7px 10px 6px;border-radius:5px;background:var(--gold-grad);
  box-shadow:0 5px 10px rgba(30,20,8,.35);color:#3a2a06;text-align:center}
.low .plq::before{content:"";position:absolute;inset:3px;border:1px solid rgba(70,48,6,.5);border-radius:3px;pointer-events:none}
.low .ttl{font-family:"Cairo","Almarai",sans-serif;font-weight:900;font-size:15px;line-height:1.55;margin:0;padding-bottom:1px;color:#3a2a06;
  text-shadow:0 1px 0 rgba(255,240,190,.7);overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;
  -webkit-line-clamp:2;line-clamp:2;overflow:hidden}
.low .lab{position:absolute;z-index:2;top:10px;left:50%;transform:translateX(-50%);max-width:calc(100% - 20px);
  padding:0 10px;border-radius:999px;background:#0F4C5C;border:1.5px solid #F6C445;color:#F6C445;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:11.5px;line-height:22px}
.low .also{display:flex;justify-content:center;flex-wrap:wrap;gap:0 2px;margin:4px 0 0;font-size:12.5px}
.low .also a{display:inline-flex;align-items:center;min-height:44px;padding:0 8px;color:var(--muted);text-decoration:none}
.low .also a:hover{color:var(--ink);text-decoration:underline}
@media (hover:hover){.low .ep-a:hover{box-shadow:7px 7px 0 var(--gold)}}
@media (hover:hover) and (prefers-reduced-motion:no-preference){.low .ep-a:hover{transform:translateY(-3px)}}
.low .ep-a:focus-visible{outline:3px solid var(--focus);outline-offset:4px}
/* three cards (the start-here picks): on two columns the third stands centred, never alone at the side */
.low .cards.three>.ep:nth-child(3):last-child{grid-column:1/-1;justify-self:center;width:calc(50% - 6px)}

/* museum-label panels: about, follow, contact */
.low .labels{display:grid;gap:18px;padding-block:34px 8px}
.low .panel{position:relative;background:var(--paper);border:2px solid var(--ink);box-shadow:6px 6px 0 var(--gold);padding:18px 18px 16px}
.low .panel .sec-h{font-size:21px;margin-bottom:10px}
.low .panel p{margin:0;color:var(--muted)}
.low .panel .row{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.low .panel .stack{display:grid;gap:10px}
.low .btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:6px 18px;
  border:2px solid var(--ink);border-radius:4px;background:var(--teal);color:#FBF7EE;box-shadow:3px 3px 0 var(--ink);
  font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:16px;text-decoration:none;text-align:center;overflow-wrap:anywhere}
.low .btn.ghost{background:transparent;color:var(--ink);box-shadow:none;border-width:1.5px}
.low .btn.wide{display:flex;width:100%}
.low .pill{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 16px;border:1.5px solid var(--ink);
  border-radius:999px;background:rgba(255,253,248,.7);font-weight:700;text-decoration:none}
.low .pill:hover,.low .btn.ghost:hover{background:#fff}
.low .ico{flex:none}
.low .foot{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:0 6px;margin-top:34px;padding-block:14px 18px;
  border-top:2px solid var(--ink);color:var(--muted);font-size:14px;text-align:center}
.low .foot a{display:inline-flex;align-items:center;min-height:44px;padding:0 6px;color:var(--muted)}
.low .foot .copy{flex-basis:100%}
@media (min-width:640px){
  .low .cards{grid-template-columns:repeat(3,minmax(0,1fr));gap:22px 16px}
  .low .cards.three>.ep:nth-child(3):last-child{grid-column:auto;justify-self:stretch;width:auto}
  .low .ttl{font-size:16px}
  .low .plq{min-height:66px}
}
@media (min-width:960px){
  .low .cards{grid-template-columns:repeat(4,minmax(0,1fr));gap:26px 20px}
  .low .cards.three{grid-template-columns:repeat(3,minmax(0,1fr));max-width:780px;margin-inline:auto}
  .low .labels{grid-template-columns:1.25fr 1fr 1fr;align-items:stretch}
  .low .sec-h{font-size:27px}
  .low .foot .copy{flex-basis:auto;margin-inline-end:auto}
}
"""

NIGHT_CSS = r"""
N .low{--ink:#F3EEE3;--muted:#C9D6D6;--paper:#0B2E37;--focus:#F6C445;color:#F3EEE3}
N .low .sec-h{color:#F6C445}
N .low .sec-h i{height:0;background:none;border-top:3px double rgba(246,196,69,.8)}
N .low .sec-h i::after{margin-top:-6px}
N .low .ep-a{background:linear-gradient(180deg,#0B2E37,#06222C);border:1px solid rgba(246,196,69,.75);
  box-shadow:inset 0 0 0 3px #06222C,inset 0 0 0 4px rgba(246,196,69,.3),0 12px 24px rgba(0,0,0,.45)}
N .low .art{border:1px solid rgba(246,196,69,.55)}
N .low .also a{color:#C9D6D6}
N .low .also a:hover{color:#F6C445}
N .low .panel{background:linear-gradient(180deg,rgba(5,28,36,.92),rgba(3,20,26,.94));border:1px solid rgba(246,196,69,.8);border-radius:3px;
  box-shadow:inset 0 0 0 5px rgba(3,20,26,.92),inset 0 0 0 6px rgba(246,196,69,.38),0 16px 32px rgba(0,0,0,.45);padding:22px 18px 18px}
N .low .panel::after{content:"";position:absolute;inset:9px;pointer-events:none;
  background:radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 0 0/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 100% 0/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 0 100%/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 100% 100%/7px 7px no-repeat}
N .low .panel p{color:#D9E3E2}
N .low .btn{background:var(--gold-grad);color:#3a2a06;border:0;border-radius:6px;box-shadow:0 6px 14px rgba(0,0,0,.4);font-weight:900;
  text-shadow:0 1px 0 rgba(255,240,190,.7)}
N .low .btn.ghost{background:transparent;color:#F6C445;border:1px solid rgba(246,196,69,.75);box-shadow:none;text-shadow:none}
N .low .pill{background:rgba(2,15,20,.55);border:1px solid rgba(246,196,69,.55);color:#F3EEE3}
N .low .pill:hover,N .low .btn.ghost:hover{background:rgba(246,196,69,.12)}
N .low .foot{border-top:1px solid rgba(246,196,69,.45);color:#C9D6D6}
N .low .foot a{color:#C9D6D6}
"""


def css(night) -> str:
    """The lower page's CSS; `night` is site_home.night (one writer of the dark-mode blocks)."""
    return DAY_CSS.strip() + "\n" + night(NIGHT_CSS)
