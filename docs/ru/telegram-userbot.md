# Telegram MTProto userbot plugin

`079-telegram-userbot-platform-plugin` добавляет experimental explicit opt-in Hermes platform `telegram_userbot`. Unit экспортирован в release manifest, но намеренно исключён из default personal profile. Он подключается через Telegram user account по MTProto с помощью Telethon. Плагин не изменяет и не заменяет official `telegram-platform`, который продолжает работать через Telegram Bot API.

## Риски и границы

Автоматизация Telegram user account может нарушать правила Telegram или привести к ограничениям аккаунта. Используй отдельный аккаунт, строгий allowlist и явное принятие operator risk. Никогда не выводи login code, API hash, 2FA password или session material в logs, prompts, config.yaml или ответы чата.

MVP поддерживает:

- profile-local Telethon file session и process lock;
- optional Telethon `StringSession`;
- deny-by-default allowlist пользователей и чатов;
- inbound text и profile-local media download;
- outbound text, replies, edits, typing, images, documents и video files;
- dynamic Hermes platform registration без изменений встроенного Telegram Bot API adapter.

## Применение PatchKit unit

```bash
cd /root/hermes-patchkit
python3 scripts/apply.py \
  --repo /root/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.7.7.2.yaml \
  --patch telegram-userbot-platform-plugin \
  --yes
```

Plugin объявляет lazy dependency `telethon>=1.40.0,<2`. До bootstrap проверь, что target runtime импортирует Telethon.

## Настройка профиля

Включи plugin и platform в target profile:

```yaml
plugins:
  enabled:
    - platforms/telegram_userbot

platforms:
  telegram_userbot:
    enabled: true
    extra:
      work_dir: /root/.hermes/profiles/telegram-userbot/telegram_userbot
      session_name: main
      allow_all_users: false
      allowed_users: []
      allowed_chats: []
      mark_read: false
      download_media: false
      max_media_bytes: 20971520
      max_media_cache_bytes: 268435456
      max_media_cache_files: 1000
      send_typing: true
```

Credentials хранятся в `/root/.hermes/profiles/telegram-userbot/.env`:

```bash
TELEGRAM_USERBOT_API_ID=...
TELEGRAM_USERBOT_API_HASH=...
TELEGRAM_USERBOT_PHONE=+...
# TELEGRAM_USERBOT_2FA_PASSWORD=...
# TELEGRAM_USERBOT_SESSION_STRING=...
```

`api_id` и `api_hash` нужны всегда. Для первого bootstrap дополнительно нужен номер телефона; последующие запуски могут использовать profile-local session file. `StringSession` optional, но особенно чувствителен: он фактически даёт доступ к аккаунту. Plugin отклоняет `api_id`, `api_hash`, `phone`, `session_string`, `two_factor_password` и `2fa_password`, если они заданы через `config.yaml`; эти значения принимаются только из environment активного профиля.

`work_dir` должен находиться внутри `HERMES_HOME` активного профиля, а `session_name` должен быть простым filename. Path traversal и absolute session names отклоняются.

Non-secret allowlists и media limits храни в `config.yaml`, а не в `.env`. Запись в `allowed_chats` разрешает сообщения от всех участников этого чата; для ограничения по sender используй `allowed_users`. Media download по умолчанию выключен и включается явно только после принятия storage risk. Вложения с неизвестным metadata size или размером выше `max_media_bytes` отклоняются до transfer. Downloads сериализованы и stream-ятся в profile-local files; actual bytes проверяются перед каждой записью, а byte/file-count quotas повторно проверяются до сохранения файла.

## Первая авторизация

Первый login запускай foreground, чтобы Telegram мог запросить login code и optional 2FA password:

```bash
cd /root/.hermes/hermes-agent
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway run -v --replace
```

Успешный file-session bootstrap создаёт:

```text
/root/.hermes/profiles/telegram-userbot/telegram_userbot/main.session
```

Не устанавливай background service, пока session не создана и allowlist остаётся пустым.

## Установка service

После успешного foreground bootstrap:

```bash
cd /root/.hermes/hermes-agent
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway install --system --force --run-as-user root
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway start
```

Проверяй profile-specific process и log, а не общий список gateway PID:

```bash
ps -eo pid,ppid,stat,lstart,cmd \
  | grep -E '[h]ermes.*--profile telegram-userbot.*gateway'
tail -n 160 /root/.hermes/profiles/telegram-userbot/logs/gateway.log
```

## Проверка

Focused runtime tests:

```bash
cd /root/.hermes/hermes-agent
scripts/run_tests.sh \
  tests/plugins/test_telegram_userbot_platform_plugin.py \
  tests/providers/test_plugin_discovery.py \
  tests/gateway/test_platform_registry.py
```

PatchKit checks:

```bash
cd /root/hermes-patchkit
python3 -m unittest tests.test_patch_catalog
python3 scripts/verify.py --self-check
```

Release patch должен чисто применяться к official `v2026.7.7.2`, а после apply должен проходить `git apply -R --check`.
