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
