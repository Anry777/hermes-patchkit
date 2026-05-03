# Patches and features

This file is the public catalog for supported PatchKit patch units and workflow features. The README links here instead of duplicating a patch list.

Compatibility is not a static promise. Run `scripts/update.py` or `scripts/tui.py` against your Hermes checkout before applying anything.

Current release anchor: `manifests/upstream-v2026.4.30.yaml`. The release-specific patch files live under `patches/v2026.4.30/` and are checked against the official `NousResearch/hermes-agent` tag `v2026.4.30`, not post-release `main`.

## Available patch units

| Patch | Status | What it does | Notes |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Stops idle CLI/TUI repaint from pulling the terminal viewport. | Applies cleanly in the latest live smoke check. |
| `020-auth-profile-root-fallback` | exported | Lets profile auth stores fall back to the root auth store when the profile has no `auth.json` yet. | Has focused auth/profile regression coverage. |
| `030-credential-pool-recovery` | exported | Improves credential-pool recovery by tracking the active credential ID, keeping invalid credentials out of cooldown recovery, and rotating round-robin entries only after leases are released. | Transplanted from the legacy fork commits `e17a823c` and `97fa2dbc`; depends on `020-auth-profile-root-fallback`. |
| `040-telegram-free-response-target-gating` | exported | Prevents Telegram free-response group chats from hijacking messages explicitly addressed to another bot or user. | Uses positive addressing: direct mentions/replies/wake words address this bot, but fresh explicit addressing to another target (`@other_bot`, `/cmd@other_bot`, `Name, ...`) wins over reply context; ambient free-response chat does not hijack unaddressed questions. |
| `050-homeassistant-tool-config-url` | exported | Lets Home Assistant tools read `platforms.homeassistant.extra.url` from profile `config.yaml` when `HASS_URL` is absent. | Keeps env override compatibility and the existing `homeassistant.local` fallback; includes focused tool/config regression coverage plus a live read-only smoke check. |
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
| `080-api-server-provider-proxy` | exported | Adds an opt-in `provider_proxy` mode to the OpenAI-compatible API Server: `/v1/models` returns an explicit catalog and `/v1/chat/completions` routes to configured provider/model targets without creating an `AIAgent`. | Generic upstream-candidate patch. Supports non-streaming and streaming Chat Completions for OpenAI-compatible providers, plus a compatibility path for `openai-codex`/Responses that adapts Responses streams into OpenAI Chat Completion SSE chunks, maps `reasoning_effort`, and filters ChatGPT Codex-rejected sampling params such as `temperature`. `/v1/responses` and `/v1/runs` still fail closed as unsupported operations. |
| `200-dashboard-profile-api` | exported | Adds an authenticated read-only profile inventory API for the built-in dashboard. | First upstream-candidate patch in the `200`–`249` UI/control-plane line; does not expose secrets, session messages, or log contents. |
| `201-dashboard-profile-selector` | exported | Adds the built-in Profiles page and sidebar selector/cards on top of `200-dashboard-profile-api`. | Shows model/provider, skills, env presence, gateway status, paths, session counts, and log-file metadata; selection does not mutate the global active profile. |
| `202-dashboard-profile-aware-pty` | exported | Adds profile-aware embedded `hermes --tui` through the existing dashboard PTY bridge. | `/chat?profile=<name>` and `/api/pty?profile=<name>` validate the profile, spawn the PTY child with profile-scoped `HERMES_HOME`, preserve resume forwarding, and do not mutate the global active profile. |

## Patch highlights

### `080-api-server-provider-proxy`

This is the current flagship PatchKit feature patch. It is not another “run the same Hermes agent on a different model” tweak. It adds a separate API Server mode for users who want Hermes to expose a standard OpenAI-compatible endpoint backed by multiple provider models.

Upstream Hermes does not provide this provider-gateway split today: its API Server path is built around the running Hermes agent/profile. `080` adds the missing boundary. When configured with `mode: provider_proxy` and a `provider_proxy.models` allowlist, the server becomes a catalog-routed provider proxy. In that mode:

- `/v1/models` returns only the configured public model IDs;
- `/v1/chat/completions` routes by `body.model` to the configured provider/model target;
- Hermes bypasses `AIAgent`, so there are no Hermes tools, memory, sessions, SOUL/context injection, or agent run semantics;
- OpenAI-compatible providers use a Chat Completions passthrough;
- `openai-codex` / Responses providers use a compatibility adapter;
- `stream: true` returns OpenAI-compatible `text/event-stream` chunks when `allow_streaming: true` is configured;
- OpenAI-style `tools`, `tool_choice`, assistant `tool_calls`, `role: tool` results, `parallel_tool_calls`, and inline `image_url` / `input_image` parts are preserved for IDE clients;
- RooCode-style `reasoning_effort` is mapped to Responses `reasoning.effort` for Codex-backed targets;
- ChatGPT Codex-rejected sampling params such as `temperature`, `top_p`, penalties, `seed`, and logprob knobs are filtered before the upstream call;
- `/v1/responses` and `/v1/runs` fail closed until separate patches add those agent-style surfaces.

Use the dedicated profile when you want to install just this provider gateway patch:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-provider-proxy.yaml \
  --yes
```

Canary/main users should use `manifests/canary-main-a1921c43c.yaml` with `profiles/canary-main-provider-proxy.yaml`.

### Grok2API sidecar bridge

The first provider_proxy sidecar pack is documented in [sidecars-grok2api.md](sidecars-grok2api.md). It keeps grok2api deployed separately, adds PatchKit profiles that select only `080`, ships loopback Docker Compose/config examples, and provides `scripts/grok2api_bridge.py` for config rendering and endpoint smoke checks. This is intentionally an explicit sidecar integration, not a vendored Grok provider and not part of default profiles.

## Release `v2026.4.30` compatibility

The release manifest intentionally excludes patch units that no longer fit the official release cleanly:

- `010-cli-tui-idle-refresh-fix` is superseded by upstream idle repaint changes in `v2026.4.30`.
- `060-codex-memory-flush-responses-contract` is obsolete because the old `flush_memories` path was removed/refactored upstream.
- MAX local-overlay patches `070`-`077` are not in the `v2026.4.30` release manifest yet; the official release has no MAX adapter, so that chain needs a fresh sequential refresh from `070` onward.
- Active `v2026.4.30` upstream/profile patches: `020`, `030`, `040`, `050`, `061`, optional `080`, and UI/control-plane `200`/`201`/`202`/`203`.

## Planned `200`+ UI line

Patch numbers `200`–`249` are reserved for the Hermes-native multi-profile dashboard line. The concept and first-wave sequence are documented separately: [ui-control-plane-plan.md](ui-control-plane-plan.md).

Initial sequence:

| Patch | Status | Intended scope |
|---|---|---|
| `200-dashboard-profile-api` | exported | Authenticated read-only endpoints `/api/dashboard/profiles` and `/api/dashboard/profiles/{name}` for safe profile inventory: model/provider, skills, gateway, session metadata and log metadata. |
| `201-dashboard-profile-selector` | exported | Built-in dashboard Profiles page plus sidebar selector/cards on top of `200`: model/provider, skills, env presence, gateway, paths, session counts and log metadata without changing the global active profile. |
| `202-dashboard-profile-aware-pty` | exported | Embedded `hermes --tui` terminal with optional `profile=<name>` on the existing PTY bridge; profile-scoped `HERMES_HOME`, resume forwarding, and an Open terminal action from the Profiles page. |
| `203-dashboard-terminal-workspace` | exported | Remote terminal workspace foundation: authenticated dashboard WebSockets (`/api/pty`, `/api/ws`, `/api/pub`, `/api/events`) stay loopback-only by default but work for remote browsers under explicit `--insecure`, unlocking live `/chat?profile=<name>` on the dashboard service. |
| `204-dashboard-runtime-registry` | planned | Read-only registry for live Hermes/TUI/gateway/worker processes. |
| `205-dashboard-worker-roster` | planned | Worker cards/roster: role, lane, mission, active task/tool and blocked reason. |
| `206-dashboard-session-log-inspector` | planned | Profile-aware sessions/logs/tool-call inspector. |
| `207-dashboard-assembly-analytics` | planned | Profile-aware analytics plus whole-assembly summary across all profiles: usage, cost, model/provider distribution, top profiles and stale profiles. |
| `208-dashboard-controlled-actions` | planned | Auth-gated controlled actions after read-only observability: stop/restart selected terminal/worker/gateway. |

## Workflow features

| Feature | Entry point | Status |
|---|---|---|
| Upstream compatibility check | `scripts/update.py` | working |
| Terminal update dashboard | `scripts/tui.py` | working |
| Target checkout preflight | `scripts/doctor.py` | working |
| Patch/profile apply with backup state | `scripts/apply.py` | working for exported patches |
| Rollback of PatchKit apply | `scripts/rollback.py` | working with regression coverage for tracked, untracked and ignored cleanup cases |
| Repository self-check | `scripts/verify.py --self-check` | working |
| Grok2API sidecar bridge helper | `scripts/grok2api_bridge.py` | working helper/docs layer over `080-api-server-provider-proxy` |

## Status meanings

- `exported`: the patch file contains a real unified diff.
- `planned`: the patch ID is kept in the manifest as planned work, but the real diff is not ready.
- `needs refresh check`: the patch exists, but current upstream compatibility needs maintainer review.
- `local-overlay`: a PatchKit-maintained integration or customization that is useful locally but not assumed to be upstream-bound.

Removed ideas are not listed here. This catalog is for PatchKit units that are meant to stay maintained.
