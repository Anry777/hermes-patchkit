import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APPLY = REPO_ROOT / "scripts" / "apply.py"
ROLLBACK = REPO_ROOT / "scripts" / "rollback.py"


class RollbackScriptTests(unittest.TestCase):
    def test_rollback_removes_patch_created_symlink_without_touching_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "target-repo"
            repo.mkdir()

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")

            (repo / "dir").mkdir()
            tracked = repo / "dir" / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "dir/tracked.txt")
            self.run_git(repo, "commit", "-m", "base")
            self.run_git(repo, "branch", "patchkit-backup-test")

            state_dir = repo / ".git" / "patchkit"
            state_dir.mkdir(parents=True)
            (state_dir / "patchkit-backup-test.json").write_text(
                json.dumps({"apply_created_untracked": ["link"]}) + "\n",
                encoding="utf-8",
            )

            (repo / "link").symlink_to("dir", target_is_directory=True)

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", "patchkit-backup-test", "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertEqual(tracked.read_text(encoding="utf-8"), "base\n")
            self.assertFalse((repo / "link").exists() or (repo / "link").is_symlink(), msg="rollback left behind the patch-created symlink")
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def test_rollback_removes_untracked_files_created_after_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "target-repo"
            repo.mkdir()

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")

            tracked = repo / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "tracked.txt")
            self.run_git(repo, "commit", "-m", "base")
            self.run_git(repo, "branch", "patchkit-backup-test")
            state_dir = repo / ".git" / "patchkit"
            state_dir.mkdir(parents=True)
            (state_dir / "patchkit-backup-test.json").write_text(
                json.dumps(
                    {
                        "backup_branch": "patchkit-backup-test",
                        "pre_apply_ref": None,
                        "apply_created_untracked": ["added.txt"],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            tracked.write_text("modified\n", encoding="utf-8")
            (repo / "added.txt").write_text("new file\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", "patchkit-backup-test", "--yes"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(tracked.read_text(encoding="utf-8"), "base\n")
            self.assertFalse((repo / "added.txt").exists(), msg="rollback left behind an untracked file")
            status = self.run_git(repo, "status", "--porcelain").stdout.strip()
            self.assertEqual(status, "")

    def test_force_apply_then_rollback_restores_preexisting_dirty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            patch_source = root / "patch-source"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")

            (repo / ".gitignore").write_text("ignored*.txt\n", encoding="utf-8")
            (repo / "target.txt").write_text("base target\n", encoding="utf-8")
            (repo / "local.txt").write_text("base local\n", encoding="utf-8")
            self.run_git(repo, "add", ".gitignore", "target.txt", "local.txt")
            self.run_git(repo, "commit", "-m", "base")

            self.run_git(root, "clone", str(repo), str(patch_source))
            self.run_git(patch_source, "config", "user.name", "PatchKit Test")
            self.run_git(patch_source, "config", "user.email", "patchkit@example.com")
            (patch_source / "target.txt").write_text("patched target\n", encoding="utf-8")
            (patch_source / "added.txt").write_text("patch-created file\n", encoding="utf-8")
            (patch_source / "ignored-created.txt").write_text("patch-created ignored file\n", encoding="utf-8")
            tracked_diff = self.run_git(patch_source, "diff", "--binary", "HEAD", "--", "target.txt").stdout
            added_diff = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", str(patch_source / "added.txt")],
                text=True,
                capture_output=True,
                check=False,
            ).stdout
            ignored_diff = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", str(patch_source / "ignored-created.txt")],
                text=True,
                capture_output=True,
                check=False,
            ).stdout
            (patchkit / "patches" / "test.patch").write_text(tracked_diff + added_diff + ignored_diff, encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {
                                "id": "test-patch",
                                "file": "patches/test.patch",
                                "status": "exported",
                                "default": False,
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            (repo / "local.txt").write_text("dirty local change\n", encoding="utf-8")
            (repo / "keep.txt").write_text("keep me\n", encoding="utf-8")
            (repo / "ignored-keep.txt").write_text("preserve ignored\n", encoding="utf-8")

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "test-patch",
                    "--yes",
                    "--force",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            self.assertTrue(backup.startswith("patchkit-backup-"), msg=apply_result.stdout)

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", backup, "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)

            self.assertEqual((repo / "target.txt").read_text(encoding="utf-8"), "base target\n")
            self.assertEqual((repo / "local.txt").read_text(encoding="utf-8"), "dirty local change\n")
            self.assertTrue((repo / "keep.txt").exists(), msg="rollback deleted a pre-existing untracked file")
            self.assertTrue((repo / "ignored-keep.txt").exists(), msg="rollback deleted a pre-existing ignored file")
            self.assertFalse((repo / "added.txt").exists(), msg="rollback left behind a patch-created file")
            self.assertFalse((repo / "ignored-created.txt").exists(), msg="rollback left behind a patch-created ignored file")
            status_lines = set(self.run_git(repo, "status", "--porcelain").stdout.splitlines())
            self.assertEqual(status_lines, {" M local.txt", "?? keep.txt"})

    def test_force_apply_records_cleanup_for_colliding_untracked_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            patch_source = root / "patch-source"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "base.txt")
            self.run_git(repo, "commit", "-m", "base")

            self.run_git(root, "clone", str(repo), str(patch_source))
            self.run_git(patch_source, "config", "user.name", "PatchKit Test")
            self.run_git(patch_source, "config", "user.email", "patchkit@example.com")
            (patch_source / "keep.txt").write_text("patch-created replacement\n", encoding="utf-8")
            patch_text = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", "keep.txt"],
                text=True,
                capture_output=True,
                check=False,
                cwd=patch_source,
            ).stdout
            (patchkit / "patches" / "collision.patch").write_text(patch_text, encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {"id": "collision", "file": "patches/collision.patch", "status": "exported", "default": False}
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            (repo / "keep.txt").write_text("pre-existing dirty file\n", encoding="utf-8")

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "collision",
                    "--yes",
                    "--force",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            state_path = repo / ".git" / "patchkit" / f"{backup}.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertIn(
                "keep.txt",
                state["apply_created_untracked"],
                msg="force apply should record patch-created path collisions so rollback can remove them before restoring dirty state",
            )

    def test_force_apply_then_rollback_restores_preexisting_ignored_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            patch_source = root / "patch-source"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")
            (repo / ".gitignore").write_text("ignored-created.txt\n", encoding="utf-8")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", ".gitignore", "base.txt")
            self.run_git(repo, "commit", "-m", "base")

            self.run_git(root, "clone", str(repo), str(patch_source))
            self.run_git(patch_source, "config", "user.name", "PatchKit Test")
            self.run_git(patch_source, "config", "user.email", "patchkit@example.com")
            (patch_source / "ignored-created.txt").write_text("patch-created ignored\n", encoding="utf-8")
            patch_text = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", "ignored-created.txt"],
                text=True,
                capture_output=True,
                check=False,
                cwd=patch_source,
            ).stdout
            (patchkit / "patches" / "ignored-collision.patch").write_text(patch_text, encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {
                                "id": "ignored-collision",
                                "file": "patches/ignored-collision.patch",
                                "status": "exported",
                                "default": False,
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            (repo / "ignored-created.txt").write_text("pre-existing ignored\n", encoding="utf-8")

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "ignored-collision",
                    "--yes",
                    "--force",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            self.assertEqual((repo / "ignored-created.txt").read_text(encoding="utf-8"), "patch-created ignored\n")

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", backup, "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertEqual((repo / "ignored-created.txt").read_text(encoding="utf-8"), "pre-existing ignored\n")
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def test_rollback_removes_patch_created_ignored_file_inside_preexisting_ignored_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            patch_source = root / "patch-source"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")
            (repo / ".gitignore").write_text("ignored-dir/\n", encoding="utf-8")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", ".gitignore", "base.txt")
            self.run_git(repo, "commit", "-m", "base")

            (repo / "ignored-dir").mkdir()
            (repo / "ignored-dir" / "pre-existing.txt").write_text("keep me\n", encoding="utf-8")

            self.run_git(root, "clone", str(repo), str(patch_source))
            self.run_git(patch_source, "config", "user.name", "PatchKit Test")
            self.run_git(patch_source, "config", "user.email", "patchkit@example.com")
            (patch_source / "ignored-dir").mkdir(exist_ok=True)
            (patch_source / "ignored-dir" / "created-by-patch.txt").write_text("patch-created ignored\n", encoding="utf-8")
            patch_text = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", "ignored-dir/created-by-patch.txt"],
                text=True,
                capture_output=True,
                check=False,
                cwd=patch_source,
            ).stdout
            (patchkit / "patches" / "ignored-dir.patch").write_text(patch_text, encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {
                                "id": "ignored-dir",
                                "file": "patches/ignored-dir.patch",
                                "status": "exported",
                                "default": False,
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "ignored-dir",
                    "--yes",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            self.assertTrue((repo / "ignored-dir" / "created-by-patch.txt").exists())
            self.assertTrue((repo / "ignored-dir" / "pre-existing.txt").exists())

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", backup, "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertFalse((repo / "ignored-dir" / "created-by-patch.txt").exists(), msg="rollback left behind ignored file inside pre-existing ignored directory")
            self.assertTrue((repo / "ignored-dir" / "pre-existing.txt").exists(), msg="rollback deleted pre-existing ignored file inside ignored directory")
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def test_rollback_treats_recorded_filenames_as_literals(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")

            tracked = repo / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "tracked.txt")
            self.run_git(repo, "commit", "-m", "base")
            self.run_git(repo, "branch", "patchkit-backup-test")

            state_dir = repo / ".git" / "patchkit"
            state_dir.mkdir(parents=True)
            (state_dir / "patchkit-backup-test.json").write_text(
                json.dumps({"apply_created_untracked": [":(glob)*"]}) + "\n",
                encoding="utf-8",
            )

            (repo / ":(glob)*").write_text("patch-created\n", encoding="utf-8")
            (repo / "keep.txt").write_text("keep me\n", encoding="utf-8")

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", "patchkit-backup-test", "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertFalse((repo / ":(glob)*").exists(), msg="rollback left the recorded literal filename behind")
            self.assertTrue((repo / "keep.txt").exists(), msg="rollback deleted an unrelated untracked file via pathspec expansion")

    def test_apply_and_rollback_remove_patch_created_ignored_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")
            (repo / ".gitignore").write_text("ignored-*.txt\n", encoding="utf-8")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", ".gitignore", "base.txt")
            self.run_git(repo, "commit", "-m", "base")

            (repo / "ignored-keep.txt").write_text("keep ignored file\n", encoding="utf-8")
            ignored_file = repo / "ignored-created.txt"
            ignored_file.write_text("patch-created ignored file\n", encoding="utf-8")
            patch_text = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", "ignored-created.txt"],
                text=True,
                capture_output=True,
                check=False,
                cwd=repo,
            ).stdout
            ignored_file.unlink()

            (patchkit / "patches" / "ignored.patch").write_text(patch_text, encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {"id": "ignored-file", "file": "patches/ignored.patch", "status": "exported", "default": False}
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "ignored-file",
                    "--yes",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            self.assertTrue((repo / "ignored-created.txt").exists(), msg="apply did not create the ignored file from the patch")
            self.assertTrue((repo / "ignored-keep.txt").exists(), msg="pre-existing ignored file disappeared during apply")

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", backup, "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertFalse((repo / "ignored-created.txt").exists(), msg="rollback left behind an ignored file created by the patch")
            self.assertTrue((repo / "ignored-keep.txt").exists(), msg="rollback deleted a pre-existing ignored file")
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def test_partial_apply_failure_still_records_cleanup_state_for_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "target-repo"
            patchkit = root / "patchkit-fixture"
            repo.mkdir()
            (patchkit / "manifests").mkdir(parents=True)
            (patchkit / "patches").mkdir(parents=True)

            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "PatchKit Test")
            self.run_git(repo, "config", "user.email", "patchkit@example.com")
            (repo / "base.txt").write_text("base\n", encoding="utf-8")
            self.run_git(repo, "add", "base.txt")
            self.run_git(repo, "commit", "-m", "base")

            added_file = repo / "added.txt"
            added_file.write_text("created by patch one\n", encoding="utf-8")
            patch_one = subprocess.run(
                ["git", "diff", "--binary", "--no-index", "/dev/null", "added.txt"],
                text=True,
                capture_output=True,
                check=False,
                cwd=repo,
            ).stdout
            added_file.unlink()
            (patchkit / "patches" / "patch-one.patch").write_text(patch_one, encoding="utf-8")
            (patchkit / "patches" / "patch-two.patch").write_text("this is not a valid patch\n", encoding="utf-8")
            (patchkit / "manifests" / "test.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "upstream": {"repo": "test/test", "ref": "HEAD"},
                        "patches": [
                            {"id": "patch-one", "file": "patches/patch-one.patch", "status": "exported", "default": False},
                            {"id": "patch-two", "file": "patches/patch-two.patch", "status": "exported", "default": False},
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(patchkit / "manifests" / "test.json"),
                    "--patch",
                    "patch-one,patch-two",
                    "--yes",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(apply_result.returncode, 0, msg=apply_result.stdout + apply_result.stderr)
            backup = self.parse_backup_name(apply_result.stdout)
            self.assertTrue((repo / "added.txt").exists(), msg="first patch should have applied before the second patch failed")

            rollback_result = subprocess.run(
                [sys.executable, str(ROLLBACK), "--repo", str(repo), "--backup", backup, "--yes"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(rollback_result.returncode, 0, msg=rollback_result.stdout + rollback_result.stderr)
            self.assertFalse((repo / "added.txt").exists(), msg="rollback left behind a file from a partially applied patch set")
            self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout.strip(), "")

    def parse_backup_name(self, stdout: str) -> str:
        for line in stdout.splitlines():
            if line.startswith("Created backup branch: "):
                return line.split(": ", 1)[1].strip()
        self.fail(f"backup branch line not found in output: {stdout!r}")

    def run_git(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
