import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_POLICY = REPO_ROOT / "scripts" / "install_operator_policy.py"
DEFAULT_POLICY = REPO_ROOT / "templates" / "office-operator-policy.md"


class InstallOperatorPolicyTests(unittest.TestCase):
    def test_dry_run_does_not_modify_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            config = home / "config.yaml"
            original = "agent:\n  system_prompt: Existing prompt\n"
            config.write_text(original, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INSTALL_POLICY), "--home", str(home)],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("Dry run complete", result.stdout)
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_write_inserts_managed_block_and_preserves_existing_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            config = home / "config.yaml"
            config.write_text(
                "agent:\n  system_prompt: |\n    Existing operator instructions.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(INSTALL_POLICY), "--home", str(home), "--write", "--backup"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            data = yaml.safe_load(config.read_text(encoding="utf-8"))
            prompt = data["agent"]["system_prompt"]
            self.assertIn("Existing operator instructions.", prompt)
            self.assertIn("[PATCHKIT_OPERATOR_POLICY_BEGIN]", prompt)
            self.assertIn("[PATCHKIT_OPERATOR_POLICY_END]", prompt)
            self.assertIn("config.yaml owns non-secret behavior", prompt)
            self.assertEqual(len(list(home.glob("config.yaml.bak_install_operator_policy_*"))), 1)

    def test_second_write_updates_block_in_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            config = home / "config.yaml"
            policy = home / "policy.md"
            config.write_text("agent:\n  system_prompt: Existing\n", encoding="utf-8")
            policy.write_text("First policy text", encoding="utf-8")
            first = subprocess.run(
                [sys.executable, str(INSTALL_POLICY), "--home", str(home), "--policy", str(policy), "--write"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
            policy.write_text("Second policy text", encoding="utf-8")

            second = subprocess.run(
                [sys.executable, str(INSTALL_POLICY), "--home", str(home), "--policy", str(policy), "--write"],
                text=True,
                capture_output=True,
            )

            self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
            prompt = yaml.safe_load(config.read_text(encoding="utf-8"))["agent"]["system_prompt"]
            self.assertEqual(prompt.count("[PATCHKIT_OPERATOR_POLICY_BEGIN]"), 1)
            self.assertNotIn("First policy text", prompt)
            self.assertIn("Second policy text", prompt)

    def test_secret_like_policy_key_values_are_rejected_without_printing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "hermes"
            home.mkdir()
            config = home / "config.yaml"
            policy = home / "policy.md"
            config.write_text("agent:\n  system_prompt: ''\n", encoding="utf-8")
            policy.write_text("API_KEY=super-secret-value\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INSTALL_POLICY), "--home", str(home), "--policy", str(policy), "--write"],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            combined = result.stdout + result.stderr
            self.assertIn("secret-like KEY=value", combined)
            self.assertNotIn("super-secret-value", combined)
            prompt = yaml.safe_load(config.read_text(encoding="utf-8"))["agent"]["system_prompt"]
            self.assertEqual(prompt, "")

    def test_default_policy_template_exists_and_mentions_core_sources(self):
        text = DEFAULT_POLICY.read_text(encoding="utf-8")
        self.assertIn("/root/.hermes/auth.json", text)
        self.assertIn("config.yaml owns non-secret", text)
        self.assertIn(".env owns only secrets", text)
        self.assertIn("Telegram routing policy belongs under `telegram:`", text)


if __name__ == "__main__":
    unittest.main()
