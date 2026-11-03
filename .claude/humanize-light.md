# humanize 요약 절차 (이 사이트 전용, 매일 작업은 이것만 읽는다)

원본: `.claude/skills/humanize-korean/` (im-not-ai v2.3.2). 아래 4번이 exit 2이거나 route가 heavy일 때만 원본 SKILL.md를 연다.

1. 초안 본문만 `_workspace/<날짜-NNN-TAG>/01_input.txt`에 저장(머리말 `---` 블록은 따로 보관). cwd = `F:\Projects\cad-tips-site`, `$env:PYTHONIOENCODING='utf-8'`, `$py='F:\Tools\Python313\python.exe'`, `$s='.claude\skills\humanize-korean\scripts'`.
2. `& $py "$s\prepare_monolith_input.py" --run-dir <run> --genre blog` → 출력의 `route_hint`만 본다.
3. 직접 윤문해 `<run>\final.md`에 쓴다(강도 보수, 고친 곳이 거의 없으면 그대로 둠). 고치는 것:
   - 연결어미(-고/-며/-지만/-면서/-아서/-어서) 바로 뒤 쉼표 삭제. 새로 만들지 않는다.
   - 문장마다 붙은 볼드, 결산어("결론적으로/요약하면/따라서" 3회+), "~할 때입니다", "중요한 것은 ~이다", "단순한 X를 넘어 Y", "~에 있어서", "가지고 있다", "~되어진다".
   - 같은 종결어미 4문장 연속이면 하나만 바꾼다.
   - 건드리지 않는 것: 수치·단위·공식·표·코드 블록·링크·고유명사, "~해야 한다/~일 수 있다" 같은 서법, 존댓말 등급.
4. `& $py "$s\restore_modality.py" --before <run>\01_input.txt --after <run>\final.md --out <run>\final.md`, 같은 인자로 `strip_injected_commas.py`, 이어서 `verify_gates.py --before .. --after .. --genre blog`. 출력은 `gate:` 줄과 FAIL 줄만 본다.
   - exit 0 채택 / exit 1 채택(heading_lost·footnote_anchor는 수식·번호 목록 오탐이 잦음 → 실제 제목·수치 변화만 직접 확인) / exit 2 원 초안 유지.
5. 숫자 목록(`\d+(?:\.\d+)?`)이 원문과 다르면 윤문본을 버린다. 채택 시 머리말 + 윤문 본문으로 초안을 덮어쓴다.
