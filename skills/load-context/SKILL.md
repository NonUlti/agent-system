---
name: load-context
description: Use at the start of a session to resume prior work — when the user says "이어서 하자", "load context", "지난번 작업 복원", or otherwise wants to pick up where a previous session left off. Lists saved handoffs (by slug) from the central index for the user to pick, then verifies the chosen handoff against its repo(s) and briefs before doing anything.
---

# Load Context (세션 핸드오프 복원)

이전 세션이 슬러그로 저장한 핸드오프를 읽어, 그 작업이 걸친 repo(들)의 현재 상태와 대조한 뒤 브리핑한다. **자동으로 작업을 재개하지 않는다** — 사용자가 명시적으로 지시하면 그때 시작한다.

핸드오프의 단위는 repo가 아니라 작업(슬러그)이다. 한 작업이 여러 repo에 걸칠 수 있고, 그 repo 목록은 핸드오프 본문의 "관련 repo"에 있다.

## When to Use

- 새 세션에서 지난 작업을 이어갈 때
- 사용자가 "이어서 하자", "load context", "지난번 거 복원"을 요청할 때

## 절차

0. **어떤 핸드오프를 복원할지 고른다.** 핸드오프는 `~/.claude/agent-system/handoffs/<슬러그>.md`에 저장되고, 중앙 색인(`~/.claude/agent-system/handoffs.tsv`, 컬럼: `슬러그 \t 저장시각 \t 목표 \t 관련repo`)이 그 목록을 모은다. 색인을 읽어 대상을 정한다:
   ```bash
   IDX="$HOME/.claude/agent-system/handoffs.tsv"
   [ -s "$IDX" ] && cat "$IDX"
   ```
   - **사용자가 인자(슬러그 일부/목표 키워드)를 줬으면** 색인 1번째 칸(슬러그)과 대조해 하나로 좁힌다. 정확히 하나면 그걸 대상으로, 여럿이 맞으면 후보만 보여주고 고르게 한다.
   - **인자가 없으면:**
     - 색인 항목 0개 → "저장된 핸드오프가 없습니다."로 종료한다. (없는 것은 오류가 아니다)
     - 1개 → 그 항목을 대상으로 한다.
     - 2개 이상 → `번호) 슬러그 · 저장시각 · 목표 · 관련repo` 목록을 사람이 읽기 좋게 보여주고, 사용자가 번호를 고를 때까지 기다린다. **자동 선택 금지.**
   - 고른 항목의 슬러그를 `SLUG`로 삼는다(아래 1·2번에서 사용).
1. **핸드오프 파일을 읽는다.**
   ```bash
   cat "$HOME/.claude/agent-system/handoffs/$SLUG.md" 2>/dev/null
   ```
   - 색인엔 있으나 파일이 없으면(색인이 낡음): "색인엔 있으나 핸드오프 파일이 사라졌습니다"라고 알리고, 그 줄을 색인에서 지울지 제안한 뒤 다시 고르게 한다. 색인 줄 삭제는 `awk -F'\t' -v s="$SLUG" '$1!=s' "$IDX" > "$IDX.tmp" && mv "$IDX.tmp" "$IDX"`.
   - 색인이 아예 없으면: "저장된 핸드오프가 없습니다."로 종료한다.
2. **현실 검증** — 핸드오프는 "쓰인 시점의 진실"이므로 현재와 대조한다. 핸드오프 본문 "관련 repo"의 **각 repo**에 대해 아래를 실행하고, 파일 존재 확인은 항상 한다. 코드 repo가 없는 조사 작업이면 git 대조는 건너뛰고 산출물·참조 파일 존재만 확인한다:
   ```bash
   git -C <repo> log -1 --pretty='%h %s' 2>/dev/null       # 현재 커밋 (해시 + 제목)
   git -C <repo> rev-parse --abbrev-ref HEAD 2>/dev/null   # 현재 브랜치
   git -C <repo> log --oneline <핸드오프-커밋>..HEAD 2>/dev/null  # 저장 이후 커밋들 (주1 참조)
   git -C <repo> status --short 2>/dev/null                # 미커밋 변경
   ```
   - 주1: `<핸드오프-커밋>` 자리에는 그 repo 항목의 "마지막 커밋" short hash를 대입한다. 없으면 이 명령은 건너뛴다. 그 해시가 현재 히스토리에 없으면(rebase/squash/amend 등) "저장 시점 커밋을 현재 히스토리에서 찾을 수 없음"을 브리핑에 표시한다.
   - 핸드오프에 적힌 repo의 커밋/브랜치와 현재가 다르면(저장 이후 커밋이 쌓였거나 브랜치가 바뀜) 그 사실을 브리핑에 명시한다.
   - 핸드오프 "다음 할 일"이나 "현재 상태"가 언급하는 파일이 실제로 존재하는지 확인하고, 없으면 표시한다.
3. **브리핑한다.** 다음을 요약해 사람이 읽기 좋게 제시한다:
   - 목표 / 현재 상태 / 다음 할 일 (핸드오프에서)
   - 관련 repo가 여럿이면 각 repo의 검증 결과를 구분해서
   - 검증 결과 어긋난 점(있으면) — "핸드오프 저장 이후 커밋 3개가 있습니다" 등
4. **지시를 기다린다.** 자동으로 다음 할 일을 실행하지 않는다.

## 원칙

- 핸드오프 내용을 그대로 믿지 말고 항상 현재 상태와 대조한다. 오래됐거나 다른 머신/세션의 작업이 끼어들었을 수 있다.
- **읽은 것·검증한 것만 전달하고, 빈칸을 추측으로 메우지 않는다.** 핸드오프에 없거나 모호한 부분을 그럴듯한 해석으로 단정하지 말 것. 핸드오프와 현재 상태가 어긋나거나 불명확하면 매끄럽게 넘기지 말고 "불명확/검증 필요"로 드러낸다. 추론을 전할 땐 확인된 사실과 구분해 표시한다.
- 브리핑은 짧게. 다음 할 일의 첫 항목을 또렷하게 전달한다.
