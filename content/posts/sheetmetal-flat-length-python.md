---
title: 파이썬으로 판금 전개 길이 계산, 여러 부품을 CSV로 한 번에
description: 판금 부품 목록을 CSV로 정리하고 파이썬 스크립트 하나로 전개 길이를 한꺼번에 계산하는 방법. BD 공식을 함수로 옮기는 법, 입력 오류 잡기, 엑셀에서 결과 여는 법까지 예제로 정리했습니다.
date: 2026-11-02
category: python
tags: 파이썬, 판금, 전개, 굽힘공제, CSV, 자동화
slug: sheetmetal-flat-length-python
---

[지난 글](/posts/sheetmetal-flat-length-excel/)에서 판금 전개 길이를 엑셀로 계산하는 방법을 정리했습니다. 부품이 몇 개일 때는 엑셀이 편하지만 한 프로젝트에 판금 부품이 수십 개씩 나오면 시트를 복사하고 굽힘 줄을 늘리는 일 자체가 번거로워집니다. 이 글에서는 **부품 목록을 CSV 파일 하나에 적어 두고 파이썬 스크립트로 전개 길이를 한 번에 뽑는 방법**을 다룹니다. 외부 라이브러리 없이 파이썬 기본 기능만 씁니다.

## 준비물

- 파이썬 3.8 이상 (python.org에서 설치, 설치할 때 "Add python.exe to PATH" 체크)
- 메모장이나 엑셀 (CSV 작성용)

`pandas` 같은 패키지는 필요 없습니다. 파이썬에 기본으로 들어 있는 `csv`, `math` 모듈만 씁니다.

## 계산 원리 다시 보기

공식은 지난 글과 같습니다. 도면의 바깥 치수를 모두 더한 다음 굽힘마다 굽힘 공제(BD)를 뺍니다.

```
BA   = π/180 × A × (R + K × T)
OSSB = tan(A/2) × (R + T)
BD   = 2 × OSSB − BA
전개 길이 = 바깥 치수의 합 − (굽힘마다 BD의 합)
```

T는 두께, R은 안쪽 굽힘 반경, K는 K-factor, A는 굽힌 각도입니다. 직각으로 굽히면 A = 90입니다.

## 입력 파일 만들기 (parts.csv)

부품 하나를 한 줄에 씁니다. 바깥 치수와 굽힘 각도는 칸 하나에 띄어쓰기로 구분해 넣습니다. 치수가 3개(ㄷ자)면 굽힘은 2개이므로 각도도 2개를 씁니다.

```
부품명,두께,안쪽R,K,바깥치수,굽힘각도
BR-01,2,2,0.4,50 30,90
CH-01,2,2,0.4,30 50 30,90 90
HAT-01,3,3,0.42,20 40 60 40 20,90 90 90 90
CV-02,1.2,1,0.35,40 60,60
ERR-01,2,2,0.4,30 50 30,90
```

| 부품 | 모양 | 조건 |
|---|---|---|
| BR-01 | ㄱ자 브래킷 | T2, R2, K0.4, 90° 1회 |
| CH-01 | ㄷ자 채널 | T2, R2, K0.4, 90° 2회 |
| HAT-01 | 모자형 | T3, R3, K0.42, 90° 4회 |
| CV-02 | 60° 꺾인 커버 | T1.2, R1, K0.35, 60° 1회 |
| ERR-01 | 일부러 틀린 줄 | 치수 3개인데 각도 1개 |

엑셀에서 작성했다면 "다른 이름으로 저장 → CSV UTF-8(쉼표로 분리)"로 저장해야 한글이 깨지지 않습니다. 마지막 ERR-01은 스크립트가 입력 실수를 잘 잡는지 보려고 넣은 줄입니다.

## 파이썬 스크립트 (flat_length.py)

```python
import csv
import math
import sys


def bend_deduction(t, r, k, angle):
    """굽힘 1회의 BD(mm). angle은 굽힌 각도(도)."""
    ba = math.radians(angle) * (r + k * t)
    ossb = math.tan(math.radians(angle) / 2) * (r + t)
    return 2 * ossb - ba


def flat_length(t, r, k, dims, angles):
    """바깥 치수 목록과 굽힘 각도 목록으로 전개 길이를 구한다."""
    if len(angles) != len(dims) - 1:
        raise ValueError(f"치수 {len(dims)}개면 각도는 {len(dims) - 1}개여야 합니다 (지금 {len(angles)}개)")
    for a in angles:
        if not 0 < a < 180:
            raise ValueError(f"굽힘 각도 {a}°는 계산할 수 없습니다 (0~180° 사이만)")
    return sum(dims) - sum(bend_deduction(t, r, k, a) for a in angles)


def main(src, dst):
    rows_out = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = row["부품명"]
            try:
                t = float(row["두께"])
                r = float(row["안쪽R"])
                k = float(row["K"])
                dims = [float(x) for x in row["바깥치수"].split()]
                angles = [float(x) for x in row["굽힘각도"].split()]
                length = flat_length(t, r, k, dims, angles)
                rows_out.append({**row, "전개길이": f"{length:.2f}", "비고": ""})
            except (ValueError, KeyError) as e:
                rows_out.append({**row, "전개길이": "", "비고": f"오류: {e}"})
                print(f"[오류] {name}: {e}")

    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"{len(rows_out)}개 부품 계산 완료 → {dst}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "parts.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "result.csv"
    main(src, dst)
```

코드가 하는 일은 세 단계입니다.

1. `bend_deduction`: 엑셀 표의 BA, OSSB, BD 열을 함수 하나로 옮긴 것입니다. `math.radians`가 엑셀의 `RADIANS`와 같은 역할을 합니다.
2. `flat_length`: 치수 개수와 각도 개수가 맞는지, 각도가 0~180° 사이인지 먼저 확인한 뒤 전개 길이를 계산합니다.
3. `main`: CSV를 한 줄씩 읽어 계산하고 원래 칸 뒤에 `전개길이`와 `비고`를 붙여 새 CSV로 저장합니다. 한 줄에서 오류가 나도 멈추지 않고 비고에 이유를 적은 뒤 다음 부품으로 넘어갑니다.

파일을 읽고 쓸 때 `utf-8-sig`를 쓴 이유가 있습니다. 엑셀이 저장한 UTF-8 CSV 맨 앞에는 BOM이라는 표시가 붙는데, 그냥 `utf-8`로 읽으면 첫 칸 이름이 `\ufeff부품명`이 되어 `row["부품명"]`에서 오류가 납니다. 결과 파일도 `utf-8-sig`로 써야 엑셀에서 더블클릭으로 열었을 때 한글이 깨지지 않습니다.

## 실행하기

`parts.csv`와 `flat_length.py`를 같은 폴더에 두고 그 폴더에서 PowerShell이나 명령 프롬프트를 열어 실행합니다.

```
python flat_length.py parts.csv result.csv
```

화면에는 이렇게 나옵니다.

```
[오류] ERR-01: 치수 3개면 각도는 2개여야 합니다 (지금 1개)
5개 부품 계산 완료 → result.csv
```

5개 줄을 모두 처리했고 그중 1개에 오류가 있다는 뜻입니다. `result.csv`를 엑셀로 열면 다음과 같습니다.

| 부품명 | 바깥치수 | 굽힘각도 | 전개길이 | 비고 |
|---|---|---|---|---|
| BR-01 | 50 30 | 90 | 76.40 | |
| CH-01 | 30 50 30 | 90 90 | 102.80 | |
| HAT-01 | 20 40 60 40 20 | 90 90 90 90 | 158.77 | |
| CV-02 | 40 60 | 60 | 98.95 | |
| ERR-01 | 30 50 30 | 90 | | 오류: 치수 3개면 각도는 2개여야 합니다 (지금 1개) |

## 결과 검산

스크립트 결과를 그대로 믿지 말고 손으로 한 번 맞춰 봅니다.

**BR-01, CH-01** (T2, R2, K0.4, 90°)

- BA = 1.5708 × (2 + 0.4 × 2) = 1.5708 × 2.8 = 4.398
- OSSB = tan(45°) × (2 + 2) = 4.000
- BD = 2 × 4 − 4.398 = 3.602
- BR-01: 50 + 30 − 3.602 = **76.40 mm**
- CH-01: 110 − 3.602 × 2 = **102.80 mm**

지난 글의 엑셀 예제와 같은 값이 나왔습니다.

**HAT-01** (T3, R3, K0.42, 90° 4회)

- BA = 1.5708 × (3 + 0.42 × 3) = 1.5708 × 4.26 = 6.692
- OSSB = tan(45°) × (3 + 3) = 6.000
- BD = 2 × 6 − 6.692 = 5.308
- 전개 길이 = 180 − 5.308 × 4 = 180 − 21.234 = **158.77 mm**

**CV-02** (T1.2, R1, K0.35, 60° 1회)

- BA = 3.1416/180 × 60 × (1 + 0.35 × 1.2) = 1.0472 × 1.42 = 1.487
- OSSB = tan(30°) × (1 + 1.2) = 0.5774 × 2.2 = 1.270
- BD = 2 × 1.270 − 1.487 = 1.053
- 전개 길이 = 100 − 1.053 = **98.95 mm**

네 부품 모두 스크립트 값과 손계산이 일치합니다.

## 실무에서 쓸 때 주의할 점

- **바깥 치수는 가상 꼭짓점 기준**: 90°가 아닌 굽힘(CV-02)에서도 바깥 치수는 두 바깥면을 연장해 만나는 점까지 잰 길이여야 합니다. 도면이 굽힘 접선이나 안쪽 기준으로 치수를 넣었다면 이 공식을 그대로 쓰면 안 됩니다.
- **헤밍(180° 접기)은 계산 불가**: A = 180이면 tan(90°)가 무한대가 되어 OSSB를 구할 수 없습니다. 그래서 스크립트에서 0~180° 사이만 받도록 막았습니다. 헤밍은 현장 BD 표를 따로 쓰는 편이 정확합니다.
- **K 값은 소재·두께별로 관리**: 위 예제의 K(0.4, 0.42, 0.35)는 계산을 보여 주기 위한 값입니다. 실제로는 지난 글에서 설명한 시험 절곡으로 구한 값을 넣어야 합니다.

> 참고: 예제의 K-factor(0.42, 0.35)는 설명용 가정값입니다. 실제 소재·장비의 시험 절곡 값으로 바꿔 쓰세요.

## 한 단계 더: 현장 BD 표로 바꾸기

현장에서 두께·R별 BD 값을 표로 관리하고 있다면 K-factor 계산 대신 표 값을 쓰는 편이 더 정확합니다. 이럴 때는 `bend_deduction` 함수만 바꾸면 됩니다.

```python
BD_TABLE = {
    # (두께, 안쪽R, 각도): BD
    (2.0, 2.0, 90.0): 3.60,
    (3.0, 3.0, 90.0): 5.31,
}


def bend_deduction(t, r, k, angle):
    key = (t, r, angle)
    if key not in BD_TABLE:
        raise ValueError(f"BD 표에 T{t} R{r} {angle}° 값이 없습니다")
    return BD_TABLE[key]
```

표에 없는 조합은 어림잡아 채우지 않고 오류로 남깁니다. 그 줄은 비고에 이유가 적히니 표에 값을 추가한 뒤 다시 실행하면 됩니다. 위 표의 3.60, 5.31은 이 글 예제의 계산값을 반올림한 것입니다. 실제로는 현장에서 잰 값을 넣어야 합니다.

## 정리

- 부품 목록을 CSV 한 장으로 관리하고 파이썬 스크립트로 전개 길이를 한 번에 계산한다.
- 엑셀 CSV를 다룰 때는 `utf-8-sig`로 읽고 써야 한글과 첫 칸 이름이 깨지지 않는다.
- 치수·각도 개수 확인과 손 검산을 습관으로 들이면 입력 실수를 일찍 잡을 수 있다.

다음 글에서는 판금 최소 플랜지 길이와 V폭을 고르는 기준을 정리해 보겠습니다.
