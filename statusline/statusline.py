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
