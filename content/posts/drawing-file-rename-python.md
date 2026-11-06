---
title: 도면 파일 이름 규칙 정하고 파이썬으로 일괄 변경하기
description: 브라켓 최종(수정).dwg 같은 제각각인 도면 파일 이름을 규칙 하나로 정리하는 방법. 이름 규칙 정하는 법, 엑셀로 새 이름 목록 쓰기, 파이썬으로 미리 점검하고 한 번에 바꾸기, 잘못 바꿨을 때 되돌리기까지 예제로 정리했습니다.
date: 2026-11-06
category: python
tags: 파이썬, 도면관리, 파일이름, 일괄변경, CSV, 자동화
slug: drawing-file-rename-python
---


설계 폴더를 열어 보면 `브라켓 최종.dwg`, `브라켓 최종(수정).dwg`, `커버_rev1.dwg`처럼 사람마다 다른 방식으로 붙인 이름이 섞여 있기 마련입니다. 어느 것이 마지막 판인지 열어 봐야 알 수 있고 검색도 잘 안 됩니다. 이 글에서는 **도면 파일 이름 규칙을 하나 정하고 파이썬 스크립트로 폴더 안의 파일 이름을 한 번에 바꾸는 방법**을 다룹니다. 바꾸기 전에 규칙 위반과 이름 겹침을 먼저 점검하고 잘못 바꿨으면 되돌릴 수 있게 만듭니다. [지난 글](/posts/sheetmetal-flat-length-python/)처럼 외부 라이브러리 없이 파이썬 기본 기능만 씁니다.

## 이름 규칙부터 정하기

규칙은 길게 만들수록 지키기 어렵습니다. 실무에서는 세 가지만 들어가면 충분합니다.

| 칸 | 예 | 뜻 |
|---|---|---|
| 프로젝트코드-도번 | K2611-101 | 어느 일의 몇 번 도면인지 |
| 품명 | 브라켓 | 사람이 읽고 알아볼 이름 |
| 리비전 | R0, R1 | 몇 번째 고친 판인지 |

칸 사이는 밑줄(`_`)로 구분해서 `K2611-101_브라켓_R0.dwg`처럼 씁니다. 이 글의 예에서는 프로젝트코드를 "영문 대문자 1자 + 숫자 4자리"로, 도번을 숫자 3자리로 정했습니다. 회사에서 이미 쓰는 번호 체계가 있으면 그것에 맞추면 됩니다.

규칙을 정할 때 지키면 좋은 것은 이렇습니다.

1. **"최종", "수정", "진짜최종" 같은 말은 쓰지 않는다.** 판 구분은 리비전 번호로만 합니다.
2. **번호는 자릿수를 고정한다.** `1`, `2`, `10` 대신 `001`, `002`, `010`으로 쓰면 탐색기에서 이름순 정렬이 번호순과 같아집니다.
3. **품명에는 밑줄을 넣지 않는다.** 밑줄이 칸 구분 기호이기 때문입니다. 띄어쓰기가 필요하면 붙여 쓰거나 하이픈을 씁니다.
4. **윈도우 파일 이름에 쓸 수 없는 글자를 피한다.** `\ / : * ? " < > |` 아홉 글자는 파일 이름에 들어갈 수 없습니다.

규칙을 정규식으로 옮기면 아래 한 줄이 됩니다. 스크립트는 이 식으로 새 이름을 검사합니다.

```
^[A-Z][0-9]{4}-[0-9]{3}_[^_]+_R[0-9]+$
```

앞에서부터 "대문자 1자, 숫자 4자리, 하이픈, 숫자 3자리, 밑줄, 밑줄이 아닌 글자 1자 이상, 밑줄, R과 숫자"라는 뜻입니다.

## 작업 순서 한눈에 보기

이름을 자동으로 추측해서 바꾸면 사고가 납니다. `브라켓 최종.dwg`가 몇 번 도면인지는 사람만 압니다. 그래서 새 이름은 사람이 엑셀에서 적고 파이썬은 점검과 실행만 맡기는 방식으로 나눴습니다.

| 단계 | 명령 | 하는 일 |
|---|---|---|
| 1 | `list` | 폴더의 도면 파일 목록을 `rename.csv`로 만든다 |
| 2 | (엑셀) | `새이름` 칸을 채운다 |
| 3 | `check` | 규칙·겹침을 점검만 하고 바꾸지 않는다 |
| 4 | `run` | 점검을 통과하면 이름을 바꾸고 기록을 남긴다 |
| 5 | `undo` | 기록을 보고 원래 이름으로 되돌린다 |

## 스크립트 (rename_drawings.py)

아래 코드를 `rename_drawings.py`로 저장합니다. 대상은 `.dwg`, `.dxf`, `.pdf` 파일이고 확장자는 원래 것을 그대로 붙입니다.

```python
import csv
import os
import re
import sys

# 이름 규칙: 프로젝트코드-도번_품명_R리비전  (예: K2611-101_브라켓_R0)
RULE = re.compile(r"^[A-Z][0-9]{4}-[0-9]{3}_[^_]+_R[0-9]+$")
BAD_CHARS = set('\\/:*?"<>|')
EXTS = {".dwg", ".dxf", ".pdf"}
LIST_FILE = "rename.csv"
LOG_FILE = "rename_log.csv"


def read_csv(path):
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            pass
    raise SystemExit(f"{path}: 글자 인코딩을 읽을 수 없습니다")


def make_list(folder):
    names = sorted(n for n in os.listdir(folder)
                   if os.path.splitext(n)[1].lower() in EXTS)
    with open(os.path.join(folder, LIST_FILE), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["현재이름", "새이름"])
        for n in names:
            w.writerow([n, ""])
    print(f"{len(names)}개 파일을 {LIST_FILE}에 적었습니다")


def make_plan(folder):
    rows = read_csv(os.path.join(folder, LIST_FILE))[1:]
    plan, errors, seen = [], [], {}
    for i, row in enumerate(rows, start=2):
        if len(row) < 2 or not row[1].strip():
            continue
        old, stem = row[0].strip(), row[1].strip()
        new = stem + os.path.splitext(old)[1]
        if not os.path.exists(os.path.join(folder, old)):
            errors.append(f"{i}행 {old}: 파일이 없습니다")
        if BAD_CHARS & set(stem):
            errors.append(f"{i}행 {stem}: 파일 이름에 쓸 수 없는 글자")
        elif not RULE.match(stem):
            errors.append(f"{i}행 {stem}: 이름 규칙과 다릅니다")
        key = new.lower()
        if key in seen:
            errors.append(f"{i}행 {new}: {seen[key]}행과 새 이름이 겹칩니다")
        seen[key] = i
        if old.lower() != key and os.path.exists(os.path.join(folder, new)):
            errors.append(f"{i}행 {new}: 같은 이름 파일이 이미 있습니다")
        plan.append((old, new))
    return plan, errors


def check(folder, run=False):
    plan, errors = make_plan(folder)
    for old, new in plan:
        print(f"{old}  ->  {new}")
    if errors:
        print(f"\n오류 {len(errors)}건, 이름을 바꾸지 않았습니다")
        for e in errors:
            print(" -", e)
        return
    if not run:
        print(f"\n문제 없음: {len(plan)}개 (run으로 실행)")
        return
    with open(os.path.join(folder, LOG_FILE), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["원래이름", "바꾼이름"])
        for old, new in plan:
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
            w.writerow([old, new])
    print(f"\n{len(plan)}개 이름을 바꿨습니다. 기록: {LOG_FILE}")


def undo(folder):
    rows = read_csv(os.path.join(folder, LOG_FILE))[1:]
    for old, new in reversed(rows):
        os.rename(os.path.join(folder, new), os.path.join(folder, old))
    os.remove(os.path.join(folder, LOG_FILE))
    print(f"{len(rows)}개 이름을 되돌렸습니다")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("list", "check", "run", "undo"):
        raise SystemExit("사용법: python rename_drawings.py list|check|run|undo 폴더")
    cmd, folder = sys.argv[1], sys.argv[2]
    if cmd == "list":
        make_list(folder)
    elif cmd == "undo":
        undo(folder)
    else:
        check(folder, run=(cmd == "run"))
```

몇 군데만 짚어 보겠습니다.

- **겹침 검사는 소문자로 비교합니다.** 윈도우는 대소문자가 다른 이름을 같은 파일로 보기 때문입니다. `R1.dwg`와 `r1.dwg`를 서로 다른 이름으로 통과시키면 실행 중에 오류가 납니다.
- **오류가 하나라도 있으면 아무것도 바꾸지 않습니다.** 절반만 바뀐 폴더가 제일 정리하기 어렵습니다.
- **CSV는 UTF-8(BOM 포함)로 쓰고 읽을 때는 UTF-8과 CP949를 차례로 시도합니다.** 엑셀에서 "CSV UTF-8"로 저장하든 그냥 "CSV"로 저장하든 한글 파일 이름이 깨지지 않게 하려는 것입니다.

## 예제로 따라 하기

`도면` 폴더에 아래 여섯 파일이 있다고 하겠습니다.

```
브라켓 최종.dwg
브라켓 최종(수정).dwg
커버_rev1.dwg
측판.dxf
측판.pdf
메모.txt
```

### 1단계: 목록 만들기

```
python rename_drawings.py list 도면
```

```
5개 파일을 rename.csv에 적었습니다
```

`메모.txt`는 대상 확장자가 아니어서 빠지고 다섯 개만 목록에 들어갑니다. 만들어진 `도면\rename.csv`는 이렇습니다.

```
현재이름,새이름
브라켓 최종(수정).dwg,
브라켓 최종.dwg,
측판.dxf,
측판.pdf,
커버_rev1.dwg,
```

### 2단계: 엑셀에서 새 이름 적기

`rename.csv`를 엑셀로 열고 B열에 새 이름을 확장자 없이 적습니다. 일부러 실수를 두 군데 넣어 보겠습니다. 브라켓 두 장에 같은 리비전을 적었고 커버의 프로젝트코드는 소문자로 썼습니다.

```
현재이름,새이름
브라켓 최종(수정).dwg,K2611-101_브라켓_R1
브라켓 최종.dwg,K2611-101_브라켓_R1
측판.dxf,K2611-103_측판_R0
측판.pdf,K2611-103_측판_R0
커버_rev1.dwg,k2611-102_커버_R1
```

측판은 DXF와 PDF가 같은 새 이름을 받지만 확장자가 달라서 겹침이 아닙니다. 바꿀 필요가 없는 파일은 B열을 비워 두면 건너뜁니다.

### 3단계: 점검

```
python rename_drawings.py check 도면
```

```
브라켓 최종(수정).dwg  ->  K2611-101_브라켓_R1.dwg
브라켓 최종.dwg  ->  K2611-101_브라켓_R1.dwg
측판.dxf  ->  K2611-103_측판_R0.dxf
측판.pdf  ->  K2611-103_측판_R0.pdf
커버_rev1.dwg  ->  k2611-102_커버_R1.dwg

오류 2건, 이름을 바꾸지 않았습니다
 - 3행 K2611-101_브라켓_R1.dwg: 2행과 새 이름이 겹칩니다
 - 6행 k2611-102_커버_R1: 이름 규칙과 다릅니다
```

행 번호는 엑셀의 행 번호와 같습니다. 1행이 제목 줄이므로 첫 파일이 2행입니다. 넣어 둔 실수 두 개가 정확히 잡혔습니다. `브라켓 최종.dwg`를 `R0`으로, 커버 코드를 `K2611`로 고치고 다시 점검하면 이렇게 나옵니다.

```
브라켓 최종(수정).dwg  ->  K2611-101_브라켓_R1.dwg
브라켓 최종.dwg  ->  K2611-101_브라켓_R0.dwg
측판.dxf  ->  K2611-103_측판_R0.dxf
측판.pdf  ->  K2611-103_측판_R0.pdf
커버_rev1.dwg  ->  K2611-102_커버_R1.dwg

문제 없음: 5개 (run으로 실행)
```

### 4단계: 실행

```
python rename_drawings.py run 도면
```

마지막 줄에 `5개 이름을 바꿨습니다. 기록: rename_log.csv`가 나오고 폴더는 이렇게 바뀝니다.

```
K2611-101_브라켓_R0.dwg
K2611-101_브라켓_R1.dwg
K2611-102_커버_R1.dwg
K2611-103_측판_R0.dxf
K2611-103_측판_R0.pdf
메모.txt
```

이름순으로 정렬했을 뿐인데 도번 순서대로 서고 같은 도번 안에서는 리비전 순서로 섭니다. 번호 자릿수를 고정한 덕분입니다.

### 5단계: 되돌리기

```
python rename_drawings.py undo 도면
```

```
5개 이름을 되돌렸습니다
```

`rename_log.csv`를 거꾸로 읽어 원래 이름으로 돌려놓고 기록 파일은 지웁니다. 되돌리기는 마지막 `run` 한 번만 기억하므로 `run`을 두 번 하기 전에 결과를 확인해 두는 게 좋습니다.

## 쓸 때 주의할 점

- CAD에서 열려 있는 파일은 이름을 바꿀 수 없습니다. 실행 전에 CAD를 닫거나 해당 도면을 닫아 둡니다.
- 외부 참조(XREF)가 걸린 도면은 조심합니다. 참조하는 쪽 도면은 예전 파일 이름을 경로로 들고 있어서 이름을 바꾸면 참조가 끊깁니다. 이런 폴더는 이름을 바꾼 뒤 CAD에서 참조 경로를 다시 잡아야 합니다.
- 처음에는 복사본 폴더로 연습합니다. 스크립트가 지우는 파일은 `rename_log.csv`뿐이지만 이름 변경 자체에 익숙해질 때까지는 복사본으로 해 보는 편이 마음이 편합니다.
- 규칙을 바꾸고 싶으면 `RULE` 한 줄만 고치면 됩니다. 예를 들어 도번이 4자리라면 `[0-9]{3}`을 `[0-9]{4}`로 바꿉니다.

## 정리

- 도면 이름은 "프로젝트코드-도번_품명_R리비전"처럼 세 칸으로 정하고 "최종·수정" 같은 말은 빼면 정렬과 검색이 쉬워집니다.
- 새 이름은 사람이 엑셀에서 적고 파이썬은 `check`로 규칙·겹침을 점검한 뒤 `run`으로 한 번에 바꿉니다.
- 오류가 있으면 아무것도 바꾸지 않으며 바꾼 기록이 남아 있어 `undo`로 되돌릴 수 있습니다.

다음 글에서는 엑셀로 부품 중량을 자동으로 계산하는 표를 만들어 보겠습니다.
