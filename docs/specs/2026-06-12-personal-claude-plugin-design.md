# 개인 공통 Claude Code 플러그인 — 설계

- 날짜: 2026-06-12
- 상태: 확정 (이름: agent-system / repo: NonUlti/agent-system)

## 목적

여러 프로젝트·머신에서 공통으로 쓸 개인 플러그인을 만든다.
GitHub public repo **하나**가 플러그인이자 셀프 마켓플레이스 역할을 한다.
(팀 플러그인 soop-membership과 동일한 패턴: marketplace.json의 `"source": "./"`)

장기적으로 Claude Code 외 다른 코딩 에이전트(Codex, Gemini CLI 등)에서도
같은 repo를 재사용한다. superpowers가 한 repo로 8개 도구를 지원하는 것과
같은 방식: skills/는 공유하고, 도구별 어댑터 파일만 루트에 추가한다.

## 결정 사항

| 항목 | 결정 |
|------|------|
| repo 구조 | 단일 repo = 플러그인 + 셀프 마켓플레이스 |
| 공개 범위 | Public GitHub repo |
| 설치 범위 | user scope (모든 프로젝트에서 사용) |
| 담을 것 | 작업 컨벤션 스킬 + 슬래시 커맨드 + 훅 — 뼈대 먼저, 내용은 점진 추가 |
| 멀티툴 전략 | 공통 가치는 skills/에 집중 (도구 중립 포맷). commands/·hooks/는 Claude 전용 편의 기능. 도구별 어댑터(AGENTS.md, gemini-extension.json 등)는 해당 도구를 실제 사용할 때 추가 |
| 이름 | **agent-system** (repo명과 일치 — 설치 명령이 `agent-system@agent-system`으로 직관적) |

## repo 구조

```
<repo>/
├── .claude-plugin/
│   ├── plugin.json        # name, version(semver), description, author
│   └── marketplace.json   # name, owner, description, plugins: [{ name, source: "./", version }]
├── skills/
│   ├── save-context/SKILL.md   # 시드 스킬 (슬래시 호출 + 자동 발동)
│   └── load-context/SKILL.md
├── hooks/
│   └── hooks.json          # 처음엔 빈 구조 {"hooks": {}}
├── .gitignore              # *-workspace/ (skill-creator eval 산출물)
└── README.md               # 설치 방법 안내

# (커맨드는 두지 않음 — 스킬이 슬래시 호출/자동 발동 둘 다 되어 commands/ 불필요)

# (미래 — 해당 도구 사용 시작 시 추가, repo 재구성 불필요)
# ├── AGENTS.md             # Codex 어댑터
# ├── gemini-extension.json # Gemini CLI 어댑터
# └── GEMINI.md
```

### 매니페스트 주의점 (구현 조사로 실증)

- **버전 이중화:** plugin.json과 marketplace.json **두 곳에 중복**. 불일치 시 plugin.json이 install 시 우선. 릴리스 시 `claude plugin tag`이 두 파일 일치를 검증하고 `{이름}--v{버전}` git 태그를 만들어 주므로 릴리스 절차에 반드시 포함.
- **`--strict` 깔끔 통과 조건:** plugin.json에 `author`, marketplace.json에 top-level `description`이 없으면 경고가 뜨고 `validate --strict`는 실패한다. 둘 다 처음부터 넣는다.
- **`claude plugin init`은 쓰지 않는다:** init은 `~/.claude/skills/<name>/`에 스캐폴딩하는 별도 메커니즘이라 self-marketplace repo 구조와 맞지 않는다. 매니페스트는 **수동 생성**한다.
- **빈 `{"hooks": {}}`는 validate 통과** 확인됨.

## 시드 콘텐츠 (최소 동작 검증용)

1. **스킬 2개** — `save-context` / `load-context` (세션 핸드오프). 커맨드는 두지 않음 —
   스킬이 그 자체로 `/agent-system:<스킬>` 슬래시 호출 + 자동 발동 둘 다 되기 때문.
   상세 설계: [2026-06-12-save-load-context-design.md](./2026-06-12-save-load-context-design.md)
2. **훅** — 빈 `hooks.json` 뼈대만. 자동 실행은 부작용 위험이 있으므로 내용 확정 후 추가

## 구축 순서

1. 매니페스트 **수동 생성** (.claude-plugin/plugin.json + marketplace.json) + 빈 hooks.json + .gitignore
2. `claude plugin validate .` (가능하면 `--strict`)로 매니페스트 검증
3. `/skill-creator`로 시드 스킬 2개 작성 (save-context, load-context)
4. 로컬 마켓플레이스 테스트 — `claude plugin marketplace add ~/agent-system` → install → 새 세션에서 스킬·슬래시 호출 확인
5. GitHub public repo에 push
6. 각 머신: `/plugin marketplace add NonUlti/agent-system` → `/plugin install agent-system@agent-system` (user scope)

## 운영(업데이트) 사이클

수정 → 버전 bump (두 json 모두) → `claude plugin tag` 검증·태깅 → push → 각 머신에서 `/plugin update <이름>`

## 검증 방법

- `claude plugin validate .` 통과
- 설치 후 새 세션에서: 스킬 자동 발동 + `/agent-system:save-context` 슬래시 호출 가능 확인
- `claude plugin details agent-system` 으로 구성요소 인벤토리 확인
- 라운드트립: 한 세션 `/agent-system:save-context` → 새 세션 `/agent-system:load-context`로 복원·검증 동작 확인

## 범위 제외 (YAGNI)

- 마켓플레이스 repo 분리 — 플러그인이 여러 개로 늘어나면 그때 marketplace.json 항목 추가로 해결
- CI 검증 파이프라인 — 초기엔 validate 수동 실행으로 충분
- MCP 서버, 서브에이전트 — 필요해지면 추가
- Codex/Gemini 어댑터 파일 — 해당 도구를 실제로 쓰기 시작할 때 추가 (구조는 이미 호환)
- 모노레포식 도구별 디렉토리 분리(claude/, codex/, shared/) + 빌드 스크립트 — superpowers도 단일 루트로 충분히 운영함
