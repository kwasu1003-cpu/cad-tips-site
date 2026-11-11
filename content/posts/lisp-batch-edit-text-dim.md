---
title: 도면 치수·문자 일괄 수정 LISP 3종 (문자 치환·치수 문자·문자 높이)
description: DWG 도면의 TEXT·MTEXT 문자열을 한 번에 바꾸는 치환 LISP, 치수 문자를 일괄 재지정하는 LISP, 문자 높이를 한꺼번에 바꾸는 LISP를 기본 AutoLISP 함수만으로 만들고 예제로 결과를 확인합니다.
date: 2026-11-11
category: lisp
tags: LISP, CADian, 문자 일괄 수정, 치수 문자, entmod
slug: lisp-batch-edit-text-dim
---

도면 수십 장에 적힌 재질 표기 `SS41`을 `SS400`으로 바꾸거나, 참고 치수 문자 뒤에 `(REF)`를 한꺼번에 붙이거나, 작게 써 놓은 주석 문자의 높이를 한 번에 키워야 할 때가 있습니다. 하나씩 더블클릭해 고치면 빠뜨리기 쉽습니다. 이 글에서는 **문자 치환, 치수 문자 재지정, 문자 높이 변경을 하는 LISP 루틴 세 개**를 만들고 예제로 결과를 확인합니다. 코드는 `vl-` 계열 함수 없이 기본 AutoLISP 함수만 써서 CADian과 AutoCAD에서 같이 쓸 수 있게 했습니다. LISP 파일을 불러오는 방법은 [CADian에서 LISP 파일 불러와 실행하는 법](/posts/cadian-lisp-load/)을 참고하세요.

## 시작 전에: 원리 한 가지와 백업

세 루틴 모두 원리가 같습니다.

1. `ssget`으로 고칠 객체를 고른다(종류 필터를 걸어 문자나 치수만 잡힘).
2. `entget`으로 객체의 데이터 목록을 읽는다.
3. 바꿀 그룹 코드 값을 `subst`로 바꿔 끼운다.
4. `entmod`로 도면에 다시 써 넣는다.

| 그룹 코드 | TEXT·MTEXT에서 | DIMENSION에서 |
|---|---|---|
| 0 | 객체 종류 (`"TEXT"`, `"MTEXT"`) | 객체 종류 (`"DIMENSION"`) |
| 1 | 문자 내용 | 사용자가 재지정한 치수 문자 |
| 40 | 문자 높이 | (치수 문자 높이는 치수 스타일에서 정함) |

일괄 수정은 한 번에 많은 객체를 바꾸므로 실행 전에 도면을 다른 이름으로 저장해 두는 습관을 들이세요. 결과가 이상하면 `U`로 되돌려 보고 다 돌아오지 않았으면 저장하지 않고 닫은 뒤 백업본을 엽니다.

## 루틴 1. TXREP: 문자열 찾아 바꾸기

선택한 TEXT와 MTEXT에서 찾을 문자열을 모두 바꿉니다. 문자열 치환 함수는 `substr`와 `strlen`으로 직접 만들었습니다.

```lisp
;; STR-REPLACE : 문자열 s 안의 old를 모두 new로 바꾼 결과를 돌려준다
(defun str-replace (s old new / lo n pos result)
  (setq lo (strlen old) n (strlen s) pos 1 result "")
  (while (<= pos n)
    (if (and (<= (+ pos lo -1) n)
             (= (substr s pos lo) old))
      (setq result (strcat result new)       ; 찾았으면 new를 붙이고 old 길이만큼 건너뜀
            pos    (+ pos lo))
      (setq result (strcat result (substr s pos 1))   ; 아니면 한 글자 복사
            pos    (1+ pos))
    )
  )
  result
)

;; TXREP : 선택한 TEXT·MTEXT에서 문자열을 찾아 모두 바꾼다
(defun c:TXREP (/ old new ss i cnt ed s1 s2)
  (setq old (getstring T "\n찾을 문자열: "))
  (setq new (getstring T "\n바꿀 문자열: "))
  (if (= old "")
    (princ "\n찾을 문자열이 비어 있어 종료합니다.")
    (if (setq ss (ssget '((0 . "TEXT,MTEXT"))))
      (progn
        (setq i 0 cnt 0)
        (while (< i (sslength ss))
          (setq ed (entget (ssname ss i))
                s1 (cdr (assoc 1 ed))
                s2 (str-replace s1 old new))
          (if (/= s1 s2)
            (if (entmod (subst (cons 1 s2) (assoc 1 ed) ed))
              (setq cnt (1+ cnt))
            )
          )
          (setq i (1+ i))
        )
        (princ (strcat "\n선택 " (itoa (sslength ss)) "개 중 " (itoa cnt) "개 수정"))
      )
    )
  )
  (princ)
)
```

`getstring`의 첫 인수 `T`는 공백이 들어간 문자열도 받겠다는 뜻입니다. 이게 없으면 스페이스바를 누르는 순간 입력이 끝납니다. 찾을 문자열이 빈 값이면 바로 끝내도록 한 것은 `old` 길이가 0일 때 치환 반복이 끝나지 않기 때문입니다.

### 예제와 검산

찾을 문자열 `SS41`, 바꿀 문자열 `SS400`으로 문자 5개를 선택했다고 하겠습니다.

| 원래 문자 | 바뀐 문자 | 수정 여부 |
|---|---|---|
| `MATL: SS41` | `MATL: SS400` | 수정 |
| `SS41 T3.2` | `SS400 T3.2` | 수정 |
| `SS41/SS41` | `SS400/SS400` | 수정(두 군데 모두) |
| `SUS304 T1.5` | `SUS304 T1.5` | 그대로 |
| `ss41 t2.0` | `ss41 t2.0` | 그대로(대소문자 다름) |

명령줄에는 `선택 5개 중 3개 수정`이 찍혀야 합니다. 바뀐 문자열이 원래와 같은 객체는 `entmod`를 건너뛰므로 수정 개수에 들어가지 않습니다. 비교에 쓴 `=`는 대소문자를 구분하므로 소문자 `ss41`은 그대로 남습니다.

### 주의할 점

- **두 번 실행하면 안 되는 치환**이 있습니다. `T3`을 `T3.2`로 바꾸면 이미 `T3.2`로 적힌 문자도 `T3.2.2`가 됩니다. 찾을 문자열이 바꿀 문자열 안에 들어 있으면 먼저 대상 문자를 좁혀서 고르세요.
- MTEXT는 줄바꿈이나 글꼴 변경이 `\P` 같은 서식 코드로 문자열 안에 들어 있습니다. 화면에서는 이어 보여도 중간에 서식 코드가 끼어 있으면 찾지 못합니다.
- 아주 긴 MTEXT는 내용이 그룹 코드 1 하나에 다 들어가지 않고 그룹 코드 3에 나뉘어 저장됩니다. 이 루틴은 그룹 코드 1만 고치므로 긴 MTEXT는 결과를 따로 확인하세요.

## 루틴 2. DMTXT: 치수 문자 일괄 재지정

치수 객체의 그룹 코드 1은 측정값 대신 표시할 문자입니다. 여기서 `<>`는 "측정값이 들어갈 자리"를 뜻합니다.

| 입력한 문자 | 측정값이 1200일 때 표시 |
|---|---|
| (빈 값, Enter만) | `1200` (재지정 해제, 측정값으로 복원) |
| `<>` | `1200` |
| `<> (REF)` | `1200 (REF)` |
| `%%c<>` | `⌀1200` |
| `1250` | `1250` (측정값과 무관하게 고정) |

`%%c`는 지름 기호를 넣는 특수 문자 코드입니다. 마지막 줄처럼 숫자를 직접 적으면 나중에 형상을 고쳐도 치수가 따라 바뀌지 않으니 되도록 `<>`를 살려 쓰는 편이 안전합니다.

```lisp
;; DMTXT : 선택한 치수의 문자를 한 번에 바꾼다 ("<>"는 측정값 자리)
(defun c:DMTXT (/ txt ss i cnt ed)
  (setq txt (getstring T "\n치수 문자(<>는 측정값, Enter만 누르면 측정값으로 복원): "))
  (if (setq ss (ssget '((0 . "DIMENSION"))))
    (progn
      (setq i 0 cnt 0)
      (while (< i (sslength ss))
        (setq ed (entget (ssname ss i)))
        (if (assoc 1 ed)
          (setq ed (subst (cons 1 txt) (assoc 1 ed) ed))
          (setq ed (append ed (list (cons 1 txt))))
        )
        (if (entmod ed) (setq cnt (1+ cnt)))
        (setq i (1+ i))
      )
      (princ (strcat "\n치수 " (itoa cnt) "개 수정"))
    )
  )
  (princ)
)
```

참고 치수 4개를 골라 `<> (REF)`를 넣으면 `치수 4개 수정`이 찍히고 각 치수가 `측정값 (REF)`로 바뀝니다. 다시 실행해 Enter만 누르면 원래 측정값 표시로 돌아옵니다. 화면이 바로 바뀌지 않으면 `REGEN`을 한 번 실행해 보세요.

## 루틴 3. TXHT: 문자 높이 한 번에 바꾸기

```lisp
;; TXHT : 선택한 TEXT·MTEXT의 문자 높이를 한 번에 바꾼다
(defun c:TXHT (/ h ss i cnt ed)
  (setq h (getreal "\n새 문자 높이: "))
  (if (and h (> h 0) (setq ss (ssget '((0 . "TEXT,MTEXT")))))
    (progn
      (setq i 0 cnt 0)
      (while (< i (sslength ss))
        (setq ed (entget (ssname ss i)))
        (if (entmod (subst (cons 40 h) (assoc 40 ed) ed))
          (setq cnt (1+ cnt))
        )
        (setq i (1+ i))
      )
      (princ (strcat "\n문자 " (itoa cnt) "개 높이를 " (rtos h 2 1) "(으)로 변경"))
    )
  )
  (princ)
)
```

높이를 묻는 곳에서 Enter만 누르거나 0 이하를 넣으면 아무것도 고르지 않고 끝납니다. 예를 들어 문자 12개를 골라 `3.5`를 넣으면 `문자 12개 높이를 3.5(으)로 변경`이 찍힙니다. 메시지의 높이는 소수 한 자리로만 표시하므로 `3.18`을 넣으면 메시지에는 `3.2`로 보이지만 실제 높이는 3.18로 들어갑니다.

MTEXT 안에서 일부 글자에만 따로 높이를 지정해 둔 경우(서식 코드 `\H`)에는 그 부분이 그룹 코드 40을 따르지 않습니다. 그런 문자는 MTEXT 편집기에서 서식을 지운 뒤 다시 실행하세요.

## 고를 대상을 좁히는 법

`ssget` 필터에 조건을 더하면 엉뚱한 문자를 고칠 일이 줄어듭니다.

| 하고 싶은 일 | 필터 예 |
|---|---|
| TEXT만 | `'((0 . "TEXT"))` |
| `NOTE` 레이어의 문자만 | `'((0 . "TEXT,MTEXT") (8 . "NOTE"))` |
| 도면 전체에서 자동 선택 | `(ssget "X" '((0 . "TEXT,MTEXT")))` |

`"X"`는 화면에서 고르지 않고 도면 전체를 검색하므로 배치(레이아웃)에 있는 도곽 문자까지 함께 잡힙니다. 처음에는 화면에서 직접 고르는 방식으로 결과를 확인한 뒤에 쓰세요.

## 정리

- 문자·치수 일괄 수정은 `ssget`으로 고르고 `entget`으로 읽은 뒤 그룹 코드를 `subst`로 바꿔 `entmod`로 쓰는 구조다
- 문자 내용은 그룹 코드 1, 문자 높이는 40, 치수 문자는 DIMENSION의 그룹 코드 1이며 `<>`가 측정값 자리다
- 실행 전에 백업하고 찾을 문자열이 바꿀 문자열 안에 들어 있으면 두 번 실행하지 않도록 대상을 좁힌다

다음 글에서는 엑셀로 BOM을 정리할 때 자주 쓰는 함수 다섯 가지를 정리해 보겠습니다.
