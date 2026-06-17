# Источник истины для Hermes profiles

В PatchKit-managed установках Hermes действует эта политика, чтобы настройки профилей не расползались между `config.yaml`, `.env`, ручными runtime-правками и systemd-состоянием.

## Таблица источников истины

| Зона | Источник истины | Примечание |
| --- | --- | --- |
| Provider OAuth state и credential pools | Root Hermes auth store: `/root/.hermes/auth.json` плюс `auth.lock` | Общий для профилей. Не дублировать provider OAuth tokens в профильные `.env`. |
| Non-secret настройки профиля | Профильный `config.yaml` | Model/provider selection, gateway behavior, routing policy, tool defaults, terminal/browser settings и integration options, которые Hermes умеет читать из config. |
| Секреты профиля | Профильный `.env` | Tokens, passwords, API keys, private keys и редкие явно описанные env-only исключения. Examples должны быть redacted. |
| Telegram routing policy | `telegram:` в профильном `config.yaml` | Allowed users/chats/topics/threads, group allowlists, home channel/thread, mention policy, free-response targets и channel prompts. В `.env` остаётся `TELEGRAM_BOT_TOKEN`. |
| Runtime code fixes | PatchKit patches, manifests и profiles | Прямая runtime-правка считается временной, пока она не представлена в PatchKit. |
| Желаемое office service state | Cleanup plan и final audit report | План описывает, что должно быть запущено и почему. |
| Фактическое service state | Hermes CLI-managed systemd units и live health/log checks | Проверять через service status, ports, health endpoints и свежие логи. |
| Cron jobs | Profile-local `cron/jobs.json` | Каждый профиль отдельно, если миграция явно не меняет ownership. |

## Операционные правила

1. Non-secret settings переносить из `.env` в `config.yaml`, а не обратно.
2. В активных строках `.env` держать только secrets/tokens/passwords и документированные env-only исключения.
3. Если Hermes пока не умеет читать non-secret setting из `config.yaml`, оформить узкое env-only исключение и отдельно планировать runtime fix.
4. Не чинить provider/auth проблемы копированием root credentials в named profiles.
5. Для правок office gateway profiles: сделать backups, проверить YAML/config loading, перезапустить только затронутый gateway service и посмотреть свежие logs.
6. После обновлений использовать `scripts/clean_profile_config.py` для нормализации `.env` и `config.yaml.example`.
7. Использовать `scripts/install_operator_policy.py`, чтобы вставить короткую operator policy в `agent.system_prompt` профиля — тогда сам Hermes-профиль будет следовать тому же split.

## Установка policy в профиль

Сначала dry-run:

```bash
python3 scripts/install_operator_policy.py --home ~/.hermes/profiles/1c
```

Запись с backup:

```bash
python3 scripts/install_operator_policy.py --home ~/.hermes/profiles/1c --write --backup
```

Helper пишет managed block в `agent.system_prompt`. Повторный запуск обновляет блок на месте, а не добавляет дубликаты.
