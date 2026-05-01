import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLEAN_PROFILE = REPO_ROOT / "scripts" / "clean_profile_config.py"


class CleanProfileConfigTests(unittest.TestCase):
    def test_clean_profile_config_generates_redacted_example_and_secrets_only_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            (home / "config.yaml").write_text(
                """
model:
  provider: openrouter
  api_key: live-config-secret
telegram:
  require_mention: true
  channel_prompts:
    "-123": |
      Local prompt
empty_section: {}
""".lstrip(),
                encoding="utf-8",
            )
            (home / ".env").write_text(
                """
TELEGRAM_BOT_TOKEN=telegram-secret
HASS_URL=http://homeassistant.local:8123
HASS_TOKEN=hass-secret
CONTEXT_COMPRESSION_ENABLED=true
HERMES_MAX_ITERATIONS=99
WEB_TOOLS_DEBUG=true
""".lstrip(),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CLEAN_PROFILE), "--home", str(home), "--write"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            example = (home / "config.yaml.example").read_text(encoding="utf-8")
            self.assertIn("api_key: <REDACTED>", example)
            self.assertNotIn("live-config-secret", example)
            self.assertIn("require_mention: true", example)
            env = (home / ".env").read_text(encoding="utf-8")
            self.assertIn("TELEGRAM_BOT_TOKEN=telegram-secret", env)
            self.assertIn("HASS_TOKEN=hass-secret", env)
            self.assertIn("# HASS_URL=http://homeassistant.local:8123", env)
            self.assertIn("# CONTEXT_COMPRESSION_ENABLED=true", env)
            self.assertIn("# WEB_TOOLS_DEBUG=true", env)
            active_keys = [line.split("=", 1)[0] for line in env.splitlines() if line and not line.startswith("#") and "=" in line]
            self.assertEqual(active_keys, ["TELEGRAM_BOT_TOKEN", "HASS_TOKEN"])

    def test_keep_env_only_keeps_known_non_secret_exceptions_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            (home / "config.yaml").write_text("agent:\n  max_turns: 10\n", encoding="utf-8")
            (home / ".env").write_text("HASS_URL=http://ha\nHASS_TOKEN=secret\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CLEAN_PROFILE), "--home", str(home), "--write", "--keep-env-only"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            env = (home / ".env").read_text(encoding="utf-8")
            self.assertIn("HASS_URL=http://ha", env)
            self.assertIn("HASS_TOKEN=secret", env)


if __name__ == "__main__":
    unittest.main()
