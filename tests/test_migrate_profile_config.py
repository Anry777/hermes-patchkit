import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATE_PROFILE = REPO_ROOT / "scripts" / "migrate_profile_config.py"
APPLY = REPO_ROOT / "scripts" / "apply.py"


FAKE_HERMES_CONFIG = r'''
import copy
import os
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "_config_version": 23,
    "curator": {
        "enabled": False,
        "interval_hours": 168,
    },
    "display": {
        "tui_auto_resume_recent": False,
    },
    "telegram": {
        "require_mention": False,
    },
}


def _config_path():
    return Path(os.environ["HERMES_HOME"]) / "config.yaml"


def _read_raw():
    path = _config_path()
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _deep_missing_defaults(defaults, current):
    if not isinstance(defaults, dict) or not isinstance(current, dict):
        return current
    merged = copy.deepcopy(current)
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_missing_defaults(value, merged[key])
    return merged


def check_config_version():
    raw = _read_raw()
    return raw.get("_config_version", 0), DEFAULT_CONFIG["_config_version"]


def migrate_config(interactive=True, quiet=False):
    home = Path(os.environ["HERMES_HOME"])
    raw = _read_raw()
    migrated = _deep_missing_defaults(DEFAULT_CONFIG, raw)
    migrated["_config_version"] = DEFAULT_CONFIG["_config_version"]
    _config_path().write_text(
        yaml.safe_dump(migrated, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (home / "logs" / "curator").mkdir(parents=True, exist_ok=True)
    return {"config_added": ["curator", "display.tui_auto_resume_recent"], "env_added": [], "warnings": []}
'''


def make_fake_hermes_repo(root: Path, *, git_repo: bool = False) -> Path:
    repo = root / "fake-hermes"
    package = repo / "hermes_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "config.py").write_text(FAKE_HERMES_CONFIG, encoding="utf-8")
    if git_repo:
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "PatchKit Tests"], cwd=repo, check=True)
        subprocess.run(["git", "add", "hermes_cli"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "init fake hermes"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def write_old_profile(home: Path) -> None:
    home.mkdir(parents=True)
    (home / "config.yaml").write_text(
        textwrap.dedent(
            """
            _config_version: 19
            model:
              provider: openai-codex
              api_key: super-secret-config-key
            telegram:
              require_mention: true
            """
        ).lstrip(),
        encoding="utf-8",
    )


class MigrateProfileConfigTests(unittest.TestCase):
    def test_dry_run_uses_target_runtime_migration_without_modifying_profile_or_printing_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root)
            home = root / "home"
            write_old_profile(home)
            before = (home / "config.yaml").read_text(encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(MIGRATE_PROFILE), "--repo", str(repo), "--home", str(home)],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual((home / "config.yaml").read_text(encoding="utf-8"), before)
            self.assertIn("Dry run complete", result.stdout)
            self.assertIn("curator", result.stdout)
            self.assertNotIn("super-secret-config-key", result.stdout + result.stderr)

    def test_write_migrates_profile_preserves_user_values_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root)
            home = root / "home"
            write_old_profile(home)

            result = subprocess.run(
                [sys.executable, str(MIGRATE_PROFILE), "--repo", str(repo), "--home", str(home), "--write"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            migrated = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertEqual(migrated["_config_version"], 23)
            self.assertEqual(migrated["telegram"]["require_mention"], True)
            self.assertEqual(migrated["curator"]["enabled"], False)
            self.assertEqual(migrated["display"]["tui_auto_resume_recent"], False)
            self.assertTrue((home / "logs" / "curator").is_dir())
            backups = list(home.glob("config.yaml.bak_migrate_profile_*"))
            self.assertEqual(len(backups), 1)
            self.assertIn("Migration complete", result.stdout)

    def test_apply_can_run_profile_migration_after_patch_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_fake_hermes_repo(root, git_repo=True)
            home = root / "home"
            write_old_profile(home)
            manifest = root / "manifests" / "test.yaml"
            profile = root / "profiles" / "empty.yaml"
            manifest.parent.mkdir()
            profile.parent.mkdir()
            manifest.write_text('{"patches": []}\n', encoding="utf-8")
            profile.write_text('{"patches": []}\n', encoding="utf-8")

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
                    "--migrate-profile-config",
                    "--hermes-home",
                    str(home),
                    "--yes",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            migrated = yaml.safe_load((home / "config.yaml").read_text(encoding="utf-8"))
            self.assertEqual(migrated["_config_version"], 23)
            self.assertIn("Profile config migration complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
