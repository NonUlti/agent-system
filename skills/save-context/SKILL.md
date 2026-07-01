---
name: save-context
description: Use when the user wants to save the current session's working state for later — finishing for the day, hitting context limits, or asking to "save context"/"핸드오프 저장"/"이어서 하게 정리해줘". Saves a handoff under a slug (usually the ticket key) in a central store; load-context restores it by that slug.
---

# Save Context (세션 핸드오프 저장)

현재 세션의 작업 상태를 슬러그(보통 지라 키)로 식별되는 핸드오프 파일 하나로 중앙 저장소에 써, 다음 세션이 슬러그를 골라 이어받을 수 있게 한다.

핸드오프의 단위는 repo가 아니라 **작업(슬러그)**이다. 그래서 (a) 한 repo에서 여러 작업을 번갈아 해도 서로 덮어쓰지 않고, (b) 한 작업이 여러 repo에 걸쳐도 핸드오프 하나에 모을 수 있다. 관련 repo들은 핸드오프 본문의 "관련 repo"에 기록한다.

## When to Use

- 오늘 작업을 끝내고 내일 이어서 할 때
- 컨텍스트 한도가 차서 새 세션으로 넘어가야 할 때
- 사용자가 "컨텍스트 저장", "핸드오프 정리", "save context"를 요청할 때

## 절차

1. **슬러그를 정한다.** 슬러그는 이 작업을 식별하는 짧은 이름이자 파일명이 된다. 영문/숫자/`-`/`_`만 쓰고 소문자로 통일한다(공백→`-`).
   - 사용자가 인자를 줬으면 그걸 슬러그로 쓴다 (`save-context soopkr-29478` → `soopkr-29478`).
   - 안 줬으면 현재 브랜치에서 유도한다 — prefix를 떼고 소문자화(`feature/soopkr-29935` → `soopkr-29935`).
   - 브랜치가 `master`/`main`/`develop` 같은 일반명이라 작업을 식별하지 못하면, 지어내지 말고 사용자에게 슬러그를 한 번 물어본다.
2. **관련 repo와 메타데이터를 수집한다.** 이 작업이 건드린 repo(들)를 확인한다. 보통 현재 repo 하나지만, 여러 repo에 걸친 작업이면 각각에 대해 아래를 모은다:
   ```bash
   date '+%Y-%m-%d %H:%M'
   git -C <repo> rev-parse --abbrev-ref HEAD 2>/dev/null      # 브랜치
   git -C <repo> log -1 --pretty='%h %s' 2>/dev/null           # 마지막 커밋 (해시 + 제목)
   ```
   코드를 안 건드린 조사·문서 작업이면 "관련 repo"에 참조한 repo만 적거나(브랜치/커밋 없이 경로만) 비워둔다. git repo가 아니면 브랜치/커밋 줄은 생략한다.
3. **아래 템플릿으로 핸드오프 파일을 쓴다.** 같은 슬러그면 그 파일만 덮어쓴다(다른 작업 파일은 건드리지 않는다). 필수 3섹션은 항상, 선택 2섹션은 해당 내용이 있을 때만. 빈 섹션을 억지로 남기지 않는다:
   ```bash
   DIR="$HOME/.claude/agent-system/handoffs"; mkdir -p "$DIR"
   # 파일: $DIR/<슬러그>.md
   ```
4. **중앙 색인을 갱신한다.** load-context가 목록으로 모아 보여줄 수 있도록 이 작업을 색인에 한 줄로 기록한다(슬러그 키로 중복 제거 → 같은 슬러그면 갱신). 컬럼: `슬러그 \t 저장시각 \t 목표 \t 관련repo`. `<목표 첫 줄>`에는 방금 쓴 핸드오프의 `## 목표` 첫 줄을, `<repo basename들>`에는 관련 repo의 basename을 쉼표로(없으면 `-`) 넣는다:
   ```bash
   IDX="$HOME/.claude/agent-system/handoffs.tsv"
   mkdir -p "$(dirname "$IDX")"; touch "$IDX"
   awk -F'\t' -v s="$SLUG" '$1!=s' "$IDX" > "$IDX.tmp" && mv "$IDX.tmp" "$IDX"
   printf '%s\t%s\t%s\t%s\n' "$SLUG" "$(date '+%Y-%m-%d %H:%M')" "<목표 첫 줄>" "<repo basename들>" >> "$IDX"
   ```
   색인은 목록용 요약일 뿐 정본은 `handoffs/<슬러그>.md`다. 색인·핸드오프 모두 로컬 전용이다.
5. **커밋하지 않는다.** 파일만 쓴다.
6. 저장한 슬러그와 파일 경로를 사용자에게 알린다.

## 핸드오프 템플릿

```markdown
# HANDOFF: <슬러그>

- 저장: <YYYY-MM-DD HH:MM>
- 관련 repo:
  - <repo경로> · <branch> · <shorthash 제목>
  - <repo가 여러 개면 줄 추가>   <!-- 코드 안 건드린 조사면 경로만, 또는 "(조사 — 코드 미수정)" -->

## 목표
<이 작업이 끝나면 무엇이 되어 있어야 하는가 — 1~3줄>

## 현재 상태
<어디까지 했고 지금 동작하는가. 막 끝낸 것과 진행 중인 것>

## 다음 할 일
1. <바로 실행 가능한 첫 항목 — 파일/명령 수준으로 구체적으로>
2. <그다음>

## 결정 사항   <!-- 선택: 다시 논쟁하지 않도록 정한 것이 있을 때만 -->
- <무엇을 왜 그렇게 정했나>

## 주의사항   <!-- 선택: 함정·미해결 이슈·건드리면 안 되는 것이 있을 때만 -->
- <주의할 점>
```

## 작성 원칙

- **부실 금지 / 장황 금지** 둘 다 피한다. "다음 할 일"의 첫 항목은 다음 세션이 즉시 손댈 수 있을 만큼 구체적이어야 한다.
- **검증 안 된 것을 사실처럼 적지 않는다.** 세션에서 실제로 일어났거나 확인된 것만 단정형으로 쓴다. 불확실한 추정은 `추정:`·`미확인:` 꼬리표를 달거나 "확인 필요"로 남기고, 그럴듯하게 지어내 빈칸을 채우지 않는다. '현재 상태'는 검증된 사실 위주로, '다음 할 일'은 실제로 합의·도출된 것만 적는다.
- 같은 슬러그의 기존 핸드오프가 있으면 그 파일만 통째로 덮어쓴다(다른 슬러그 파일은 건드리지 않는다).
