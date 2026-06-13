#!/usr/bin/env python3
"""agent-system custom statusLine renderer (stdlib only)."""

import json
import subprocess
import sys

# --- 설정 상수 (언제든 조정 가능) ---
BAR_WIDTH = 20

# 256-color ANSI (주황은 16색에 없어 256색 사용)
GREEN = "\033[38;5;40m"
ORANGE = "\033[38;5;208m"
RED = "\033[38;5;196m"
DIM = "\033[2m"
RESET = "\033[0m"

# 윗줄 항목 강조색 (기본값 — 취향에 맞게 조정)
BR_COLOR = "\033[36m"          # 브랜치: cyan
MODEL_COLOR = "\033[38;5;75m"  # 모델: blue
EFFORT_COLOR = "\033[38;5;245m"  # effort: grey
COST_COLOR = DIM               # 비용: dim

SEP = f"{DIM} · {RESET}"


def format_tokens(n):
    """토큰 수를 축약 문자열로. None -> '—'."""
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        s = f"{n / 1_000_000:.1f}M"
    elif n >= 1000:
        s = f"{n / 1000:.1f}k"
    else:
        return str(n)
    return s.replace(".0M", "M").replace(".0k", "k")


def bar_fill(pct, width=BAR_WIDTH):
    """채울 칸 수. [0, width]로 클램프."""
    try:
        p = float(pct)
    except (TypeError, ValueError):
        p = 0.0
    filled = round(p / 100 * width)
    return max(0, min(width, filled))


def pick_color(pct):
    """사용 %에 따른 단색. <50 초록 / <80 주황 / 그 이상 빨강."""
    try:
        p = float(pct)
    except (TypeError, ValueError):
        p = 0.0
    if p < 50:
        return GREEN
    if p < 80:
        return ORANGE
    return RED


def make_bar(pct, width=BAR_WIDTH):
    """색이 입혀진 20칸 막대 문자열."""
    fill = bar_fill(pct, width)
    color = pick_color(pct)
    return f"{color}{'█' * fill}{'░' * (width - fill)}{RESET}"


def branch_from_worktree(data):
    return (data.get("workspace") or {}).get("git_worktree")


def branch_from_git(cwd):
    if not cwd:
        return None
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=2,
        )
    except Exception:
        return None
    branch = out.stdout.strip()
    return branch or None


def resolve_branch(data):
    return branch_from_worktree(data) or branch_from_git(data.get("cwd"))


def _c(color, text):
    return f"{color}{text}{RESET}"


def render(data):
    """파싱된 dict -> 최대 2줄 문자열. 사용 가능한 칸만 ` · `로 잇고,
    빈 줄은 만들지 않는다."""
    if not isinstance(data, dict):
        data = {}

    seg1 = []
    branch = resolve_branch(data)
    if branch:
        seg1.append(_c(BR_COLOR, branch))
    model = (data.get("model") or {}).get("display_name")
    if model:
        seg1.append(_c(MODEL_COLOR, model))
    effort = (data.get("effort") or {}).get("level")
    if effort:
        seg1.append(_c(EFFORT_COLOR, effort))
    cost = (data.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        seg1.append(_c(COST_COLOR, f"${cost:.3f}"))

    seg2 = []
    cw = data.get("context_window") or {}
    pct = cw.get("used_percentage")
    if pct is not None:
        seg2.append(f"{make_bar(pct)} {_c(pick_color(pct), str(round(pct)) + '%')}")
    if cw:
        toks = f"↑{format_tokens(cw.get('total_input_tokens'))} " \
               f"↓{format_tokens(cw.get('total_output_tokens'))}"
        seg2.append(_c(DIM, toks))
    rl = ((data.get("rate_limits") or {}).get("five_hour") or {}).get("used_percentage")
    if rl is not None:
        seg2.append(_c(DIM, f"5h {round(rl)}%"))

    lines = []
    if seg1:
        lines.append(SEP.join(seg1))
    if seg2:
        lines.append(SEP.join(seg2))
    return "\n".join(lines)


def main():
    raw = ""
    data = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
    except Exception:
        data = {}
    try:
        out = render(data)
    except Exception:
        out = ""
        if isinstance(data, dict):
            out = (data.get("model") or {}).get("display_name") or ""
    if out:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
