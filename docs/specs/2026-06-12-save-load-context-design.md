# save-context / load-context — 설계

- 날짜: 2026-06-12
- 상태: 확정
- 상위 문서: [2026-06-12-personal-claude-plugin-design.md](./2026-06-12-personal-claude-plugin-design.md)

## 목적

세션 핸드오프. 현재 세션에서 하던 작업의 상태(목표, 진행 상황, 결정 사항, 다음 할 일)를
파일로 저장하고, 새 세션에서 이어서 작업한다. 컨텍스트 한도가 차거나
내일 이어서 할 때 사용한다.

agent-system 플러그인의 첫 시드 콘텐츠이며, 이후 스킬들의 형식 견본이 된다.

## 결정 사항

| 항목 | 결정 | 비고 |
|------|------|------|
| 컨텍스트의 의미 | 세션 핸드오프 (작업 상태 저장·복원) | 프로젝트 지식 베이스 아님 |
| 저장 위치 | 작업 중인 프로젝트 repo 안 `.claude/HANDOFF.md` | 프로젝트별 자연 분리 |
| 파일 관리 | 단일 파일 덮어쓰기 | 이력은 필요 시 git이 담당 |
| 호출 방식 | **스킬만 2개** (commands/ 없음) | 스킬은 그 자체로 `/agent-system:save-context` 슬래시 호출 + 자동 발동 둘 다 됨 — 아래 결정 변경 노트 참조 |
| 커밋 | 스킬은 파일만 쓰고 커밋하지 않음 | 머신 간 이동이 필요할 때만 사용자가 직접 커밋 |
| 구현 도구 | /skill-creator로 스킬 작성 | |

### 결정 변경 노트 (2026-06-13)

브레인스토밍 당시엔 Q3-C "슬래시 커맨드(진입점) + 스킬(본체)"로 정했으나,
구현 조사에서 다음이 확인되어 **스킬만 2개**로 변경한다:

- 스킬은 그 자체로 `/agent-system:save-context`처럼 슬래시 호출이 된다
  (`/superpowers:brainstorming` 호출이 실증). 따라서 커맨드 wrapper는 기능 중복.
- 공식 `plugin-dev` 가이드가 `commands/`를 "legacy, 신규는 skills/로" 라고 명시.
  (단 commands/는 폐기 아님 — 여전히 동작하고 공식 플러그인 다수가 사용 중)
- 스킬만 두면 ① 자동 발동 ② 본문 지연 로드(토큰 절약) ③ 멀티툴 재사용(skills/만)이라는
  원래 설계 목표("공통 가치는 skills/에 집중")에 더 부합.

## 구조

```
agent-system/
├── .claude-plugin/
│   ├── plugin.json        # name, version, description, author (author 없으면 --strict 경고)
│   └── marketplace.json   # name, owner, description(없으면 --strict 경고), plugins:[{name, source:"./", version}]
├── skills/
│   ├── save-context/SKILL.md   # 절차 본체 + 슬래시 진입점 (description으로 자동 발동도)
│   └── load-context/SKILL.md   # 읽기 + 검증 규칙
├── hooks/hooks.json       # {"hooks": {}} — 빈 뼈대 (validate 통과 확인됨)
├── docs/specs/            # 설계 문서
├── .gitignore             # *-workspace/ (skill-creator eval 산출물 차단)
└── README.md              # 설치 안내
```

## save-context 동작

1. 현재 세션의 작업 내용을 정리해 `.claude/HANDOFF.md`에 **덮어쓰기**
   (`.claude/` 디렉토리가 없으면 생성)
2. 커밋·push 하지 않는다 — 파일 쓰고 끝
3. 저장 완료 후 사용자에게 파일 경로를 알려준다

### HANDOFF.md 구조

```markdown
# HANDOFF
<!-- 메타데이터: 저장 시각 / 브랜치 / 마지막 커밋 해시 -->
<!-- git repo가 아니면 git 항목 생략 -->

## 목표          ← 필수. 이 작업이 끝나면 뭐가 되어 있어야 하는가
## 현재 상태      ← 필수. 어디까지 했고, 지금 동작하는가
## 다음 할 일     ← 필수. 구체적 순서. 첫 항목은 바로 실행 가능한 수준으로
## 결정 사항      ← 선택. 무엇을 왜 그렇게 정했나 (다시 논쟁하지 않도록)
## 주의사항      ← 선택. 함정, 미해결 이슈, 건드리면 안 되는 것
```

- 선택 섹션은 해당 내용이 있을 때만 쓴다. 빈 섹션을 억지로 채우지 않는다
- 실패 모드 두 가지를 모두 피한다: 너무 부실해서 복원 불가 / 너무 장황해서 load 때 토큰 낭비

## load-context 동작

1. `.claude/HANDOFF.md` 읽기 — 없으면 "저장된 핸드오프가 없습니다" 안내하고 종료
2. **현실 검증** — 핸드오프는 "쓰인 시점의 진실"이므로 현재 상태와 대조:
   - 메타데이터의 커밋·브랜치 vs 현재 git 상태 (저장 이후 커밋 유무, 브랜치 변경)
   - 문서에 언급된 파일들이 실제 존재하는지
   - 어긋나는 점은 브리핑에 포함
3. 브리핑 — 목표 / 현재 상태 / 다음 할 일 요약 후 **지시 대기** (자동 재개하지 않음)

## 검증 방법

플러그인 로컬 설치(② 로컬 마켓플레이스) 후 실제 라운드트립:

1. 한 세션에서 작업하다 `/save-context` → `.claude/HANDOFF.md` 내용 확인
2. 새 세션에서 `/load-context` → 브리핑이 정확한지, 검증이 동작하는지 확인
3. HANDOFF.md 없는 프로젝트에서 `/load-context` → 안내 메시지 확인

## 범위 제외 (YAGNI)

- 자동 커밋/push — 당분간 한 머신에서만 사용
- 타임스탬프 이력, 작업명 슬롯 — 단일 파일로 시작, 병행 작업이 늘면 재검토
- 세션 종료 훅으로 자동 저장 — 자동 실행 부작용 원칙(상위 문서)에 따라 보류
