import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.4.23-240-ge5647d78.yaml"
PATCH_FILE = REPO_ROOT / "patches" / "030-credential-pool-recovery.patch"
TELEGRAM_TARGET_GATING_PATCH = REPO_ROOT / "patches" / "040-telegram-free-response-target-gating.patch"
MAX_FILE_ATTACHMENTS_PATCH = REPO_ROOT / "patches" / "075-max-gateway-file-attachments.patch"
MAX_MEDIA_DIRECTIVE_SAFETY_PATCH = REPO_ROOT / "patches" / "076-max-media-directive-safety.patch"
MAX_MARKDOWN_FORMATTING_PATCH = REPO_ROOT / "patches" / "077-max-markdown-formatting.patch"
GROK2API_PROFILE = REPO_ROOT / "profiles" / "grok2api-sidecar.yaml"
GROK2API_CANARY_PROFILE = REPO_ROOT / "profiles" / "canary-main-grok2api-sidecar.yaml"
GROK2API_SCRIPT = REPO_ROOT / "scripts" / "grok2api_bridge.py"
GROK2API_DOC_EN = REPO_ROOT / "docs" / "en" / "sidecars-grok2api.md"
GROK2API_DOC_RU = REPO_ROOT / "docs" / "ru" / "sidecars-grok2api.md"
GROK2API_NOTICE = REPO_ROOT / "examples" / "sidecars" / "grok2api" / "THIRD_PARTY_NOTICE.md"
GROK2API_COMPOSE = REPO_ROOT / "examples" / "sidecars" / "grok2api" / "docker-compose.yml"


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

    def test_telegram_free_response_target_gating_is_exported_real_patch(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next(patch for patch in manifest["patches"] if patch["id"] == "telegram-free-response-target-gating")

        self.assertEqual(entry["status"], "exported")
        self.assertEqual(entry["track"], "upstream-fix")

        patch_text = TELEGRAM_TARGET_GATING_PATCH.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", patch_text)
        self.assertIn("diff --git", patch_text)
        self.assertIn("gateway/platforms/telegram.py", patch_text)
        self.assertIn("tests/gateway/test_telegram_group_gating.py", patch_text)
        self.assertIn("_message_mentions_other_target", patch_text)
        self.assertIn("_is_reply_to_other_bot", patch_text)
        self.assertIn("_message_has_leading_vocative", patch_text)
        self.assertIn("_message_looks_like_question", patch_text)
        self.assertIn("test_free_response_chats_ignore_messages_addressed_to_other_bot", patch_text)
        self.assertIn("test_reply_context_does_not_override_fresh_addressing_to_other_bot", patch_text)
        self.assertIn("/status@other_bot", patch_text)

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

    def test_grok2api_sidecar_bridge_assets_are_protocol_layer_not_vendored_patch(self):
        profile = json.loads(GROK2API_PROFILE.read_text(encoding="utf-8"))
        canary_profile = json.loads(GROK2API_CANARY_PROFILE.read_text(encoding="utf-8"))

        self.assertEqual(profile["patches"], ["api-server-provider-proxy"])
        self.assertEqual(canary_profile["patches"], ["api-server-provider-proxy"])

        script_text = GROK2API_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Grok2API sidecar bridge helper", script_text)
        self.assertIn("render-config", script_text)
        self.assertIn("write-profile", script_text)
        self.assertIn("doctor", script_text)
        self.assertIn("list-models", script_text)
        self.assertIn("sync-models", script_text)
        self.assertIn("provider_proxy", script_text)

        doc_en = GROK2API_DOC_EN.read_text(encoding="utf-8")
        doc_ru = GROK2API_DOC_RU.read_text(encoding="utf-8")
        notice = GROK2API_NOTICE.read_text(encoding="utf-8")
        compose = GROK2API_COMPOSE.read_text(encoding="utf-8")

        for doc in (doc_en, doc_ru):
            self.assertIn("profiles/grok2api-sidecar.yaml", doc)
            self.assertIn("scripts/grok2api_bridge.py", doc)
            self.assertIn("MIT", doc)
            self.assertIn("official Grok API provider", doc)

        self.assertIn("does not vendor grok2api code", notice)
        self.assertIn("MIT License", notice)
        self.assertIn("ghcr.io/chenyme/grok2api:latest", compose)
        self.assertIn("127.0.0.1:8000", compose)

    def test_grok2api_sync_models_discovers_and_filters_chat_catalog(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/v1/models":
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = {
                    "object": "list",
                    "data": [
                        {"id": "grok-4.20-fast"},
                        {"id": "grok-4.20-auto"},
                        {"id": "grok-imagine-image"},
                        {"id": "grok-imagine-video"},
                    ],
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                profile_dir = Path(tmpdir) / "provider-proxy-grok2api"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(GROK2API_SCRIPT),
                        "sync-models",
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}/v1",
                        "--profile-dir",
                        str(profile_dir),
                        "--write",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                config_text = (profile_dir / "config.yaml").read_text(encoding="utf-8")
                self.assertIn('id: "grok2api/grok-4.20-fast"', config_text)
                self.assertIn('model: "grok-4.20-auto"', config_text)
                self.assertNotIn("grok-imagine-image", config_text)
                self.assertNotIn("grok-imagine-video", config_text)
                self.assertIn("dry-run", subprocess.run(
                    [
                        sys.executable,
                        str(GROK2API_SCRIPT),
                        "sync-models",
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}/v1",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                ).stdout)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
