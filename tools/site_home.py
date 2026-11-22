"""The home page's first screen (design v2, approved by the owner 2026-11-22 «ابدأ البناء»): intro + latest episode + the
suggestion box. Day = the covers' cream paper; night (prefers-color-scheme: dark) = the museum sister cover (lamp, gold frame,
book on the pedestal, brass plaque). Source of the look: studio/site/proposal-2026-11-22/tools-v2/template.html.

Imported by build_site.py (a sibling file: install_pages.py ships it to the Pages repo as tools/site_home.py, a test fails when the
copy drifts). Pure functions of their arguments: no file, no network, no clock, so a rebuild changes nothing by itself.

Strict-CSP rules kept here: no inline script (the box's script is assets/suggest.js), no external image (the pictures are
assets/home/*.webp made by make_home_assets.py, the logo is assets/apple-touch-icon.png), no inline style attribute.
Every class of this screen lives under .stage, so the rest of the page (the live dark site) keeps its own CSS untouched;
the one shared name clash (.btn) is avoided by calling this screen's button .pbtn.
"""
from __future__ import annotations

import html
import re

E = html.escape

# The topic chips. Keys are the contract with the Worker (proposal-2026-11-22/worker.js TOPICS) and with assets/suggest.js
# HINTS; a test fails when the three disagree.
TOPICS = (
    ("daily", "شيء نستخدمه كل يوم"),
    ("food", "أكلة أو مشروب"),
    ("habit", "عادة أو كلمة"),
    ("invention", "اختراع"),
    ("place", "مكان أو مدينة"),
    ("heritage", "تراث وتقاليد"),
    ("home", "في البيت"),
    ("other", "أخرى"),
)
QUESTION = "ما الشيء الذي تودّ أن نحكي أصله؟"
PLACEHOLDER = "شيء تستخدمه أو تأكله أو تقوله كل يوم، ولم تسأل يومًا من أين جاء؟"  # also the first of PROMPTS in suggest.js
TEXT_MIN, TEXT_MAX = 3, 200  # the Worker's MIN_LEN / MAX_LEN
HOME_ASSETS = ("home/paper.webp", "home/wall.webp", "home/floor.webp", "home/beam.webp", "home/pedestal.webp",
               "home/book.webp", "suggest.js")  # under assets/; build_site.py copies them on the PC and checks they exist

STAR = ('<svg class="star {cls}" viewBox="-1 -1 2 2" aria-hidden="true"><path d="M0 -1 C0.1 -0.32 0.32 -0.1 1 0 C0.32 0.1 '
        '0.1 0.32 0 1 C-0.1 0.32 -0.32 0.1 -1 0 C-0.32 -0.1 -0.1 -0.32 0 -1Z"/></svg>')

# ---------------------------------------------------------------- CSS (day; the night blocks below are expanded by night())
DAY_CSS = r"""
.stage{--bg:#F3EEE3;--text:#14232B;--muted:#4D5D63;--title1:#14232B;--title2:#0F4C5C;--frame:#14232B;--rule:#0F4C5C;
  --diamond:#F6C445;--focus:#1A7089;--err:#A63D2A;--day:block;--day-flex:flex;--night:none;--night-flex:none;
  --gold-grad:linear-gradient(135deg,#fff0a8 0%,#F6C445 28%,#b8862b 52%,#f6d77a 74%,#9a6a12 100%);
  color-scheme:light;color:var(--text);line-height:1.7;font-family:"Almarai",Tahoma,sans-serif;
  position:relative;isolation:isolate;overflow:hidden;border-bottom:3px solid #F6C445;
  padding:12px max(16px,env(safe-area-inset-right,0px)) 28px max(16px,env(safe-area-inset-left,0px))}
.stage::before{content:"";position:absolute;inset:0;z-index:-2;
  background:linear-gradient(180deg,rgba(243,238,227,0) 0%,rgba(243,238,227,0) 70%,#F3EEE3 100%),url(assets/home/paper.webp) center top/cover no-repeat,#F3EEE3}
.stage h1,.stage h2,.stage h3{font-family:"Cairo","Almarai",Tahoma,sans-serif;margin:0;text-wrap:balance}
.stage .sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
.stage .star{position:absolute;fill:var(--diamond);stroke:rgba(20,10,0,.35);stroke-width:.05;pointer-events:none}
.stage .day{display:var(--day)}
.stage .night{display:var(--night)}
.stage-in{max-width:480px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr);gap:18px}
.stage .frame,.stage .painting{display:contents}

/* section menu: a details pop-up on phones (no script), a plain row from 900 px */
.stage .menu{position:absolute;top:8px;left:max(10px,env(safe-area-inset-left,0px));z-index:5}
.stage .menu summary{list-style:none;display:inline-flex;align-items:center;justify-content:center;width:44px;min-height:44px;padding:0;cursor:pointer;
  border:1.5px solid var(--frame);border-radius:999px;background:rgba(255,253,248,.85);color:var(--text);
  font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:14px}
.stage .menu summary::-webkit-details-marker{display:none}
.stage .menu nav{position:absolute;top:calc(100% + 6px);left:0;min-width:200px;display:grid;padding:6px;
  background:#FBF7EE;border:2px solid var(--frame);box-shadow:5px 5px 0 var(--diamond)}
.stage .menu nav a,.stage .topnav a{display:flex;align-items:center;min-height:44px;padding:0 12px;text-decoration:none;font-weight:700}
.stage .topnav{display:none}
.stage .menu summary:focus-visible,.stage .menu nav a:focus-visible,.stage .topnav a:focus-visible{outline:3px solid var(--focus);outline-offset:2px}

.stage .intro{position:relative;text-align:center;min-width:0}
.stage .intro::before{content:"";position:absolute;z-index:-1;left:50%;top:32px;width:760px;height:760px;transform:translate(-50%,-50%);
  background:repeating-conic-gradient(from 0deg,rgba(184,134,43,.13) 0deg 6deg,transparent 6deg 14deg);
  -webkit-mask-image:radial-gradient(circle,#000 8%,transparent 46%);mask-image:radial-gradient(circle,#000 8%,transparent 46%);
  mix-blend-mode:multiply;pointer-events:none}
.stage .mark{position:relative;display:var(--day);width:60px;height:60px;margin:0 auto}
.stage .mark img{display:block;width:100%;height:100%;border-radius:50%;filter:drop-shadow(0 6px 10px rgba(6,34,44,.25))}
.stage .mark .s1{width:22px;height:22px;top:-6px;left:-26px}
.stage .mark .s2{width:10px;height:10px;top:18px;left:-34px}
.stage .intro h1{font-weight:900;font-size:40px;line-height:1.15;margin-top:4px;color:var(--title1);letter-spacing:0}
.stage .intro h1 span{color:var(--title2)}
.stage .mast{display:var(--day-flex);align-items:center;gap:10px;max-width:300px;margin:4px auto 0;color:var(--text)}
.stage .mast i{flex:1;height:2px;background:var(--frame)}
.stage .mast svg{width:15px;height:15px;flex:none;fill:var(--diamond);stroke:var(--frame);stroke-width:2;stroke-linejoin:miter}
.stage .mast span{font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:16px;line-height:1.5;white-space:nowrap}
.stage .divider{display:var(--night-flex)}
.stage .chip-name{display:var(--night)}
.stage .breath{color:var(--muted);margin:6px auto 0;max-width:33ch;font-size:15px;line-height:1.65}
/* the latest episode: one straight line (no tilt anywhere) */
.stage .latest{display:inline-flex;align-items:center;gap:10px;min-height:46px;margin-top:12px;padding:5px 10px 5px 14px;
  background:#14232B;color:#F6C445;box-shadow:5px 5px 0 #F6C445;overflow:hidden;
  text-decoration:none;font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:15px;line-height:1.3;max-width:100%;text-align:start}
.stage .latest img{width:26px;height:35px;object-fit:cover;flex:none;outline:1.5px solid #F6C445}
.stage .latest .t{min-width:0;overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-clamp:2;overflow-wrap:anywhere}
.stage .latest small{font:inherit;font-weight:700;color:#F3EEE3;opacity:.88}
.stage .latest svg{flex:none}

.stage .card{position:relative;background:#FBF7EE;border:3px solid #14232B;box-shadow:8px 8px 0 #F6C445;padding:16px 18px 14px}
.stage .card .s3{width:24px;height:24px;top:-13px;left:-12px}
.stage .card h2{font-weight:800;font-size:20px;line-height:1.35;text-align:center;color:var(--text)}
.stage .card .line{width:56px;height:4px;background:var(--rule);margin:8px auto 14px}
.stage .lead{color:var(--muted);text-align:center;margin:0;font-size:15px}
.stage fieldset{border:0;margin:0 0 12px;padding:0;min-width:0}
.stage .chips{display:flex;flex-wrap:wrap;justify-content:center;gap:6px}
.stage .chip{position:relative;display:inline-flex;align-items:center;min-height:44px}
.stage .chip input{position:absolute;opacity:0;inset:0;margin:0;cursor:pointer;width:100%;height:100%}
.stage .chip span{display:inline-flex;align-items:center;min-height:44px;padding:0 11px;border-radius:999px;background:rgba(255,253,248,.7);color:#14232B;
  border:1.5px solid #14232B;font-family:"Cairo","Almarai",sans-serif;font-size:13.5px;font-weight:700;line-height:1;
  transition:background .15s,color .15s,border-color .15s}
.stage .chip input:checked + span{background:#0F4C5C;color:#FBF7EE;border-color:#0F4C5C}
.stage .chip input:focus-visible + span{outline:3px solid var(--focus);outline-offset:2px}
.stage .field{position:relative}
.stage textarea{display:block;width:100%;min-height:86px;resize:none;border:2px solid #14232B;border-radius:8px;background:#FFFDF8;
  color:var(--text);font:inherit;font-size:16px;line-height:1.6;padding:10px 12px 22px}
.stage textarea::placeholder{color:var(--muted);opacity:.92}
.stage textarea:focus{outline:2px solid var(--focus);outline-offset:1px}
.stage textarea[aria-invalid="true"]{border-color:var(--err)}
.stage textarea[readonly]{opacity:.7}
.stage .count{position:absolute;bottom:4px;left:10px;font-size:12px;color:var(--muted)}
/* honeypot: clipped in place (an off-screen left:-9999px would make a horizontal scroll in RTL) */
.stage .hp{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
.stage .msg{margin:8px 2px 0;font-size:14px;font-weight:700;color:var(--err)}
.stage .msg:empty{display:none}
.stage .oops{display:none}
.stage .oops:target{display:block}
.stage .pbtn{position:relative;display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:50px;margin-top:12px;
  border:2px solid #14232B;border-radius:4px;background:#0F4C5C;color:#FBF7EE;box-shadow:4px 4px 0 #14232B;padding:0 14px;
  font-family:"Cairo","Almarai",sans-serif;font-weight:800;font-size:17px;cursor:pointer;text-decoration:none}
.stage .pbtn:active{transform:translate(1px,1px);box-shadow:2px 2px 0 #14232B}
.stage .pbtn:focus-visible,.stage .latest:focus-visible,.stage .note a:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
.stage .pbtn[disabled]{opacity:.8;cursor:progress}
.stage .pbtn.ghost{background:transparent;color:var(--text);border:1px solid var(--frame);box-shadow:none}
.stage .spin{width:18px;height:18px;border-radius:50%;border:2.5px solid currentColor;border-inline-end-color:transparent;display:none}
.stage .sending .spin{display:inline-block}
@media (prefers-reduced-motion:no-preference){.stage .sending .spin{animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}}
.stage .note{color:var(--muted);font-size:12.5px;margin:10px 2px 0;line-height:1.6;text-align:center}
.stage .note a{color:var(--muted);display:inline-block;padding:13px 6px;margin:-13px 0}
.stage .thanks{display:none;text-align:center;padding:4px 2px 2px}
.stage .thanks .book{position:relative;display:inline-block;width:84px;height:98px;margin-top:4px}
.stage .thanks .book img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 6px 8px rgba(30,20,8,.35))}
.stage .thanks .book .s4{width:22px;height:22px;top:-4px;left:-20px}
.stage .thanks .book .s5{width:9px;height:9px;top:22px;left:-26px}
.stage .thanks h3{font-weight:800;font-size:21px;margin-top:6px;color:var(--text)}
.stage .thanks p{color:var(--muted);margin:4px 0 0}
.stage .card.done form,.stage .card:has(#thanks:target) form{display:none}
.stage .card.done .thanks,.stage #thanks:target{display:block}

@media (max-width:899px) and (max-height:720px){
  .stage{padding-top:8px}
  .stage-in{gap:12px}
  .stage .mark{width:42px;height:42px}
  .stage .mark .s1{width:16px;height:16px;left:-20px}
  .stage .mark .s2{width:8px;height:8px;top:10px;left:-26px}
  .stage .intro h1{font-size:32px;margin-top:0}
  .stage .card h2{font-size:18px}
  .stage .mast{margin-top:2px}
  .stage .breath{font-size:14px;line-height:1.55;margin-top:4px}
  .stage .latest{margin-top:8px;min-height:44px}
  .stage .card{padding:14px 14px 12px}
  .stage .card .line{margin:4px auto 8px}
  .stage fieldset{margin-bottom:10px}
  .stage .chip span{padding:0 9px;font-size:13px}
  .stage .chips{gap:4px}
  .stage textarea{min-height:64px;padding-bottom:18px}
  .stage .pbtn{margin-top:8px;min-height:46px}
  .stage .breath{display:none}
  .stage .mark{display:none}
}
@media (min-width:900px){
  .stage{padding:8px 32px 64px}
  .stage .menu{display:none}
  .stage .topnav{display:flex;flex-wrap:wrap;gap:0 4px;max-width:1040px;margin:0 auto 4px;font-size:15px}
  .stage .topnav a{color:var(--muted)}
  .stage .topnav a:hover{color:var(--text)}
  .stage-in{max-width:1040px;grid-template-columns:minmax(0,1fr) 440px;gap:64px;align-items:center;min-height:min(78vh,700px)}
  .stage .mark{width:96px;height:96px}
  .stage .mark .s1{width:30px;height:30px;top:-8px;left:-38px}
  .stage .mark .s2{width:13px;height:13px;top:26px;left:-48px}
  .stage .intro::before{top:48px;width:1000px;height:1000px}
  .stage .intro h1{font-size:64px;margin-top:10px}
  .stage .mast{max-width:380px}
  .stage .mast span{font-size:19px}
  .stage .breath{font-size:17px;max-width:36ch}
  .stage .card{padding:22px 24px 18px}
  .stage .card h2{font-size:23px}
}
"""

# NIGHT: the museum sister cover (render/src/CoverSisters.jsx «Museum»). Every rule starts with N; night() writes N as :root inside
# @media (prefers-color-scheme:dark), so the higher specificity wins over the day rules and the media blocks above.
NIGHT = r"""
N .stage{--bg:#06222C;--text:#F3EEE3;--muted:#D9E3E2;--focus:#F6C445;--err:#FFB1A3;--diamond:#F6C445;--day:none;--day-flex:none;
  --night:block;--night-flex:flex;color-scheme:dark;padding:0;background:#0B2E37;border-bottom:0}
N .stage::before{background:radial-gradient(ellipse 70% 260px at 50% 0,rgba(255,232,170,.42),transparent 72%),url(assets/home/wall.webp) center top/cover no-repeat;bottom:64px}
N .stage-in{max-width:none;display:block;padding:0 10px}
N .stage .menu summary{background:rgba(4,24,31,.82);border:1px solid rgba(246,196,69,.75);color:#F6C445}
N .stage .menu nav{background:#06222C;border:1px solid rgba(246,196,69,.8);box-shadow:0 12px 24px rgba(0,0,0,.5)}
N .stage .menu nav a{color:#F3EEE3}
N .stage .lamp{display:block;position:relative;width:128px;height:46px;margin:12px auto 0}
N .stage .lamp .bar{position:absolute;left:0;top:0;width:128px;height:18px;border-radius:10px 10px 4px 4px;background:var(--gold-grad);box-shadow:0 4px 8px rgba(0,0,0,.55)}
N .stage .lamp .strip{position:absolute;left:7px;top:14px;width:114px;height:4px;border-radius:2px;background:#fff6d0;box-shadow:0 0 10px 4px rgba(255,230,160,.55)}
N .stage .lamp .arm{position:absolute;left:59px;top:18px;width:10px;height:28px;background:var(--gold-grad)}
N .stage .frame{display:block;position:relative;max-width:560px;margin:0 auto;padding:10px;background:var(--gold-grad);
  box-shadow:0 14px 28px rgba(0,0,0,.65),inset 0 0 0 1px rgba(255,244,200,.75),inset 0 0 0 3px rgba(120,80,10,.5)}
N .stage .frame::before{content:"";position:absolute;inset:8px;border:2px solid #5e420a;pointer-events:none}
N .stage .corner{display:block;position:absolute;width:14px;height:14px;background:#5e420a;clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);z-index:2}
N .stage .corner::before{content:"";position:absolute;inset:2px;background:var(--gold-grad);clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}
N .stage .corner.c1{top:8px;right:8px}
N .stage .corner.c2{top:8px;left:8px}
N .stage .corner.c3{bottom:8px;right:8px}
N .stage .corner.c4{bottom:8px;left:8px}
N .stage .painting{display:block;position:relative;overflow:hidden;padding:20px 12px 0;text-align:center;
  background:linear-gradient(180deg,rgba(5,30,38,.62) 0%,rgba(5,30,38,.42) 30%,rgba(5,30,38,0) 52%),url(assets/home/beam.webp) center top/auto 100% no-repeat,#124351;
  box-shadow:inset 0 0 40px rgba(0,0,0,.6)}
N .stage .painting::before{content:"";position:absolute;inset:8px;border:1px solid rgba(246,196,69,.7);pointer-events:none;z-index:1}
N .stage .painting>*{position:relative;z-index:2}
N .stage .intro::before{display:none}
N .stage .chip-name{display:inline-block;margin:0;height:32px;padding:0 18px;border-radius:16px;background:#0F4C5C;border:2px solid #F6C445;
  color:#F6C445;font-family:"Cairo","Almarai",sans-serif;font-weight:900;font-size:15px;line-height:28px;white-space:nowrap}
N .stage .intro h1{font-size:48px;line-height:1.3;margin:8px 0 -.3em;padding-bottom:.3em;color:transparent;
  background:linear-gradient(180deg,#fff0a8 0,#F6C445 .6em,#c98a14 1.3em,#c98a14 100%);-webkit-background-clip:text;background-clip:text;
  filter:drop-shadow(2px 3px 0 rgba(6,20,26,.6))}
N .stage .intro h1 span{color:transparent}
N .stage .divider{justify-content:center;align-items:center;gap:8px;height:10px;margin:10px auto 0}
N .stage .divider i{width:64px;border-top:3px double #F6C445}
N .stage .divider b{width:11px;height:11px;background:#F6C445;clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}
N .stage .breath{color:#F3EEE3;font-size:14.5px;line-height:1.6;margin-top:8px;text-shadow:0 2px 8px rgba(0,0,0,.55)}
N .stage .latest{margin-top:10px;background:rgba(4,24,31,.78);color:#F6C445;border:1px solid rgba(246,196,69,.75);box-shadow:none;border-radius:4px;padding:5px 10px 5px 12px}
N .stage .card{margin-top:14px;text-align:start;background:linear-gradient(180deg,rgba(5,28,36,.9),rgba(3,20,26,.92));border:1px solid rgba(246,196,69,.8);
  border-radius:3px;box-shadow:inset 0 0 0 5px rgba(3,20,26,.92),inset 0 0 0 6px rgba(246,196,69,.38),0 16px 32px rgba(0,0,0,.45);padding:20px 14px 16px}
N .stage .card::after{content:"";position:absolute;inset:9px;pointer-events:none;
  background:radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 0 0/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 100% 0/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 0 100%/7px 7px no-repeat,
    radial-gradient(circle at 40% 40%,#fff3c0 0,#c9a24a 40%,#7a5a10 62%,transparent 68%) 100% 100%/7px 7px no-repeat}
N .stage .card .s3{display:none}
N .stage .card h2{color:#F6C445;font-size:19px}
N .stage .card .line{display:flex;justify-content:center;align-items:center;gap:6px;width:auto;height:8px;background:none;margin:6px auto 12px}
N .stage .card .line::before{content:"";width:40px;border-top:3px double rgba(246,196,69,.8)}
N .stage .card .line::after{content:"";width:40px;border-top:3px double rgba(246,196,69,.8)}
N .stage .lead{color:#D9E3E2}
N .stage .chip span{padding:0 10px;font-size:13px;background:rgba(2,15,20,.6);color:#F3EEE3;border:1px solid rgba(246,196,69,.45)}
N .stage .chip input:checked + span{background:var(--gold-grad);color:#3a2a06;border-color:#F6C445}
N .stage textarea{background:rgba(2,15,20,.6);border:1px solid rgba(246,196,69,.42);border-radius:4px;color:#F3EEE3}
N .stage textarea::placeholder{color:#C9D6D6}
N .stage .count{color:#C9D6D6}
N .stage .pbtn{background:var(--gold-grad);color:#3a2a06;border:0;border-radius:6px;box-shadow:0 6px 14px rgba(0,0,0,.4);font-weight:900;font-size:19px;text-shadow:0 1px 0 rgba(255,240,190,.7)}
N .stage .pbtn::before{content:"";position:absolute;inset:4px;border:1px solid rgba(70,48,6,.55);border-radius:4px;pointer-events:none}
N .stage .pbtn:active{box-shadow:0 3px 8px rgba(0,0,0,.4)}
N .stage .pbtn.ghost{background:transparent;color:#F6C445;border:1px solid rgba(246,196,69,.75);text-shadow:none;box-shadow:none}
N .stage .pbtn.ghost::before{display:none}
N .stage .note{color:#D9E3E2}
N .stage .note a{color:#D9E3E2}
N .stage .thanks .book{display:none}
N .stage .thanks h3{color:#F6C445}
N .stage .thanks p{color:#D9E3E2}
N .stage .hero{display:block;position:relative;width:88%;margin:20% auto 0;aspect-ratio:870/288}
N .stage .hero::before{content:"";position:absolute;inset:0;background:url(assets/home/pedestal.webp) center/100% 100% no-repeat;
  -webkit-mask-image:linear-gradient(180deg,transparent 0,#000 20%),linear-gradient(90deg,transparent 0,#000 4.5%,#000 95.5%,transparent 100%);-webkit-mask-composite:source-in;
  mask-image:linear-gradient(180deg,transparent 0,#000 20%),linear-gradient(90deg,transparent 0,#000 4.5%,#000 95.5%,transparent 100%);mask-composite:intersect}
N .stage .hero-book{display:block;position:absolute;left:50%;bottom:60%;width:26%;transform:translateX(-50%);z-index:3}
N .stage .hero-book img{display:block;width:100%;height:auto;filter:drop-shadow(0 6px 8px rgba(0,0,0,.5)) drop-shadow(0 0 16px rgba(246,196,69,.35))}
N .stage .hero-book .s6{width:30%;height:auto;aspect-ratio:1;top:-4%;left:-38%}
N .stage .hero-book .s7{width:12%;height:auto;aspect-ratio:1;top:22%;left:-46%}
N .stage .floor{display:block;position:relative;height:64px;margin-top:20px;background:url(assets/home/floor.webp) center top/cover no-repeat}
N .stage .plaque{display:flex;position:absolute;left:50%;top:-24px;transform:translateX(-50%);width:min(250px,72%);height:50px;align-items:center;justify-content:center;
  border-radius:6px;background:var(--gold-grad);box-shadow:0 6px 12px rgba(0,0,0,.5);color:#3a2a06;font-family:"Cairo","Almarai",sans-serif;
  font-weight:900;font-size:19px;text-shadow:0 1px 0 rgba(255,240,190,.7);white-space:nowrap}
N .stage .plaque::before{content:"";position:absolute;inset:5px;border:1px solid rgba(70,48,6,.55);border-radius:4px}
N .stage .plaque::after{content:"";position:absolute;inset:8px;
  background:radial-gradient(circle at 35% 35%,#fff3c0,#7a5a10 70%,transparent 72%) 0 0/5px 5px no-repeat,
    radial-gradient(circle at 35% 35%,#fff3c0,#7a5a10 70%,transparent 72%) 100% 0/5px 5px no-repeat,
    radial-gradient(circle at 35% 35%,#fff3c0,#7a5a10 70%,transparent 72%) 0 100%/5px 5px no-repeat,
    radial-gradient(circle at 35% 35%,#fff3c0,#7a5a10 70%,transparent 72%) 100% 100%/5px 5px no-repeat}
"""
NIGHT_SHORT = r"""
N .stage .lamp{margin-top:6px;height:30px;width:104px}
N .stage .lamp .bar{width:104px;height:14px}
N .stage .lamp .strip{width:90px;top:11px}
N .stage .lamp .arm{left:47px;top:14px;height:16px;width:8px}
N .stage .frame{padding:8px}
N .stage .painting{padding:12px 10px 0}
N .stage .chip-name{height:28px;line-height:24px;font-size:14px}
N .stage .intro h1{font-size:36px;margin-top:2px}
N .stage .divider{margin-top:4px}
N .stage .breath{display:none}
N .stage .latest{margin-top:6px}
N .stage .card{margin-top:10px;padding:14px 12px 10px}
N .stage .card .line{margin:4px auto 8px}
N .stage .pbtn{font-size:17px}
"""
NIGHT_DESKTOP = r"""
N .stage .topnav{padding:10px 32px 0}
N .stage .topnav a{color:#F3EEE3;background:rgba(4,24,31,.78);border-radius:999px;margin:0 2px;padding:0 14px}
N .stage .topnav a:hover{color:#F6C445}
N .stage-in{padding:0 32px}
N .stage .lamp{margin-top:28px;transform:scale(1.25);transform-origin:50% 100%}
N .stage .frame{padding:14px}
N .stage .frame::before{inset:11px}
N .stage .corner.c1{top:12px;right:12px}
N .stage .corner.c2{top:12px;left:12px}
N .stage .corner.c3{bottom:12px;right:12px}
N .stage .corner.c4{bottom:12px;left:12px}
N .stage .painting{padding:30px 40px 0}
N .stage .intro h1{font-size:64px}
N .stage .card{padding:24px 26px 18px}
N .stage .hero{width:80%;margin-top:18%}
N .stage .floor{height:88px;margin-top:28px}
N .stage::before{bottom:88px}
N .stage .plaque{top:-28px;width:300px;height:58px;font-size:20px}
"""
DIAMOND = '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M7 1 13 7 7 13 1 7Z"/></svg>'
SHORT = "(max-width:899px) and (max-height:720px)"
DESK = "(min-width:900px)"


def night(rules: str, media: str = "") -> str:
    """Write each `N ...` rule as `:root ...` inside @media (prefers-color-scheme:dark) [and MEDIA]. A rule without N fails."""
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", rules, flags=re.S)):
        sels = []
        for s in sel.split(","):
            s = s.strip()
            if not (s == "N" or s.startswith(("N ", "N."))):
                raise ValueError(f"night rule without N: {s!r}")
            sels.append(":root" + s[1:])
        out.append(",".join(sels) + "{" + " ".join(body.split()) + "}")
    query = "(prefers-color-scheme:dark)" + (f" and {media}" if media else "")
    return f"@media {query}{{\n" + "\n".join(out) + "\n}"


def css() -> str:
    """All first-screen CSS: day, then the three night blocks (base, short phones, desktop)."""
    return "\n".join((DAY_CSS.strip(), night(NIGHT), night(NIGHT_SHORT, SHORT), night(NIGHT_DESKTOP, DESK)))


def menu(items) -> str:
    """The section links twice: a <details> pop-up for phones and a plain row from 900 px (only one is ever displayed)."""
    links = "".join(f'<a href="{E(h)}">{E(t)}</a>' for h, t in items)
    burger = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
              'stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>')
    return (f'<details class="menu"><summary>{burger}<span class="sr">القائمة</span></summary><nav aria-label="أقسام الصفحة">{links}</nav></details>\n'
            f'<nav class="topnav" aria-label="أقسام الصفحة">{links}</nav>')


def latest_strip(title: str, url: str, img: str | None) -> str:
    """The newest public episode; "" when there is none (a site with zero visible episodes still builds)."""
    if not (title and url):
        return ""
    pic = f'<img src="{E(img)}" alt="" width="26" height="35">' if img else ""
    return (f'<a class="latest" href="{E(url)}" rel="noopener" target="_blank">{pic}'
            f'<span class="t"><small>الأحدث:</small> {E(title)}</span>'
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5v14l11-7z"/></svg></a>')


def suggest_form(action: str) -> str:
    """The inline box (needs a Worker). Works without the script too: the browser checks the field and the Worker answers
    303 to /#thanks or /#suggest-error (CSS :target shows the panel)."""
    chips = "".join(f'<label class="chip"><input type="radio" name="topic" value="{k}"><span>{E(t)}</span></label>' for k, t in TOPICS)
    return f"""<form id="sform" method="post" action="{E(action)}">
<h2 id="h-suggest">{QUESTION}</h2>
<div class="line" aria-hidden="true"></div>
<fieldset><legend class="sr">من أي باب هو؟ (اختياري)</legend><div class="chips">{chips}</div></fieldset>
<div class="field"><label for="stext" class="sr">{QUESTION}</label>
<textarea id="stext" name="text" rows="2" required minlength="{TEXT_MIN}" maxlength="{TEXT_MAX}" aria-describedby="smsg" placeholder="{PLACEHOLDER}"></textarea>
<span class="count" id="scount" aria-hidden="true">0 / {TEXT_MAX}</span></div>
<div class="hp" aria-hidden="true"><label>موقعك <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
<input type="hidden" name="src" id="ssrc" value="">
<input type="hidden" name="t" id="st" value="">
<p class="msg" id="smsg" role="status" aria-live="polite"></p>
<p class="msg oops" id="suggest-error">لم يصل الاقتراح، جرّب مرة أخرى بعد قليل.</p>
<button class="pbtn" id="sbtn" type="submit"><span class="spin" aria-hidden="true"></span><span id="sbtn-label">أرسل الاقتراح</span></button>
<p class="note">دون تسجيل ودون ذكر اسمك، ونقرأ كل اقتراح. لا تكتب رقمًا أو حسابًا أو أي معلومة شخصية. <a href="privacy.html">الخصوصية</a></p>
</form>
<div class="thanks" id="thanks" tabindex="-1">
<span class="book" aria-hidden="true"><img src="assets/home/book.webp" alt="" width="84" height="98">{STAR.format(cls="s4")}{STAR.format(cls="s5")}</span>
<h3>وصل اقتراحك، شكرًا لك</h3>
<p>نقرأ كل اقتراح بأنفسنا. وإذا صار حكاية، ستراه على القناة.</p>
<a class="pbtn ghost" href="#suggest" id="sagain">اقترح شيئًا آخر</a>
</div>"""


def suggest_link(url: str) -> str:
    """Fallback when no Worker is set: the same card with one button to the old form (never a dead box)."""
    return f"""<h2 id="h-suggest">{QUESTION}</h2>
<div class="line" aria-hidden="true"></div>
<p class="lead">اكتب اسم الشيء في نموذج قصير، دون تسجيل ودون ذكر اسمك.</p>
<a class="pbtn" href="{E(url)}" rel="noopener" target="_blank">أرسل اقتراحك</a>
<p class="note">لا تكتب رقمًا أو حسابًا أو أي معلومة شخصية. <a href="privacy.html">الخصوصية</a></p>"""


def first_screen(*, latest_title: str, latest_url: str, latest_img: str | None, nav, action: str = "", fallback_url: str) -> str:
    """The whole first screen. action = the Worker's /suggest URL (inline box), or "" for the link fallback."""
    box = suggest_form(action) if action else suggest_link(fallback_url)
    return f"""<div class="stage">
{menu(nav)}
<div class="lamp night" aria-hidden="true"><i class="arm"></i><i class="bar"></i><i class="strip"></i></div>
<div class="stage-in"><div class="frame">
<i class="corner c1 night" aria-hidden="true"></i><i class="corner c2 night" aria-hidden="true"></i><i class="corner c3 night" aria-hidden="true"></i><i class="corner c4 night" aria-hidden="true"></i>
<div class="painting">
<header class="intro">
<span class="mark"><img src="assets/apple-touch-icon.png" alt="شعار أصل الحكاية" width="64" height="64">{STAR.format(cls="s1")}{STAR.format(cls="s2")}</span>
<p class="chip-name">كل شيء له بداية</p>
<h1>أصل <span>الحكاية</span></h1>
<p class="mast"><i></i>{DIAMOND}<span>كل شيء له بداية</span>{DIAMOND}<i></i></p>
<div class="divider" aria-hidden="true"><i></i><b></b><i></i></div>
<p class="breath">حكايات قصيرة عن أصل الأشياء التي نستخدمها كل يوم، ولا نعرف من أين جاءت.</p>
{latest_strip(latest_title, latest_url, latest_img)}
</header>
<section class="card" id="suggest" aria-labelledby="h-suggest">
{STAR.format(cls="s3")}
{box}
</section>
<div class="hero night" aria-hidden="true"><div class="hero-book"><img src="assets/home/book.webp" alt="" width="240" height="281">{STAR.format(cls="s6")}{STAR.format(cls="s7")}</div></div>
</div></div></div>
<div class="floor night"><div class="plaque" role="img" aria-label="من متحف أصل الحكاية">من متحف أصل الحكاية</div></div>
</div>"""
