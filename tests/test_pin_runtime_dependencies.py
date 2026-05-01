import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PIN_DEPS = REPO_ROOT / "scripts" / "pin_runtime_dependencies.py"
APPLY = REPO_ROOT / "scripts" / "apply.py"


def make_fake_hermes_repo(root: Path, *, git_repo: bool = False) -> Path:
    repo = root / "fake-hermes"
    python_bin = repo / "venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_bin.chmod(0o755)
    if git_repo:
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "PatchKit Tests"], cwd=repo, check=True)
        (repo / "README.md").write_text("fake hermes\n", encoding="utf-8")
        (repo / ".gitignore").write_text("venv/\n.venv/\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "init fake hermes"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def make_fake_uv(root: Path) -> tuple[Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    log = root / "uv-args.txt"
    uv = bin_dir / "uv"
    uv.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['PATCHKIT_FAKE_UV_LOG']).write_text('\\n'.join(sys.argv[1:]) + '\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    return bin_dir, log


class PinRuntimeDependenciesTests(unittest.TestCase):
    def test_dry_run_reports_default_pin_without_invoking_uv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root)
            bin_dir, log = make_fake_uv(root)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            env["PATCHKIT_FAKE_UV_LOG"] = str(log)

            result = subprocess.run(
                [sys.executable, str(PIN_DEPS), "--repo", str(repo)],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("setuptools<80", result.stdout)
            self.assertIn("Dry run complete", result.stdout)
            self.assertFalse(log.exists())

    def test_write_installs_default_pin_with_uv_against_runtime_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root)
            bin_dir, log = make_fake_uv(root)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            env["PATCHKIT_FAKE_UV_LOG"] = str(log)

            result = subprocess.run(
                [sys.executable, str(PIN_DEPS), "--repo", str(repo), "--write"],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            args = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(args, ["pip", "install", "--python", str(repo / "venv" / "bin" / "python"), "setuptools<80"])
            self.assertIn("Runtime dependency pinning complete", result.stdout)

    def test_apply_can_pin_runtime_dependencies_after_patch_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root, git_repo=True)
            bin_dir, log = make_fake_uv(root)
            manifest = root / "manifests" / "test.yaml"
            profile = root / "profiles" / "empty.yaml"
            manifest.parent.mkdir()
            profile.parent.mkdir()
            manifest.write_text('{"patches": []}\n', encoding="utf-8")
            profile.write_text('{"patches": []}\n', encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            env["PATCHKIT_FAKE_UV_LOG"] = str(log)

            result = subprocess.run(
                [
                    sys.executable,
                    str(APPLY),
                    "--repo",
                    str(repo),
                    "--manifest",
                    str(manifest),
                    "--profile",
                    str(profile),
                    "--pin-runtime-dependencies",
                    "--yes",
                ],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(log.exists())
            self.assertIn("Runtime dependency pinning complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
