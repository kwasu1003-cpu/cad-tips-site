"""정적 사이트 생성기: content/posts/*.md -> public/

사용법: python build.py
SEO: canonical, 메타 설명, OG 태그, JSON-LD(BlogPosting/BreadcrumbList), sitemap.xml, robots.txt, RSS, 관련 글 내부 링크
"""
import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
POSTS = ROOT / "content" / "posts"
OUT = ROOT / "public"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base_url"].rstrip("/")


def parse(path):
    """--- 로 감싼 머리말(key: value)과 본문 분리"""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"머리말 없음: {path.name}")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["slug"] = meta.get("slug") or path.stem
    meta["url"] = f"/posts/{meta['slug']}/"
    meta["updated"] = meta.get("updated") or meta["date"]
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    meta["html"] = md.convert(m.group(2))
    meta["toc"] = md.toc if md.toc_tokens else ""
    for k in ("title", "description", "date", "category"):
        if not meta.get(k):
            raise ValueError(f"{path.name}: '{k}' 누락")
    return meta


def esc(s):
    return html.escape(s, quote=True)


def page(title, desc, path, body, jsonld=None, og_type="website"):
    url = BASE + path
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    ads = ""
    if SITE.get("adsense_client"):
        ads = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={SITE["adsense_client"]}" '
               'crossorigin="anonymous"></script>')
    nav = "".join(f'<a href="/category/{k}/">{esc(v)}</a>' for k, v in SITE["categories"].items())
    return f"""<!doctype html>
<html lang="{SITE['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{esc(SITE['title'])}">
<meta property="og:locale" content="ko_KR">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'])}" href="/feed.xml">
<link rel="stylesheet" href="/style.css">
{ld}{ads}
</head>
<body>
<header class="site"><a class="brand" href="/">{esc(SITE['title'])}</a><nav>{nav}</nav></header>
<main>{body}</main>
<footer class="site"><p>© {datetime.now().year} {esc(SITE['title'])} · <a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/feed.xml">RSS</a></p></footer>
</body>
</html>
"""


def card(p):
    cat = SITE["categories"].get(p["category"], p["category"])
    return (f'<li class="card"><a href="{p["url"]}"><h2>{esc(p["title"])}</h2></a>'
            f'<p>{esc(p["description"])}</p><small>{p["date"]} · {esc(cat)}</small></li>')


def related(p, posts, n=4):
    """같은 분류·겹치는 태그 순으로 관련 글(내부 링크)"""
    def score(q):
        return (q["category"] == p["category"]) * 2 + len(set(q["tags"]) & set(p["tags"]))
    cands = sorted((q for q in posts if q is not p), key=lambda q: (score(q), q["date"]), reverse=True)
    return [q for q in cands if score(q) > 0][:n] or cands[:n]


def write(path, content):
    f = OUT / path.lstrip("/")
    if path.endswith("/"):
        f = f / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8")


def build():
    posts = sorted((parse(f) for f in POSTS.glob("*.md")), key=lambda p: p["date"], reverse=True)
    posts = [p for p in posts if p.get("draft", "false").lower() != "true"]
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)

    for p in posts:
        cat = SITE["categories"].get(p["category"], p["category"])
        rel = "".join(f'<li><a href="{q["url"]}">{esc(q["title"])}</a></li>' for q in related(p, posts))
        tags = " ".join(f'<span class="tag">#{esc(t)}</span>' for t in p["tags"])
        toc = f'<details class="toc" open><summary>목차</summary>{p["toc"]}</details>' if p["toc"] else ""
        body = (f'<article><p class="crumb"><a href="/">홈</a> › <a href="/category/{p["category"]}/">{esc(cat)}</a></p>'
                f'<h1>{esc(p["title"])}</h1><p class="meta">작성 {p["date"]}'
                + (f' · 수정 {p["updated"]}' if p["updated"] != p["date"] else "")
                + f'</p>{toc}<div class="body">{p["html"]}</div><p>{tags}</p></article>'
                + (f'<aside class="related"><h2>함께 보면 좋은 글</h2><ul>{rel}</ul></aside>' if rel else ""))
        ld = [{
            "@context": "https://schema.org", "@type": "BlogPosting",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "dateModified": p["updated"],
            "author": {"@type": "Person", "name": SITE["author"]},
            "mainEntityOfPage": BASE + p["url"], "inLanguage": "ko-KR", "keywords": ", ".join(p["tags"]),
        }, {
            "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "홈", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": cat, "item": f"{BASE}/category/{p['category']}/"},
                {"@type": "ListItem", "position": 3, "name": p["title"], "item": BASE + p["url"]},
            ]}]
        write(p["url"], page(f'{p["title"]} | {SITE["title"]}', p["description"], p["url"], body, ld, "article"))

    lis = "".join(card(p) for p in posts)
    write("/", page(SITE["title"], SITE["description"], "/",
                    f'<h1 class="hero">{esc(SITE["title"])}</h1><p class="lead">{esc(SITE["description"])}</p><ul class="cards">{lis}</ul>',
                    [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE["title"], "url": BASE + "/", "inLanguage": "ko-KR"}]))

    for k, v in SITE["categories"].items():
        items = [p for p in posts if p["category"] == k]
        lis = "".join(card(p) for p in items) or "<li>아직 글이 없습니다.</li>"
        write(f"/category/{k}/", page(f"{v} | {SITE['title']}", f"{v} 관련 글 모음", f"/category/{k}/", f"<h1>{esc(v)}</h1><ul class='cards'>{lis}</ul>"))

    for name in ("about", "privacy"):
        src = ROOT / "content" / f"{name}.md"
        if src.exists():
            t, b = src.read_text(encoding="utf-8").split("\n", 1)
            write(f"/{name}/", page(f"{t.lstrip('# ')} | {SITE['title']}", t.lstrip("# "), f"/{name}/", markdown.markdown(f"{t}\n{b}")))

    write("/404.html", page("페이지를 찾을 수 없습니다", "404", "/404.html", '<h1>페이지를 찾을 수 없습니다</h1><p><a href="/">홈으로</a></p>'))

    urls = [("/", posts[0]["updated"] if posts else "")] + [(p["url"], p["updated"]) for p in posts] \
        + [(f"/category/{k}/", "") for k in SITE["categories"] if any(p["category"] == k for p in posts)]
    sm = "".join(f"<url><loc>{BASE}{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")

    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{BASE}{p['url']}</link><guid>{BASE}{p['url']}</guid>"
        f"<pubDate>{datetime.strptime(p['date'], '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0900')}</pubDate>"
        f"<description>{esc(p['description'])}</description></item>" for p in posts[:20])
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{esc(SITE["title"])}</title>'
        f'<link>{BASE}/</link><description>{esc(SITE["description"])}</description><language>ko</language>{items}</channel></rss>',
        encoding="utf-8")
    print(f"빌드 완료: 글 {len(posts)}편 -> {OUT}")


if __name__ == "__main__":
    build()
