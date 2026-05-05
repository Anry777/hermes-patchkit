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
| `070-max-platform-plugin` | exported | Adds MAX messenger as an official Hermes platform plugin rather than core gateway patches. | Single local-overlay patch for the `v2026.4.30` release manifest. It ships `plugins/platforms/max/plugin.yaml`, `plugins/platforms/max/adapter.py`, webhook-first production delivery, explicit polling fallback for local testing, native image/file attachments, safe `MEDIA:` handling, `send_message` media delivery, and MAX Markdown formatting. Enable the plugin separately with Hermes plugin/config workflow and set `MAX_BOT_TOKEN`. |
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
- MAX support is now a single release-pinned local-overlay plugin patch, `070-max-platform-plugin`; the previous split `070`-`077` core-gateway chain is kept only in legacy/canary manifests, not in `upstream-v2026.4.30.yaml`.
- Active `v2026.4.30` upstream/profile patches: `020`, `030`, `040`, `050`, `061`, `070-max-platform-plugin`, optional `080`, and UI/control-plane `200`–`215`.

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
