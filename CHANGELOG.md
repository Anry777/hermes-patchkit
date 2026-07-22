# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog.

## [Unreleased]

### Changed
- re-anchored PatchKit to Hermes Agent `v2026.7.20` / `0.19.0`, adding `manifests/upstream-v2026.7.20.yaml`, `profiles/v2026.7.20-upstream-fixes.yaml`, `profiles/v2026.7.20-personal.yaml`, `profiles/v2026.7.20-with-telegram-userbot.yaml`, and refreshed `patches/v2026.7.20/` exports.
- narrowed the v0.19 personal overlay by removing or reducing pieces now covered by upstream: general Telegram overflow duplicate handling, baseline media-delivery path denylist, adjacent session-reset recovery, and most credential-pool refresh/lease work.

### Added
- `079-telegram-userbot-platform-plugin`: experimental opt-in Telegram MTProto user-account adapter backed by Telethon, with profile-local locked sessions, deny-by-default allowlists, text/reply/edit/typing support, optional human-paced replies with per-sender bypass IDs, inbound media caching, native file delivery, focused tests, and EN/RU operator documentation.

### Fixed
- `100-vibemode-provider-plugin`: VibeMode OpenAI-wire clients now remove only OpenAI SDK `X-Stainless-*` identity metadata at the final HTTPX request boundary. This fixes false `Invalid API key` responses for valid `glm-5.2` credentials while preserving `Authorization`, `User-Agent: HermesAgent/1.0`, request payloads, and every non-VibeMode provider; main-agent, auxiliary sync/async, and API-server provider-proxy transports have regression coverage.
- `079-telegram-userbot-platform-plugin`: locally allowlisted Telethon senders are declared authorized before gateway dispatch, preventing bot-oriented pairing; the human-account transport now also suppresses onboarding, silently ignores recognized Hermes slash commands before active-session mutation, keeps internal agent failures server-side, and fails approval prompts closed without sending bot control UI. Suppressed `/stop`, `/new`, and `/reset` leave active tasks, guards, and pending work untouched; ordinary model replies and unknown slash-prefixed conversation text remain unaffected.

### Changed
- `079-telegram-userbot-platform-plugin`: added opt-in asynchronous human pacing with length-aware typing, jitter, generation-time accounting, an upper bound, and per-sender bypass IDs; narrowed the exported unit to its own plugin and focused tests by removing unrelated provider/registry test hunks.
- refreshed public README/catalog anchors to the current `v2026.7.20` / Hermes `0.19.0` release line.

### Fixed
- `080-api-server-provider-proxy`: Chat Completions requests routed to the ChatGPT Codex backend now reuse Hermes' canonical Codex Cloudflare headers (`originator`, Codex `User-Agent`, and JWT-derived account ID), preventing valid OAuth requests from being blocked as non-Codex traffic.

## 2026-07-05 — Hermes 0.18 re-anchor

### Changed
- re-anchored PatchKit to Hermes Agent `v2026.7.1` / `0.18.0`, adding `manifests/upstream-v2026.7.1.yaml`, `profiles/v2026.7.1-upstream-fixes.yaml`, `profiles/v2026.7.1-provider-proxy.yaml`, `profiles/v2026.7.1-personal.yaml`, and refreshed `patches/v2026.7.1/` exports.
- retired the stale NeuroGate provider patch line and kept VibeMode as the canonical provider plugin.
- kept the active v0.18 personal profile focused on 12 units: `010`, `020`, `030`, `041`, `070`, `078`, `080`, `090`, `096`, `097`, `099`, and `100`.

### Fixed
- `070-max-platform-plugin` and `078-max-userbot-platform-plugin`: accept the current gateway reconnect callback shape; `070` also keeps MAX persistent tool-progress bubbles compact and coalesces the first burst so raw command/URL previews are not posted as chat content.
- `041-telegram-rich-flood-fallback`: restores the PatchKit Telegram duplicate guard for v0.18 when a finalized overflow first-chunk edit hits flood control; Hermes keeps the visible streaming prefix and sends only the missing tail instead of a second full formatted answer.
- `100-vibemode-provider-plugin`: sends `User-Agent: HermesAgent/1.0` through provider-profile metadata for both OpenAI-compatible and Anthropic Messages transports, uses Bearer auth for VibeMode Messages, and treats Cloudflare/WAF 403 blocks as transport/header failures instead of exhausting the credential pool.

### Retired
- `040-telegram-free-response-target-gating`, `091-email-smtp-ssl`, `092-gateway-document-media-types`, and `098-api-server-fallback-model-kwarg`: upstream v0.18 covers these behaviors for the release line.
- `050-homeassistant-tool-config-url`: the old config-sourced Home Assistant tool URL overlay is no longer selected for v0.18 profiles.

## 2026-05-16 — Hermes 0.14 re-anchor

- added release-pinned `v2026.5.16` / Hermes Agent `0.14.0` manifest and profiles: `v2026.5.16-upstream-fixes`, `v2026.5.16-provider-proxy`, and `v2026.5.16-personal`;
- refreshed active patch units `020`, `030`, `040`, `050`, `061`, `070`, and `080` against official tag `v2026.5.16`;
- kept `020`, `030`, and `040` as narrower overlays on top of adjacent upstream auth, credential-pool, and Telegram gating primitives instead of dropping them;
- marked the Grok2API sidecar bridge as legacy fallback infrastructure now that Hermes 0.14 has native `xai` / `xai-oauth` support; no new active `v2026.5.16-grok2api-sidecar` profile is shipped;
- kept `080-api-server-provider-proxy` as the generic provider proxy / Codex Responses proxy layer; native xAI does not replace it.
