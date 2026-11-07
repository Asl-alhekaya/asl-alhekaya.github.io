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
sys.path[:0] = [str(HERE), str(HERE.parent / "studio_app")]  # Pages repo: site_data.py sits next to this file
from site_data import dump, promote, today_kuwait, visible  # noqa: E402
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

# ---- Visitor stats (owner 2026-11-07 «فعل كل شي»): Cloudflare Web Analytics, cookie-less, counts visits only. ----
# The site token is public by design (it sits in every page's source, it is not a secret). Empty = no counter and the CSP
# stays script-free. privacy.html (Pages repo, hand-written) section 3 says what is counted; keep the two in step.
ANALYTICS_TOKEN = "c151d936e0444cbea7fa60e3e09dd8c6"  # Cloudflare Web Analytics site asl-alhekaya.github.io (owner account, added 2026-11-07)
CF_SCRIPT_HOST = "https://static.cloudflareinsights.com"
CF_REPORT_HOST = "https://cloudflareinsights.com"


def csp():
    """The pages' Content-Security-Policy: nothing external except Google Fonts, plus the counter's two hosts when it is on."""
    counter = f" script-src {CF_SCRIPT_HOST}; connect-src {CF_REPORT_HOST};" if ANALYTICS_TOKEN else ""
    return ("default-src 'none'; img-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            f"font-src https://fonts.gstatic.com;{counter} base-uri 'none'; form-action 'none'")


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


def tile(ep, img):
    url = ep.get("links", {}).get("youtube", LINKS["youtube"][1])
    pic = f'<img src="{img}" alt="غلاف {E(ep["title"])}" loading="lazy" width="540" height="960">' if img else ""
    alt = "".join(f'<a href="{E(ep["links"][k])}" rel="noopener" target="_blank">{n}</a>'
                  for k, n in ALT.items() if ep.get("links", {}).get(k))
    return (f'<div class="ep"><a class="tile" href="{url}" rel="noopener" target="_blank">{pic}'
            f'<span>{E(ep["title"])}</span></a>' + (f'<div class="alt">{alt}</div>' if alt else "") + '</div>')


def icons():
    """Favicon and phone icon from the round book logo (ffmpeg, already used for the covers). Without ffmpeg (the cloud
    build) the icons already in the site folder stay."""
    if not Path(FF).exists():
        return
    for name, size in (("favicon.png", 64), ("apple-touch-icon.png", 180)):
        out = SITE / "assets" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([FF, "-loglevel", "error", "-y", "-i", str(LOGO), "-vf", f"scale={size}:{size}", str(out)], check=True)


def static_files(today):
    """robots.txt, sitemap.xml and a small 404 page: what search engines and wrong links need."""
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod></url>" for u in ("", "links.html", "privacy.html", "terms.html"))
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (SITE / "404.html").write_text("""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>الصفحة غير موجودة | أصل الحكاية</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0B1416;color:#EEF3F2;font-family:Tahoma,sans-serif;text-align:center}
a{color:#F2C14E;font-weight:700}</style></head>
<body><main><h1>هذي الصفحة ما لقيناها</h1><p>رجع للصفحة الرئيسية وشوف الحكايات.</p><p><a href="/">أصل الحكاية</a></p></main></body></html>
""", encoding="utf-8")


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
    return [by_id[i] for i in START_HERE if i in by_id and i != eps[0]["id"]][:3]


def contact_buttons():
    """Instagram DM always; the mail button only when CONTACT_EMAIL is set (the one config value)."""
    mail = f'<a class="btn ghost wide" href="mailto:{E(CONTACT_EMAIL)}">{E(CONTACT_EMAIL)}</a>' if CONTACT_EMAIL else ""
    return f'<a class="btn wide" href="{DM_URL}" rel="noopener" target="_blank">راسلنا على إنستغرام</a>{mail}'


CONTACT_LINE = "لأي سؤال أو ملاحظة، راسلنا على الإيميل أو على إنستغرام."


def render_links(eps, imgs, root=""):
    """links.html: the phone-first hub for the Instagram bio. Same public data and same strict CSP as index.html (no
    JavaScript, no trackers). A pure function of the episodes + the constants above, so a rebuild changes nothing by itself.
    root = "" for /links.html, "../" for the short copy /l/ (same page, same canonical)."""
    by_id = {e["id"]: e for e in eps}
    latest = eps[0]

    yt = yt_url

    def pic(e):
        img = imgs.get(e["id"])
        return f'<img src="{root}{img}" alt="غلاف {E(e["title"])}" loading="lazy" width="540" height="960">' if img else ""

    start = start_picks(eps)  # the latest has its own card
    start_html = ""
    if start:
        cards = "".join(f'<a class="mini" href="{yt(e)}" rel="noopener" target="_blank">{pic(e)}<span>{E(e["title"])}</span></a>'
                        for e in start)
        start_html = ('<section class="card" aria-labelledby="h-start"><h2 id="h-start">ابدأ من هنا</h2>'
                      f'<p class="sub">جديد على القناة؟ هذي ثلاث حكايات تعرّفك عليها.</p><div class="trio">{cards}</div></section>')
    accounts = "".join(f'<a class="acct" href="{u}" rel="noopener" target="_blank">{icon(k)}{n}</a>' for k, n, u in HUB_ACCOUNTS)
    note = E(CONTACT_NOTE) if CONTACT_NOTE else CONTACT_LINE
    home = root or "./"
    image = BASE + OG_IMAGE
    desc = "كل روابط أصل الحكاية في مكان واحد: حسابات القناة، آخر حلقة، وكل الحكايات."
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp()}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#0B1416">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Reem+Kufi:wght@600;700&display=swap">
<style>
:root{{--bg:#0B1416;--card:#13232A;--ink:#EEF3F2;--cream:#F6EBCB;--muted:#A7BABD;--gold:#F2C14E;--teal:#1E5463;--line:#2A4753}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;background:radial-gradient(130% 60% at 50% 0%,var(--teal) 0%,transparent 70%),var(--bg);color:var(--ink);font-family:"Almarai",Tahoma,sans-serif;line-height:1.7}}
a{{color:inherit}}
main{{max-width:480px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-right,0px)) 24px max(16px,env(safe-area-inset-left,0px));display:grid;gap:14px}}
h1,h2{{font-family:"Reem Kufi","Almarai",sans-serif;text-wrap:balance;margin:0}}
.top{{text-align:center}}
.top img{{width:96px;height:96px;border-radius:50%;box-shadow:0 0 0 3px var(--gold),0 14px 30px rgba(0,0,0,.5)}}
.top h1{{color:var(--cream);font-size:34px;margin-top:10px;line-height:1.3}}
.top p{{color:var(--muted);margin:2px 0 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px}}
.card h2{{color:var(--gold);font-size:21px}}
.sub{{color:var(--muted);font-size:14px;margin:2px 0 12px}}
.tag{{display:inline-block;background:var(--gold);color:#1A1405;font-weight:800;border-radius:6px;padding:0 10px;font-size:13px}}
.latest{{display:grid;grid-template-columns:96px 1fr;gap:14px;align-items:center}}
.latest img{{width:96px;height:auto;aspect-ratio:9/16;object-fit:cover;border-radius:12px;display:block;background:#0B1416}}
.latest h2{{color:var(--cream);margin:6px 0 10px;font-size:22px;line-height:1.4}}
.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;background:var(--gold);color:#1A1405;padding:8px 18px;border-radius:12px;font-weight:800;text-decoration:none;text-align:center}}
.btn.ghost{{background:transparent;color:var(--ink);border:1px solid #3A5560}}
.btn.wide{{display:flex;width:100%}}
.trio{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.mini{{position:relative;display:block;border-radius:12px;overflow:hidden;background:#0B1416;text-decoration:none}}
.mini img{{width:100%;height:auto;aspect-ratio:9/16;object-fit:cover;display:block}}
.mini span{{position:absolute;inset:auto 0 0 0;padding:22px 6px 6px;background:linear-gradient(transparent,rgba(0,0,0,.9));font-size:13px;font-weight:800;line-height:1.35}}
.accts{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.acct{{display:flex;align-items:center;justify-content:center;gap:9px;min-height:52px;border:1px solid #3A5560;border-radius:14px;font-weight:800;text-decoration:none;background:rgba(255,255,255,.03)}}
.acct:first-child{{grid-column:1/-1;background:var(--gold);border-color:var(--gold);color:#1A1405}}
.stack{{display:grid;gap:10px}}
.ico{{flex:none}}
@media (prefers-reduced-motion:no-preference){{.top img{{animation:float 5s ease-in-out infinite}}@keyframes float{{50%{{transform:translateY(-5px)}}}}}}
a:focus-visible{{outline:3px solid var(--gold);outline-offset:3px}}
a.btn:hover,a.acct:hover,a.mini:hover{{filter:brightness(1.1)}}
footer{{text-align:center;color:var(--muted);font-size:13px;padding-top:6px}}
footer a{{color:var(--muted)}}
</style>
</head>
<body>
<main>
<div class="top"><img src="{root}assets/apple-touch-icon.png" alt="شعار أصل الحكاية" width="180" height="180"><h1>أصل الحكاية</h1><p>كل شيء له بداية</p></div>
<section class="card" aria-label="آخر حلقة"><div class="latest">{pic(latest)}<div><span class="tag">الأحدث</span><h2>{E(latest["title"])}</h2><a class="btn" href="{yt(latest)}" rel="noopener" target="_blank">شاهد الحلقة</a></div></div></section>
{start_html}
<a class="btn wide" href="{home}#all">كل الحلقات ({len(eps)})</a>
<section class="card" aria-labelledby="h-follow"><h2 id="h-follow">تابعنا</h2><p class="sub">نفس الحكايات على كل المنصات.</p><div class="accts">{accounts}</div></section>
<section class="card" aria-labelledby="h-suggest"><h2 id="h-suggest">اقترح حكاية</h2><p class="sub">وش الشيء اللي تبي نعرف أصله؟ اكتب لنا اسمه.</p><a class="btn wide" href="{SUGGEST_URL}" rel="noopener" target="_blank">أرسل اقتراحك</a></section>
<section class="card" aria-labelledby="h-biz"><h2 id="h-biz">تواصل معنا</h2><p class="sub">{note}</p><div class="stack">{contact_buttons()}</div></section>
<footer><a href="{home}">الموقع</a> · <a href="{root}privacy.html">سياسة الخصوصية</a> · <a href="{root}terms.html">شروط الاستخدام</a><br>© 2026 أصل الحكاية</footer>
</main>
{beacon()}</body>
</html>
"""


def main():
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
    latest = eps[0]
    series = {}
    for e in eps:
        if e.get("series"):
            series.setdefault(e["series"], []).append(e)
    series_html = ""
    for name, parts in series.items():
        chips = "".join(f'<span class="part">الجزء {p.get("part")}</span>' for p in sorted(parts, key=lambda p: p.get("part", 0)))
        series_html += f'<section><h3>سلسلة {E(name)}</h3><div class="parts">{chips}<span class="part soon">الأجزاء الجاية قريبًا</span></div></section>'
    tiles = "".join(tile(e, imgs[e["id"]]) for e in eps)
    plats = "".join(f'<a class="plat" href="{u}" rel="noopener" target="_blank">{icon(k)}{n}</a>' for k, (n, u) in LINKS.items())
    picks = start_picks(eps)
    start_section = ('<section id="start"><h3>ابدأ من هنا</h3><p class="sub">جديد على القناة؟ هذي ثلاث حكايات تعرّفك عليها.</p>'
                     f'<div class="rail three">{"".join(tile(e, imgs[e["id"]]) for e in picks)}</div></section>') if picks else ""
    latest_img = imgs[latest["id"]]
    page = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp()}">
<meta name="referrer" content="strict-origin-when-cross-origin">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&family=Reem+Kufi:wght@600;700&display=swap">
<style>
:root{{--bg:#0B1416;--card:#13232A;--ink:#EEF3F2;--muted:#A7BABD;--gold:#F2C14E;--line:#1F3239}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Almarai",Tahoma,sans-serif;line-height:1.8}}
a{{color:inherit}}
.wrap{{max-width:1100px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
header{{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding-block:14px}}
.logo{{font-family:"Reem Kufi","Almarai",sans-serif;font-size:26px;color:var(--gold);text-decoration:none}}
nav{{display:flex;gap:16px;flex-wrap:wrap;font-size:15px}}
nav a{{color:var(--muted);text-decoration:none}}
nav a:hover,nav a:focus-visible{{color:var(--ink)}}
.hero{{display:grid;grid-template-columns:1fr 280px;gap:28px;align-items:end;padding-block:34px;background:radial-gradient(120% 90% at 85% 10%,#1E5463 0%,transparent 60%)}}
.tag{{display:inline-block;background:var(--gold);color:#1A1405;font-weight:800;border-radius:6px;padding:2px 10px;font-size:13px}}
h1,h2,h3{{font-family:"Reem Kufi","Almarai",sans-serif;text-wrap:balance;margin:0}}
.hero h1{{font-size:clamp(32px,6vw,56px);margin:10px 0 8px;line-height:1.3}}
.hero p{{color:var(--muted);font-size:17px;margin:0 0 18px;max-width:54ch}}
.btns{{display:flex;gap:10px;flex-wrap:wrap}}
.btn{{background:var(--gold);color:#1A1405;padding:11px 18px;border-radius:10px;font-weight:800;text-decoration:none}}
.btn.ghost{{background:transparent;color:var(--ink);border:1px solid #3A5560}}
.btn:focus-visible,.tile:focus-visible,.plat:focus-visible{{outline:3px solid var(--gold);outline-offset:3px}}
.hero img{{width:100%;height:auto;border-radius:16px;box-shadow:0 30px 60px rgba(0,0,0,.6)}}
section{{padding-block:18px}}
h3{{font-size:22px;margin-bottom:12px}}
.parts{{display:flex;gap:8px;flex-wrap:wrap}}
.part{{background:var(--card);border:1px solid #23404A;border-radius:10px;padding:10px 14px;font-weight:700;font-size:14px}}
.part.soon{{opacity:.55}}
.rail{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}
.ep{{display:flex;flex-direction:column;gap:6px}}
.alt{{display:flex;gap:12px;font-size:12px}}
.alt a{{color:var(--muted)}}
.tile{{display:block;position:relative;border-radius:12px;overflow:hidden;background:var(--card);text-decoration:none}}
.tile img{{width:100%;height:auto;display:block}}
.tile span{{position:absolute;bottom:0;left:0;right:0;padding:26px 8px 8px;background:linear-gradient(transparent,rgba(0,0,0,.85));font-size:14px;font-weight:800}}
.about p{{color:var(--muted);max-width:68ch;margin:0}}
.plats{{display:flex;gap:10px;flex-wrap:wrap}}
.plat{{display:inline-flex;align-items:center;gap:8px;border:1px solid #2E4A54;border-radius:999px;padding:9px 18px;font-weight:700;text-decoration:none}}
.sub{{color:var(--muted);margin:-6px 0 12px}}
.rail.three{{grid-template-columns:repeat(3,minmax(0,1fr));max-width:560px}}
.stack{{display:grid;gap:10px;max-width:360px}}
.btn.wide{{display:flex;justify-content:center}}
.logo{{display:inline-flex;align-items:center;gap:10px}}
.logo img{{width:36px;height:36px;border-radius:50%;box-shadow:0 0 0 2px var(--gold)}}
.ico{{flex:none}}
footer{{border-top:1px solid var(--line);color:var(--muted);padding-block:18px;margin-top:18px;font-size:14px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
footer a{{color:var(--muted)}}
@media (max-width:640px){{.hero{{grid-template-columns:1fr}} .hero img{{max-width:240px}}}}
@media (prefers-reduced-motion:no-preference){{.tile img{{transition:transform .2s}} .tile:hover img{{transform:scale(1.03)}}}}
</style>
</head>
<body>
<div class="wrap">
<header><a class="logo" href="#top"><img src="assets/apple-touch-icon.png" alt="" width="36" height="36">أصل الحكاية</a><nav><a href="#start">ابدأ من هنا</a><a href="#series">السلاسل</a><a href="#all">كل الحكايات</a><a href="#about">عن القناة</a><a href="#follow">تابعنا</a><a href="#contact">تواصل معنا</a></nav></header>
<main id="top">
<div class="hero">
<div><span class="tag">الأحدث</span><h1>{E(latest["title"])}</h1><p>كل شيء له بداية. نعود إلى اللحظة الأولى وراء الأشياء التي نستخدمها كل يوم، ونرويها حكايةً قصيرة لا تُنسى.</p>
<div class="btns"><a class="btn" href="{latest.get("links", {}).get("youtube", LINKS["youtube"][1])}" rel="noopener" target="_blank">شاهد على يوتيوب</a><a class="btn ghost" href="#all">كل الحكايات</a></div></div>
{f'<img src="{latest_img}" alt="غلاف {E(latest["title"])}" width="540" height="960">' if latest_img else ""}
</div>
{start_section}
<div id="series">{series_html}</div>
<section id="all"><h3>كل الحكايات</h3><div class="rail">{tiles}</div></section>
<section id="about" class="about"><h3>عن أصل الحكاية</h3><p>فيديوهات قصيرة بالعربية الفصحى عن أصل الاختراعات والاكتشافات. كل معلومة نذكرها لها مصدر موثوق على الأقل، والرسوم مولّدة بالذكاء الاصطناعي لتصوير الأجواء، وهي ليست صورًا تاريخية.</p></section>
<section id="follow"><h3>تابعنا</h3><div class="plats">{plats}</div></section>
<section id="suggest"><h3>اقترح حكاية</h3><p class="sub">وش الشيء اللي تبي نعرف أصله؟ اكتب لنا اسمه.</p><div class="stack"><a class="btn wide" href="{SUGGEST_URL}" rel="noopener" target="_blank">أرسل اقتراحك</a></div></section>
<section id="contact"><h3>تواصل معنا</h3><p class="sub">{E(CONTACT_NOTE) if CONTACT_NOTE else CONTACT_LINE}</p><div class="stack">{contact_buttons()}</div></section>
</main>
<footer><span>© 2026 أصل الحكاية</span><span><a href="links.html">كل الروابط</a> · <a href="privacy.html">سياسة الخصوصية</a> · <a href="terms.html">شروط الاستخدام</a></span></footer>
</div>
{beacon()}</body>
</html>
"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    (SITE / "links.html").write_text(render_links(eps, imgs), encoding="utf-8")
    (SITE / "l").mkdir(exist_ok=True)  # short link for the bio: the same hub at /l/ (canonical stays links.html)
    (SITE / "l" / "index.html").write_text(render_links(eps, imgs, "../"), encoding="utf-8")
    icons()
    static_files(today)
    print(f"index.html + links.html + l/: {len(eps)} episodes, latest «{latest['title']}», covers {sum(1 for v in imgs.values() if v)}")


if __name__ == "__main__":
    main()
