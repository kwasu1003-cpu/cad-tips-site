"""매일 점검: 글 머리말 검사, 내부/외부 깨진 링크, (배포 후) 실제 사이트 응답 확인

사용법: python check.py [--live]   결과는 reports/YYYY-MM-DD.md 에 저장
"""
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

import build

ROOT = Path(__file__).parent
OUT = ROOT / "public"
UA = {"User-Agent": "Mozilla/5.0 (site-check)"}


def fetch_status(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405):
                continue
            return e.code
        except Exception as e:
            return f"오류 {type(e).__name__}"


def main():
    live = "--live" in sys.argv
    problems, notes = [], []

    # 1) 머리말 품질
    slugs = set()
    for f in sorted(build.POSTS.glob("*.md")):
        try:
            p = build.parse(f)
        except ValueError as e:
            problems.append(str(e))
            continue
        if not 15 <= len(p["title"]) <= 60:
            problems.append(f"{f.name}: 제목 길이 {len(p['title'])}자 (15~60자 권장)")
        if not 60 <= len(p["description"]) <= 160:
            problems.append(f"{f.name}: 설명 길이 {len(p['description'])}자 (60~160자 권장)")
        if p["slug"] in slugs:
            problems.append(f"{f.name}: 주소(slug) 중복")
        slugs.add(p["slug"])
        if len(re.sub(r"<[^>]+>", "", p["html"])) < 1500:
            notes.append(f"{f.name}: 본문이 짧음 (1500자 미만)")

    # 2) 빌드 후 링크 검사
    build.build()
    ext = set()
    for page in OUT.rglob("*.html"):
        for href in re.findall(r'href="([^"#]+)', page.read_text(encoding="utf-8")):
            if href.startswith("http"):
                if not href.startswith(build.BASE):
                    ext.add(href)
            elif href.startswith("/"):
                t = OUT / href.lstrip("/")
                if not (t.is_file() or (t / "index.html").is_file()):
                    problems.append(f"깨진 내부 링크: {page.relative_to(OUT)} -> {href}")
    for url in sorted(ext):
        s = fetch_status(url)
        if s != 200:
            problems.append(f"외부 링크 응답 {s}: {url}")

    # 3) 실제 사이트(배포 후)
    if live:
        sm = (OUT / "sitemap.xml").read_text(encoding="utf-8")
        for url in re.findall(r"<loc>(.*?)</loc>", sm):
            s = fetch_status(url)
            if s != 200:
                problems.append(f"사이트 응답 {s}: {url}")

    report = [f"# 점검 결과 {date.today()}", "", f"문제 {len(problems)}건, 참고 {len(notes)}건", ""]
    report += ["## 문제"] + [f"- {x}" for x in problems] + ["", "## 참고"] + [f"- {x}" for x in notes]
    out = ROOT / "reports" / f"{date.today()}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
