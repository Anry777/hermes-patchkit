# News

## 2026-07-13 — VibeMode GLM SDK header compatibility

PatchKit now applies a provider-scoped HTTPX request filter for VibeMode OpenAI-wire clients. It removes only OpenAI SDK `X-Stainless-*` identity metadata after the SDK has fully materialized the request, fixing false `Invalid API key` responses from valid `glm-5.2` credentials while preserving bearer authorization, `User-Agent: HermesAgent/1.0`, request payloads, and all non-VibeMode providers.

The behavior is declared by the VibeMode provider profile and enforced in the main-agent, auxiliary sync/async, and API-server provider-proxy OpenAI client paths. Regression coverage verifies the VibeMode strip, non-VibeMode isolation, and preservation of authorization and Hermes User-Agent headers.

---

# Новости

## 2026-07-13 — Совместимость VibeMode GLM с SDK headers

PatchKit добавляет provider-scoped HTTPX request filter для VibeMode OpenAI-wire clients. Он удаляет только identity metadata OpenAI SDK `X-Stainless-*` после полной сборки request внутри SDK. Это устраняет ложный `Invalid API key` для валидных credentials `glm-5.2`, сохраняя bearer authorization, `User-Agent: HermesAgent/1.0`, request payload и все остальные providers без изменений.

Поведение объявлено в VibeMode provider profile и применяется в main-agent, auxiliary sync/async и API-server provider-proxy OpenAI client paths. Regression tests проверяют удаление headers только для VibeMode, изоляцию остальных providers и сохранение authorization/Hermes User-Agent.

---

## 2026-07-12 — Optional human pacing for Telegram userbot

PatchKit unit `079-telegram-userbot-platform-plugin` now supports opt-in human-paced replies on the Telethon/MTProto path only. With `human_pacing_enabled: true`, a reply can wait through a short silent thinking phase, then show Telegram typing while a length-aware delay accounts for time already spent generating the response. The delay is asynchronous, jittered, capped, and applies only to replies associated with an inbound sender.

`human_pacing_excluded_user_ids` bypasses both artificial phases for selected Telegram sender IDs, including inside groups where sender ID and chat ID differ. Locally admitted `allowed_users`/`allowed_chats` senders are also declared authorized before gateway dispatch, so the Telegram user account no longer sends Hermes' bot-oriented pairing prompt to valid contacts; unknown senders remain denied at Telethon intake. The unsolicited first-message home-channel onboarding notice is suppressed for Telegram userbot as well, while explicit `/sethome` remains available. The feature remains disabled by default, does not modify the official Bot API adapter, and does not delay unrelated outbound service messages. The `079` export was also narrowed to its own plugin and directly required gateway capability/test hunks, removing unrelated provider/registry test changes. Validation covered PatchKit catalog/self-check, clean apply and reverse-check against official `v2026.7.7.2`, and focused userbot, home-onboarding, access-policy, and typing tests.

---

# Новости

## 2026-07-12 — Опциональный human pacing для Telegram userbot

PatchKit unit `079-telegram-userbot-platform-plugin` теперь поддерживает opt-in человекоподобный темп ответа только в Telethon/MTProto path. При `human_pacing_enabled: true` сначала выдерживается короткая тихая thinking-пауза, затем Telegram показывает typing, пока length-aware задержка учитывает уже прошедшее время генерации. Ожидание асинхронное, с jitter и верхним пределом; оно применяется только к ответам, связанным с входящим sender.

`human_pacing_excluded_user_ids` полностью обходит обе искусственные фазы для выбранных Telegram sender ID, в том числе в группах, где sender ID не равен chat ID. Локально допущенные через `allowed_users`/`allowed_chats` отправители теперь также объявляются авторизованными до gateway dispatch, поэтому Telegram user account больше не посылает валидным контактам bot-style pairing prompt Hermes; неизвестные отправители по-прежнему отклоняются на входе Telethon. Для Telegram userbot также подавлен самовольный first-message home-channel onboarding notice, при этом явная команда `/sethome` остаётся доступной. По умолчанию pacing выключен, official Bot API adapter не изменяется, а несвязанные служебные исходящие сообщения не задерживаются. Export `079` сужен до собственного plugin и непосредственно необходимых gateway capability/test hunks: чужие provider/registry test changes удалены. Проверены PatchKit catalog/self-check, чистое применение и reverse-check на official `v2026.7.7.2`, а также focused tests userbot, home-onboarding, access-policy и typing.

---

## 2026-07-12 — Provider proxy Codex Cloudflare headers

PatchKit's provider-proxy Chat Completions adapter now reuses Hermes' canonical Codex Cloudflare headers when routing to `chatgpt.com/backend-api/codex`. Valid Codex OAuth calls now carry the required `originator`, Codex-shaped `User-Agent`, and JWT-derived account ID instead of being blocked as generic server-side OpenAI SDK traffic.

The fix refreshes the existing `080-api-server-provider-proxy` behavior inside the `v2026.7.7.2` personal overlay and adds focused regression coverage; no adjacent patch unit was created.

---

# Новости

## 2026-07-12 — Codex Cloudflare headers в provider proxy

Chat Completions adapter PatchKit provider-proxy теперь переиспользует canonical Codex Cloudflare headers Hermes при routing в `chatgpt.com/backend-api/codex`. Valid Codex OAuth calls получают обязательные `originator`, Codex-shaped `User-Agent` и account ID из JWT вместо блокировки как generic server-side OpenAI SDK traffic.

Fix обновляет существующее поведение `080-api-server-provider-proxy` внутри personal overlay `v2026.7.7.2` и добавляет focused regression coverage; новый соседний patch unit не создавался.

---

## 2026-07-11 — Experimental Telegram MTProto userbot plugin

PatchKit now carries `079-telegram-userbot-platform-plugin`, a separate experimental `telegram_userbot` Hermes platform backed by Telethon. It keeps the official Telegram Bot API adapter untouched while adding a user-account MTProto path with profile-local locked sessions, deny-by-default user/chat allowlists, text/reply/edit/typing support, inbound media caching, and native file delivery.

Live use requires explicit operator risk acceptance, Telegram API credentials in the profile `.env`, a foreground login-code/2FA bootstrap, and a non-empty allowlist before service installation. See [docs/en/telegram-userbot.md](docs/en/telegram-userbot.md).

---

# Новости

## 2026-07-11 — Experimental Telegram MTProto userbot plugin

PatchKit теперь несёт `079-telegram-userbot-platform-plugin`: отдельную experimental Hermes platform `telegram_userbot` на базе Telethon. Official Telegram Bot API adapter остаётся без изменений, а для user account добавляется MTProto path с profile-local locked session, deny-by-default allowlist пользователей/чатов, text/reply/edit/typing, inbound media cache и native file delivery.

Live use требует явного принятия operator risk, Telegram API credentials в profile `.env`, foreground bootstrap с login code/2FA и непустой allowlist до установки service. См. [docs/ru/telegram-userbot.md](docs/ru/telegram-userbot.md).

---

## 2026-07-05 — Hermes 0.18 re-anchor

PatchKit is refreshed against official Hermes Agent `v2026.7.1` / `0.18.0`. The active release manifest is `manifests/upstream-v2026.7.1.yaml`; release patch files live under `patches/v2026.7.1/`.

The v0.18 personal profile carries 11 active units: `010`, `020`, `030`, `070`, `078`, `080`, `090`, `096`, `097`, `099`, and `100`. Units now covered by upstream v0.18 are retired instead of re-exported: Telegram free-response/rich delivery fixes, gateway document media types, API-server fallback-model kwargs, SMTP_SSL, and the old Home Assistant config URL overlay. VibeMode remains active with a provider-profile `User-Agent: HermesAgent/1.0` override for Responses compatibility.

---

# Новости

## 2026-07-05 — Re-anchor на Hermes 0.18

PatchKit refresh'нут against official Hermes Agent `v2026.7.1` / `0.18.0`. Активный release manifest: `manifests/upstream-v2026.7.1.yaml`; release patch files лежат в `patches/v2026.7.1/`.

Personal profile для v0.18 несёт 11 active units: `010`, `020`, `030`, `070`, `078`, `080`, `090`, `096`, `097`, `099` и `100`. Всё, что upstream v0.18 уже закрыл, retired вместо повторного экспорта: Telegram free-response/rich delivery fixes, gateway document media types, API-server fallback-model kwargs, SMTP_SSL и старый Home Assistant config URL overlay. VibeMode остаётся active с provider-profile `User-Agent: HermesAgent/1.0` override для Responses compatibility.

---

## 2026-06-30 — Telegram streamed final edit duplicate guard

PatchKit refreshes `041-telegram-rich-flood-fallback` for the Hermes `v2026.6.19` / `0.17.0` line. The unit already covered rich-message `RetryAfter` fallback and long-response overflow duplicates; it now also covers the shorter streamed-response path where Telegram accepts a visible preview but flood-limits the final formatting/finalize edit.

When the exact final text is already visible, Hermes now marks the stream content delivered and suppresses the gateway's normal final-send fallback. That prevents a second Telegram bubble about the same agent turn while preserving the existing guard that still sends a fallback when the visible preview is incomplete.

---

# Новости

## 2026-06-30 — Защита от дубля Telegram при streamed final edit

PatchKit обновляет `041-telegram-rich-flood-fallback` для release line Hermes `v2026.6.19` / `0.17.0`. Unit уже закрывал rich-message `RetryAfter` fallback и дубли при long-response overflow; теперь он закрывает и более короткий streamed-response путь, где Telegram уже показал preview, но flood-limit'ит финальный formatting/finalize edit.

Если точный финальный текст уже виден, Hermes теперь помечает stream content как доставленный и подавляет обычный gateway final-send fallback. Это не даёт появиться второму Telegram bubble про тот же agent turn, при этом старый guard сохраняется: если видимый preview неполный, fallback всё ещё может отправить полный ответ.

---

## 2026-06-21 — Classic CLI scrollback-safe idle refresh default restored

PatchKit carries `010-cli-tui-idle-refresh-fix` again for the Hermes `v2026.6.19` / `0.17.0` release line. Upstream 0.17 kept the `display.cli_refresh_interval` config knob, but changed the default back to `1.0` so the idle status bar keeps ticking. On terminals with auto-scroll-on-output, that one-second prompt_toolkit repaint pulls mouse-wheel scrollback back to the bottom while the agent is idle.

PatchKit's release profile now sets the default back to `0`. Existing profile configs can still carry an explicit `display.cli_refresh_interval: 1.0`, which overrides the patched default; normalize those profiles with `hermes --profile <profile> config set display.cli_refresh_interval 0`. Operators who prefer the ticking idle timer can still opt in by setting a positive `display.cli_refresh_interval` in their profile config.

---

# Новости

## 2026-06-21 — Вернули scrollback-safe default для idle refresh в classic CLI

PatchKit снова несёт `010-cli-tui-idle-refresh-fix` для release line Hermes `v2026.6.19` / `0.17.0`. В upstream 0.17 остался config knob `display.cli_refresh_interval`, но default вернули на `1.0`, чтобы idle status bar тикал. В терминалах с auto-scroll-on-output этот prompt_toolkit repaint раз в секунду тянет mouse-wheel scrollback обратно вниз, пока агент idle.

PatchKit release profile теперь возвращает default в `0`. Но существующие profile configs могут уже явно содержать `display.cli_refresh_interval: 1.0`, и такой explicit value перекрывает patched default; нормализуй такие профили командой `hermes --profile <profile> config set display.cli_refresh_interval 0`. Если нужен ticking idle timer, operator всё ещё может явно поставить positive `display.cli_refresh_interval` в profile config.

---

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
