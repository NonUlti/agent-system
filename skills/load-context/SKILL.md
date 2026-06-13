---
name: load-context
description: Use at the start of a session to resume prior work — when the user says "이어서 하자", "load context", "지난번 작업 복원", or otherwise wants to pick up where a previous session left off. Reads .claude/HANDOFF.md, verifies it against the current repo state, and briefs before doing anything.
---

# Load Context (세션 핸드오프 복원)

이전 세션이 `.claude/HANDOFF.md`에 남긴 작업 상태를 읽어, 현재 repo 상태와 대조한 뒤 브리핑한다. **자동으로 작업을 재개하지 않는다** — 사용자가 명시적으로 지시하면 그때 시작한다.

## When to Use

- 새 세션에서 지난 작업을 이어갈 때
- 사용자가 "이어서 하자", "load context", "지난번 거 복원"을 요청할 때

## 절차

1. **repo 루트로 이동 후 핸드오프 파일을 읽는다.** save-context와 같은 위치(repo 루트의 `.claude/`)를 보도록 루트로 고정한다:
   ```bash
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
   cat .claude/HANDOFF.md 2>/dev/null
   ```
   파일이 없으면: "이 프로젝트에 저장된 핸드오프(.claude/HANDOFF.md)가 없습니다." 라고 알리고 종료한다. (없는 것은 오류가 아니다)
2. **현실 검증** — 핸드오프는 "쓰인 시점의 진실"이므로 현재와 대조한다. 아래 git 명령은 git repo일 때만 실행하고, 파일 존재 확인은 git 여부와 무관하게 항상 한다:
   ```bash
   git log -1 --pretty='%h %s' 2>/dev/null       # 현재 커밋 (해시 + 제목)
   git rev-parse --abbrev-ref HEAD 2>/dev/null   # 현재 브랜치
   git log --oneline <핸드오프-커밋>..HEAD 2>/dev/null  # 저장 이후 커밋들 (주1 참조)
   git status --short 2>/dev/null                # 미커밋 변경
   ```
   - 주1: `<핸드오프-커밋>` 자리에는 핸드오프 파일의 "마지막 커밋:" 줄에서 읽은 short hash를 대입한다. 그 줄이 없으면 이 명령은 건너뛴다.
   - 핸드오프 메타데이터의 커밋/브랜치와 현재가 다르면(저장 이후 커밋이 쌓였거나 브랜치가 바뀜) 그 사실을 브리핑에 명시한다.
   - 핸드오프 "다음 할 일"이나 "현재 상태"가 언급하는 파일이 실제로 존재하는지 확인하고, 없으면 표시한다.
3. **브리핑한다.** 다음을 요약해 사람이 읽기 좋게 제시한다:
   - 목표 / 현재 상태 / 다음 할 일 (핸드오프에서)
   - 검증 결과 어긋난 점(있으면) — "핸드오프 저장 이후 커밋 3개가 있습니다" 등
4. **지시를 기다린다.** 자동으로 다음 할 일을 실행하지 않는다.

## 원칙

- 핸드오프 내용을 그대로 믿지 말고 항상 현재 상태와 대조한다. 오래됐거나 다른 머신/세션의 작업이 끼어들었을 수 있다.
- 브리핑은 짧게. 다음 할 일의 첫 항목을 또렷하게 전달한다.
