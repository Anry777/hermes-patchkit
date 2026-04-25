import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.4.23-240-ge5647d78.yaml"
PATCH_FILE = REPO_ROOT / "patches" / "030-credential-pool-recovery.patch"


class PatchCatalogTests(unittest.TestCase):
    def test_credential_pool_recovery_is_exported_real_patch(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next(patch for patch in manifest["patches"] if patch["id"] == "credential-pool-recovery")

        self.assertEqual(entry["status"], "exported")
        self.assertIn("transplanted_from_commit", entry)

        patch_text = PATCH_FILE.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", patch_text)
        self.assertIn("diff --git", patch_text)
        self.assertIn("agent/credential_pool.py", patch_text)
        self.assertIn("tests/agent/test_credential_pool.py", patch_text)


if __name__ == "__main__":
    unittest.main()
