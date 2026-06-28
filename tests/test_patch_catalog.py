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
RELEASE_2026_4_30_MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.4.30.yaml"
RELEASE_2026_5_16_MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.5.16.yaml"
RELEASE_2026_5_29_MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.5.29.yaml"
RELEASE_2026_6_5_MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.6.5.yaml"
RELEASE_2026_6_19_MANIFEST = REPO_ROOT / "manifests" / "upstream-v2026.6.19.yaml"
PATCH_FILE = REPO_ROOT / "patches" / "030-credential-pool-recovery.patch"
TELEGRAM_TARGET_GATING_PATCH = REPO_ROOT / "patches" / "040-telegram-free-response-target-gating.patch"
RELEASE_2026_4_30_PATCH_DIR = REPO_ROOT / "patches" / "v2026.4.30"
RELEASE_2026_5_16_PATCH_DIR = REPO_ROOT / "patches" / "v2026.5.16"
RELEASE_2026_5_29_PATCH_DIR = REPO_ROOT / "patches" / "v2026.5.29"
RELEASE_2026_6_5_PATCH_DIR = REPO_ROOT / "patches" / "v2026.6.5"
RELEASE_2026_6_19_PATCH_DIR = REPO_ROOT / "patches" / "v2026.6.19"
RELEASE_MAX_PLATFORM_PLUGIN_PATCH = RELEASE_2026_4_30_PATCH_DIR / "070-max-platform-plugin.patch"
MAX_FILE_ATTACHMENTS_PATCH = REPO_ROOT / "patches" / "075-max-gateway-file-attachments.patch"
MAX_MEDIA_DIRECTIVE_SAFETY_PATCH = REPO_ROOT / "patches" / "076-max-media-directive-safety.patch"
MAX_MARKDOWN_FORMATTING_PATCH = REPO_ROOT / "patches" / "077-max-markdown-formatting.patch"
GROK2API_PROFILE = REPO_ROOT / "profiles" / "grok2api-sidecar.yaml"
GROK2API_CANARY_PROFILE = REPO_ROOT / "profiles" / "canary-main-grok2api-sidecar.yaml"
GROK2API_RELEASE_PROFILE = REPO_ROOT / "profiles" / "v2026.4.30-grok2api-sidecar.yaml"
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

    def test_v2026_4_30_manifest_is_pinned_to_release_tag_and_refreshed_patches(self):
        manifest = json.loads(RELEASE_2026_4_30_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["upstream"]["ref"], "v2026.4.30")
        self.assertEqual(manifest["upstream"]["commit"], "73bf3ab1b22314ed9dfecbb59242c03742fe72af")

        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(
            ids[:6],
            [
                "auth-profile-root-fallback",
                "credential-pool-recovery",
                "telegram-free-response-target-gating",
                "homeassistant-tool-config-url",
                "codex-auxiliary-tool-role-flattening",
                "api-server-provider-proxy",
            ],
        )
        self.assertIn("max-platform-plugin", ids)
        for old_max_id in (
            "max-gateway-text-mvp",
            "max-gateway-image-input",
            "max-gateway-oneme-url-safety",
            "max-gateway-image-output",
            "max-send-message-media-routing",
            "max-gateway-file-attachments",
            "max-media-directive-safety",
            "max-markdown-formatting",
        ):
            self.assertNotIn(old_max_id, ids)
        self.assertNotIn("cli-tui-idle-refresh-fix", ids)
        self.assertNotIn("codex-memory-flush-responses-contract", ids)
        self.assertTrue((RELEASE_2026_4_30_PATCH_DIR / "040-telegram-free-response-target-gating.patch").exists())
        max_entry = next(patch for patch in manifest["patches"] if patch["id"] == "max-platform-plugin")
        self.assertEqual(max_entry["track"], "local-overlay")
        self.assertEqual(max_entry["depends_on"], [])

        max_patch_text = RELEASE_MAX_PLATFORM_PLUGIN_PATCH.read_text(encoding="utf-8")
        self.assertNotIn("PLACEHOLDER PATCH", max_patch_text)
        self.assertIn("diff --git", max_patch_text)
        self.assertIn("plugins/platforms/max/plugin.yaml", max_patch_text)
        self.assertIn("plugins/platforms/max/adapter.py", max_patch_text)
        self.assertIn("tests/plugins/test_max_platform_plugin.py", max_patch_text)
        self.assertIn("ctx.register_platform", max_patch_text)
        self.assertIn("MAX_BOT_TOKEN", max_patch_text)
        self.assertNotIn("gateway/platforms/max.py", max_patch_text)
        self.assertNotIn("Platform.MAX", max_patch_text)

        for entry in manifest["patches"]:
            self.assertEqual(entry["base_upstream"], manifest["upstream"]["commit"])
            self.assertTrue(entry["file"].startswith("patches/v2026.4.30/"))
            self.assertIn("diff --git", (REPO_ROOT / entry["file"]).read_text(encoding="utf-8"))


    def test_v2026_5_16_manifest_is_pinned_to_hermes_0_14_and_refreshed_patches(self):
        manifest = json.loads(RELEASE_2026_5_16_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["upstream"]["ref"], "v2026.5.16")
        self.assertEqual(manifest["upstream"]["commit"], "a91a57fa5a13d516c38b07a141a9ce8a3daabeb0")

        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(
            ids,
            [
                "auth-profile-root-fallback",
                "credential-pool-recovery",
                "telegram-free-response-target-gating",
                "homeassistant-tool-config-url",
                "codex-auxiliary-tool-role-flattening",
                "codex-sdk-output-none-recovery",
                "max-platform-plugin",
                "api-server-provider-proxy",
                "lsp-configured-websocket-transport",
                "email-smtp-ssl",
                "1c-document-types",
                "neurogate-provider-plugin",
            ],
        )
        self.assertNotIn("cli-tui-idle-refresh-fix", ids)
        self.assertNotIn("codex-memory-flush-responses-contract", ids)

        for entry in manifest["patches"]:
            self.assertEqual(entry["base_upstream"], manifest["upstream"]["commit"])
            self.assertEqual(entry["refreshed_for"], "v2026.5.16")
            self.assertTrue(entry["file"].startswith("patches/v2026.5.16/"))
            patch_text = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8")
            self.assertIn("diff --git", patch_text)
            self.assertNotIn("PLACEHOLDER PATCH", patch_text)

        provider_profile = json.loads((REPO_ROOT / "profiles" / "v2026.5.16-provider-proxy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(provider_profile["patches"], ["api-server-provider-proxy"])
        self.assertFalse((REPO_ROOT / "profiles" / "v2026.5.16-grok2api-sidecar.yaml").exists())

    def test_v2026_5_29_manifest_is_pinned_to_hermes_0_15_1_and_retire_audit(self):
        manifest = json.loads(RELEASE_2026_5_29_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["upstream"]["ref"], "v2026.5.29")
        self.assertEqual(manifest["upstream"]["commit"], "e71a2bd11b733f3be7cf99deafde0066c343d462")

        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(
            ids,
            [
                "auth-profile-root-fallback",
                "credential-pool-recovery",
                "telegram-free-response-target-gating",
                "homeassistant-tool-config-url",
                "codex-auxiliary-tool-role-flattening",
                "max-platform-plugin",
                "api-server-provider-proxy",
                "lsp-configured-websocket-transport",
                "email-smtp-ssl",
                "gateway-document-media-types",
                "neurogate-provider-plugin",
                "provider-plugin-model-switch",
                "root-home-media-delivery",
                "gateway-busy-text-compat",
                "gateway-explicit-media-delivery-safety",
            ],
        )
        self.assertNotIn("codex-sdk-output-none-recovery", ids)
        retired = manifest.get("retired_patches", [])
        self.assertEqual([entry["id"] for entry in retired], ["codex-sdk-output-none-recovery"])

        for entry in manifest["patches"]:
            self.assertEqual(entry["base_upstream"], manifest["upstream"]["commit"])
            self.assertEqual(entry["refreshed_for"], "v2026.5.29")
            self.assertTrue(entry["file"].startswith("patches/v2026.5.29/"))
            patch_text = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8")
            self.assertIn("diff --git", patch_text)
            self.assertNotIn("PLACEHOLDER PATCH", patch_text)

        personal_profile = json.loads((REPO_ROOT / "profiles" / "v2026.5.29-personal.yaml").read_text(encoding="utf-8"))
        self.assertEqual(personal_profile["patches"], ids)
        provider_profile = json.loads((REPO_ROOT / "profiles" / "v2026.5.29-provider-proxy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(provider_profile["patches"], ["api-server-provider-proxy"])

        lsp_patch_text = (RELEASE_2026_5_29_PATCH_DIR / "090-lsp-configured-websocket-transport.patch").read_text(encoding="utf-8")
        self.assertIn("websockets>=15.0.0,<16.0.0", lsp_patch_text)

        busy_patch_text = (RELEASE_2026_5_29_PATCH_DIR / "095-gateway-busy-text-compat.patch").read_text(encoding="utf-8")
        self.assertIn("_load_busy_text_mode", busy_patch_text)
        self.assertIn("test_busy_text_mode_inherits_busy_input_mode_when_absent", busy_patch_text)
        self.assertIn("display.busy_input_mode", busy_patch_text)

    def test_v2026_6_5_manifest_is_pinned_to_hermes_0_16_and_retires_root_home_unit(self):
        manifest = json.loads(RELEASE_2026_6_5_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["upstream"]["ref"], "v2026.6.5")
        self.assertEqual(manifest["upstream"]["commit"], "3c231eb3979ab9c57d5cd6d02f1d577a3b718b43")

        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(
            ids,
            [
                "auth-profile-root-fallback",
                "credential-pool-recovery",
                "telegram-free-response-target-gating",
                "homeassistant-tool-config-url",
                "codex-auxiliary-tool-role-flattening",
                "max-platform-plugin",
                "api-server-provider-proxy",
                "lsp-configured-websocket-transport",
                "email-smtp-ssl",
                "gateway-document-media-types",
                "neurogate-provider-plugin",
                "gateway-busy-text-compat",
                "provider-plugin-model-switch",
                "gateway-explicit-media-delivery-safety",
                "api-server-fallback-model-kwarg",
                "gateway-auto-reset-context-continuity",
            ],
        )
        self.assertNotIn("root-home-media-delivery", ids)
        retired_ids = [entry["id"] for entry in manifest.get("retired_patches", [])]
        self.assertIn("codex-sdk-output-none-recovery", retired_ids)
        self.assertIn("root-home-media-delivery", retired_ids)

        for entry in manifest["patches"]:
            self.assertEqual(entry["base_upstream"], manifest["upstream"]["commit"])
            self.assertEqual(entry["refreshed_for"], "v2026.6.5")
            self.assertTrue(entry["file"].startswith("patches/v2026.6.5/"))
            patch_text = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8")
            self.assertIn("diff --git", patch_text)
            self.assertNotIn("PLACEHOLDER PATCH", patch_text)

        personal_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.5-personal.yaml").read_text(encoding="utf-8"))
        self.assertEqual(personal_profile["patches"], ids)
        upstream_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.5-upstream-fixes.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("root-home-media-delivery", upstream_profile["patches"])
        self.assertIn("gateway-document-media-types", upstream_profile["patches"])
        provider_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.5-provider-proxy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(provider_profile["patches"], ["api-server-provider-proxy", "api-server-fallback-model-kwarg"])

        media_patch_text = (RELEASE_2026_6_5_PATCH_DIR / "092-gateway-document-media-types.patch").read_text(encoding="utf-8")
        self.assertIn('".epf"', media_patch_text)
        self.assertIn('".cfe"', media_patch_text)
        self.assertIn("MEDIA_TAG_CLEANUP_RE", media_patch_text)

        explicit_media_patch_text = (RELEASE_2026_6_5_PATCH_DIR / "097-gateway-explicit-media-delivery-safety.patch").read_text(encoding="utf-8")
        self.assertIn("auto_upload_local_paths", explicit_media_patch_text)
        self.assertIn("test_auto_upload_local_paths", explicit_media_patch_text)

    def test_v2026_6_19_manifest_is_pinned_to_hermes_0_17_and_retires_absorbed_units(self):
        manifest = json.loads(RELEASE_2026_6_19_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["upstream"]["ref"], "v2026.6.19")
        self.assertEqual(manifest["upstream"]["commit"], "2bd1977d8fad185c9b4be47884f7e87f1add0ce3")

        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(
            ids,
            [
                "cli-tui-idle-refresh-fix",
                "auth-profile-root-fallback",
                "credential-pool-recovery",
                "telegram-free-response-target-gating",
                "telegram-rich-flood-fallback",
                "homeassistant-tool-config-url",
                "max-platform-plugin",
                "max-userbot-platform-plugin",
                "api-server-provider-proxy",
                "lsp-configured-websocket-transport",
                "email-smtp-ssl",
                "gateway-document-media-types",
                "neurogate-provider-plugin",
                "provider-plugin-model-switch",
                "gateway-explicit-media-delivery-safety",
                "api-server-fallback-model-kwarg",
                "gateway-auto-reset-context-continuity",
                "vibemode-provider-plugin",
            ],
        )
        retired_ids = [entry["id"] for entry in manifest.get("retired_patches", [])]
        self.assertIn("codex-auxiliary-tool-role-flattening", retired_ids)
        self.assertIn("gateway-busy-text-compat", retired_ids)

        for entry in manifest["patches"]:
            self.assertEqual(entry["base_upstream"], manifest["upstream"]["commit"])
            self.assertEqual(entry["refreshed_for"], "v2026.6.19")
            self.assertTrue(entry["file"].startswith("patches/v2026.6.19/"))
            patch_text = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8")
            self.assertIn("diff --git", patch_text)
            self.assertNotIn("PLACEHOLDER PATCH", patch_text)

        personal_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.19-personal.yaml").read_text(encoding="utf-8"))
        self.assertEqual(personal_profile["patches"], ids)
        upstream_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.19-upstream-fixes.yaml").read_text(encoding="utf-8"))
        self.assertIn("cli-tui-idle-refresh-fix", upstream_profile["patches"])
        self.assertNotIn("codex-auxiliary-tool-role-flattening", upstream_profile["patches"])
        self.assertNotIn("gateway-busy-text-compat", upstream_profile["patches"])
        provider_profile = json.loads((REPO_ROOT / "profiles" / "v2026.6.19-provider-proxy.yaml").read_text(encoding="utf-8"))
        self.assertEqual(provider_profile["patches"], ["api-server-provider-proxy", "api-server-fallback-model-kwarg"])

        auxiliary_patch = RELEASE_2026_6_19_PATCH_DIR / "061-codex-auxiliary-tool-role-flattening.patch"
        busy_patch = RELEASE_2026_6_19_PATCH_DIR / "095-gateway-busy-text-compat.patch"
        idle_patch = RELEASE_2026_6_19_PATCH_DIR / "010-cli-tui-idle-refresh-fix.patch"
        idle_patch_text = idle_patch.read_text(encoding="utf-8")
        self.assertIn('"cli_refresh_interval": 0', idle_patch_text)
        self.assertIn("test_default_config_disables_cli_refresh_interval", idle_patch_text)
        self.assertFalse(auxiliary_patch.exists())
        self.assertFalse(busy_patch.exists())

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
        release_profile = json.loads(GROK2API_RELEASE_PROFILE.read_text(encoding="utf-8"))

        self.assertEqual(profile["patches"], ["api-server-provider-proxy"])
        self.assertEqual(canary_profile["patches"], ["api-server-provider-proxy"])
        self.assertEqual(release_profile["patches"], ["api-server-provider-proxy"])

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
            self.assertIn("profiles/v2026.4.30-grok2api-sidecar.yaml", doc)
            self.assertIn("legacy", doc.lower())
            self.assertIn("xai-oauth", doc)
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
