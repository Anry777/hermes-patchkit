# News

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
