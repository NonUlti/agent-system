import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statusline as sl

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip(s):
    return ANSI.sub("", s)


class TestStatusline(unittest.TestCase):
    def test_format_tokens(self):
        self.assertEqual(sl.format_tokens(None), "—")
        self.assertEqual(sl.format_tokens(0), "0")
        self.assertEqual(sl.format_tokens(500), "500")
        self.assertEqual(sl.format_tokens(999), "999")
        self.assertEqual(sl.format_tokens(1000), "1k")
        self.assertEqual(sl.format_tokens(1500), "1.5k")
        self.assertEqual(sl.format_tokens(15000), "15k")
        self.assertEqual(sl.format_tokens(15500), "15.5k")
        self.assertEqual(sl.format_tokens(1_200_000), "1.2M")
        self.assertEqual(sl.format_tokens(2_000_000), "2M")

    def test_bar_fill(self):
        self.assertEqual(sl.bar_fill(0), 0)
        self.assertEqual(sl.bar_fill(8), 2)     # 0.08*20=1.6 -> round 2
        self.assertEqual(sl.bar_fill(50), 10)
        self.assertEqual(sl.bar_fill(80), 16)
        self.assertEqual(sl.bar_fill(100), 20)
        self.assertEqual(sl.bar_fill(120), 20)  # 클램프
        self.assertEqual(sl.bar_fill(-5), 0)    # 클램프

    def test_pick_color(self):
        self.assertEqual(sl.pick_color(0), sl.GREEN)
        self.assertEqual(sl.pick_color(49), sl.GREEN)
        self.assertEqual(sl.pick_color(50), sl.ORANGE)
        self.assertEqual(sl.pick_color(79), sl.ORANGE)
        self.assertEqual(sl.pick_color(80), sl.RED)
        self.assertEqual(sl.pick_color(100), sl.RED)

    def test_make_bar(self):
        bar = sl.make_bar(8)
        # 색코드 제거 후 20칸, 앞 2칸 채움
        self.assertEqual(strip(bar), "██" + "░" * 18)
        self.assertIn(sl.GREEN, bar)  # 8% -> 초록


    def test_branch_from_worktree(self):
        data = {"workspace": {"git_worktree": "feature-x"}}
        self.assertEqual(sl.branch_from_worktree(data), "feature-x")
        self.assertIsNone(sl.branch_from_worktree({}))
        self.assertIsNone(sl.branch_from_worktree({"workspace": {}}))

    def test_branch_from_git_non_repo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(sl.branch_from_git(d))
        self.assertIsNone(sl.branch_from_git(None))

    def test_branch_from_git_real_repo(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-b", "my-branch", d],
                           capture_output=True, check=True)
            self.assertEqual(sl.branch_from_git(d), "my-branch")

    def test_resolve_branch_prefers_worktree(self):
        data = {"workspace": {"git_worktree": "wt"}, "cwd": "/tmp"}
        self.assertEqual(sl.resolve_branch(data), "wt")


if __name__ == "__main__":
    unittest.main()
