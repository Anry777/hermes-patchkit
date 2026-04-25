import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
UPDATE = REPO_ROOT / "scripts" / "update.py"
TUI = REPO_ROOT / "scripts" / "tui.py"


class UpdateScriptTests(unittest.TestCase):
    def test_update_dry_run_classifies_patches_without_touching_live_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upstream = root / "upstream"
            live = root / "live-hermes"
            patchkit = root / "patchkit-fixture"
            reports = root / "reports"
            patchkit.mkdir()
            (patchkit / "patches").mkdir()
            (patchkit / "profiles").mkdir()
            (patchkit / "manifests").mkdir()

            upstream.mkdir()
            self.run_git(upstream, "init", "-b", "main")
            self.configure_git(upstream)
            (upstream / "clean.txt").write_text("base clean\n", encoding="utf-8")
            (upstream / "upstreamed.txt").write_text("base upstreamed\n", encoding="utf-8")
            (upstream / "conflict.txt").write_text("base conflict\n", encoding="utf-8")
            self.run_git(upstream, "add", ".")
            self.run_git(upstream, "commit", "-m", "base")
            base_head = self.run_git(upstream, "rev-parse", "HEAD").stdout.strip()

            clean_patch = self.make_patch(upstream, "clean.txt", "patched clean\n")
            upstreamed_patch = self.make_patch(upstream, "upstreamed.txt", "fixed upstreamed\n")
            conflict_patch = self.make_patch(upstream, "conflict.txt", "patched conflict\n")

            (patchkit / "patches" / "clean.patch").write_text(clean_patch, encoding="utf-8")
            (patchkit / "patches" / "upstreamed.patch").write_text(upstreamed_patch, encoding="utf-8")
            (patchkit / "patches" / "conflict.patch").write_text(conflict_patch, encoding="utf-8")
            manifest = patchkit / "manifests" / "test.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": str(upstream), "ref": "main"},
                        "patches": [
                            {"id": "clean-fix", "file": "patches/clean.patch", "status": "exported"},
                            {"id": "already-upstreamed", "file": "patches/upstreamed.patch", "status": "exported"},
                            {"id": "needs-refresh", "file": "patches/conflict.patch", "status": "exported"},
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            profile = patchkit / "profiles" / "test.json"
            profile.write_text(
                json.dumps({"name": "test", "patches": ["clean-fix", "already-upstreamed", "needs-refresh"]}, indent=2) + "\n",
                encoding="utf-8",
            )

            (upstream / "upstreamed.txt").write_text("fixed upstreamed\n", encoding="utf-8")
            (upstream / "conflict.txt").write_text("different upstream change\n", encoding="utf-8")
            self.run_git(upstream, "add", ".")
            self.run_git(upstream, "commit", "-m", "upstream moved")

            subprocess.run(["git", "clone", str(upstream), str(live)], text=True, capture_output=True, check=True)
            self.configure_git(live)
            self.run_git(live, "checkout", base_head)
            live_head_before = self.run_git(live, "rev-parse", "HEAD").stdout.strip()

            result = subprocess.run(
                [
                    sys.executable,
                    str(UPDATE),
                    "--repo",
                    str(live),
                    "--manifest",
                    str(manifest),
                    "--profile",
                    str(profile),
                    "--upstream",
                    "origin/main",
                    "--report-dir",
                    str(reports),
                    "--no-color",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("clean-fix", result.stdout)
            self.assertIn("applies-cleanly", result.stdout)
            self.assertIn("already-upstreamed", result.stdout)
            self.assertIn("already-present", result.stdout)
            self.assertIn("needs-refresh", result.stdout)
            self.assertIn("conflict", result.stdout)
            self.assertEqual(self.run_git(live, "rev-parse", "HEAD").stdout.strip(), live_head_before)
            self.assertEqual(self.run_git(live, "status", "--porcelain").stdout.strip(), "")
            report_files = sorted(reports.glob("update-*.md"))
            self.assertEqual(len(report_files), 1)
            report = report_files[0].read_text(encoding="utf-8")
            self.assertIn("clean-fix", report)
            self.assertIn("applies-cleanly", report)
            self.assertIn("already-present", report)
            self.assertIn("conflict", report)

    def test_update_refuses_dirty_live_repo_before_cloning_upstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            patchkit = root / "patchkit"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir()
            self.run_git(repo, "init", "-b", "main")
            self.configure_git(repo)
            (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "tracked.txt")
            self.run_git(repo, "commit", "-m", "base")
            (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
            manifest = patchkit / "manifests" / "test.json"
            manifest.write_text(
                json.dumps({"version": 1, "upstream": {"repo": str(repo), "ref": "main"}, "patches": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(UPDATE), "--repo", str(repo), "--manifest", str(manifest), "--upstream", "HEAD"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("dirty", result.stdout + result.stderr)

    def test_tui_once_renders_dashboard_without_interactive_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            patchkit = root / "patchkit"
            reports = root / "reports"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            self.run_git(repo, "init", "-b", "main")
            self.configure_git(repo)
            (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "tracked.txt")
            self.run_git(repo, "commit", "-m", "base")
            manifest = patchkit / "manifests" / "test.json"
            manifest.write_text(
                json.dumps({"version": 1, "upstream": {"repo": str(repo), "ref": "HEAD"}, "patches": []}, indent=2) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(TUI),
                    "--once",
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(manifest),
                    "--upstream",
                    "HEAD",
                    "--report-dir",
                    str(reports),
                    "--no-color",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("PatchKit TUI", result.stdout)
            self.assertIn("Safe to apply automatically: yes", result.stdout)
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def make_patch(self, repo: Path, filename: str, patched_text: str) -> str:
        original = (repo / filename).read_text(encoding="utf-8")
        (repo / filename).write_text(patched_text, encoding="utf-8")
        patch_text = self.run_git(repo, "diff", "--binary", "HEAD", "--", filename).stdout
        (repo / filename).write_text(original, encoding="utf-8")
        self.run_git(repo, "checkout", "--", filename)
        return patch_text

    def configure_git(self, repo: Path) -> None:
        self.run_git(repo, "config", "user.name", "PatchKit Test")
        self.run_git(repo, "config", "user.email", "patchkit@example.com")

    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)


if __name__ == "__main__":
    unittest.main()
