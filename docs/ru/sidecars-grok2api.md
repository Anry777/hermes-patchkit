# Grok2API sidecar bridge

Это первый sidecar bridge в PatchKit: используем уже существующий patch `080-api-server-provider-proxy`, чтобы провести локальный grok2api через dedicated Hermes API Server profile.

Идея не в том, чтобы копировать grok2api внутрь Hermes. grok2api остаётся отдельным sidecar, а Hermes даёт catalog-routed OpenAI-compatible front door.

## Что получаем

- локальный `/v1/models` catalog из Hermes provider_proxy mode;
- routing по `body.model` к OpenAI-compatible grok2api endpoint;
- без Hermes `AIAgent`, SOUL prompt, tools, memory, sessions и transcript state в proxy path;
- обратимый PatchKit profile: `profiles/grok2api-sidecar.yaml`;
- маленький doctor script: `scripts/grok2api_bridge.py`.

## Лицензия и граница риска

У Grok2API MIT license (`Copyright (c) 2026 Chenyme`) по upstream `LICENSE`, проверенному 2026-04-30. PatchKit не vendoring'ит его код; интеграция идёт по протоколу, attribution лежит в `examples/sidecars/grok2api/THIRD_PARTY_NOTICE.md`.

MIT покрывает код. Она не меняет Grok/xAI terms, риск бана аккаунтов, Cloudflare/WAF поведение и хрупкость reverse-engineered web flows. Этот bridge нужно считать explicit self-hosted sidecar integration, не official Grok API provider.

## Установить Hermes provider proxy patch

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/grok2api-sidecar.yaml \
  --yes
```

Для canary/main проверки используй `manifests/canary-main-a1921c43c.yaml` и `profiles/canary-main-grok2api-sidecar.yaml`.

## Запустить grok2api как loopback sidecar

```bash
mkdir -p ~/grok2api-sidecar
cp examples/sidecars/grok2api/docker-compose.yml ~/grok2api-sidecar/docker-compose.yml
cp examples/sidecars/grok2api/.env.example ~/grok2api-sidecar/.env
cd ~/grok2api-sidecar
docker compose up -d
```

После первого старта настрой сам grok2api: поменяй admin key, API key, app URL при необходимости и добавь аккаунты по его документации. Держи container на `127.0.0.1`, если поверх него нет отдельного auth/network layer.

## Создать dedicated Hermes profile

Показать config:

```bash
python3 scripts/grok2api_bridge.py render-config \
  --base-url http://127.0.0.1:8000/v1 \
  --public-model grok2api/grok-3 \
  --target-model grok-3
```

Или записать skeleton profile:

```bash
python3 scripts/grok2api_bridge.py write-profile \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --public-model grok2api/grok-3 \
  --target-model grok-3
```

Потом локально заполни `~/.hermes/profiles/provider-proxy-grok2api/.env`:

```dotenv
OPENAI_API_KEY=<grok2api app.api_key, если он настроен>
API_SERVER_KEY=<Bearer key для клиентов Hermes API Server>
```

Bridge использует `provider: openai` плюс `base_url: http://127.0.0.1:8000/v1`, поэтому provider_proxy path разговаривает с grok2api как с OpenAI-compatible endpoint.

## Автоматически синхронизировать catalog моделей

Когда grok2api уже запущен, model ids не нужно переносить руками. Helper может спросить у sidecar `/v1/models` и сгенерировать Hermes provider_proxy allowlist из ответа:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1
```

Без `--write` это dry run: команда показывает найденные sidecar ids, отфильтрованные public ids, которые Hermes будет показывать наружу, и generated config. Default filter намеренно chat-only: include `^grok-`, exclude `imagine`, `image`, `video`, `edit`, потому что текущий provider_proxy patch обслуживает `/v1/chat/completions`, а не image/video endpoints grok2api.

После проверки dry run можно записать dedicated profile config:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --write \
  --backup
```

Public ids по умолчанию получают prefix, например `grok2api/grok-4.20-auto` мапится на internal sidecar model `grok-4.20-auto`. Посмотреть raw sidecar ids без записи config можно так:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py list-models \
  --base-url http://127.0.0.1:8000/v1
```

Если catalog в grok2api поменялся, повтори `sync-models --write --backup` и перезапусти Hermes gateway для этого profile.

## Doctor checks

Проверить только catalog endpoint:

```bash
OPENAI_API_KEY=<sidecar-key> \
python3 scripts/grok2api_bridge.py doctor \
  --base-url http://127.0.0.1:8000/v1 \
  --skip-chat
```

Минимальный chat smoke:

```bash
OPENAI_API_KEY=<sidecar-key> \
python3 scripts/grok2api_bridge.py doctor \
  --base-url http://127.0.0.1:8000/v1 \
  --model grok-3
```

Скрипт redacts API key в printed errors/bodies.

## Запустить Hermes API Server

```bash
hermes --profile provider-proxy-grok2api gateway start
```

Проверка клиентом:

```bash
export API_SERVER_KEY=<Bearer key для клиентов Hermes API Server>

curl -s http://127.0.0.1:8642/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"

curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"grok2api/grok-3","messages":[{"role":"user","content":"say ok"}],"stream":false}'
```

## Рабочие defaults

- Держать grok2api и Hermes provider_proxy в dedicated profiles/directories.
- Не expose'ить grok2api напрямую в публичный интернет.
- Не жить на `latest` вслепую для long-running deploy: после smoke tests pin image tag/digest.
- Не класть реальные ключи в repo files или examples.
- Не включать это в default/minimal profiles; bridge должен быть explicit.
