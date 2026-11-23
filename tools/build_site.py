"""Build the public website «أصل الحكاية» (design 2, «السينما», owner 2026-10-17) into the site repository.

Public only: titles, dates, covers and platform links from studio/brain/episodes-public.json (brain.py export).
Never scripts, prompts, costs or anything private: those stay in the private studio, never in this public repo.
Static HTML, a strict Content-Security-Policy; GitHub Pages serves it. The only script is the optional cookie-less visitor
counter (Cloudflare Web Analytics, ANALYTICS_TOKEN below): no cookies, no ads, no personal profile; empty token = no script at all.
Usage: python build_site.py [SITE_DIR] [--promote]   (default C:\\Claude Code\\asl-alhikaya-site)
Then review, and push only with the owner's yes (a public change).

Two homes, ONE copy of this file (studio/site/cloud/install_pages.py copies it to the Pages repo as tools/build_site.py,
a test fails when the copy drifts): the PC build above, and the cloud build (Pages repo workflow site.yml), which reads
data/episodes-public.json from the Pages repo itself. Everything that differs between them is an env override:
ASL_SITE_DATA (episodes json), ASL_SITE_COVERS (covers folder, PC only), ASL_SITE_FFMPEG (missing: covers and icons
already in the site folder are kept, nothing is converted), ASL_SITE_LOGO. ADR-008.

Below the first screen (design v3, 2026-11-22): site_lower.py, the site's own episode cards (assets/cards/<id>.webp made by
make_card_art.py on the PC; a missing card shows the old cover), no series block; site_legal.py gives privacy.html and terms.html
the site's look without touching their text.

--promote (cloud): a cloud publish writes the episode as status "pending" (a private or scheduled upload, ADR-008); every
build asks YouTube's public oEmbed endpoint (no token) and promotes the ones that answer 200 to "published". A pending
episode never shows on the site.
"""

import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "studio_app")]  # Pages repo: site_data.py and site_home.py sit next to this file
from site_data import dump, promote, today_kuwait, visible  # noqa: E402
import site_home  # noqa: E402  (the home page's first screen: intro + latest + suggestion box, design v2 2026-11-22)
import site_lower  # noqa: E402  (below the first screen + the links hub: the site's own episode cards, design v3 2026-11-22)
import site_privacy  # noqa: E402  (privacy.html's box sections follow SUGGEST_WORKER_URL)
import site_legal  # noqa: E402  (privacy.html and terms.html wear the site's look; their text is never touched)
ASL = HERE.parents[1]
_ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SITE = Path(_ARGS[0]) if _ARGS else Path(r"C:\Claude Code\asl-alhikaya-site")
FF = os.environ.get("ASL_SITE_FFMPEG", r"C:\Users\User\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
COVERS = Path(os.environ.get("ASL_SITE_COVERS") or ASL / "studio" / "render" / "out")
DATA = Path(os.environ.get("ASL_SITE_DATA") or ASL / "studio" / "brain" / "episodes-public.json")
LINKS = {
    "youtube": ("يوتيوب", "https://www.youtube.com/@asl.alhekaya_tv/shorts"),
    "instagram": ("إنستغرام", "https://www.instagram.com/asl.alhekaya_tv/"),
    "tiktok": ("تيك توك", "https://www.tiktok.com/@asl.alhekaya_tv"),
    "facebook": ("فيسبوك", "https://www.facebook.com/1304517989419331"),
}
E = html.escape
BASE = "https://asl-alhekaya.github.io/"
# identity v4 (DECISION-076): the round logo of the cover kit (tracked and shipped to the cloud; the old ep08 file was local only)
LOGO = Path(os.environ.get("ASL_SITE_LOGO") or ASL / "studio" / "render" / "public" / "cover-kit" / "sisters" / "logo.png")
ALT = {"instagram": "إنستغرام", "facebook": "فيسبوك"}

# ---- Links hub (links.html = the ONE link in the Instagram bio, owner 2026-11-07). Every value to edit later is here. ----
HUB_ACCOUNTS = (
    ("youtube", "يوتيوب", LINKS["youtube"][1]),
    ("instagram", "إنستغرام", LINKS["instagram"][1]),
    ("tiktok", "تيك توك", LINKS["tiktok"][1]),
    ("facebook", "فيسبوك", LINKS["facebook"][1]),
    ("threads", "ثريدز", "https://www.threads.com/@asl.alhekaya_tv"),
)
DM_URL = "https://ig.me/m/asl.alhekaya_tv"  # opens a direct message to the Instagram account
SUGGEST_URL = "https://docs.google.com/forms/d/e/1FAIpQLSedk0L4NDfFcKsEDVEF9TqHzi3TysLcbzONCDBg_SR7AdgwMQ/viewform"  # «اقترح حكاية»: Google Form "اقترح حكاية - أصل الحكاية" (owner's channel Google account, anyone with the link, no sign-in, one required paragraph question); answers go to the Sheet «اقتراحات الحكايات - أصل الحكاية» (studio/suggestions/suggestions.py reads the new ones); fall back to DM_URL if it is ever deleted
CONTACT_EMAIL = "aslalhekaya.tv@gmail.com"  # «تواصل معنا»: the official email (owner 2026-11-07); empty = no mail button, Instagram DM only
CONTACT_NOTE = ""  # optional line under the contact title; empty = the default line (no words about ads, sponsorship or prices: owner 2026-11-07)
START_HERE = ("EP-19", "EP-18", "EP-16", "EP-13")  # «ابدأ من هنا»: preferred episode ids, first three that are public and not the featured latest
OG_IMAGE = "assets/og-links.jpg"  # 1200x630 card made by studio/site/make_og.py

# ---- Inline suggestion box on the home page's first screen (design v2, owner «ابدأ البناء» 2026-11-22). ----
# The Worker's origin only, https, no path, no trailing slash, e.g. "https://asl-suggest.<account>.workers.dev"
# (worker.js in studio/site/proposal-2026-11-22; deployed 2026-11-22 with studio/site/deploy_worker.py, live tests passed).
# Empty = the box is one button to SUGGEST_URL (the old Google Form), no script and the CSP stays as before, so the site never
# ships a dead box. The value reaches the live site only through install_pages.py --push (owner's yes); privacy.html's
# suggestion-box text follows it in the same cloud run. Rollback of the box only: set "" and push again.
SUGGEST_WORKER_URL = "https://asl-suggest.asl-alhekaya.workers.dev"
# ?src= tags for the links we control (the page sends the tag with a suggestion; [a-z0-9-] only, the Worker's SRC_RE).
# Print the ready links with: python build_site.py --src-links
SRC_TAGS = {
    "ig-bio": "Instagram bio",
    "ig-story": "Instagram story link sticker",
    "yt-desc": "YouTube description / pinned comment",
    "tt-bio": "TikTok bio",
}

# ---- Visitor stats (owner 2026-11-07 «فعل كل شي»): Cloudflare Web Analytics, cookie-less, counts visits only. ----
# The site token is public by design (it sits in every page's source, it is not a secret). Empty = no counter and the CSP
# stays script-free. privacy.html (Pages repo, hand-written) section 3 says what is counted; keep the two in step.
ANALYTICS_TOKEN = "c151d936e0444cbea7fa60e3e09dd8c6"  # Cloudflare Web Analytics site asl-alhekaya.github.io (owner account, added 2026-11-07)
CF_SCRIPT_HOST = "https://static.cloudflareinsights.com"
CF_REPORT_HOST = "https://cloudflareinsights.com"


def worker_origin():
    """SUGGEST_WORKER_URL checked: "" (no box) or an https origin. Anything else stops the build (never a box posting to http
    or to a path the CSP cannot name)."""
    url = SUGGEST_WORKER_URL
    if url and not re.fullmatch(r"https://[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+", url):
        raise SystemExit("SUGGEST_WORKER_URL must be empty or an https origin like https://asl-suggest.NAME.workers.dev "
                         "(lower case, no path, no trailing slash)")
    return url


def csp(box=False):
    """The pages' Content-Security-Policy: nothing external except Google Fonts, plus the counter's two hosts when it is on.
    box=True (the home page with SUGGEST_WORKER_URL set) adds the box: script-src 'self' (assets/suggest.js), connect-src and
    form-action the Worker. form-action also keeps 'self' because the no-script path ends in the Worker's 303 back to this
    site, and browsers check form-action on that redirect too. Without the box it stays form-action 'none'."""
    worker = worker_origin() if box else ""
    scripts = (["'self'"] if worker else []) + ([CF_SCRIPT_HOST] if ANALYTICS_TOKEN else [])
    connect = ([worker] if worker else []) + ([CF_REPORT_HOST] if ANALYTICS_TOKEN else [])
    parts = ["default-src 'none'", "img-src 'self'", "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
             "font-src https://fonts.gstatic.com"]
    if scripts:
        parts.append("script-src " + " ".join(scripts))
    if connect:
        parts.append("connect-src " + " ".join(connect))
    parts += ["base-uri 'none'", f"form-action {worker} 'self'" if worker else "form-action 'none'"]
    return "; ".join(parts)


def beacon():
    """The one counter tag (deferred, no cookies), or nothing when ANALYTICS_TOKEN is empty."""
    if not ANALYTICS_TOKEN:
        return ""
    if not re.fullmatch(r"[0-9a-f]{32}", ANALYTICS_TOKEN):
        raise SystemExit("ANALYTICS_TOKEN must be the 32-character Cloudflare Web Analytics site token")
    return (f'<script defer src="{CF_SCRIPT_HOST}/beacon.min.js" '
            f"data-cf-beacon='{{\"token\": \"{ANALYTICS_TOKEN}\"}}'></script>\n")


def cover(ep):
    name = ep.get("cover")
    out = SITE / "assets" / "covers" / f"{ep['id'].lower()}.jpg"
    if not name or not (COVERS / name).exists() or not Path(FF).exists():
        # The render out folder is scratch (the 2026-10-17 dedup moved old card copies to the Recycle Bin): a cover
        # already published stays published; a site rebuild never takes a cover down (E64).
        return f"assets/covers/{out.name}" if out.exists() else None
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FF, "-loglevel", "error", "-y", "-i", str(COVERS / name), "-vf", "scale=540:-1", "-q:v", "4", str(out)],
                   check=True)
    return f"assets/covers/{out.name}"


def card_art(ep):
    """The episode's site card picture (site_lower.card_file) when it is in the site folder, else None (the card then shows
    the old cover as a framed painting). The PC build copies studio/site/assets/cards/ in first (cards()); the cloud build
    links what install_pages.py and after_publish.py put in the Pages repo."""
    rel = f"{site_lower.CARDS_DIR}/{site_lower.card_file(ep['id'])}"
    return rel if (SITE / rel).is_file() else None


def cards():
    """Copy the card pictures made by make_card_art.py (studio/site/assets/cards/, their one source) into the site folder when
    they differ. Nothing to copy in the cloud build (tools/ has no assets/ next to it). A missing card is never an error."""
    src_dir = HERE / "assets" / "cards"
    if not src_dir.is_dir():
        return
    for src in sorted(src_dir.glob("*.webp")):
        dst = SITE / site_lower.CARDS_DIR / src.name
        if not dst.is_file() or dst.read_bytes() != src.read_bytes():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())


def tile(ep, img, root="", heading="h3"):
    """One episode card (site_lower.card): the site's card art, or the old cover when there is none; YouTube link + the
    other platforms' small links."""
    alt = "".join(f'<a href="{E(ep["links"][k])}" rel="noopener" target="_blank">{n}</a>'
                  for k, n in ALT.items() if ep.get("links", {}).get(k))
    return site_lower.card(ep, art=card_art(ep), cover=img, url=yt_url(ep), alt_links=alt, root=root, heading=heading)


def icons():
    """Favicon and phone icon from the round book logo (ffmpeg, already used for the covers). Without ffmpeg (the cloud
    build) the icons already in the site folder stay."""
    if not Path(FF).exists():
        return
    for name, size in (("favicon.png", 64), ("apple-touch-icon.png", 180)):
        out = SITE / "assets" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([FF, "-loglevel", "error", "-y", "-i", str(LOGO), "-vf", f"scale={size}:{size}", str(out)], check=True)


def home_assets():
    """The first screen's pictures and script (site_home.HOME_ASSETS). Their one source is studio/site/assets/ (pictures made by
    make_home_assets.py): the PC build copies them into the site folder; the cloud build (tools/ in the Pages repo, no such
    folder) uses the copies install_pages.py put in assets/. Either way a missing file stops the build (no broken page)."""
    src_dir = HERE / "assets"
    missing = []
    for rel in site_home.HOME_ASSETS:
        src, dst = src_dir / rel, SITE / "assets" / rel
        if src.is_file() and (not dst.is_file() or dst.read_bytes() != src.read_bytes()):
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        if not dst.is_file():
            missing.append(f"assets/{rel}")
    if missing:
        raise SystemExit("first-screen files missing in the site folder (run studio/site/cloud/install_pages.py): " + ", ".join(missing))


def src_links():
    """The ready ?src= links for the bios and descriptions (SRC_TAGS), one per line."""
    return "\n".join(f"{BASE}?src={tag}   {where}" for tag, where in SRC_TAGS.items())


def static_files(today):
    """robots.txt, sitemap.xml and a small 404 page: what search engines and wrong links need."""
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod></url>" for u in ("", "links.html", "privacy.html", "terms.html"))
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (SITE / "404.html").write_text(NOT_FOUND, encoding="utf-8")


# The 404 page: the site's two looks (cream paper by day, the museum teal by night), no script, no picture.
NOT_FOUND = """<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>الصفحة غير موجودة | أصل الحكاية</title>
<meta name="theme-color" content="#F3EEE3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B2E37" media="(prefers-color-scheme: dark)">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700&family=Cairo:wght@800;900&display=swap">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;padding:16px;box-sizing:border-box;background:#F3EEE3;color:#14232B;
font-family:"Almarai",Tahoma,sans-serif;text-align:center;line-height:1.8}
main{max-width:420px;background:#FBF7EE;border:2px solid #14232B;box-shadow:6px 6px 0 #F6C445;padding:26px 22px}
h1{font-family:"Cairo","Almarai",sans-serif;font-weight:900;font-size:28px;margin:0 0 6px}p{margin:0 0 14px;color:#4D5D63}
a{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 20px;background:#0F4C5C;color:#FBF7EE;
border:2px solid #14232B;border-radius:4px;font-family:"Cairo","Almarai",sans-serif;font-weight:800;text-decoration:none}
a:focus-visible{outline:3px solid #1A7089;outline-offset:3px}
@media (prefers-color-scheme:dark){body{background:#0B2E37;color:#F3EEE3}main{background:#06222C;border:1px solid rgba(246,196,69,.8);
box-shadow:inset 0 0 0 5px #06222C,inset 0 0 0 6px rgba(246,196,69,.38),0 16px 32px rgba(0,0,0,.45)}h1{color:#F6C445}p{color:#D9E3E2}
a{background:linear-gradient(135deg,#fff0a8 0%,#F6C445 28%,#b8862b 52%,#f6d77a 74%,#9a6a12 100%);color:#3a2a06;border:0}
a:focus-visible{outline-color:#F6C445}}</style></head>
<body><main><h1>لم نجد هذه الصفحة</h1><p>ربما تغيّر الرابط. عُد إلى الصفحة الرئيسية لتتصفّح الحكايات.</p><a href="/">إلى أصل الحكاية</a></main></body></html>
"""


# Simplified outline glyphs (24 px grid, currentColor): inline SVG, so the strict CSP (no external images) is untouched.
ICONS = {
    "youtube": '<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.5v5l4.5-2.5z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".7"/>',
    "tiktok": '<path d="M13.5 3v11.2a3.6 3.6 0 1 1-3.6-3.6"/><path d="M13.5 3c.4 2.7 2.2 4.4 5 4.7"/>',
    "facebook": '<circle cx="12" cy="12" r="9"/><path d="M13.6 20v-8.6"/><path d="M10.6 11.4h5.4"/><path d="M13.6 11.4V9.6c0-1.4.8-2.1 2.3-2.1"/>',
    "threads": '<circle cx="12" cy="12" r="9"/><path d="M15.7 12.6c0 1.9-1.6 3.1-3.6 3.1s-3.3-1.2-3.3-2.7c0-1.7 1.5-2.6 3.3-2.6s3.5 1 3.5 3"/><path d="M8.9 9.4c.9-1.6 3-2 4.5-1.3 1 .5 1.7 1.4 1.9 2.6"/>',
}


def icon(key):
    body = ICONS.get(key, "")
    return (f'<svg class="ico" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>') if body else ""


def yt_url(e):
    return e.get("links", {}).get("youtube", LINKS["youtube"][1])


def start_picks(eps):
    """«ابدأ من هنا»: the first three START_HERE episodes that are public and are not the featured latest."""
    by_id = {e["id"]: e for e in eps}
    if not eps:
        return []
    return [by_id[i] for i in START_HERE if i in by_id and i != eps[0]["id"]][:3]


def contact_buttons():
    """Instagram DM always; the mail button only when CONTACT_EMAIL is set (the one config value)."""
    mail = f'<a class="btn ghost wide" href="mailto:{E(CONTACT_EMAIL)}">{E(CONTACT_EMAIL)}</a>' if CONTACT_EMAIL else ""
    return f'<a class="btn wide" href="{DM_URL}" rel="noopener" target="_blank">راسلنا على إنستغرام</a>{mail}'


CONTACT_LINE = "لأي سؤال أو ملاحظة، راسلنا على البريد الإلكتروني أو على إنستغرام."
ABOUT = ("فيديوهات قصيرة بالعربية الفصحى عن أصل الاختراعات والاكتشافات والأشياء التي نستخدمها كل يوم. لكل معلومة نذكرها مصدر "
         "موثوق واحد على الأقل، والرسوم مولّدة بالذكاء الاصطناعي لتصوير الأجواء، وهي ليست صورًا تاريخية.")
FONTS = "https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Cairo:wght@700;800;900&display=swap"


def latest_card(e, pic, href, art):
    """links.html: the newest public episode, its card picture beside the title and the button."""
    kind = "art" if art else ("art paint" if pic else "art empty")
    return (f'<section class="panel" aria-label="آخر حلقة"><div class="newest"><span class="{kind}">{pic}</span><div>'
            f'<span class="tag">الأحدث</span><h2 class="nt">{E(e["title"])}</h2>'
            f'<a class="btn" href="{href}" rel="noopener" target="_blank">شاهد الحلقة</a></div></div></section>')


HUB_CSS = """
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:#F3EEE3}
main.low{max-width:480px;margin:0 auto;padding:22px max(16px,env(safe-area-inset-right,0px)) 8px max(16px,env(safe-area-inset-left,0px));
  display:grid;gap:18px}
.low .top{text-align:center}
.low .top img{width:92px;height:92px;border-radius:50%;box-shadow:0 0 0 3px #F6C445,0 10px 24px rgba(6,34,44,.3)}
.low .top h1{font-family:"Cairo","Almarai",sans-serif;font-weight:900;font-size:34px;line-height:1.25;margin:8px 0 0;color:#14232B}
.low .top h1 span{color:#0F4C5C}
.low .top p{margin:0;color:#4D5D63;font-family:"Cairo","Almarai",sans-serif;font-weight:800}
.low .panel .sec-h{margin-bottom:4px}
.low .panel .sub{margin-bottom:12px}
.low .newest{display:grid;grid-template-columns:112px minmax(0,1fr);gap:14px;align-items:center}
.low .newest .nt{font-family:"Cairo","Almarai",sans-serif;font-weight:900;font-size:21px;line-height:1.35;margin:4px 0 10px;overflow-wrap:anywhere}
.low .tag{display:inline-block;background:#14232B;color:#F6C445;font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:13px;
  padding:0 10px;border-radius:3px}
.low .accts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.low .accts .pill:first-child{grid-column:1/-1}
.low .panel .cards{gap:16px 12px}
.low .panel .ep-a{padding:5px 5px 0}
.low .panel .ttl{font-size:14px}
"""
HUB_NIGHT = """
N body{background:#0B2E37}
N .low .top h1{color:transparent;background:linear-gradient(180deg,#fff0a8 0,#F6C445 .6em,#c98a14 1.3em,#c98a14 100%);
  -webkit-background-clip:text;background-clip:text}
N .low .top h1 span{color:transparent}
N .low .top p{color:#F6C445}
N .low .tag{background:var(--gold-grad);color:#3a2a06}
"""


def render_links(eps, imgs, root=""):
    """links.html: the phone-first hub for the Instagram bio. Same public data, same strict CSP and the same card design as
    index.html (no JavaScript but the counter). A pure function of the episodes + the constants above and the card files in
    the site folder, so a rebuild changes nothing by itself. root = "" for /links.html, "../" for the short copy /l/."""
    latest = eps[0] if eps else None
    start = start_picks(eps)  # the latest has its own card
    start_html = ""
    if start:
        start_html = ('<section class="panel" aria-labelledby="h-start">' + site_lower.heading("ابدأ من هنا", "h-start")
                      + '<p class="sub">جديد على القناة؟ إليك ثلاث حكايات تعرّفك بها.</p>'
                      + site_lower.grid([tile(e, imgs.get(e["id"]), root) for e in start], "three") + '</section>')
    latest_html = ""
    if latest:
        art, img = card_art(latest), imgs.get(latest["id"])
        pic = (f'<img src="{root}{art}" alt="" width="{site_lower.CARD_W}" height="{site_lower.CARD_H}">' if art else
               f'<img src="{root}{img}" alt="" width="540" height="960">' if img else "")
        latest_html = latest_card(latest, pic, E(yt_url(latest)), art)
    accounts = "".join(f'<a class="pill" href="{E(u)}" rel="noopener" target="_blank">{icon(k)}{n}</a>' for k, n, u in HUB_ACCOUNTS)
    note = E(CONTACT_NOTE) if CONTACT_NOTE else CONTACT_LINE
    home = root or "./"
    image = BASE + OG_IMAGE
    desc = "كل روابط أصل الحكاية في مكان واحد: حسابات القناة، آخر حلقة، وكل الحكايات."
    style = HUB_CSS.strip() + "\n" + site_lower.css(site_home.night) + "\n" + site_home.night(HUB_NIGHT)
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp()}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#F3EEE3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B2E37" media="(prefers-color-scheme: dark)">
<title>أصل الحكاية | كل الروابط</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}links.html">
<link rel="icon" type="image/png" href="{root}assets/favicon.png">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_AR">
<meta property="og:site_name" content="أصل الحكاية">
<meta property="og:url" content="{BASE}links.html">
<meta property="og:title" content="أصل الحكاية | كل شيء له بداية">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="أصل الحكاية: كتاب أصفر صغير وعبارة كل شيء له بداية">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="أصل الحكاية | كل شيء له بداية">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{image}">
<link rel="stylesheet" href="{FONTS}">
<style>
{style}
</style>
</head>
<body>
<main class="low">
<header class="top"><img src="{root}assets/apple-touch-icon.png" alt="شعار أصل الحكاية" width="180" height="180"><h1>أصل <span>الحكاية</span></h1><p>كل شيء له بداية</p></header>
{latest_html}
{start_html}
<a class="btn wide" href="{home}#all">كل الحلقات ({len(eps)})</a>
<section class="panel" aria-labelledby="h-follow">{site_lower.heading("تابعنا", "h-follow")}<p class="sub">الحكايات نفسها على كل المنصات.</p><div class="accts">{accounts}</div></section>
<section class="panel" aria-labelledby="h-suggest">{site_lower.heading("اقترح حكاية", "h-suggest")}<p class="sub">ما الشيء الذي تودّ أن نحكي أصله؟ اكتب لنا اسمه.</p><a class="btn wide" href="{SUGGEST_URL}" rel="noopener" target="_blank">أرسل اقتراحك</a></section>
<section class="panel" aria-labelledby="h-biz">{site_lower.heading("تواصل معنا", "h-biz")}<p class="sub">{note}</p><div class="stack">{contact_buttons()}</div></section>
<footer class="foot"><a href="{home}">الموقع</a> · <a href="{root}privacy.html">سياسة الخصوصية</a> · <a href="{root}terms.html">شروط الاستخدام</a><span class="copy">© 2026 أصل الحكاية</span></footer>
</main>
{beacon()}</body>
</html>
"""


def main():
    if "--src-links" in sys.argv:
        print(src_links())
        return
    eps = json.loads(DATA.read_text(encoding="utf-8"))
    today = today_kuwait()
    if "--promote" in sys.argv:
        eps, done = promote(eps, today)
        if done:
            DATA.write_text(dump(eps), encoding="utf-8")
            print("promoted:", ", ".join(done))
    eps = visible(eps, today)
    eps.sort(key=lambda e: e.get("published", ""), reverse=True)
    imgs = {e["id"]: cover(e) for e in eps}
    cards()  # the site's own card pictures into the site folder first: tile() links only files that are there
    latest = eps[0] if eps else None  # zero public episodes: no latest strip, the page still builds
    # «الأجزاء القادمة قريبًا» series block removed (owner 2026-11-22): series parts are ordinary cards with their part label
    tiles = site_lower.grid([tile(e, imgs[e["id"]]) for e in eps])
    plats = "".join(f'<a class="pill" href="{E(u)}" rel="noopener" target="_blank">{icon(k)}{n}</a>' for k, (n, u) in LINKS.items())
    picks = start_picks(eps)
    start_section = ('<section id="start" class="sec" aria-labelledby="h-start">' + site_lower.heading("ابدأ من هنا", "h-start")
                     + '<p class="sub">جديد على القناة؟ إليك ثلاث حكايات تعرّفك بها.</p>'
                     + site_lower.grid([tile(e, imgs[e["id"]]) for e in picks], "three") + '</section>') if picks else ""
    latest_img = imgs[latest["id"]] if latest else None  # the cover: the link preview (og:image) stays the video cover
    worker = worker_origin()
    home_assets()
    site_privacy.update(SITE, box=bool(worker))
    site_legal.update(SITE)
    nav = [("#suggest", "اقترح حكاية")] + ([("#start", "ابدأ من هنا")] if picks else []) + [
        ("#all", "كل الحكايات"), ("#about", "عن القناة"), ("#follow", "تابعنا"), ("#contact", "تواصل معنا")]
    first = site_home.first_screen(latest_title=latest["title"] if latest else "", latest_url=yt_url(latest) if latest else "",
                                   latest_img=(card_art(latest) or latest_img) if latest else None, nav=nav,
                                   action=f"{worker}/suggest" if worker else "", fallback_url=SUGGEST_URL)
    # fetchpriority high (2026-11-24): at the default low priority, on a slow phone the box showed 4-16 s before its script ran,
    # and a tap in that gap gave no sign of sending («النعال» arrived three times)
    box_script = '<script defer fetchpriority="high" src="assets/suggest.js"></script>\n' if worker else ""
    note = E(CONTACT_NOTE) if CONTACT_NOTE else CONTACT_LINE
    page = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="{csp(box=True)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#F3EEE3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B2E37" media="(prefers-color-scheme: dark)">
<title>أصل الحكاية | كل شيء له بداية</title>
<meta name="description" content="قصص قصيرة عن البدايات: كيف بدأت الاختراعات والاكتشافات التي نستخدمها كل يوم. فيديوهات قصيرة بالعربية الفصحى.">
<link rel="canonical" href="{BASE}">
<link rel="icon" type="image/png" href="assets/favicon.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_AR">
<meta property="og:url" content="{BASE}">
<meta property="og:title" content="أصل الحكاية">
<meta property="og:description" content="كل شيء له بداية… حكايات قصيرة عن أصل الأشياء.">
{f'<meta property="og:image" content="{BASE}{latest_img}">' if latest_img else ""}
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{FONTS}">
<style>
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:#F3EEE3;color:#14232B}}
@media (prefers-color-scheme:dark){{body{{background:#0B2E37;color:#F3EEE3}}}}
.wrap{{max-width:1100px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
{site_home.css()}
{site_lower.css(site_home.night)}
</style>
</head>
<body>
<main id="top">
{first}
<div class="low"><div class="wrap">
{start_section}
<section id="all" class="sec" aria-labelledby="h-all">{site_lower.heading("كل الحكايات", "h-all")}<p class="sub">الأحدث أولًا. اختر حكاية لتشاهدها على يوتيوب.</p>{tiles}</section>
<div class="labels">
<section id="about" class="panel" aria-labelledby="h-about">{site_lower.heading("عن أصل الحكاية", "h-about")}<p>{ABOUT}</p></section>
<section id="follow" class="panel" aria-labelledby="h-follow">{site_lower.heading("تابعنا", "h-follow")}<div class="row">{plats}</div></section>
<section id="contact" class="panel" aria-labelledby="h-contact">{site_lower.heading("تواصل معنا", "h-contact")}<p class="sub">{note}</p><div class="stack">{contact_buttons()}</div></section>
</div>
</div></div>
</main>
<footer class="low"><div class="wrap foot"><span class="copy">© 2026 أصل الحكاية</span><a href="links.html">كل الروابط</a><a href="privacy.html">سياسة الخصوصية</a><a href="terms.html">شروط الاستخدام</a></div></footer>
{box_script}{beacon()}</body>
</html>
"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    (SITE / "links.html").write_text(render_links(eps, imgs), encoding="utf-8")
    (SITE / "l").mkdir(exist_ok=True)  # short link for the bio: the same hub at /l/ (canonical stays links.html)
    (SITE / "l" / "index.html").write_text(render_links(eps, imgs, "../"), encoding="utf-8")
    icons()
    static_files(today)
    print(f"index.html + links.html + l/: {len(eps)} episodes, latest «{latest['title'] if latest else '-'}», covers {sum(1 for v in imgs.values() if v)}")


if __name__ == "__main__":
    main()
