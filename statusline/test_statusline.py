import os
import re
import sys
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


if __name__ == "__main__":
    unittest.main()
