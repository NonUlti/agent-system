---
name: load-context
description: Use at the start of a session to resume prior work — when the user says "이어서 하자", "load context", "지난번 작업 복원", or otherwise wants to pick up where a previous session left off. Lists saved handoffs from the central index (one per project) for the user to pick, then verifies the chosen handoff against its repo state and briefs before doing anything.
---

# Load Context (세션 핸드오프 복원)

이전 세션이 `.claude/HANDOFF.md`에 남긴 작업 상태를 읽어, 현재 repo 상태와 대조한 뒤 브리핑한다. **자동으로 작업을 재개하지 않는다** — 사용자가 명시적으로 지시하면 그때 시작한다.

## When to Use

- 새 세션에서 지난 작업을 이어갈 때
- 사용자가 "이어서 하자", "load context", "지난번 거 복원"을 요청할 때

## 절차

0. **어떤 핸드오프를 복원할지 고른다.** 핸드오프는 프로젝트마다 각 repo 루트의 `.claude/HANDOFF.md`로 흩어져 저장되고, 중앙 색인(`~/.claude/agent-system/handoffs.tsv`, 컬럼: `저장시각 \t repo경로 \t 브랜치 \t 목표`)이 그 목록을 모은다. 색인을 읽어 대상을 정한다:
   ```bash
   IDX="$HOME/.claude/agent-system/handoffs.tsv"
   [ -s "$IDX" ] && cat "$IDX"
   ```
   - **사용자가 인자(프로젝트 이름/경로 일부)를 줬으면** 색인 2번째 칸(repo 경로)과 대조해 하나로 좁힌다. 정확히 하나면 그걸 대상으로, 여럿이 맞으면 후보만 보여주고 고르게 한다.
   - **인자가 없으면:**
     - 색인 항목 0개 → 아래 1번으로 가서 현재 repo 루트의 HANDOFF.md를 본다.
     - 1개 → 그 항목을 대상으로 한다.
     - 2개 이상 → `번호) 프로젝트(repo basename) · 저장시각 · 목표` 목록을 사람이 읽기 좋게 보여주고, 사용자가 번호를 고를 때까지 기다린다. **자동 선택 금지.**
   - 고른 항목의 repo 경로를 `ROOT`로 삼는다(아래 1·2번에서 사용).
1. **핸드오프 파일을 읽는다.** 0번에서 고른 `ROOT`가 있으면 그 경로를, 없으면 현재 repo 루트를 본다:
   ```bash
   ROOT="${ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
   cat "$ROOT/.claude/HANDOFF.md" 2>/dev/null
   ```
   - 색인에서 골랐는데 파일이 없으면(색인이 낡음): "색인엔 있으나 핸드오프 파일이 사라졌습니다"라고 알리고, 그 줄을 색인에서 지울지 제안한 뒤 다시 고르게 한다. 색인 줄 삭제는 `awk -F'\t' -v r="$ROOT" '$2!=r' "$IDX" > "$IDX.tmp" && mv "$IDX.tmp" "$IDX"`.
   - 색인도 없고 현재 repo에도 없으면: "저장된 핸드오프가 없습니다."로 종료한다. (없는 것은 오류가 아니다)
   - non-git 프로젝트라면 save를 실행했던 디렉토리와 같은 곳에서 실행해야 같은 파일을 읽는다.
2. **현실 검증** — 핸드오프는 "쓰인 시점의 진실"이므로 현재와 대조한다. git 명령은 골라진 `ROOT`에서 실행하고(`git -C "$ROOT" …`), 파일 존재 확인은 git 여부와 무관하게 항상 한다:
   ```bash
   git -C "$ROOT" log -1 --pretty='%h %s' 2>/dev/null       # 현재 커밋 (해시 + 제목)
   git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null   # 현재 브랜치
   git -C "$ROOT" log --oneline <핸드오프-커밋>..HEAD 2>/dev/null  # 저장 이후 커밋들 (주1 참조)
   git -C "$ROOT" status --short 2>/dev/null                # 미커밋 변경
   ```
   - 주1: `<핸드오프-커밋>` 자리에는 핸드오프 파일의 "마지막 커밋:" 줄에서 읽은 short hash를 대입한다. 그 줄이 없으면 이 명령은 건너뛴다. 그 해시가 현재 히스토리에 없으면(rebase/squash/amend 등) "저장 시점 커밋을 현재 히스토리에서 찾을 수 없음"을 브리핑에 표시한다.
   - 핸드오프 메타데이터의 커밋/브랜치와 현재가 다르면(저장 이후 커밋이 쌓였거나 브랜치가 바뀜) 그 사실을 브리핑에 명시한다.
   - 핸드오프 "다음 할 일"이나 "현재 상태"가 언급하는 파일이 실제로 존재하는지 확인하고, 없으면 표시한다.
3. **브리핑한다.** 다음을 요약해 사람이 읽기 좋게 제시한다:
   - 목표 / 현재 상태 / 다음 할 일 (핸드오프에서)
   - 검증 결과 어긋난 점(있으면) — "핸드오프 저장 이후 커밋 3개가 있습니다" 등
4. **지시를 기다린다.** 자동으로 다음 할 일을 실행하지 않는다.

## 원칙

- 핸드오프 내용을 그대로 믿지 말고 항상 현재 상태와 대조한다. 오래됐거나 다른 머신/세션의 작업이 끼어들었을 수 있다.
- **읽은 것·검증한 것만 전달하고, 빈칸을 추측으로 메우지 않는다.** 핸드오프에 없거나 모호한 부분을 그럴듯한 해석으로 단정하지 말 것. 핸드오프와 현재 상태가 어긋나거나 불명확하면 매끄럽게 넘기지 말고 "불명확/검증 필요"로 드러낸다. 추론을 전할 땐 확인된 사실과 구분해 표시한다.
- 브리핑은 짧게. 다음 할 일의 첫 항목을 또렷하게 전달한다.
