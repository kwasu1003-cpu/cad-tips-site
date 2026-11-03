# CLAUDE.md — CAD 실무 자동화 노트 (부업 사이트)

답과 안내는 모두 한글로 쓴다.

## 1. 작업 원칙

우선순위: 정확성 > 검증 > 최소 변경 > 명확성 > 유지보수성

- 파일·API·스키마가 있다고 가정하지 말고 먼저 읽어서 확인한다.
- 수정 전에 관련 파일을 읽고, 수정 후에는 테스트·실행으로 검증한다.
- 요청된 작업에만 변경을 국한하고, 관련 없는 리팩토링은 하지 않는다.
- 가장 단순한 해결책을 선호하고, 불필요한 의존성·추상화를 추가하지 않는다.
- 막히면 멈추고 무엇이 막혔는지, 무엇이 검증됐는지 보고한다. 검증 없이 성공했다고 하지 않는다.

## 2. 배포 규칙 (중요)

- 배포는 `git push origin main`으로만 한다.
- Netlify CLI, Vercel CLI, Cloudflare wrangler 등으로 직접 배포하지 않는다.
- 배포·서버 구성은 기존 방식 그대로 유지하고 임의로 바꾸지 않는다.
- 매일 8시 예약 작업의 글 1편 발행은 승인됨(2026-11-01). 그 밖의 게시·계정 로그인·결제는 매번 사용자 확인을 받는다.

## 3. 환경

- Windows 10 Pro, 셸은 Windows PowerShell 5.1 (`&&`, `||` 사용 불가 → `;` 와 `if ($?) { }` 사용)
- C 드라이브 여유가 적으므로 설치·큰 파일은 F 드라이브(`F:\Tools`, `F:\Projects`)에 둔다.
- Python 3.13: `F:\Tools\Python313\python.exe` (사용 패키지: `markdown`)
- Node.js 24: `C:\Program Files\nodejs`
- git 2.56 (Portable): `F:\Tools\Git\cmd\git.exe` (사용자 PATH에 등록됨)
- 유료 API는 쓰지 않는다.

## 4. 금지

- `F:\Projects\AI-CAD`(판금 전개·도면 검색 프로그램)는 다른 작업이 진행 중이므로 건드리지 않는다.

## 5. 프로젝트별 정보

- 위치: `F:\Projects\cad-tips-site`
- 사이트 주소: https://cad-tips-site.kwasu1003.workers.dev (`site.json`의 `base_url`)
- 주제: CAD 실무·판금 설계·엑셀/파이썬/LISP 업무 자동화 팁
- 수익: Google AdSense (비용 0원 운영, 애드센스 신청 시 개인 도메인 필요)
- 발행: 하루 1편, 매일 8시 예약 작업이 검증 후 자동 발행 (2026-11-01 사용자 승인). 그 외 수동 게시·로그인·결제는 매번 사용자 확인

| 파일·폴더 | 역할 |
|---|---|
| `site.json` | 사이트 이름·주소(`base_url`)·분류·애드센스 ID |
| `content/drafts/` | 검토 대기 초안 |
| `content/posts/` | 발행할 글 (머리말: title, description, date, category, tags, slug) |
| `content/주제목록.md` | 앞으로 쓸 주제, 다 쓴 주제는 `[x]` |
| `build.py` | 사이트 생성 → `public/` |
| `check.py` | 점검(머리말·깨진 링크, `--live`로 실제 사이트) → `reports/날짜.md` |
| `운영절차.md` | 매일 발행·점검 절차 |
| `deploy.ps1` | 점검 → 커밋 → `git push origin main`. Cloudflare(Workers, GitHub `kwasu1003-cpu/cad-tips-site` 연결)가 push를 받아 `python build.py`로 빌드, 출력 폴더 `public`. 실행: `powershell -ExecutionPolicy Bypass -File deploy.ps1 "메시지"` |
| `.claude/skills/humanize-korean/` | 한국어 AI 티 윤문 스킬 (im-not-ai v2.3.2, MIT, 복사 설치. 원본 저장소 `F:\Tools\im-not-ai`). 런타임 에이전트는 `.claude/agents/humanize-*.md`. 작업 폴더 `_workspace/`는 git 제외 |
| `.claude/humanize-light.md` | 이 사이트용 윤문 요약 절차(~2KB). 매일 작업은 이것만 읽는다 |
| `requirements.txt` | Cloudflare 빌드용 파이썬 패키지 |

검증 명령:

```powershell
& F:\Tools\Python313\python.exe F:\Projects\cad-tips-site\check.py
```

글 작성 기준: 제목 15~60자, 설명 60~160자, 본문 1,500자 이상, 예제 수치는 검산 포함.

## 6. 출력·파일 읽기 규칙 (입력 토큰 절약)

- 명령 출력은 결과 판단에 필요한 줄만 본다: 설치·다운로드는 마지막 3줄(`| Select-Object -Last 3`), `check.py`는 `문제 N건` 줄과 문제 목록, git은 `--short`·`--oneline`, 게이트는 `gate:`·`FAIL` 줄.
- 로그는 통째로 읽지 않는다: 오류 줄(`Select-String 'error|fail|오류'`)·건수·마지막 상태만 뽑는다.
- 긴 파일은 필요한 부분만: 위치를 grep으로 찾고 offset/limit로 읽는다. 숫자 검증은 수치 목록만 뽑아 대조, 보안 검토는 import·subprocess·urllib 등만 grep.
- 끝난 시행착오는 다시 읽지 않는다. 원인과 해결은 아래 표에 한 줄로 남기고, 다음엔 표부터 본다.

## 7. 자주 나는 문제 (원인 → 해결, 새로 해결하면 한 줄 추가)

| 증상 | 원인 → 해결 |
|---|---|
| push 시 로그인 창 없이 `Repository not found` | 앱 환경이 `GCM_INTERACTIVE=never`라 로그인 불가 → 저장소 설정을 `credential.helper ""` + `manager`로 해 두었음(저장된 로그인 사용). 새 로그인이 필요하면 별도 cmd 창(`Start-Process cmd`)에서 push |
| `.ps1` 실행 시 "스크립트를 실행할 수 없으므로" | PowerShell 실행 정책 → `powershell -ExecutionPolicy Bypass -File <파일>` 또는 `.cmd`(한글 주석 금지) |
| `git add` 때 "LF will be replaced by CRLF" 경고 다발 | autocrlf 변환 경고 → 저장소에 `core.safecrlf false` 설정함 |
| 예약 작업이 커밋만 하고 사이트에 안 올라감 | 위 push 로그인 문제 → `git status -sb`의 `ahead N` 확인 후 push |
| humanize `verify_gates` P3 FAIL(heading_lost·footnote_anchor) | 번호 목록·수식 괄호 오탐 → 실제 제목·수치 변화만 직접 대조 |
| PowerShell에서 한글 출력 깨짐 | `$env:PYTHONIOENCODING='utf-8'` |
