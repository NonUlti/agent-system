# save-context / load-context 플러그인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `agent-system` 플러그인 뼈대(매니페스트·hooks·README)를 만들고, 세션 핸드오프 스킬 2개(`save-context`, `load-context`)를 추가해 로컬 설치로 라운드트립까지 검증한다.

**Architecture:** 단일 GitHub repo가 플러그인이자 자기 마켓플레이스(`source: "./"`). 사용자 진입점은 슬래시-호출 가능한 스킬 2개 — 커맨드 파일은 두지 않는다(스킬이 슬래시 호출 + 자동 발동 둘 다 됨). `save-context`는 현재 세션 상태를 프로젝트의 `.claude/HANDOFF.md`에 덮어쓰고(커밋 안 함), `load-context`는 그 파일을 읽고 git 현실과 대조해 브리핑한다.

**Tech Stack:** Claude Code 플러그인 시스템(`.claude-plugin/` 매니페스트, `skills/<name>/SKILL.md`), `claude plugin` CLI(validate/tag/marketplace/install), `/skill-creator` 스킬, git.

**검증 환경 메모:** 이 계획의 모든 `claude plugin ...` 동작은 본 조사에서 throwaway 플러그인으로 실증됨. 핵심 사실:
- `claude plugin validate .` 는 marketplace 매니페스트를 검증. plugin.json에 `author`, marketplace.json에 top-level `description`이 없으면 경고 → `--strict`는 실패.
- `install`은 commit SHA로 스냅샷을 뜨므로, repo 파일을 고쳐도 **커밋 + 버전 bump + 재설치/업데이트 + 세션 재시작** 전엔 반영 안 됨.
- 스킬은 `/agent-system:<skill>` 로 슬래시 호출됨 + description으로 자동 발동.

---

## File Structure

| 경로 | 책임 |
|------|------|
| `~/agent-system/.claude-plugin/plugin.json` | 플러그인 정체성: name, version(SSOT), description, author |
| `~/agent-system/.claude-plugin/marketplace.json` | 셀프 마켓플레이스: name(=agent-system), owner, description, plugins[{name, source:"./", version}] |
| `~/agent-system/hooks/hooks.json` | 빈 훅 뼈대 `{"hooks": {}}` |
| `~/agent-system/.gitignore` | `*-workspace/`(skill-creator eval 산출물), OS 잡파일 |
| `~/agent-system/README.md` | 설치·사용·업데이트 안내 |
| `~/agent-system/skills/save-context/SKILL.md` | 세션 상태를 `.claude/HANDOFF.md`로 저장하는 절차 + 템플릿 |
| `~/agent-system/skills/load-context/SKILL.md` | `.claude/HANDOFF.md` 읽기 + git 현실 검증 + 브리핑 절차 |

이미 존재: `~/agent-system/{LICENSE, README.md(stub), docs/specs/*, .git}`. `.claude-plugin/`, `skills/`, `hooks/` 는 아직 없음.

---

## Task 1: 매니페스트 + 뼈대 파일 생성

**Files:**
- Create: `~/agent-system/.claude-plugin/plugin.json`
- Create: `~/agent-system/.claude-plugin/marketplace.json`
- Create: `~/agent-system/hooks/hooks.json`
- Create: `~/agent-system/.gitignore`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p ~/agent-system/.claude-plugin ~/agent-system/hooks ~/agent-system/skills
```

- [ ] **Step 2: `plugin.json` 작성**

`~/agent-system/.claude-plugin/plugin.json`:
```json
{
  "name": "agent-system",
  "version": "0.1.0",
  "description": "개인 공통 작업 컨벤션 — 세션 핸드오프 스킬(save-context/load-context). 점진 확장 예정.",
  "author": {
    "name": "NonUlti"
  }
}
```

- [ ] **Step 3: `marketplace.json` 작성**

`~/agent-system/.claude-plugin/marketplace.json`:
```json
{
  "name": "agent-system",
  "owner": {
    "name": "NonUlti"
  },
  "description": "NonUlti 개인 공통 플러그인 마켓플레이스",
  "plugins": [
    {
      "name": "agent-system",
      "source": "./",
      "version": "0.1.0",
      "description": "개인 공통 작업 컨벤션 — 세션 핸드오프 스킬(save-context/load-context)"
    }
  ]
}
```

주의: plugin.json의 `version`과 marketplace.json `plugins[0].version` 은 **항상 같아야** 한다(`claude plugin tag`이 강제). plugin.json의 `name`(`agent-system`)은 plugins[] 항목의 `name`과 일치해야 한다. 마켓플레이스 top-level `name`도 `agent-system`이라, 설치는 `agent-system@agent-system`이 된다.

- [ ] **Step 4: 빈 `hooks.json` 작성**

`~/agent-system/hooks/hooks.json`:
```json
{ "hooks": {} }
```

- [ ] **Step 5: `.gitignore` 작성**

`~/agent-system/.gitignore`:
```gitignore
# skill-creator eval 산출물 (스킬 디렉토리 형제로 생성됨)
*-workspace/

# OS
.DS_Store
```

- [ ] **Step 6: validate로 매니페스트 검증**

```bash
cd ~/agent-system && claude plugin validate .
```
Expected: `✔ Validation passed` (경고 없음 — author/description을 넣었으므로). 다음도 통과해야 한다:
```bash
cd ~/agent-system && claude plugin validate . --strict
```
Expected: `✔ Validation passed` (또는 경고 0개로 strict 통과). 경고가 뜨면 누락 필드를 채운다.

- [ ] **Step 7: 커밋**

```bash
cd ~/agent-system && git add .claude-plugin hooks .gitignore && \
git commit -m "feat: 플러그인 매니페스트 + 빈 hooks + gitignore 뼈대

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 2: `save-context` 스킬 작성 (/skill-creator)

**Files:**
- Create: `~/agent-system/skills/save-context/SKILL.md`

`/skill-creator`는 절대경로로 출력 위치를 지정하면 그 자리에 SKILL.md를 쓴다. eval/packaging은 건너뛴다(주관적 워크플로우 스킬이라 불필요). 아래는 skill-creator가 생성해야 할 **최종 SKILL.md의 목표 내용**이다 — skill-creator 대화로 만들든 직접 쓰든 결과물이 이와 같아야 한다.

- [ ] **Step 1: 스킬 디렉토리 준비**

```bash
mkdir -p ~/agent-system/skills/save-context
```

- [ ] **Step 2: `/skill-creator` 실행 (또는 직접 작성)**

skill-creator에 전달할 의도: "세션 핸드오프 저장 스킬. 절대경로 `~/agent-system/skills/save-context/SKILL.md`에 작성. eval/packaging 생략." 아래 목표 내용대로 SKILL.md를 만든다.

`~/agent-system/skills/save-context/SKILL.md`:
````markdown
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
````

- [ ] **Step 3: 작성 결과 검증**

```bash
test -f ~/agent-system/skills/save-context/SKILL.md && echo "OK: SKILL.md 존재"
head -5 ~/agent-system/skills/save-context/SKILL.md   # frontmatter name: save-context 확인
ls -d ~/agent-system/skills/*-workspace 2>/dev/null && echo "경고: workspace 폴더 생성됨 — gitignore로 무시되는지 확인"
```
Expected: SKILL.md 존재, frontmatter `name: save-context`, 디렉토리명과 일치.

- [ ] **Step 4: 매니페스트 재검증 (스킬 추가 후)**

```bash
cd ~/agent-system && claude plugin validate .
```
Expected: `✔ Validation passed`.

- [ ] **Step 5: 커밋**

```bash
cd ~/agent-system && git add skills/save-context && \
git commit -m "feat: save-context 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 3: `load-context` 스킬 작성 (/skill-creator)

**Files:**
- Create: `~/agent-system/skills/load-context/SKILL.md`

- [ ] **Step 1: 스킬 디렉토리 준비**

```bash
mkdir -p ~/agent-system/skills/load-context
```

- [ ] **Step 2: `/skill-creator` 실행 (또는 직접 작성)**

`~/agent-system/skills/load-context/SKILL.md`:
````markdown
---
name: load-context
description: Use at the start of a session to resume prior work — when the user says "이어서 하자", "load context", "지난번 작업 복원", or otherwise wants to pick up where a previous session left off. Reads .claude/HANDOFF.md, verifies it against the current repo state, and briefs before doing anything.
---

# Load Context (세션 핸드오프 복원)

이전 세션이 `.claude/HANDOFF.md`에 남긴 작업 상태를 읽어, 현재 repo 상태와 대조한 뒤 브리핑한다. **자동으로 작업을 재개하지 않는다** — 사용자가 "고"라고 하면 시작한다.

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
2. **현실 검증** — 핸드오프는 "쓰인 시점의 진실"이므로 현재와 대조한다 (git repo일 때):
   ```bash
   git log -1 --pretty='%h %s' 2>/dev/null       # 현재 커밋 (해시 + 제목)
   git rev-parse --abbrev-ref HEAD 2>/dev/null   # 현재 브랜치
   git log --oneline <핸드오프-커밋>..HEAD 2>/dev/null  # 저장 이후 커밋들
   git status --short 2>/dev/null                # 미커밋 변경
   ```
   - 핸드오프 메타데이터의 커밋/브랜치와 현재가 다르면(저장 이후 커밋이 쌓였거나 브랜치가 바뀜) 그 사실을 브리핑에 명시한다.
   - 핸드오프 "다음 할 일"이나 "현재 상태"가 언급하는 파일이 실제로 존재하는지 확인하고, 없으면 표시한다.
3. **브리핑한다.** 다음을 요약해 사람이 읽기 좋게 제시한다:
   - 목표 / 현재 상태 / 다음 할 일 (핸드오프에서)
   - 검증 결과 어긋난 점(있으면) — "핸드오프 저장 이후 커밋 3개가 있습니다" 등
4. **지시를 기다린다.** 자동으로 다음 할 일을 실행하지 않는다.

## 원칙

- 핸드오프 내용을 그대로 믿지 말고 항상 현재 상태와 대조한다. 오래됐거나 다른 머신/세션의 작업이 끼어들었을 수 있다.
- 브리핑은 짧게. 다음 할 일의 첫 항목을 또렷하게 전달한다.
````

- [ ] **Step 3: 작성 결과 검증**

```bash
test -f ~/agent-system/skills/load-context/SKILL.md && echo "OK"
head -5 ~/agent-system/skills/load-context/SKILL.md   # name: load-context 확인
```

- [ ] **Step 4: 커밋**

```bash
cd ~/agent-system && git add skills/load-context && \
git commit -m "feat: load-context 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 4: README 작성

**Files:**
- Modify: `~/agent-system/README.md` (현재 41바이트 stub)

- [ ] **Step 1: README 작성**

`~/agent-system/README.md`:
```markdown
# agent-system

NonUlti 개인 공통 Claude Code 플러그인. 여러 프로젝트·머신에서 공유하는 작업 컨벤션을 담는다.
단일 repo가 플러그인이자 자기 마켓플레이스(`source: "./"`)다.

## 담긴 것

- **save-context** — 현재 세션 작업 상태를 `.claude/HANDOFF.md`로 저장 (세션 핸드오프)
- **load-context** — `.claude/HANDOFF.md`를 읽고 현재 상태와 대조해 복원 브리핑

스킬은 슬래시(`/agent-system:save-context`)로도, 자연어("컨텍스트 저장해줘")로도 호출된다.

## 설치 (각 머신에서)

```
/plugin marketplace add NonUlti/agent-system
/plugin install agent-system@agent-system
```

설치 후 Claude Code를 재시작하면 적용된다. (user scope가 기본)

## 사용

- 작업을 멈출 때: `/agent-system:save-context`
- 이어서 할 때(새 세션): `/agent-system:load-context`

`save-context`는 `.claude/HANDOFF.md`만 쓰고 커밋하지 않는다. 다른 머신으로 옮기려면 그 파일을 직접 커밋·push 한다.

## 업데이트 (내용 수정 후)

1. `skills/` 등 수정
2. 버전 bump — `.claude-plugin/plugin.json`과 `marketplace.json`의 `version` **둘 다** 같은 값으로
3. `claude plugin validate .` (가능하면 `--strict`)
4. `git commit` → `claude plugin tag --push` (버전 일치 검증 + `agent-system--v<버전>` 태그 + push)
5. `git push`
6. 각 머신: `/plugin marketplace update agent-system` → `/plugin update agent-system` → 재시작

## 개발/로컬 테스트

push 전 로컬 작업 트리로 검증:
```
claude plugin marketplace add ~/agent-system
claude plugin install agent-system@agent-system
```
주의: install은 커밋 SHA로 스냅샷을 뜬다. 파일을 고쳤다면 커밋 + 버전 bump 후 marketplace update / plugin update 하고 세션을 재시작해야 반영된다.
```

- [ ] **Step 2: 커밋**

```bash
cd ~/agent-system && git add README.md && \
git commit -m "docs: README 설치·사용·업데이트 안내

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 5: 로컬 설치 + 라운드트립 검증

플러그인이 실제로 로드되고 두 스킬이 동작하는지 확인한다. **install은 스냅샷이므로 앞 Task들의 커밋이 끝난 상태여야 한다.**

- [ ] **Step 1: 최종 validate**

```bash
cd ~/agent-system && claude plugin validate . --strict
```
Expected: `✔ Validation passed`.

- [ ] **Step 2: 로컬 마켓플레이스 등록 + 설치**

```bash
claude plugin marketplace add ~/agent-system
claude plugin install agent-system@agent-system
claude plugin details agent-system
```
Expected: `details`가 skills 2개(save-context, load-context)를 인벤토리에 표시.

- [ ] **Step 3: 새 세션에서 컴포넌트 노출 확인 (사용자 수행)**

Claude Code를 재시작한 뒤 새 세션에서:
- `/agent-system:save-context`, `/agent-system:load-context`가 슬래시 자동완성에 뜨는지
- 임의 프로젝트에서 `/agent-system:save-context` 실행 → `.claude/HANDOFF.md`가 템플릿대로 생성되는지 (`cat .claude/HANDOFF.md`로 확인)

- [ ] **Step 4: 라운드트립 (사용자 수행)**

- 핸드오프가 있는 프로젝트에서 **새 세션** 시작 → `/agent-system:load-context` → 목표/현재 상태/다음 할 일 브리핑이 정확한지, 저장 이후 커밋이 있으면 그걸 짚어주는지 확인.
- HANDOFF.md가 **없는** 프로젝트에서 `/agent-system:load-context` → "저장된 핸드오프가 없습니다" 안내가 나오는지 확인.

- [ ] **Step 5: GitHub push**

```bash
cd ~/agent-system && git push origin master
```
(원격 기본 브랜치명이 `main`이면 `git push origin HEAD` 사용. 현재 로컬 브랜치는 `master`.)

- [ ] **Step 6: (선택) 정식 설치 경로 전환**

로컬 마켓플레이스를 GitHub 것으로 교체해 정식 경로까지 검증:
```bash
claude plugin marketplace remove agent-system
claude plugin marketplace add NonUlti/agent-system
claude plugin install agent-system@agent-system
```

---

## 완료 기준

- [ ] `claude plugin validate . --strict` 통과
- [ ] `claude plugin details agent-system`에 skills 2개 표시
- [ ] 새 세션에서 `/agent-system:save-context`로 `.claude/HANDOFF.md` 생성됨
- [ ] 새 세션에서 `/agent-system:load-context`가 핸드오프 브리핑 + git 검증 수행
- [ ] HANDOFF 없는 프로젝트에서 load-context가 안내 메시지 출력
- [ ] GitHub에 push 완료
