# News

## 2026-06-21 — Experimental MAX userbot gateway via PyMax

PatchKit now carries `078-max-userbot-platform-plugin`, a separate experimental `max_userbot` gateway plugin backed by MaxApiTeam/PyMax (`maxapi-python`). This is for deployments where official MAX Bot API bot creation is unavailable, but a user-account integration is acceptable.

The unit is intentionally separate from the official `070-max-platform-plugin`: it stores PyMax sessions profile-locally, locks the session file, supports TCP/WebClient bootstrap paths, allowlists, text/reply/edit, media mapping, PyMax file delivery, progress edits, and inline approval payloads. It uses MAX internal APIs rather than the official Bot API, so live use requires operator risk acceptance and a real account SMS/QR bootstrap.

---

# Новости

## 2026-06-21 — Experimental MAX userbot gateway через PyMax

PatchKit теперь несёт `078-max-userbot-platform-plugin`: отдельный experimental `max_userbot` gateway plugin на базе MaxApiTeam/PyMax (`maxapi-python`). Это вариант для случаев, когда official MAX Bot API bot создать нельзя, но допустима интеграция через user account.

Unit намеренно отделён от official `070-max-platform-plugin`: PyMax sessions хранятся profile-local, session file блокируется lock'ом, поддержаны TCP/WebClient bootstrap paths, allowlists, text/reply/edit, media mapping, PyMax file delivery, progress edits и inline approval payloads. Это internal MAX API, а не official Bot API, поэтому live use требует operator risk acceptance и реальный SMS/QR bootstrap аккаунта.

---

## 2026-06-20 — Hermes 0.17 re-anchor

PatchKit is now refreshed against official Hermes Agent `v2026.6.19` / `0.17.0`. The active release manifest is `manifests/upstream-v2026.6.19.yaml`; release patch files live under `patches/v2026.6.19/`.

Retirement audit: `061-codex-auxiliary-tool-role-flattening` and `095-gateway-busy-text-compat` are no longer carried as standalone units because upstream 0.17 absorbed those behaviors. The personal profile now carries 14 active units.

---

# Новости

## 2026-06-20 — Re-anchor на Hermes 0.17

PatchKit refresh'нут against official Hermes Agent `v2026.6.19` / `0.17.0`. Активный release manifest: `manifests/upstream-v2026.6.19.yaml`; release patch files лежат в `patches/v2026.6.19/`.

Retirement audit: `061-codex-auxiliary-tool-role-flattening` и `095-gateway-busy-text-compat` больше не несутся как отдельные units, потому что upstream 0.17 поглотил это поведение. Personal profile теперь содержит 14 active units.

---

## 2026-05-16 — Hermes 0.14 re-anchor and Grok sidecar retirement path

PatchKit is now refreshed against official Hermes Agent `v2026.5.16` / `0.14.0`. The active core profile stays release-pinned and uses `manifests/upstream-v2026.5.16.yaml` with `profiles/v2026.5.16-personal.yaml`.

The Grok2API sidecar bridge is no longer the preferred Grok path. Hermes 0.14 has native xAI / SuperGrok provider support through `xai` and `xai-oauth`; use that first. Keep `scripts/grok2api_bridge.py`, the old sidecar docs, and `examples/sidecars/grok2api/` only as a legacy fallback for cases where native xAI OAuth does not cover the target account/model/client.

What changed operationally:

- active patch units `020`, `030`, `040`, `050`, `061`, `070`, and `080` were re-exported for `v2026.5.16`;
- `020`, `030`, and `040` are narrower rewrites on top of adjacent upstream 0.14 primitives;
- `080-api-server-provider-proxy` remains the generic provider proxy / Codex Responses proxy layer and is not replaced by native xAI;
- no new release-pinned Grok2API profile is added for 0.14.

---

# Новости

## 2026-05-16 — Re-anchor на Hermes 0.14 и retirement path для Grok sidecar

PatchKit refresh'нут against official Hermes Agent `v2026.5.16` / `0.14.0`. Активный core profile остаётся release-pinned и использует `manifests/upstream-v2026.5.16.yaml` + `profiles/v2026.5.16-personal.yaml`.

Grok2API sidecar bridge больше не preferred Grok path. В Hermes 0.14 есть native xAI / SuperGrok provider support через `xai` и `xai-oauth`; сначала используем его. `scripts/grok2api_bridge.py`, старые sidecar docs и `examples/sidecars/grok2api/` оставлены только как legacy fallback, если native xAI OAuth не закрывает нужный account/model/client.

Операционно:

- active patch units `020`, `030`, `040`, `050`, `061`, `070` и `080` re-exported для `v2026.5.16`;
- `020`, `030` и `040` стали более узкими rewrites поверх соседних upstream 0.14 primitives;
- `080-api-server-provider-proxy` остаётся generic provider proxy / Codex Responses proxy layer и не заменяется native xAI;
- новый release-pinned Grok2API profile для 0.14 не добавляется.

---

## 2026-04-30 — Grok2API sidecar bridge: Grok-style models behind Hermes Provider Proxy

This is the kind of PatchKit feature that changes what the repo can do.

Hermes PatchKit now has a Grok2API sidecar bridge pack. It lets you run `chenyme/grok2api` as a separate local sidecar and expose selected Grok-style chat models through Hermes' OpenAI-compatible API Server provider proxy.

Why this is cool:

- Hermes stays generic. Grok2API is not vendored into Hermes and is not presented as an official Grok provider.
- The bridge is protocol-level: client → Hermes API Server → provider_proxy catalog → grok2api sidecar.
- Model discovery is automated, but safe: `sync-models` reads `/v1/models`, filters chat-capable IDs, and writes an explicit allowlist only when you pass `--write`.
- Unknown models fail closed. Hermes exposes only the public IDs you intentionally allow.
- The pack ships with EN/RU docs, dedicated profiles, Docker Compose examples, third-party notice, endpoint doctor checks, and catalog regression coverage.

Try the dry run:

```bash
OPENAI_API_KEY=<grok2api app.api_key> \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1
```

Then write the dedicated profile config:

```bash
OPENAI_API_KEY=<grok2api app.api_key> \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --write \
  --backup
```

Important boundary: Grok2API is a reverse-engineered gateway, not an official xAI/Grok API client. MIT licensing helps with code reuse, but it does not remove ToS, account-ban, Cloudflare/WAF, or upstream-breakage risk. Keep it loopback-only by default and use separate API keys.

Read more:

- docs/en/sidecars-grok2api.md
- docs/ru/sidecars-grok2api.md
- profiles/grok2api-sidecar.yaml
- examples/sidecars/grok2api/

---

# Новости

## 2026-04-30 — Grok2API sidecar bridge: Grok-подобные модели за Hermes Provider Proxy

Вот это уже не просто очередной patch в списке. Это новый класс возможностей для PatchKit.

В Hermes PatchKit появился Grok2API sidecar bridge pack. Он позволяет держать `chenyme/grok2api` отдельным локальным sidecar'ом и выводить выбранные Grok-подобные chat models через OpenAI-compatible Hermes API Server provider proxy.

Почему это круто:

- Hermes остаётся generic. Мы не vendoring'им Grok2API внутрь Hermes и не называем это официальным Grok provider.
- Bridge работает на уровне протокола: client → Hermes API Server → provider_proxy catalog → grok2api sidecar.
- Discovery моделей автоматизирован, но безопасен: `sync-models` читает `/v1/models`, оставляет chat-compatible IDs и пишет явный allowlist только с `--write`.
- Unknown models fail closed. Hermes показывает наружу только те public IDs, которые ты явно разрешил.
- В pack уже есть EN/RU docs, отдельные profiles, Docker Compose examples, third-party notice, doctor checks и regression coverage для catalog sync.

Dry run:

```bash
OPENAI_API_KEY=<grok2api app.api_key> \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1
```

Записать dedicated profile config:

```bash
OPENAI_API_KEY=<grok2api app.api_key> \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --write \
  --backup
```

Важная граница: Grok2API — reverse-engineered gateway, а не официальный xAI/Grok API client. MIT-лицензия помогает с reuse кода, но не убирает ToS, риск бана аккаунта, Cloudflare/WAF и риск поломки после upstream changes. По умолчанию держим sidecar только на loopback и используем отдельные API keys.

Подробнее:

- docs/en/sidecars-grok2api.md
- docs/ru/sidecars-grok2api.md
- profiles/grok2api-sidecar.yaml
- examples/sidecars/grok2api/
