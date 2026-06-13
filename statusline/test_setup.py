import json
import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP = os.path.join(REPO, "setup-statusline.sh")
SRC = os.path.join(REPO, "statusline", "statusline.py")


class TestSetup(unittest.TestCase):
    def _run(self, home):
        env = dict(os.environ, HOME=home)
        return subprocess.run(["bash", SETUP], env=env,
                              capture_output=True, text=True)

    def test_fresh_install(self):
        with tempfile.TemporaryDirectory() as home:
            r = self._run(home)
            self.assertEqual(r.returncode, 0, r.stderr)
            dest = os.path.join(home, ".claude", "statusline.py")
            self.assertTrue(os.path.islink(dest))
            self.assertEqual(os.path.realpath(dest), os.path.realpath(SRC))
            with open(os.path.join(home, ".claude", "settings.json")) as f:
                d = json.load(f)
            self.assertEqual(d["statusLine"]["type"], "command")
            self.assertEqual(d["statusLine"]["command"], "~/.claude/statusline.py")

    def test_preserves_existing_keys_and_backs_up(self):
        with tempfile.TemporaryDirectory() as home:
            cdir = os.path.join(home, ".claude")
            os.makedirs(cdir)
            with open(os.path.join(cdir, "settings.json"), "w") as f:
                json.dump({"theme": "dark"}, f)
            r = self._run(home)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(os.path.join(cdir, "settings.json")) as f:
                d = json.load(f)
            self.assertEqual(d["theme"], "dark")        # 기존 키 보존
            self.assertIn("statusLine", d)              # 새 키 머지
            backups = os.listdir(os.path.join(cdir, "backups"))
            self.assertTrue(any(b.startswith("settings.json.bak.") for b in backups))


if __name__ == "__main__":
    unittest.main()
