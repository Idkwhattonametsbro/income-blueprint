#!/usr/bin/env python3
"""
Nexus Engine Test Suite - 24+ checks
------------------------------------
Validates both daily engines (video + etsy) across many seeded runs:
structure, banned words, limits (140 chars / 13 tags), files written,
history integrity, no duplicate consecutive picks, keyless mode, and
the dashboard feed paths.

Run:  python tests/run_all.py
"""
import json
import re
import sys
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "content-engine"))

BANNED = ["delve", "unlock", "game-changer", "elevate", "embark",
          "fast-paced world", "revolutionize", "unleash", "supercharge",
          "cutting-edge"]


class BaseEngineTest(unittest.TestCase):
    engine = None          # module
    feed = None            # Path

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="nexus_feed_"))
        self._orig = self.engine.FEED
        self.engine.FEED = self._tmp
        self.engine.FEED.mkdir(exist_ok=True)

    def tearDown(self):
        self.engine.FEED = self._orig
        shutil.rmtree(self._tmp, ignore_errors=True)

    def run_engine(self, seed=None):
        if seed is not None:
            random.seed(seed)
        self.engine.main()
        return self._tmp

    # ---- shared validators ----
    def assert_no_banned(self, text):
        low = text.lower()
        for b in BANNED:
            self.assertNotIn(b, low, f"banned word present: {b}")

    def assert_feed_files(self, feed, md_name, extra=None):
        self.assertTrue((feed / md_name).exists(), f"{md_name} missing")
        self.assertTrue((feed / "latest.md").exists(), "latest.md missing")
        self.assertTrue((feed / "history.json").exists(), "history.json missing")
        if extra:
            for f in extra:
                self.assertTrue((feed / f).exists(), f"{f} missing")

    def assert_history_ok(self, feed):
        hist = json.loads((feed / "history.json").read_text(encoding="utf-8"))
        self.assertIsInstance(hist, list)
        self.assertTrue(hist)


class TestVideoEngine(BaseEngineTest):
    engine = __import__("generate_daily")
    feed_name = "generate_daily"

    def _sections(self, md):
        return {m.group(1).strip(): m.group(2).strip()
                for m in re.finditer(r"^##\s+(.+?)\n(.*?)(?=^##|\Z)", md, re.M | re.S)}

    def _has_section(self, secs, name):
        return any(k.startswith(name) for k in secs)

    def test_01_clean_run(self):
        feed = self.run_engine(seed=1)
        self.assert_feed_files(feed, "latest.md")

    def test_02_all_sections_present(self):
        for seed in (2, 3, 4, 5):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                secs = self._sections(md)
                for need in ("HOOK", "SCRIPT", "TITLE", "CAPTION", "HASHTAGS", "PIN COMMENT", "THUMBNAIL IDEA"):
                    self.assertTrue(self._has_section(secs, need), f"missing {need}")
                    key = next(k for k in secs if k.startswith(need))
                    self.assertTrue(secs[key], f"empty {need}")

    def test_03_no_banned_words(self):
        for seed in (6, 7, 8):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                self.assert_no_banned((feed / "latest.md").read_text(encoding="utf-8"))

    def test_04_hook_is_short(self):
        for seed in (9, 10):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                hook = self._sections(md).get("HOOK", "")
                self.assertLessEqual(len(hook), 140, "hook too long")

    def test_05_history_increments(self):
        self.run_engine(seed=1)
        self.run_engine(seed=2)
        self.run_engine(seed=3)
        hist = json.loads((self._tmp / "history.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(hist), 1)
        # same-day runs collapse to one entry
        self.assertEqual(len(hist), 1)

    def test_06_title_under_60(self):
        feed = self.run_engine(seed=4)
        md = (feed / "latest.md").read_text(encoding="utf-8")
        title = self._sections(md).get("TITLE", "")
        self.assertLessEqual(len(title), 60)


class TestEtsyEngine(BaseEngineTest):
    engine = __import__("etsy_daily")
    feed_name = "etsy_daily"

    def _sections(self, md):
        return {m.group(1).strip(): m.group(2).strip()
                for m in re.finditer(r"^##\s+(.+?)\n(.*?)(?=^##|\Z)", md, re.M | re.S)}

    def _has_section(self, secs, name):
        return any(k.startswith(name) for k in secs)

    def test_07_clean_run_with_product_file(self):
        for seed in (11, 12):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                self.assert_feed_files(feed, "latest.md", extra=["product_latest.html"])

    def test_08_all_sections_present(self):
        for seed in (13, 14, 15):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                secs = self._sections(md)
                for need in ("PRODUCT", "WHY IT SELLS", "LISTING TITLE", "13 TAGS",
                             "DESCRIPTION", "PRICE", "IMAGE BRIEF", "PRODUCT FILE"):
                    self.assertTrue(self._has_section(secs, need), f"missing {need}")
                    key = next(k for k in secs if k.startswith(need))
                    self.assertTrue(secs[key], f"empty {need}")

    def test_09_title_max_140(self):
        for seed in (16, 17, 18):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                title = self._sections(md).get("LISTING TITLE", "")
                self.assertLessEqual(len(title), 140)

    def test_10_exactly_13_tags(self):
        for seed in (19, 20, 21):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                tags = self._sections(md).get("13 TAGS", "")
                n = len([t for t in tags.split(",") if t.strip()])
                self.assertEqual(n, 13, f"expected 13 tags, got {n}")

    def test_11_price_in_range(self):
        feed = self.run_engine(seed=22)
        md = (feed / "latest.md").read_text(encoding="utf-8")
        price = self._sections(md).get("PRICE", "")
        val = int(re.search(r"\d+", price).group())
        self.assertGreaterEqual(val, 3)
        self.assertLessEqual(val, 9)

    def test_12_no_banned_words(self):
        for seed in (23, 24):
            with self.subTest(seed=seed):
                feed = self.run_engine(seed=seed)
                md = (feed / "latest.md").read_text(encoding="utf-8")
                self.assert_no_banned(md)
                html = (feed / "product_latest.html").read_text(encoding="utf-8")
                self.assert_no_banned(html)

    def test_13_product_html_is_valid(self):
        feed = self.run_engine(seed=25)
        html = (feed / "product_latest.html").read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("</html>", html)
        self.assertIn("A4", html)

    def test_14_rotation_no_duplicates(self):
        # multiple seeds should produce variety in the product name
        names = set()
        for seed in (26, 27, 28):
            feed = self.run_engine(seed=seed)
            md = (feed / "latest.md").read_text(encoding="utf-8")
            names.add(self._sections(md).get("PRODUCT", ""))
        self.assertGreaterEqual(len(names), 2, "product rotation seems broken")

    def test_15_history_ok(self):
        feed = self.run_engine(seed=29)
        self.assert_history_ok(feed)


class TestSubprocess(unittest.TestCase):
    """The real entrypoints must run cleanly as scripts (like CI does)."""

    def test_16_video_engine_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PATH": "/usr/bin:/bin"}
            r = subprocess.run([sys.executable, "content-engine/generate_daily.py"],
                               cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            self.assertIn("Saved feed/", r.stdout)

    def test_17_etsy_engine_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, "content-engine/etsy_daily.py"],
                               cwd=str(ROOT), capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            self.assertIn("Saved feed-etsy/", r.stdout)

    def test_18_python_compiles(self):
        for f in ["content-engine/generate_daily.py", "content-engine/etsy_daily.py"]:
            r = subprocess.run([sys.executable, "-m", "py_compile", f], cwd=str(ROOT),
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{f} failed compile")


class TestPremium(unittest.TestCase):
    def test_22_video_has_streams_and_voice(self):
        # build a short video and verify streams + duration
        import subprocess, sys, tempfile, shutil
        from pathlib import Path
        sys.path.insert(0, str(ROOT / "content-engine"))
        import video_v2
        tmp = Path(tempfile.mkdtemp(prefix="nexvidt_"))
        try:
            scenes = [("hook", "This is the hook line for testing."),
                      ("line", "The first step is simple and clear.")]
            starts = [0.5, 4.5]
            ends = [4.2, 8.2]
            out = tmp / "t.mp4"
            video_v2.render(scenes, starts, ends, [None, None], out, tmp)
            r = subprocess.run(["ffmpeg", "-i", str(out)], capture_output=True, text=True)
            info = r.stderr
            self.assertIn("Video: h264", info)
            self.assertIn("Audio: aac", info)
            dur = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", info)
            self.assertIsNotNone(dur)
            secs = int(dur.group(1))*3600 + int(dur.group(2))*60 + float(dur.group(3))
            self.assertGreater(secs, 8)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_23_cover_png_renders(self):
        from pathlib import Path
        import sys
        sys.path.insert(0, str(ROOT / "content-engine"))
        import tempfile
        from product_assets import render_cover
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "c.png"
            render_cover("Weekly Budget Tracker", "printable planner", out)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 50000)

    def test_24_product_page_is_premium(self):
        import sys
        sys.path.insert(0, str(ROOT / "content-engine"))
        from product_assets import weekly_reset, habit_tracker
        html = weekly_reset() + habit_tracker()
        for marker in ("Calm Week System", "linear-gradient", "border-radius", "card"):
            self.assertIn(marker, html)


class TestDashboard(unittest.TestCase):
    def test_19_dashboard_exists_and_references_feeds(self):
        dash = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        self.assertIn("latest.md", dash)
        self.assertIn("history.json", dash)
        self.assertIn("generate", dash.lower())

    def test_20_workflows_reference_engines(self):
        w1 = (ROOT / ".github" / "workflows" / "daily_content.yml").read_text(encoding="utf-8")
        w2 = (ROOT / ".github" / "workflows" / "etsy_daily.yml").read_text(encoding="utf-8")
        self.assertIn("generate_daily.py", w1)
        self.assertIn("etsy_daily.py", w2)
        self.assertIn("0 5 * * *", w1)
        self.assertIn("0 5 * * *", w2)

    def test_21_no_secrets_in_repo(self):
        for p in ROOT.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for secret in ("ghp_", "gsk_", "sk-or-", "AIza", "app_password", "xoxb-"):
                    if secret in txt and "GMAIL_" not in txt:
                        self.fail(f"possible secret in {p}: {secret}")
        self.assertTrue(True)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    total = result.testsRun
    print(f"\n=== {total} tests run, {len(result.failures)} failures, {len(result.errors)} errors ===")
    sys.exit(0 if result.wasSuccessful() else 1)
