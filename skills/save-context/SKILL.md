---
name: save-context
description: Use when the user wants to save the current session's working state for later — finishing for the day, hitting context limits, or asking to "save context"/"핸드오프 저장"/"이어서 하게 정리해줘". Writes a handoff file the load-context skill can restore from.
---

# Save Context (세션 핸드오프 저장)

현재 세션의 작업 상태를 프로젝트의 `.claude/HANDOFF.md` 한 파일에 덮어써, 다음 세션이 이어받을 수 있게 한다.

## When to Use

- 오늘 작업을 끝내고 내일 이어서 할 때
- 컨텍스트 한도가 차서 새 세션으로 넘어가야 할 때
- 사용자가 "컨텍스트 저장", "핸드오프 정리", "save context"를 요청할 때

## 절차

1. **repo 루트로 이동.** 핸드오프는 repo 루트의 `.claude/`에 둔다 (하위 디렉토리에서 실행해도 같은 위치를 쓰도록 루트로 고정):
   ```bash
   cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
   mkdir -p .claude
   ```
   non-git 프로젝트에서는 루트 탐지가 안 되어 현재 디렉토리(`pwd`)가 기준이 된다. 그럴 땐 save와 load를 같은 디렉토리(보통 프로젝트 루트)에서 실행해야 같은 `.claude/HANDOFF.md`를 가리킨다.
2. **메타데이터 수집** (git repo일 때만 git 부분 포함):
   ```bash
   date '+%Y-%m-%d %H:%M'
   git rev-parse --abbrev-ref HEAD 2>/dev/null     # 브랜치
   git log -1 --pretty='%h %s' 2>/dev/null          # 마지막 커밋 (해시 + 제목)
   ```
   git repo가 아니면(git 명령이 실패하면) 메타데이터의 브랜치/커밋 줄은 생략한다.
3. **아래 템플릿으로 `.claude/HANDOFF.md`를 덮어쓴다.** 필수 3섹션은 항상, 선택 2섹션은 해당 내용이 있을 때만 쓴다. 빈 섹션을 억지로 남기지 않는다.
4. **커밋하지 않는다.** 파일만 쓴다. (머신 간 이동이 필요하면 사용자가 직접 커밋)
5. 저장한 파일 경로를 사용자에게 알린다.

## HANDOFF.md 템플릿

```markdown
# HANDOFF

- 저장: <YYYY-MM-DD HH:MM>
- 브랜치: <branch>  (git repo가 아니면 이 줄 생략)
- 마지막 커밋: <shorthash> <제목>  (없으면 생략)

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
- 기존 `.claude/HANDOFF.md`가 있으면 통째로 덮어쓴다(단일 파일, 이력은 git 몫).
