# Patches and features

This file is the public catalog for supported PatchKit patch units and workflow features. The README links here instead of duplicating a patch list.

Compatibility is not a static promise. Run `scripts/update.py` or `scripts/tui.py` against your Hermes checkout before applying anything.

## Available patch units

| Patch | Status | What it does | Notes |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Stops idle CLI/TUI repaint from pulling the terminal viewport. | Applies cleanly in the latest live smoke check. |
| `020-auth-profile-root-fallback` | exported | Lets profile auth stores fall back to the root auth store when the profile has no `auth.json` yet. | Has focused auth/profile regression coverage. |
| `030-credential-pool-recovery` | exported | Improves credential-pool recovery by tracking the active credential ID, keeping invalid credentials out of cooldown recovery, and rotating round-robin entries only after leases are released. | Transplanted from the legacy fork commits `e17a823c` and `97fa2dbc`; depends on `020-auth-profile-root-fallback`. |
| `060-codex-memory-flush-responses-contract` | exported, needs refresh check | Keeps Codex memory flush on the Responses transport contract. | Conflicts with current fetched upstream in `run_agent.py`; refresh or retire before the next live upstream merge. |
| `061-codex-auxiliary-tool-role-flattening` | exported | Flattens unsupported transcript roles such as `tool` before auxiliary Codex Responses calls. | Applies cleanly in the latest live smoke check. |
| `070-max-gateway-text-mvp` | exported | Adds a text-only MAX messenger gateway using webhook-first production inbound delivery, explicit `MAX_TRANSPORT=polling` for local testing, configurable polling cadence, operator status diagnostics, and `POST /messages` outbound text. | Local-overlay patch; webhook remains the default production transport, while `GET /updates` is available only as an opt-in dev/test fallback (`MAX_POLL_TIMEOUT`, `MAX_POLL_IDLE_SLEEP`). The polling request timeout now has headroom over MAX long-poll timeout so idle polls do not spam `ReadTimeout` stack traces. `hermes status` and gateway setup now spell out active MAX mode and missing webhook/public URL pieces without needing a live approved bot. |
| `071-max-gateway-image-input` | exported | Extends the MAX gateway to accept inbound image attachments and pass them to Hermes vision analysis as photo events. | Depends on `070-max-gateway-text-mvp`. Handles `MessageBody.attachments` image/photo payloads with `url`, `download_url`, `urls`, or `photos` variants, picks the largest photo variant when present, caches image URLs locally before dispatch, and keeps image-only messages instead of dropping them. |
| `072-max-gateway-oneme-url-safety` | exported | Allows MAX's exact image CDN host `i.oneme.ru` through URL safety when it resolves to `198.18.0.0/15`, so inbound photos can be cached locally before vision analysis. | Depends on `071-max-gateway-image-input`. The exception is exact-host and HTTPS-only: subdomains, HTTP URLs, and unrelated hosts that resolve to benchmark/private-style addresses remain blocked by SSRF protection. |
| `073-max-gateway-image-output` | exported | Adds outbound MAX image delivery: local `MEDIA:/path` images and markdown image URLs are uploaded through MAX `/uploads?type=image` and sent as native image attachments. | Depends on `072-max-gateway-oneme-url-safety`. Preserves text-only sending, supports optional captions/notify metadata, uses multipart field `data`, and retries `attachment.not.ready` from the final `POST /messages`. |
| `074-max-send-message-media-routing` | exported | Routes `send_message` tool `MEDIA:/path` image attachments for MAX into the native MAX image upload path instead of omitting them as unsupported media. | Depends on `073-max-gateway-image-output`. Supports raster image attachments (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) and updates the MAX prompt hint to avoid SVG photo delivery. |
| `075-max-gateway-file-attachments` | exported | Adds native MAX file/document delivery and inbound document caching: non-image `MEDIA:/path` files are uploaded through `/uploads?type=file`, and inbound file attachments become Hermes document events. | Depends on `074-max-send-message-media-routing`. Keeps raster images on the existing native image path, routes files such as `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, and `.xlsx` through file attachments, and avoids exposing local filesystem paths as chat text. |
| `076-max-media-directive-safety` | exported | Stops documented `MEDIA:` examples and markdown/code snippets from being parsed as real attachments. | Depends on `075-max-gateway-file-attachments`. `MEDIA:` directives for MAX must be real local paths on their own plain line, not placeholder paths, inline code, or fenced code blocks. |
| `077-max-markdown-formatting` | exported | Makes outgoing MAX text less flat by sending text and captions with official MAX Markdown formatting by default. | Depends on `076-max-media-directive-safety`. Adds configurable `MAX_TEXT_FORMAT` (`markdown`, `html`, or invalid/disabled values to omit formatting metadata), preserves explicit per-message metadata overrides, and updates the MAX prompt hint to use concise MAX-safe Markdown without wrapping `MEDIA:` lines in code blocks. Fresh runtime live sends confirmed that MAX renders both Markdown and HTML formatting; if raw Markdown appears again, restart the gateway/tool process before changing payload logic. |

## Workflow features

| Feature | Entry point | Status |
|---|---|---|
| Upstream compatibility check | `scripts/update.py` | working |
| Terminal update dashboard | `scripts/tui.py` | working |
| Target checkout preflight | `scripts/doctor.py` | working |
| Patch/profile apply with backup state | `scripts/apply.py` | working for exported patches |
| Rollback of PatchKit apply | `scripts/rollback.py` | working with regression coverage for tracked, untracked and ignored cleanup cases |
| Repository self-check | `scripts/verify.py --self-check` | working |

## Status meanings

- `exported`: the patch file contains a real unified diff.
- `planned`: the patch ID is kept in the manifest as planned work, but the real diff is not ready.
- `needs refresh check`: the patch exists, but current upstream compatibility needs maintainer review.
- `local-overlay`: a PatchKit-maintained integration or customization that is useful locally but not assumed to be upstream-bound.

Removed ideas are not listed here. This catalog is for PatchKit units that are meant to stay maintained.
