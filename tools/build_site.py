"""Build the public website «أصل الحكاية» (design 2, «السينما», owner 2026-10-17) into the site repository.

Public only: titles, dates, covers and platform links from studio/brain/episodes-public.json (brain.py export).
Never scripts, prompts, costs or anything private: those stay in the private studio, never in this public repo.
Static HTML, no JavaScript, no trackers, a strict Content-Security-Policy; GitHub Pages serves it.
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
LOGO = Path(os.environ.get("ASL_SITE_LOGO") or ASL / "studio" / "render" / "public" / "ep08" / "logo-round.png")
ALT = {"instagram": "إنستغرام", "facebook": "فيسبوك"}


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
    urls = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod></url>" for u in ("", "privacy.html", "terms.html"))
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>'
                                      f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (SITE / "404.html").write_text("""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>الصفحة غير موجودة | أصل الحكاية</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0B1416;color:#EEF3F2;font-family:Tahoma,sans-serif;text-align:center}
a{color:#F2C14E;font-weight:700}</style></head>
<body><main><h1>هذي الصفحة ما لقيناها</h1><p>رجع للصفحة الرئيسية وشوف الحكايات.</p><p><a href="/">أصل الحكاية</a></p></main></body></html>
""", encoding="utf-8")


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
    plats = "".join(f'<a class="plat" href="{u}" rel="noopener" target="_blank">{n}</a>' for n, u in LINKS.values())
    latest_img = imgs[latest["id"]]
    page = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; base-uri 'none'; form-action 'none'">
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
.plat{{border:1px solid #2E4A54;border-radius:999px;padding:9px 18px;font-weight:700;text-decoration:none}}
footer{{border-top:1px solid var(--line);color:var(--muted);padding-block:18px;margin-top:18px;font-size:14px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
footer a{{color:var(--muted)}}
@media (max-width:640px){{.hero{{grid-template-columns:1fr}} .hero img{{max-width:240px}}}}
@media (prefers-reduced-motion:no-preference){{.tile img{{transition:transform .2s}} .tile:hover img{{transform:scale(1.03)}}}}
</style>
</head>
<body>
<div class="wrap">
<header><a class="logo" href="#top">أصل الحكاية</a><nav><a href="#series">السلاسل</a><a href="#all">كل الحكايات</a><a href="#about">عن القناة</a><a href="#follow">تابعنا</a></nav></header>
<main id="top">
<div class="hero">
<div><span class="tag">الأحدث</span><h1>{E(latest["title"])}</h1><p>كل شيء له بداية. نعود إلى اللحظة الأولى وراء الأشياء التي نستخدمها كل يوم، ونرويها حكايةً قصيرة لا تُنسى.</p>
<div class="btns"><a class="btn" href="{latest.get("links", {}).get("youtube", LINKS["youtube"][1])}" rel="noopener" target="_blank">شاهد على يوتيوب</a><a class="btn ghost" href="#all">كل الحكايات</a></div></div>
{f'<img src="{latest_img}" alt="غلاف {E(latest["title"])}" width="540" height="960">' if latest_img else ""}
</div>
<div id="series">{series_html}</div>
<section id="all"><h3>كل الحكايات</h3><div class="rail">{tiles}</div></section>
<section id="about" class="about"><h3>عن أصل الحكاية</h3><p>فيديوهات قصيرة بالعربية الفصحى عن أصل الاختراعات والاكتشافات. كل معلومة نذكرها لها مصدر موثوق على الأقل، والرسوم مولّدة بالذكاء الاصطناعي لتصوير الأجواء، وهي ليست صورًا تاريخية.</p></section>
<section id="follow"><h3>تابعنا</h3><div class="plats">{plats}</div></section>
</main>
<footer><span>© 2026 أصل الحكاية</span><span><a href="privacy.html">سياسة الخصوصية</a> · <a href="terms.html">شروط الاستخدام</a></span></footer>
</div>
</body>
</html>
"""
    (SITE / "index.html").write_text(page, encoding="utf-8")
    icons()
    static_files(today)
    print(f"index.html: {len(eps)} episodes, latest «{latest['title']}», covers {sum(1 for v in imgs.values() if v)}")


if __name__ == "__main__":
    main()
