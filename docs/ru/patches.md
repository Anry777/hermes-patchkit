# Patch'и и фичи

Это публичный каталог поддерживаемых patch units и workflow-фич PatchKit. README ссылается сюда, а не дублирует список patch'ей прямо на первом экране.

Совместимость не статична. Перед apply нужно запускать `scripts/update.py` или `scripts/tui.py` против своего Hermes checkout.

Текущий релизный якорь: `manifests/upstream-v2026.6.5.yaml`. Release-specific patch files лежат в `patches/v2026.6.5/` и проверяются против official tag `v2026.6.5` / Hermes Agent `0.16.0` из `NousResearch/hermes-agent`, а не против post-release `main`.

## Доступные patch units

| Patch | Статус | Что делает | Примечания |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Убирает idle CLI/TUI repaint, который тянул terminal viewport. | На последнем live smoke check применяется чисто. |
| `020-auth-profile-root-fallback` | exported | Делает `auth.json` и `auth.lock` root-global: все профили разделяют OAuth state и credential pools вместо fork profile-local auth stores. | Изоляция config, sessions, skills и logs сохраняется; есть focused shared-auth regression coverage. |
| `030-credential-pool-recovery` | exported | Улучшает credential-pool recovery: отслеживает active credential ID, сохраняет независимые `openai-codex` OAuth pool entries, не возвращает invalid credentials через cooldown recovery и откладывает round-robin rotation до release lease. | Codex `auth add` теперь создаёт независимый pool credential вместо перезаписи singleton; singleton re-auth синхронизирует только настоящие legacy aliases. Зависит от `020-auth-profile-root-fallback`. |
| `040-telegram-free-response-target-gating` | exported | Не даёт Telegram free-response группам перехватывать сообщения, явно адресованные другому боту или пользователю, поддерживает release-pinned владение forum topic через `telegram.allowed_threads`, показывает стабильные Telegram sender IDs в context/shared-group prefixes и удерживает `send_message(target="telegram")` в текущем/home Telegram forum topic вместо отправки attachment в другой topic. | Использует positive addressing: direct mentions/replies/wake words адресуют текущего бота, но новая явная адресация другому target (`@other_bot`, `/cmd@other_bot`, `Имя, ...`) сильнее reply context; ambient free-response chat не перехватывает вопросы без явного обращения. В явно разрешённом forum topic с `require_mention: false` обычные сообщения принимаются, даже если Telegram прикрепил reply metadata от другого bot/service message. При `privacy.redact_pii: true` sender IDs хэшируются до попадания в prompt. |
| `050-homeassistant-tool-config-url` | exported | Даёт Home Assistant tools читать `platforms.homeassistant.extra.url` из profile `config.yaml`, если `HASS_URL` отсутствует. | Сохраняет env override compatibility и прежний fallback на `homeassistant.local`; есть focused regression coverage для tool/config и live read-only smoke check. |
| `060-codex-memory-flush-responses-contract` | exported, needs refresh check | Держит Codex memory flush на Responses transport contract. | Конфликтует с текущим fetched upstream в `run_agent.py`; перед следующим live upstream merge нужно refresh или retire. |
| `061-codex-auxiliary-tool-role-flattening` | exported | Flatten unsupported transcript roles вроде `tool` перед auxiliary Codex Responses calls. | Чисто применяется в последнем live smoke check. |
| `062-codex-sdk-output-none-recovery` | exported | Ловит TypeError из Codex Responses stream iteration / `stream.get_final_response()`, когда ChatGPT Codex шлёт `response.completed` с `output:null`, и восстанавливает auxiliary/title-generation streams, которые падают с missing `response.completed` после уже собранных deltas/items. | Сохраняет metadata SDK terminal response (`usage`, `model`, `id`), если она есть, обрабатывает явный `output=None`, re-raise-ит исходную stream error, когда восстанавливать нечего, отслеживает fallback `function_call` events, чтобы incidental text deltas не превращались в plain text, и содержит focused runtime + auxiliary regression tests. |
| `070-max-platform-plugin` | exported | Добавляет MAX messenger как официальный Hermes platform plugin вместо core gateway patches. | Единый local-overlay patch для release manifest `v2026.5.16`. Внутри — `plugins/platforms/max/plugin.yaml`, `plugins/platforms/max/adapter.py`, webhook-first production delivery, явный polling fallback для локального теста, native image/file/audio attachments (включая official `AudioAttachment` transcription и MIME handling, когда MAX Bot API реально его доставляет), group-chat typing indicator через `POST /chats/{chatId}/actions`, настраиваемый in-chat tool progress для MAX (`display.platforms.max.tool_progress`, default `new`, `off` отключает) с компактными/coalesced edit-in-place updates через `PUT /messages?message_id=...` без raw non-verbose command previews, native approval-кнопки через MAX inline keyboard callbacks / `POST /answers?callback_id=...`, безопасный разбор `MEDIA:`, media delivery через `send_message` и MAX Markdown formatting. Plugin включается отдельно через штатный Hermes plugin/config workflow, нужен `MAX_BOT_TOKEN`. |
| `090-lsp-configured-websocket-transport` | exported | Добавляет config-driven custom LSP servers и WebSocket transport для Hermes LSP, чтобы подключать external language servers вроде BSL LS без hardcoded profile paths/endpoints. | Основной формат — `lsp.servers.<server_id>`; compatibility alias — `lsp.custom_servers`. `.bsl` регистрируется через config как `language_id: bsl`. `hermes lsp status/list/which/test` понимают WebSocket targets и controlled unavailable status. |
| `091-email-smtp-ssl` | exported | Добавляет env-переменную `EMAIL_SMTP_SECURITY` для выбора SMTP_SSL (implicit TLS, порт 465) vs STARTTLS (explicit TLS). | Затрагивает gateway EmailAdapter и `send_message_tool`. По умолчанию SMTP_SSL на порту 465, STARTTLS на остальных; поведение не меняется, если env не задан и порт не 465. |
| `092-gateway-document-media-types` | exported | Синхронизирует document/media attachment types в gateway. | Сохраняет поддержку `.epf`/`.cfe` для 1C как binary documents и чинит явные `MEDIA:<path>` для поддержанных артефактов вроде `.md`, `.markdown`, `.json`, `.yaml`, `.html`: они извлекаются и отправляются native attachments вместо plain text; broad `\S+` fallback не возвращается. |
| `093-neurogate-provider-plugin` | exported | Добавляет NeuroGate как bundled model-provider plugin. | Единственный provider id — `neurogate` без aliases. `hermes auth add neurogate --type api-key` сохраняет credential pool entry с `https://api.neurogate.space/v1`; runtime routing принудительно использует `codex_responses`, чтобы GPT-5.x/Responses-compatible endpoints не падали обратно в Chat Completions. |
| `096-provider-plugin-model-switch` | exported | Делает model-provider plugins видимыми для `/model`, `/mode` и context resolution. | Общий fix для provider plugins: `resolve_provider_full()`, provider labels, API-mode detection, no-args model picker и `get_model_context_length()` теперь читают зарегистрированные `ProviderProfile`, поэтому plugin-backed providers вроде `neurogate` не требуют дублирующего `config.yaml providers:` entry, не падают с `Unknown provider` и могут объявлять provider-enforced context windows (`neurogate` + `gpt-5.5` = 272,000 tokens). |
| `097-gateway-explicit-media-delivery-safety` | exported | Делает отправку локальных файлов через gateway явной по умолчанию. | `MEDIA:/path` и structured `artifacts=[...]` продолжают отправляться как native attachments после validation; bare `/absolute/path/file` остаётся текстом, если оператор явно не включил `gateway.auto_upload_local_paths: true`. `gateway.strict` остаётся отдельным validation layer. |
| `098-api-server-fallback-model-kwarg` | exported | Не даёт OpenAI-compatible API Server fallback path дважды передавать `model` в `AIAgent`. | Если provider fallback возвращает runtime kwargs со своим fallback model, `_create_agent()` вынимает этот model, использует его как effective override и не трогает остальные runtime kwargs. Это чинит `AIAgent() got multiple values for keyword argument 'model'` после auth/quota failure primary provider. |
| `094-root-home-media-delivery` | retired in `v2026.6.5` | Upstream 0.16 уже принимает active `/root` home как deliverable media location и сохраняет блокировку credential subdirs / Hermes auth/env files. | Отдельный PatchKit unit не переносится в `v2026.6.5`; оставшаяся работа по `.epf`/`.cfe` и explicit-media parity живёт в `092`/`097`. |
| `080-api-server-provider-proxy` | exported | Добавляет opt-in raw provider proxy modes для OpenAI-compatible API Server: `provider_proxy` держит `/v1/models` как explicit catalog и маршрутизирует `/v1/chat/completions`; `codex_responses_proxy` открывает Responses-native Codex OAuth bridge на `/v1/responses` без создания `AIAgent`. | Generic upstream-candidate patch. Поддерживает non-streaming и streaming Chat Completions для OpenAI-compatible provider'ов, плюс compatibility path для `openai-codex`/Responses, который адаптирует Responses streams в OpenAI Chat Completion SSE chunks, мапит `reasoning_effort` и фильтрует sampling params вроде `temperature`, которые ChatGPT Codex отвергает. Новый Responses-native mode сохраняет Responses SSE events (`response.created`, `response.output_text.delta`, `response.completed`) и может live-discover Codex models с allow/deny filters. `/v1/runs` по-прежнему fail-closed как unsupported operation. |
| `200-dashboard-profile-api` | exported | Добавляет authenticated read-only profile inventory API для built-in dashboard. | Первый upstream-candidate patch в UI/control-plane линейке `200`–`249`; не раскрывает secrets, session messages или log contents. |
| `201-dashboard-profile-selector` | exported | Добавляет built-in Profiles page и sidebar selector/cards поверх `200-dashboard-profile-api`. | Показывает model/provider, skills, env presence, gateway status, paths, session counts и log-file metadata; selection не меняет global active profile. |
| `202-dashboard-profile-aware-pty` | exported | Добавляет profile-aware embedded `hermes --tui` через existing dashboard PTY bridge. | `/chat?profile=<name>` и `/api/pty?profile=<name>` валидируют profile, запускают PTY child с profile-scoped `HERMES_HOME`, сохраняют resume forwarding и не меняют global active profile. |

## Заметные patch'и

### `080-api-server-provider-proxy`

Это сейчас флагманский feature patch в PatchKit. Это не очередная настройка “запусти того же Hermes agent на другой модели”. Patch добавляет отдельный режим API Server для случая, когда нужен стандартный OpenAI-compatible endpoint поверх нескольких provider models.

Upstream Hermes сегодня не даёт такого разделения provider gateway и agent endpoint: его API Server path завязан на работающий Hermes agent/profile. `080` добавляет недостающую границу. Если включить `mode: provider_proxy` и задать allowlist `provider_proxy.models`, сервер становится catalog-routed provider proxy. В этом режиме:

- `/v1/models` возвращает только configured public model IDs;
- `/v1/chat/completions` маршрутизирует запрос по `body.model` к configured provider/model target;
- Hermes обходит `AIAgent`, поэтому нет Hermes tools, memory, sessions, SOUL/context injection и agent run semantics;
- OpenAI-compatible provider'ы идут через Chat Completions passthrough;
- `openai-codex` / Responses provider'ы идут через compatibility adapter;
- `stream: true` отдаёт OpenAI-compatible `text/event-stream` chunks, если в конфиге включён `allow_streaming: true`;
- OpenAI-style `tools`, `tool_choice`, assistant `tool_calls`, `role: tool` results, `parallel_tool_calls` и inline `image_url` / `input_image` parts сохраняются для IDE clients;
- RooCode-style `reasoning_effort` мапится в Responses `reasoning.effort` для Codex-backed targets;
- sampling params, которые ChatGPT Codex отвергает (`temperature`, `top_p`, penalties, `seed`, logprob knobs), фильтруются перед upstream call.

В тот же patch unit `080` теперь входит `mode: codex_responses_proxy` для отдельного profile/port, когда client говорит на Responses wire нативно. В этом режиме:

- `/v1/models` может live-query `openai-codex` model catalog и затем применить configured allow/deny regex filters;
- `/v1/responses` пересылает Responses body клиента в Codex Responses backend через Hermes OAuth credential pool;
- `stream: true` сохраняет Responses SSE events вроде `response.created`, `response.output_text.delta`, `response.completed`, а не конвертирует их в Chat Completions chunks;
- `/v1/chat/completions` и `/v1/runs` fail-closed, чтобы Responses-native clients не делили смешанный wire contract с Chat Completions clients.

Если нужен только provider gateway patch, используй отдельный profile:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.5.16.yaml \
  --profile profiles/v2026.5.16-provider-proxy.yaml \
  --yes
```

Для canary/main — `manifests/canary-main-a1921c43c.yaml` и `profiles/canary-main-provider-proxy.yaml`.

### Grok2API sidecar bridge

Первый sidecar pack поверх provider_proxy описан в [sidecars-grok2api.md](sidecars-grok2api.md), но после Hermes `0.14.0` это legacy fallback infrastructure. Для Grok и SuperGrok предпочитаем native upstream `xai` / `xai-oauth`. Старые grok2api helper/examples остаются для явных self-hosted fallback cases, но PatchKit не добавляет новый active profile `v2026.5.16-grok2api-sidecar`.

## Совместимость с релизом `v2026.5.16` / Hermes 0.14

0.14 manifest держит active core overlays release-pinned и не возвращает старую dashboard/UI линейку `200`–`215` в personal runtime line. Итог retirement audit:

- `010-cli-tui-idle-refresh-fix` остаётся superseded upstream.
- `060-codex-memory-flush-responses-contract` остаётся obsolete после upstream memory-flush refactors.
- `020`, `030` и `040` refresh'нуты как более узкие overlays поверх соседних upstream auth, credential-pool и Telegram gating primitives.
- `050`, `061`, `070-max-platform-plugin` и `080-api-server-provider-proxy` всё ещё несут PatchKit behavior, который upstream 0.14 не заменил.
- Grok2API sidecar profiles теперь legacy fallback only; сначала используем native `xai` / `xai-oauth`.

## Планируемая UI-линейка `200`+

Для Hermes-native multi-profile dashboard зарезервирован отдельный диапазон patch numbers: `200`–`249`. Концепция и first-wave sequence описаны отдельно: [ui-control-plane-plan.md](ui-control-plane-plan.md).

Стартовая последовательность:

| Patch | Статус | Что должен сделать |
|---|---|---|
| `200-dashboard-profile-api` | exported | Authenticated read-only endpoints `/api/dashboard/profiles` и `/api/dashboard/profiles/{name}` для safe profile inventory: model/provider, skills, gateway, sessions metadata, logs metadata. |
| `201-dashboard-profile-selector` | exported | Встроенная dashboard страница Profiles и sidebar selector/cards поверх `200`: model/provider, skills, env, gateway, paths, session counts и log metadata без изменения global active profile. |
| `202-dashboard-profile-aware-pty` | exported | Embedded `hermes --tui` terminal с optional `profile=<name>` поверх существующего PTY bridge; profile-scoped `HERMES_HOME`, resume forwarding и кнопка Open terminal из Profiles page. |
| `203-dashboard-terminal-workspace` | exported | Foundation для remote terminal workspace: authenticated dashboard WebSockets (`/api/pty`, `/api/ws`, `/api/pub`, `/api/events`) остаются loopback-only по умолчанию, но работают для remote browser при явном `--insecure`; это разблокирует live `/chat?profile=<name>` на dashboard service. |
| `204-dashboard-runtime-registry` | exported | Authenticated read-only `/api/dashboard/runtimes`: dashboard process state, live PTY sessions с profile/cwd/pid/resume/terminal size, action subprocess liveness и event-channel counts без argv/env/output/session/log/memory bodies. |
| `205-dashboard-worker-roster` | exported | Authenticated read-only `/api/dashboard/worker-roster`: configured profile-local workers из `dashboard/worker_roster.json` плюс live PTY runtime workers из `204`, с safe role/lane/mission/model/capability/process metadata без secrets/env/output/session/log/memory bodies. |
| `206-dashboard-terminal-profile-lifecycle` | exported | Bugfix/control slice: Open terminal из profile создаёт уникальный `/chat?profile=<name>&terminal=<id>` channel вместо reuse default Chat terminal; Chat page получила Close terminal поверх `DELETE /api/dashboard/runtimes/pty/{id}`. |
| `207-dashboard-session-log-inspector` | exported | Profile-aware read-only session/log inspector: `/api/dashboard/profiles/{name}/sessions`, `/sessions/{session_id}` and `/logs` expose safe session counts, token/cost metadata, message/tool-call summaries and log-file metadata without message bodies, raw tool args, system prompts, log contents, env or secrets. |
| `208-dashboard-terminal-workspace-tabs` | exported | App-level multi-terminal workspace tabs: default Chat and profile terminals remain separate mounted PTY panes, switching tabs does not kill other terminals, and closing a tab requires confirmation before terminating exactly that PTY via `DELETE /api/dashboard/runtimes/pty/{id}`. |
| `209-dashboard-assembly-analytics` | exported | Authenticated safe whole-assembly analytics across all profiles: profile activity/staleness, token and cost totals, API/tool-call counts, top profiles и model/provider distribution без session IDs, message bodies, tool args, logs, env или secrets. |
| `210-dashboard-controlled-actions` | exported | Auth-gated allowlisted dashboard mutation layer: `/api/dashboard/actions` lists exact-confirmation actions, а `/api/dashboard/actions/{id}/run` запускает только confirmed gateway restart / Hermes update actions с existing detached action status logs. |
| `211-dashboard-control-plane-unification` | exported | Стабилизирует dashboard как единый control plane: authenticated `/api/dashboard/overview` становится общей semantic source для sidebar, Overview, Sessions, profiles, terminals и gateway platforms; stale platform rows требуют attention, а bundled example plugin скрыт до явного dev opt-in. |
| `212-dashboard-visual-polish` | exported | Полирует unified dashboard overview после `211`: shared visual primitives для content shell, cards, hero, KPI grid, density table, freshness rows и sidebar status, улучшая spacing/contrast/hierarchy без изменения data contract. |
| `213-dashboard-overview-semantic-cleanup` | exported | Уточняет semantics unified Overview: assembly-wide scope, selected-profile context, structured Action required items и runtime health evidence вместо путаницы profile stale/urgent alert. Stale session history остаётся metadata; активные alert items имеют source, severity, reason, message и action; provider-proxy отображается как service/API health evidence. |
| `214-dashboard-messaging-adapters-semantics` | exported | Переименовывает Gateway platforms в Messaging adapters и разделяет adapter availability от event freshness. Connected-but-stale adapters остаются check-freshness metadata; Action required создаётся только для unhealthy adapter state. |
| `215-dashboard-system-overview-semantics` | exported | Делает Overview общесистемной сводкой: убирает доминирующий `Selected profile`, добавляет `system_summary`, profile table и memory inventory с live Hindsight bank counts. | `selected_profile` остаётся backward-compatible API-полем; memory section отделяет shared Hindsight bank от local profile memory и показывает только metadata/counts без содержимого памяти; endpoint запускает sync Hindsight probe вне FastAPI event loop, чтобы не получать count fallback. |

## Workflow-фичи

| Фича | Entry point | Статус |
|---|---|---|
| Проверка совместимости с upstream | `scripts/update.py` | работает |
| Terminal update dashboard | `scripts/tui.py` | работает |
| Preflight target checkout | `scripts/doctor.py` | работает |
| Apply patch/profile с backup state | `scripts/apply.py` | работает для exported patches |
| Rollback PatchKit apply | `scripts/rollback.py` | работает; есть regression coverage для tracked, untracked и ignored cleanup cases |
| Self-check репозитория | `scripts/verify.py --self-check` | работает |
| Grok2API sidecar bridge helper | `scripts/grok2api_bridge.py` | legacy fallback helper/docs layer поверх `080-api-server-provider-proxy`; для Grok предпочитаем native `xai` / `xai-oauth` |

## Что значат статусы

- `exported`: patch file содержит реальный unified diff.
- `planned`: patch ID оставлен в manifest как запланированная работа, но real diff ещё не готов.
- `needs refresh check`: patch существует, но совместимость с текущим upstream требует review.
- `local-overlay`: поддерживаемая PatchKit integration/customization, полезная локально, но не обязательно upstream-bound.

Удалённые идеи здесь не перечисляются. Этот каталог — только для PatchKit units, которые реально планируется поддерживать.
