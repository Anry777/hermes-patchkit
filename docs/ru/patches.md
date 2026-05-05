# Patch'и и фичи

Это публичный каталог поддерживаемых patch units и workflow-фич PatchKit. README ссылается сюда, а не дублирует список patch'ей прямо на первом экране.

Совместимость не статична. Перед apply нужно запускать `scripts/update.py` или `scripts/tui.py` против своего Hermes checkout.

Текущий релизный якорь: `manifests/upstream-v2026.4.30.yaml`. Release-specific patch files лежат в `patches/v2026.4.30/` и проверяются против official tag `v2026.4.30` из `NousResearch/hermes-agent`, а не против post-release `main`.

## Доступные patch units

| Patch | Статус | Что делает | Примечания |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Убирает idle CLI/TUI repaint, который тянул terminal viewport. | На последнем live smoke check применяется чисто. |
| `020-auth-profile-root-fallback` | exported | Даёт profile auth stores фолбэк на root auth store, если в profile ещё нет `auth.json`. | Есть focused auth/profile regression coverage. |
| `030-credential-pool-recovery` | exported | Улучшает credential-pool recovery: отслеживает active credential ID, не возвращает invalid credentials через cooldown recovery и откладывает round-robin rotation до release lease. | Перенесён из legacy fork commits `e17a823c` и `97fa2dbc`; зависит от `020-auth-profile-root-fallback`. |
| `040-telegram-free-response-target-gating` | exported | Не даёт Telegram free-response группам перехватывать сообщения, явно адресованные другому боту или пользователю. | Использует positive addressing: direct mentions/replies/wake words адресуют текущего бота, но новая явная адресация другому target (`@other_bot`, `/cmd@other_bot`, `Имя, ...`) сильнее reply context; ambient free-response chat не перехватывает вопросы без явного обращения. |
| `050-homeassistant-tool-config-url` | exported | Даёт Home Assistant tools читать `platforms.homeassistant.extra.url` из profile `config.yaml`, если `HASS_URL` отсутствует. | Сохраняет env override compatibility и прежний fallback на `homeassistant.local`; есть focused regression coverage для tool/config и live read-only smoke check. |
| `060-codex-memory-flush-responses-contract` | exported, needs refresh check | Держит Codex memory flush на Responses transport contract. | Конфликтует с текущим fetched upstream в `run_agent.py`; перед следующим live upstream merge нужно refresh или retire. |
| `061-codex-auxiliary-tool-role-flattening` | exported | Flatten unsupported transcript roles вроде `tool` перед auxiliary Codex Responses calls. | Чисто применяется в последнем live smoke check. |
| `070-max-platform-plugin` | exported | Добавляет MAX messenger как официальный Hermes platform plugin вместо core gateway patches. | Единый local-overlay patch для release manifest `v2026.4.30`. Внутри — `plugins/platforms/max/plugin.yaml`, `plugins/platforms/max/adapter.py`, webhook-first production delivery, явный polling fallback для локального теста, native image/file attachments, group-chat typing indicator через `POST /chats/{chatId}/actions`, настраиваемый in-chat tool progress для MAX (`display.platforms.max.tool_progress`, default `new`, `off` отключает) с edit-in-place updates через `PUT /messages?message_id=...`, native approval-кнопки через MAX inline keyboard callbacks / `POST /answers?callback_id=...`, безопасный разбор `MEDIA:`, media delivery через `send_message` и MAX Markdown formatting. Plugin включается отдельно через штатный Hermes plugin/config workflow, нужен `MAX_BOT_TOKEN`. |
| `080-api-server-provider-proxy` | exported | Добавляет opt-in `provider_proxy` mode для OpenAI-compatible API Server: `/v1/models` отдаёт explicit catalog, а `/v1/chat/completions` маршрутизирует запросы к configured provider/model без создания `AIAgent`. | Generic upstream-candidate patch. Поддерживает non-streaming и streaming Chat Completions для OpenAI-compatible provider'ов, плюс compatibility path для `openai-codex`/Responses, который адаптирует Responses streams в OpenAI Chat Completion SSE chunks, мапит `reasoning_effort` и фильтрует sampling params вроде `temperature`, которые ChatGPT Codex отвергает. `/v1/responses` и `/v1/runs` по-прежнему fail-closed как unsupported operation. |
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
- sampling params, которые ChatGPT Codex отвергает (`temperature`, `top_p`, penalties, `seed`, logprob knobs), фильтруются перед upstream call;
- `/v1/responses` и `/v1/runs` fail-closed до отдельных patch'ей для agent-style surfaces.

Если нужен только provider gateway patch, используй отдельный profile:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-provider-proxy.yaml \
  --yes
```

Для canary/main — `manifests/canary-main-a1921c43c.yaml` и `profiles/canary-main-provider-proxy.yaml`.

### Grok2API sidecar bridge

Первый sidecar pack поверх provider_proxy описан в [sidecars-grok2api.md](sidecars-grok2api.md). grok2api остаётся отдельным сервисом, PatchKit добавляет profiles, которые выбирают только `080`, кладёт loopback Docker Compose/config examples и даёт `scripts/grok2api_bridge.py` для render config и smoke checks endpoint'а. Это явно sidecar integration, не vendored Grok provider и не часть default profiles.

## Совместимость с релизом `v2026.4.30`

Release manifest намеренно не включает patch units, которые больше не ложатся чисто на официальный релиз:

- `010-cli-tui-idle-refresh-fix` superseded upstream-правками idle repaint в `v2026.4.30`.
- `060-codex-memory-flush-responses-contract` obsolete, потому что старый `flush_memories` path upstream удалил/переработал.
- MAX support теперь один release-pinned local-overlay plugin patch `070-max-platform-plugin`; прежняя split-цепочка `070`-`077` с core gateway changes оставлена только в legacy/canary manifests, не в `upstream-v2026.4.30.yaml`.
- Активные `v2026.4.30` patches сейчас: `020`, `030`, `040`, `050`, `061`, `070-max-platform-plugin`, optional `080` и UI/control-plane `200`–`215`.

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
| Grok2API sidecar bridge helper | `scripts/grok2api_bridge.py` | working helper/docs layer поверх `080-api-server-provider-proxy` |

## Что значат статусы

- `exported`: patch file содержит реальный unified diff.
- `planned`: patch ID оставлен в manifest как запланированная работа, но real diff ещё не готов.
- `needs refresh check`: patch существует, но совместимость с текущим upstream требует review.
- `local-overlay`: поддерживаемая PatchKit integration/customization, полезная локально, но не обязательно upstream-bound.

Удалённые идеи здесь не перечисляются. Этот каталог — только для PatchKit units, которые реально планируется поддерживать.
