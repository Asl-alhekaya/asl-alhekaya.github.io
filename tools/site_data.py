"""Public data of the website «أصل الحكاية», shared by the PC build, the cloud build and the cloud feed (ADR-008).

Pure stdlib, one copy: studio/site/build_site.py imports it (the Pages repo gets both files from install_pages.py),
studio_app/site_feed.py imports it on the cloud runner. An episode entry is the public subset of the brain board:
id, title, series, part, published (date), status, year, cover, links, publish_on. `status: "pending"` = a private or
scheduled cloud upload that YouTube does not show publicly yet; it never shows on the site.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KUWAIT = timezone(timedelta(hours=3))  # no daylight saving: the future-date gate must not depend on the machine's clock


def today_kuwait():
    return datetime.now(KUWAIT).date().isoformat()


def visible(eps, today):
    """What the site shows: everything dated today or earlier except `pending` (a private or scheduled cloud upload that
    YouTube does not show yet, ADR-008). The board's own "scheduled" status stays visible once its day came, as always."""
    return [e for e in eps if e.get("status") != "pending" and e.get("published") and str(e["published"])[:10] <= today]


def upsert(eps, new):
    """Add or update one episode by id. Fields of `new` win, links are merged (a TikTok link added by hand survives a
    re-publish), the order of the file is kept (a new id goes last). Returns a new list; same input = same output."""
    out, found = [], False
    for e in eps:
        if e.get("id") == new["id"]:
            merged = {**e, **{k: v for k, v in new.items() if k != "links"}}
            merged["links"] = {**e.get("links", {}), **new.get("links", {})}
            out.append(merged)
            found = True
        else:
            out.append(e)
    return out if found else out + [dict(new)]


def youtube_id(url):
    tail = str(url or "").split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    return tail if len(tail) == 11 else ""


def oembed_public(url, timeout=15):
    """True only when YouTube's public oEmbed answers 200 for the video (a private or deleted one does not). A network
    error is False: the episode just waits for the next build."""
    vid = youtube_id(url)
    if not vid:
        return False
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://youtube.com/shorts/{vid}&format=json",
                                    timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def promote(eps, today, probe=oembed_public):
    """pending -> published for the episodes YouTube shows publicly now. The date is the scheduled day (`publish_on`) when
    it is not in the future, else today. Returns (new list, ids promoted)."""
    out, done = [], []
    for e in eps:
        if e.get("status") == "pending" and probe(e.get("links", {}).get("youtube", "")):
            day = min(str(e.get("publish_on") or today)[:10], today)
            e = {k: v for k, v in e.items() if k != "publish_on"}
            e.update({"status": "published", "published": day})
            done.append(e["id"])
        out.append(e)
    return out, done


def dump(eps):
    return json.dumps(eps, ensure_ascii=False, indent=2) + "\n"
