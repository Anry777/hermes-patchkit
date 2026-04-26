import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.4.23-240-ge5647d78.yaml"
PATCH_FILE = REPO_ROOT / "patches" / "030-credential-pool-recovery.patch"
MAX_FILE_ATTACHMENTS_PATCH = REPO_ROOT / "patches" / "075-max-gateway-file-attachments.patch"
MAX_MEDIA_DIRECTIVE_SAFETY_PATCH = REPO_ROOT / "patches" / "076-max-media-directive-safety.patch"
MAX_MARKDOWN_FORMATTING_PATCH = REPO_ROOT / "patches" / "077-max-markdown-formatting.patch"


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

    def test_max_file_attachments_is_exported_real_patch(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next(patch for patch in manifest["patches"] if patch["id"] == "max-gateway-file-attachments")

        self.assertEqual(entry["status"], "exported")
        self.assertEqual(entry["track"], "local-overlay")
        self.assertIn("max-send-message-media-routing", entry["depends_on"])

        patch_text = MAX_FILE_ATTACHMENTS_PATCH.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", patch_text)
        self.assertIn("diff --git", patch_text)
        self.assertIn("gateway/platforms/max.py", patch_text)
        self.assertIn("tools/send_message_tool.py", patch_text)
        self.assertIn("tests/gateway/test_max.py", patch_text)
        self.assertIn("/uploads", patch_text)
        self.assertIn('"type": "file"', patch_text)
        self.assertIn("send_document", patch_text)

    def test_max_media_directive_safety_is_exported_real_patch(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next(patch for patch in manifest["patches"] if patch["id"] == "max-media-directive-safety")

        self.assertEqual(entry["status"], "exported")
        self.assertEqual(entry["track"], "local-overlay")
        self.assertIn("max-gateway-file-attachments", entry["depends_on"])

        patch_text = MAX_MEDIA_DIRECTIVE_SAFETY_PATCH.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", patch_text)
        self.assertIn("diff --git", patch_text)
        self.assertIn("gateway/platforms/base.py", patch_text)
        self.assertIn("agent/prompt_builder.py", patch_text)
        self.assertIn("test_media_tag_inside_fenced_code_block_is_documentation_not_attachment", patch_text)
        self.assertIn("/absolute/path", patch_text)
        self.assertIn("code block", patch_text)

    def test_max_markdown_formatting_is_exported_real_patch(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next(patch for patch in manifest["patches"] if patch["id"] == "max-markdown-formatting")

        self.assertEqual(entry["status"], "exported")
        self.assertEqual(entry["track"], "local-overlay")
        self.assertIn("max-media-directive-safety", entry["depends_on"])

        patch_text = MAX_MARKDOWN_FORMATTING_PATCH.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", patch_text)
        self.assertIn("diff --git", patch_text)
        self.assertIn("gateway/platforms/max.py", patch_text)
        self.assertIn("gateway/config.py", patch_text)
        self.assertIn("agent/prompt_builder.py", patch_text)
        self.assertIn("MAX_TEXT_FORMAT", patch_text)
        self.assertIn("DEFAULT_TEXT_FORMAT", patch_text)
        self.assertIn("format\": \"markdown", patch_text)


if __name__ == "__main__":
    unittest.main()
