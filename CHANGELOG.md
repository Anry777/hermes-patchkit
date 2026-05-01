# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog.

## [Unreleased]

### Fixed
- `072-max-gateway-oneme-url-safety`: MAX inbound photos from `i.oneme.ru` are no longer blocked by URL safety when that exact HTTPS CDN host resolves to `198.18.0.0/15`; subdomains, HTTP, and unrelated benchmark/private-style hosts remain blocked.
- `070-max-gateway-text-mvp`: MAX polling now gives HTTP reads timeout headroom over the long-poll `timeout` parameter and treats idle `ReadTimeout` as an empty poll instead of logging repeated error stack traces; startup allowlist diagnostics also recognize `MAX_ALLOWED_USERS`, `MAX_GROUP_ALLOWED_USERS`, and `MAX_ALLOW_ALL_USERS`.

### Added
- release-pinned `v2026.4.30` manifest and profiles: `v2026.4.30-upstream-fixes`, `v2026.4.30-provider-proxy`, `v2026.4.30-grok2api-sidecar`, and `v2026.4.30-personal`.
- refreshed `v2026.4.30` patch exports for `020`, `030`, `040`, `061`, and `080`; `040-telegram-free-response-target-gating` is now a first-class PatchKit patch for the clean official release.
- `scripts/grok2api_bridge.py list-models` and `sync-models` can now discover `/v1/models` from a running grok2api sidecar, filter chat-compatible ids, and generate/write the Hermes provider_proxy catalog with optional config backup.
- Grok2API sidecar bridge pack on top of `080-api-server-provider-proxy`: dedicated profiles, EN/RU docs, loopback Docker Compose/config examples, third-party MIT notice, and `scripts/grok2api_bridge.py` for config rendering/profile skeletons/endpoint doctor checks
- real exported upstream-candidate patch `080-api-server-provider-proxy`, adding an opt-in `provider_proxy` mode for the OpenAI-compatible API Server with explicit model catalog routing, OpenAI-compatible Chat Completions passthrough, Codex Responses compatibility, and fail-closed unsupported endpoints
- real exported local-overlay patch `077-max-markdown-formatting`, defaulting MAX outgoing text/captions to official Markdown formatting with `MAX_TEXT_FORMAT` configuration, MAX-safe Markdown prompt guidance, and live MAX Markdown/HTML rendering confirmation from fresh runtime sends
- real exported local-overlay patch `076-max-media-directive-safety`, preventing MAX `MEDIA:` documentation examples, placeholder paths, inline code, and fenced code blocks from being misrouted as native attachments
- real exported local-overlay patch `075-max-gateway-file-attachments`, adding MAX native file/document upload for non-image `MEDIA:/path` attachments and inbound file attachment caching as Hermes document events
- real exported local-overlay patch `074-max-send-message-media-routing`, routing `send_message` tool `MEDIA:/path` raster images for MAX through native image upload/send instead of omitting attachments as unsupported media
- real exported local-overlay patch `073-max-gateway-image-output`, adding MAX outbound image upload/send support for local `MEDIA:/path` images and markdown image URLs, with caption support and `attachment.not.ready` retry handling
- real exported local-overlay patch `071-max-gateway-image-input`, extending MAX inbound handling to image/photo attachments and image-only messages, with local image caching for Hermes vision tools
- real exported local-overlay patch `070-max-gateway-text-mvp` for a webhook-first, text-only MAX messenger gateway with explicit `MAX_TRANSPORT=polling` local-test fallback, configurable `MAX_POLL_TIMEOUT` / `MAX_POLL_IDLE_SLEEP` polling cadence, and CLI/status operator diagnostics for MAX setup without a live approved bot
- dedicated patch/feature catalog docs: `docs/en/patches.md` and `docs/ru/patches.md`
- `scripts/update.py`, a safe upstream compatibility checker that tests selected patches against a temporary upstream clone and writes markdown reports
- `scripts/tui.py`, a small terminal UI/guide over the update checker
- real exported upstream-fix patch `020-auth-profile-root-fallback`, including profile-to-root auth fallback tests
- real exported upstream-fix patch `030-credential-pool-recovery`, transplanted from the legacy fork credential-pool recovery commits
- real exported upstream-fix patches `060-codex-memory-flush-responses-contract` and `061-codex-auxiliary-tool-role-flattening`
- pinned manifest/profile entries for the exported auth, credential-pool and Codex patches
- unittest coverage for update classification and rollback cleanup after patches add new files

### Changed
- stable README/getting-started/update-workflow examples now point at the official `v2026.4.30` release manifest rather than post-release `origin/main` or the older `v2026.4.23` anchor.
- added `NEWS.md` and first-screen README links for the Grok2API sidecar bridge announcement, with a more public-facing summary of provider_proxy + safe model discovery
- README/README.ru and patch catalog docs now position `080-api-server-provider-proxy` as the featured provider gateway patch, with first-screen install commands and a clearer agent-endpoint vs provider-proxy distinction
- README/README.ru now link to the patch catalog instead of duplicating the patch list inline
- removed unsupported placeholder patch ideas from manifests, profiles and patch files
- README and update workflow docs now lead with the one-command update/TUI flow instead of maintainer-only manual steps
- `apply.py` now captures rollback state for exported patches, including patch-created untracked files and pre-apply dirty state when `--force` is used; forced apply now snapshots cleanup baselines after stashing dirty state so same-path untracked and ignored collisions are still recorded for rollback
- forced apply no longer hides root `venv/` or `.venv/` directories when capturing dirty state, preventing PatchKit from making an in-repo Hermes runtime virtualenv disappear
- `rollback.py` now restores the backup branch, removes only PatchKit-recorded untracked files, re-applies pre-existing dirty state captured during forced apply, and deletes recorded symlinks literally instead of following them into tracked content
- README and getting-started docs now point at a real exported patch flow instead of a placeholder-only example
