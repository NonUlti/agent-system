---
description: statusLine(상태바)를 ~/.claude에 설치 — 번들된 setup-statusline.sh 실행
disable-model-invocation: true
---

이 플러그인에 번들된 statusLine 설치기를 실행해 상태바를 설치한다.

1. Bash로 실행한다: `bash "$CLAUDE_PLUGIN_ROOT/setup-statusline.sh"`
   - `$CLAUDE_PLUGIN_ROOT`는 Claude Code가 플러그인 커맨드에 제공하는 설치 경로 환경변수다.
   - 만약 셸에 `$CLAUDE_PLUGIN_ROOT`가 없으면, `~/.claude/plugins/cache/agent-system/`(또는 `~/.claude/plugins/marketplaces/agent-system`) 아래 설치 경로를 찾아 그 안의 `setup-statusline.sh`를 실행한다.
   - 이 스크립트는 번들된 `statusline/statusline.py`를 `~/.claude/statusline.py`로 심링크하고, `~/.claude/settings.json`에 `statusLine` 키를 머지한다(기존 settings.json은 `~/.claude/backups/`로 백업).
2. 스크립트 출력(심링크 경로 · 설정 경로)을 사용자에게 그대로 전한다.
3. 마지막에 안내한다: **"새 세션 또는 재시작 후 입력창 아래에 상태바가 나타납니다."**

스크립트가 0이 아닌 코드로 종료하면 출력을 보여주고 원인을 설명한다. 그 외 다른 작업은 하지 않는다.
