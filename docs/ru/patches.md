# Patch'и и функции

Это публичный каталог поддерживаемых PatchKit patch units и workflow features. README ссылается сюда вместо дублирования списка patch'ей.

Совместимость не статична. Перед применением запускай `scripts/update.py` или `scripts/tui.py` against нужного Hermes checkout.

Текущий релизный якорь: `manifests/upstream-v2026.7.7.2.yaml`. Release-specific patch files лежат в `patches/v2026.7.7.2/` и проверяются против official tag `v2026.7.7.2` / Hermes Agent `0.18.2` из `NousResearch/hermes-agent`, а не против post-release `main`.

## Доступные patch units

| Patch | Status | Что делает | Notes |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Останавливает idle repaint classic CLI, который тянет terminal viewport. | PatchKit держит default `display.cli_refresh_interval` в `0`; явный profile config всё равно главнее. |
| `020-auth-profile-root-fallback` | exported | Делает `auth.json` и `auth.lock` root-global, чтобы профили делили provider OAuth state и credential pools. | Config, sessions, skills и logs остаются profile-local. |
| `030-credential-pool-recovery` | exported | Сохраняет оставшиеся PatchKit safety semantics для credential pool на Hermes v0.18. | Codex aux не обходит exhausted pools через singleton; stale ok+reset markers очищаются; terminal dead credentials не держат retry reset state. Depends on `020`. |
| `041-telegram-rich-flood-fallback` | exported | Возвращает Telegram duplicate-safety для v0.18 сценария finalize + overflow split + first-chunk flood-control. | Если Telegram flood-limit’ит косметический финальный edit первого chunk, Hermes считает уже видимый streaming prefix partial-overflow delivery и отправляет только недостающий tail вместо duplicate full formatted final answer. |
| `070-max-platform-plugin` | exported | Добавляет MAX messenger как official Hermes platform plugin вместо core gateway patches. | Webhook-first, explicit polling fallback, native media/files/audio, Markdown, typing, progress edits, approval buttons и safe media delivery. |
| `078-max-userbot-platform-plugin` | exported | Добавляет отдельный experimental `max_userbot` platform plugin на базе MaxApiTeam/PyMax. | Internal/unofficial MAX user-account path; live use требует operator risk acceptance и SMS/QR bootstrap. |
| `079-telegram-userbot-platform-plugin` | exported | Добавляет отдельный experimental plugin `telegram_userbot` на базе Telethon/MTProto. | User-account path с profile-local locked sessions, deny-by-default allowlists без bot-style pairing после локального допуска, подавленным самовольным home-channel onboarding и опциональным длино-зависимым human pacing с исключениями по sender ID; см. [telegram-userbot.md](telegram-userbot.md). |
| `080-api-server-provider-proxy` | exported | Добавляет opt-in raw provider proxy modes в OpenAI-compatible API Server. | Включает catalog-routed Chat Completions provider proxy, обязательные Codex headers для Cloudflare и Responses-native `codex_responses_proxy` без создания `AIAgent`. |
| `090-lsp-configured-websocket-transport` | exported | Добавляет config-driven custom LSP servers и WebSocket transport для Hermes LSP. | Позволяет подключать внешние language servers вроде BSL LS без hardcoded profile paths/endpoints. |
| `096-provider-plugin-model-switch` | exported | Делает model-provider plugins видимыми для `/model`, `/mode`, runtime provider resolution и context-window metadata. | Plugin-backed providers вроде `vibemode` больше не требуют duplicate `config.yaml providers:` entries. |
| `097-gateway-explicit-media-delivery-safety` | exported | Делает gateway local-file delivery explicit по умолчанию. | `MEDIA:/path` и structured artifacts отправляются как native attachments; bare absolute paths остаются текстом, если не включить `gateway.auto_upload_local_paths: true`. |
| `099-gateway-auto-reset-context-continuity` | exported | Сохраняет gateway chat context после idle/daily auto-reset. | Новые auto-reset sessions линкуются к expired parent и rehydrate'ят reset-parent transcripts; manual `/new` и `/reset` остаются fresh. |
| `100-vibemode-provider-plugin` | exported | Добавляет VibeMode provider plugin, User-Agent propagation, Bearer auth для Messages, per-model endpoint metadata и provider-scoped SDK header filtering. | Отправляет `User-Agent: HermesAgent/1.0` через OpenAI-compatible и Anthropic Messages transports, удаляет только `X-Stainless-*` identity metadata из VibeMode OpenAI-wire requests на финальной HTTPX-границе, не использует x-api-key auth для VibeMode Messages и не exhaust'ит credentials на Cloudflare/WAF blocks; список моделей остаётся live-discovered через `/v1/models`. |
| `040-telegram-free-response-target-gating` | retired in `v2026.7.1` | Upstream v0.18 уже несёт нужное Telegram gating behavior для release line. | Отдельный v0.18 patch file не поставляется. |
| `050-homeassistant-tool-config-url` | retired in `v2026.7.1` | Upstream/config-sourced behavior больше не требует старый PatchKit Home Assistant tool URL overlay. | v0.18 profiles его не выбирают. |
| `091-email-smtp-ssl` | retired in `v2026.7.1` | Upstream v0.18 email plugin использует SMTP_SSL для port 465 и STARTTLS иначе. | Отдельный v0.18 patch file не поставляется. |
| `092-gateway-document-media-types` | retired in `v2026.7.1` | Upstream v0.18 имеет unified media/document extension handling и MEDIA cleanup regexes. | Отдельный v0.18 patch file не поставляется. |
| `098-api-server-fallback-model-kwarg` | retired in `v2026.7.1` | Upstream v0.18 делает pop duplicate `model` kwargs перед API Server fallback agent construction. | Отдельный v0.18 patch file не поставляется. |

## Заметные patch'и

### `080-api-server-provider-proxy`

Это сейчас флагманский feature patch в PatchKit. Это не очередная настройка “запусти того же Hermes agent на другой модели”. Patch добавляет отдельный режим API Server для случая, когда нужен стандартный OpenAI-compatible endpoint поверх нескольких provider models.

Upstream Hermes сегодня не даёт такого разделения provider gateway и agent endpoint: его API Server path завязан на работающий Hermes agent/profile. `080` добавляет недостающую границу. Если включить `mode: provider_proxy` и задать allowlist `provider_proxy.models`, сервер становится catalog-routed provider proxy. В этом режиме:

- `/v1/models` возвращает только configured public model IDs;
- `/v1/chat/completions` маршрутизирует запрос по `body.model` к configured provider/model target;
- Hermes обходит `AIAgent`, поэтому нет Hermes tools, memory, sessions, SOUL/context injection и agent run semantics;
- OpenAI-compatible provider'ы идут через Chat Completions passthrough;
- `openai-codex` / Responses provider'ы идут через compatibility adapter;
- ChatGPT Codex targets переиспользуют canonical Cloudflare headers Hermes (`originator`, Codex `User-Agent` и account ID из JWT), поэтому valid OAuth traffic не выглядит как generic server-side SDK request;
- `stream: true` отдаёт OpenAI-compatible `text/event-stream` chunks, если в конфиге включён `allow_streaming: true`;
- OpenAI-style `tools`, `tool_choice`, assistant `tool_calls`, `role: tool` results, `parallel_tool_calls` и inline `image_url` / `input_image` parts сохраняются для IDE clients;
- RooCode-style `reasoning_effort` мапится в Responses `reasoning.effort` для Codex-backed targets;
- sampling params, которые ChatGPT Codex отвергает (`temperature`, `top_p`, penalties, `seed`, logprob knobs), фильтруются перед upstream call.

В тот же patch unit `080` теперь входит `mode: codex_responses_proxy` для отдельного profile/port, когда client говорит на Responses wire нативно. В этом режиме:

- `/v1/models` может live-query `openai-codex` model catalog и затем применить configured allow/deny regex filters;
- `/v1/responses` пересылает Responses body клиента в Codex Responses backend через Hermes OAuth credential pool; для ChatGPT Codex backend принудительно ставит `store: false`, даже если client прислал `store: true`;
- завершённые non-streaming responses и полностью дочитанные streams записывают success выбранному pool credential, а upstream 401/402/429 помечают выбранный credential exhausted и ротируют pool;
- `stream: true` сохраняет Responses SSE events вроде `response.created`, `response.output_text.delta`, `response.completed`, а не конвертирует их в Chat Completions chunks;
- `/v1/chat/completions` и `/v1/runs` fail-closed, чтобы Responses-native clients не делили смешанный wire contract с Chat Completions clients.

Если нужен только provider gateway patch, используй отдельный profile:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.7.1.yaml \
  --profile profiles/v2026.7.1-provider-proxy.yaml \
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
