# Hermes PatchKit

Оставь official Hermes upstream базой. Нужные фиксы и фичи держи отдельными patch'ами.

Ты пропатчил Hermes. Upstream обновился. Что теперь?

Hermes PatchKit проверяет твои локальные фиксы на свежем upstream checkout до того, как трогает live-установку.
Он показывает, какие patch'и всё ещё применяются, какие уже похожи на upstreamed, а какие нужно обновить.

## Главный patch сейчас: Provider Proxy Gateway

`080-api-server-provider-proxy` — самый сильный patch в текущем наборе. Upstream Hermes API Server работает как agent endpoint, привязанный к профилю и его модели. PatchKit добавляет отдельный opt-in режим для другой задачи: один OpenAI-compatible gateway поверх explicit catalog моделей провайдера.

В режиме `provider_proxy` `/v1/models` показывает только allowlisted model IDs, а `/v1/chat/completions` маршрутизирует запрос по `body.model` к настроенному provider/model target. Hermes не создаёт `AIAgent` для этих запросов: между клиентом и provider'ом нет SOUL prompt, tools, memory, sessions и agent run state. Для `openai-codex` patch держит OpenAI-compatible поверхность, а внутри использует Responses compatibility path.

Если нужен локальный Hermes-hosted endpoint, который фронтит несколько provider models через стандартный OpenAI-compatible API, начинать нужно с этого patch'а.

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/provider-proxy.yaml \
  --yes
```

## Безопасная проверка upstream

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Для headless/CI режима:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Обычная проверка безопасна: PatchKit подтягивает upstream metadata, клонирует candidate в `/tmp`, проверяет выбранные patch'и там и пишет отчёт в `reports/`. Он не применяет patch'и и не merge'ит upstream в live checkout.

Пример вывода:

```text
Hermes PatchKit update check

Repo:      /home/me/.hermes/hermes-agent
Manifest:  upstream-v2026.4.23-240-ge5647d78.yaml
Current:   runtime-upstream-v2026.4.23 @ 456dc58
Upstream:  origin/main @ abc1234

Patch status:
  ✓ selected-patch-a                       applies-cleanly
  ✓ selected-patch-b                       already-present
  ! selected-patch-c                       conflict

Safe to apply automatically: no (1 patch(es) need attention)
Report: /path/to/hermes-patchkit/reports/update-20260425-211530.md
```

## Зачем это нужно

Долгоживущий fork удобен, пока upstream стоит на месте. Как только upstream начинает жить, каждое обновление превращается в merge-ремонт, а граница между «официальной базой» и «моими локальными правками» исчезает.

PatchKit возвращает эту границу:

- официальный Hermes остаётся runtime-базой;
- локальные изменения живут в маленьких именованных patch files;
- profiles описывают повторяемые наборы patch'ей;
- update check сначала работает на временном upstream clone;
- apply и rollback остаются явными.

## Текущий статус

Проект ещё ранний, но safety loop уже рабочий:

- `scripts/update.py` — one-command проверка совместимости с новым upstream и markdown report;
- `scripts/tui.py` — маленький terminal UI поверх update checker;
- `scripts/doctor.py` — preflight target checkout и выбранных patch'ей;
- `scripts/apply.py` — apply profile или списка patch'ей с backup state;
- `scripts/rollback.py` — откат PatchKit apply;
- `scripts/verify.py` — self-check репозитория;
- `scripts/grok2api_bridge.py` — helper для dedicated Grok2API sidecar bridge поверх provider_proxy mode;
- поддерживаемый список patch'ей и фич: [docs/ru/patches.md](docs/ru/patches.md).

Свежие заметные patch'и:

- Grok2API sidecar bridge — protocol-level интеграция: grok2api остаётся снаружи Hermes, а наружу его выводит `080` provider_proxy gateway. См. [docs/ru/sidecars-grok2api.md](docs/ru/sidecars-grok2api.md).
- `080-api-server-provider-proxy` — главный provider gateway patch, описанный выше. Он превращает Hermes API Server в opt-in OpenAI-compatible proxy поверх explicit provider/model catalog, без запуска Hermes agent layer для этих запросов.
- `070`–`077` — MAX local-overlay chain: от webhook-first text MVP до native images/files и Markdown formatting.

## Быстрый старт

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit

python3 scripts/verify.py --self-check

python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Если нужен неинтерактивный вывод:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Для одного patch'а:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## Что значат статусы

| Status | Meaning |
|---|---|
| `applies-cleanly` | Patch применился к upstream candidate. |
| `already-present` | Reverse patch применился, значит upstream, вероятно, уже содержит ровно это изменение. |
| `conflict` | Patch больше не применяется чисто: его нужно refresh'нуть или retired. |
| `placeholder` | В manifest есть зарезервированный patch ID, но real diff ещё не экспортирован. |

`update.py` возвращает:

- `0`, если выбранный patch set структурно безопасен;
- `2`, если хотя бы один patch требует внимания;
- `1`, если preflight или выполнение упали.

## Каталог patch'ей

Поддерживаемый список patch units и workflow-фич живёт в [docs/ru/patches.md](docs/ru/patches.md).

## Почему не просто жить на fork

| Долгоживущий fork | PatchKit |
|---|---|
| runtime base несёт кастомную историю | runtime base может оставаться official upstream |
| upstream updates копят merge debt | upstream updates становятся проверкой patch'ей |
| public и private изменения смешиваются | каждое изменение живёт отдельным patch'ем |
| rollback обычно ручной | rollback встроен в workflow |

## Структура

```text
hermes-patchkit/
├── manifests/
├── profiles/
├── patches/
├── scripts/
├── docs/en/
├── docs/ru/
├── reports/
└── .github/
```

## Документы

- список patch'ей и фич: [docs/ru/patches.md](docs/ru/patches.md)
- English README: [README.md](README.md)
- Grok2API sidecar bridge: [docs/ru/sidecars-grok2api.md](docs/ru/sidecars-grok2api.md)
- update workflow: [docs/ru/update-workflow.md](docs/ru/update-workflow.md)
- rollback: [docs/ru/rollback.md](docs/ru/rollback.md)
- roadmap: [ROADMAP.md](ROADMAP.md)
- contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- changelog: [CHANGELOG.md](CHANGELOG.md)

## License

MIT
