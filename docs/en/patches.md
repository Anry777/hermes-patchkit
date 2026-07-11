# Patches and features

This file is the public catalog for supported PatchKit patch units and workflow features. The README links here instead of duplicating a patch list.

Compatibility is not a static promise. Run `scripts/update.py` or `scripts/tui.py` against your Hermes checkout before applying anything.

Current release anchor: `manifests/upstream-v2026.7.7.2.yaml`. The release-specific patch files live under `patches/v2026.7.7.2/` and are checked against the official `NousResearch/hermes-agent` tag `v2026.7.7.2` / Hermes Agent `0.18.2`, not post-release `main`.

## Available patch units

| Patch | Status | What it does | Notes |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Stops idle classic-CLI repaint from pulling the terminal viewport. | PatchKit keeps `display.cli_refresh_interval` defaulted to `0`; explicit profile config still wins. |
| `020-auth-profile-root-fallback` | exported | Makes `auth.json` and `auth.lock` root-global so all profiles share provider OAuth state and credential pools. | Keeps config, sessions, skills and logs profile-local. |
| `030-credential-pool-recovery` | exported | Keeps the remaining PatchKit credential-pool safety semantics on Hermes v0.18. | Codex aux does not bypass exhausted pools through the singleton; stale ok+reset markers are cleared; terminal dead credentials do not keep retry reset state. Depends on `020`. |
| `041-telegram-rich-flood-fallback` | exported | Restores Telegram duplicate-safety for the v0.18 finalize + overflow split + first-chunk flood-control path. | If Telegram flood-limits the cosmetic first-chunk finalize edit, Hermes treats the visible streaming prefix as partial-overflow delivery and sends only the missing tail instead of posting a duplicate full formatted final answer. |
| `070-max-platform-plugin` | exported | Adds MAX messenger as an official Hermes platform plugin rather than core gateway patches. | Webhook-first, explicit polling fallback, native media/files/audio, Markdown, typing, progress edits, approval buttons, and safe media delivery. |
| `078-max-userbot-platform-plugin` | exported | Adds a separate experimental `max_userbot` platform plugin backed by MaxApiTeam/PyMax. | Internal/unofficial MAX user-account path; live use requires operator risk acceptance and SMS/QR bootstrap. |
| `079-telegram-userbot-platform-plugin` | exported | Adds a separate experimental `telegram_userbot` platform plugin backed by Telethon/MTProto. | User-account path with profile-local locked sessions and deny-by-default allowlists; see [telegram-userbot.md](telegram-userbot.md). |
| `080-api-server-provider-proxy` | exported | Adds opt-in raw provider proxy modes to the OpenAI-compatible API Server. | Includes catalog-routed Chat Completions provider proxy and Responses-native `codex_responses_proxy` without creating `AIAgent` instances. |
| `090-lsp-configured-websocket-transport` | exported | Adds config-driven custom LSP servers and a WebSocket transport for Hermes LSP. | Lets external language servers such as BSL LS connect without hardcoded profile paths/endpoints. |
| `096-provider-plugin-model-switch` | exported | Makes model-provider plugins visible to `/model`, `/mode`, runtime provider resolution, and context-window metadata. | Plugin-backed providers such as `vibemode` no longer need duplicate `config.yaml providers:` entries. |
| `097-gateway-explicit-media-delivery-safety` | exported | Makes gateway local-file delivery explicit by default. | `MEDIA:/path` and structured artifacts deliver as native attachments; bare absolute paths stay text unless `gateway.auto_upload_local_paths: true`. |
| `099-gateway-auto-reset-context-continuity` | exported | Keeps gateway chat context across idle/daily auto-reset. | New auto-reset sessions link to the expired parent and rehydrate reset-parent transcripts; manual `/new` and `/reset` stay fresh. |
| `100-vibemode-provider-plugin` | exported | Adds the VibeMode provider plugin, User-Agent propagation, Bearer auth for Messages, and per-model endpoint metadata. | Sends `User-Agent: HermesAgent/1.0` across OpenAI-compatible and Anthropic Messages transports, avoids x-api-key auth on VibeMode Messages, and avoids exhausting credentials on Cloudflare/WAF 403 blocks; model availability remains live-discovered from `/v1/models`. |
| `040-telegram-free-response-target-gating` | retired in `v2026.7.1` | Upstream v0.18 now carries the Telegram gating behavior needed for the release line. | No standalone v0.18 patch file is shipped. |
| `050-homeassistant-tool-config-url` | retired in `v2026.7.1` | Upstream/config-sourced behavior no longer needs PatchKit's old Home Assistant tool URL overlay. | The v0.18 profiles do not select it. |
| `091-email-smtp-ssl` | retired in `v2026.7.1` | Upstream v0.18 email plugin uses SMTP_SSL for port 465 and STARTTLS otherwise. | No standalone v0.18 patch file is shipped. |
| `092-gateway-document-media-types` | retired in `v2026.7.1` | Upstream v0.18 has unified media/document extension handling and MEDIA cleanup regexes. | No standalone v0.18 patch file is shipped. |
| `098-api-server-fallback-model-kwarg` | retired in `v2026.7.1` | Upstream v0.18 pops duplicate `model` kwargs before API Server fallback agent construction. | No standalone v0.18 patch file is shipped. |

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
- ChatGPT Codex-rejected sampling params such as `temperature`, `top_p`, penalties, `seed`, and logprob knobs are filtered before the upstream call.

The same `080` unit also includes `mode: codex_responses_proxy` for a separate profile/port when the client speaks Responses natively. In that mode:

- `/v1/models` can live-query the `openai-codex` model catalog and then apply configured allow/deny regex filters;
- `/v1/responses` forwards the caller's Responses body to the Codex Responses backend through Hermes' OAuth credential pool; for the ChatGPT Codex backend it forces `store: false` even when a client sends `store: true`;
- completed non-streaming responses and completed streams record success for the selected pool credential, while 401/402/429 upstream failures mark that selected credential exhausted and rotate the pool;
- `stream: true` keeps Responses SSE events such as `response.created`, `response.output_text.delta`, and `response.completed` instead of converting them to Chat Completions chunks;
- `/v1/chat/completions` and `/v1/runs` fail closed so Responses-native clients do not share a mixed wire contract with Chat Completions clients.

Use the dedicated profile when you want to install just this provider gateway patch:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.7.1.yaml \
  --profile profiles/v2026.7.1-provider-proxy.yaml \
  --yes
```

Canary/main users should use `manifests/canary-main-a1921c43c.yaml` with `profiles/canary-main-provider-proxy.yaml`.

### Grok2API sidecar bridge

The first provider_proxy sidecar pack is documented in [sidecars-grok2api.md](sidecars-grok2api.md), but after Hermes `0.14.0` it is legacy fallback infrastructure. Prefer native upstream `xai` / `xai-oauth` for Grok and SuperGrok. The old grok2api helper/examples stay available for explicit self-hosted fallback cases, but PatchKit does not add a new `v2026.5.16-grok2api-sidecar` active profile.

## Release `v2026.5.16` / Hermes 0.14 compatibility

The 0.14 manifest keeps the active core overlays release-pinned and excludes old dashboard/UI `200`–`215` work from the personal runtime line. Retirement audit result:

- `010-cli-tui-idle-refresh-fix` remains superseded upstream.
- `060-codex-memory-flush-responses-contract` remains obsolete after upstream memory-flush refactors.
- `020`, `030`, and `040` were refreshed as narrower overlays on top of adjacent upstream auth, credential-pool, and Telegram gating primitives.
- `050`, `061`, `070-max-platform-plugin`, and `080-api-server-provider-proxy` still carry PatchKit behavior not replaced by upstream 0.14.
- Grok2API sidecar profiles are legacy fallback only; use native `xai` / `xai-oauth` first.

## Planned `200`+ UI line

Patch numbers `200`–`249` are reserved for the Hermes-native multi-profile dashboard line. The concept and first-wave sequence are documented separately: [ui-control-plane-plan.md](ui-control-plane-plan.md).

Initial sequence:

| Patch | Status | Intended scope |
|---|---|---|
| `200-dashboard-profile-api` | exported | Authenticated read-only endpoints `/api/dashboard/profiles` and `/api/dashboard/profiles/{name}` for safe profile inventory: model/provider, skills, gateway, session metadata and log metadata. |
| `201-dashboard-profile-selector` | exported | Built-in dashboard Profiles page plus sidebar selector/cards on top of `200`: model/provider, skills, env presence, gateway, paths, session counts and log metadata without changing the global active profile. |
| `202-dashboard-profile-aware-pty` | exported | Embedded `hermes --tui` terminal with optional `profile=<name>` on the existing PTY bridge; profile-scoped `HERMES_HOME`, resume forwarding, and an Open terminal action from the Profiles page. |
| `203-dashboard-terminal-workspace` | exported | Remote terminal workspace foundation: authenticated dashboard WebSockets (`/api/pty`, `/api/ws`, `/api/pub`, `/api/events`) stay loopback-only by default but work for remote browsers under explicit `--insecure`, unlocking live `/chat?profile=<name>` on the dashboard service. |
| `204-dashboard-runtime-registry` | exported | Authenticated read-only `/api/dashboard/runtimes`: dashboard process state, live PTY sessions with profile/cwd/pid/resume/terminal size, action subprocess liveness and event-channel counts without argv/env/output/session/log/memory bodies. |
| `205-dashboard-worker-roster` | exported | Authenticated read-only `/api/dashboard/worker-roster`: configured profile-local workers from `dashboard/worker_roster.json` plus live PTY runtime workers from `204`, with safe role/lane/mission/model/capability/process metadata and no secrets/env/output/session/log/memory bodies. |
| `206-dashboard-terminal-profile-lifecycle` | exported | Bugfix/control slice: Open terminal from a profile creates a unique `/chat?profile=<name>&terminal=<id>` channel instead of reusing the default Chat terminal; Chat now has Close terminal backed by `DELETE /api/dashboard/runtimes/pty/{id}`. |
| `207-dashboard-session-log-inspector` | exported | Profile-aware read-only session/log inspector: `/api/dashboard/profiles/{name}/sessions`, `/sessions/{session_id}` and `/logs` expose safe session counts, token/cost metadata, message/tool-call summaries and log-file metadata without message bodies, raw tool args, system prompts, log contents, env or secrets. |
| `208-dashboard-terminal-workspace-tabs` | exported | App-level multi-terminal workspace tabs: default Chat and profile terminals remain separate mounted PTY panes, switching tabs does not kill other terminals, and closing a tab requires confirmation before terminating exactly that PTY via `DELETE /api/dashboard/runtimes/pty/{id}`. |
| `209-dashboard-assembly-analytics` | exported | Authenticated safe whole-assembly analytics across all profiles: profile activity/staleness, token and cost totals, API/tool-call counts, top profiles, and model/provider distribution without session IDs, message bodies, tool args, logs, env or secrets. |
| `210-dashboard-controlled-actions` | exported | Auth-gated allowlisted dashboard mutation layer: `/api/dashboard/actions` lists exact-confirmation actions and `/api/dashboard/actions/{id}/run` runs only confirmed gateway restart / Hermes update actions while preserving detached action status logs. |
| `211-dashboard-control-plane-unification` | exported | Stabilizes the dashboard into one control plane: authenticated `/api/dashboard/overview` becomes the shared semantic source for sidebar, Overview, Sessions, profiles, terminals and gateway platforms; stale platform rows require attention and the bundled example plugin is hidden unless explicitly enabled for development. |
| `212-dashboard-visual-polish` | exported | Polishes the unified dashboard overview after `211`: shared visual primitives for the content shell, cards, hero, KPI grid, density table, freshness rows, and sidebar status improve spacing/contrast/hierarchy without changing the data contract. |
| `213-dashboard-overview-semantic-cleanup` | exported | Clarifies unified Overview semantics: assembly-wide scope, selected-profile context, structured Action required items, and runtime health evidence instead of mixing profile staleness with urgent alerts. Stale session history stays metadata; active alert items carry source, severity, reason, message and action; provider-proxy is shown as service/API health evidence. |
| `214-dashboard-messaging-adapters-semantics` | exported | Renames Gateway platforms to Messaging adapters and separates adapter availability from event freshness. Connected-but-stale adapters remain check-freshness metadata; only unhealthy adapter state creates Action required items. |
| `215-dashboard-system-overview-semantics` | exported | Makes Overview a system-wide summary: removes the dominant `Selected profile` framing, adds `system_summary`, a profile table, and memory inventory with live Hindsight bank counts. | `selected_profile` remains as a backward-compatible API field; the memory section separates shared Hindsight banks from local profile memory and shows only metadata/counts without memory contents; the endpoint runs sync Hindsight probing off the FastAPI event loop to avoid count fallbacks. |

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
