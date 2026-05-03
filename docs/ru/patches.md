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
| `070-max-gateway-text-mvp` | exported | Добавляет text-only gateway для MAX messenger: production inbound delivery через webhook-first, явный `MAX_TRANSPORT=polling` для локального теста, настраиваемый polling cadence, operator status diagnostics и outbound text через `POST /messages`. | Local-overlay patch; webhook остаётся production default, а `GET /updates` доступен только как opt-in dev/test fallback (`MAX_POLL_TIMEOUT`, `MAX_POLL_IDLE_SLEEP`). Polling request timeout теперь имеет запас поверх MAX long-poll timeout, поэтому idle polls не засыпают лог `ReadTimeout` stack trace'ами. `hermes status` и gateway setup теперь показывают активный MAX mode и недостающие webhook/public URL настройки без live approved bot. |
| `071-max-gateway-image-input` | exported | Расширяет MAX gateway: принимает входящие image attachments и передаёт их в Hermes vision analysis как photo events. | Зависит от `070-max-gateway-text-mvp`. Обрабатывает image/photo payloads в `MessageBody.attachments` с `url`, `download_url`, `urls` или `photos`, выбирает самый крупный photo variant, кеширует image URLs локально перед dispatch и не отбрасывает сообщения только с картинкой. |
| `072-max-gateway-oneme-url-safety` | exported | Разрешает точный MAX image CDN host `i.oneme.ru` в URL safety, когда он резолвится в `198.18.0.0/15`, чтобы входящие фото кешировались локально перед vision analysis. | Зависит от `071-max-gateway-image-input`. Исключение строго exact-host и HTTPS-only: subdomains, HTTP URL'ы и несвязанные hosts, которые резолвятся в benchmark/private-style адреса, остаются заблокированы SSRF-защитой. |
| `073-max-gateway-image-output` | exported | Добавляет исходящую отправку изображений в MAX: локальные `MEDIA:/path` images и markdown image URLs загружаются через MAX `/uploads?type=image` и отправляются как native image attachments. | Зависит от `072-max-gateway-oneme-url-safety`. Не меняет text-only отправку, поддерживает optional captions/notify metadata, использует multipart field `data` и retry для `attachment.not.ready` на финальном `POST /messages`. |
| `074-max-send-message-media-routing` | exported | Направляет `MEDIA:/path` image attachments из tool `send_message` для MAX в native MAX image upload path вместо отбрасывания как unsupported media. | Зависит от `073-max-gateway-image-output`. Поддерживает raster images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) и уточняет MAX prompt hint: SVG не использовать для photo delivery. |
| `075-max-gateway-file-attachments` | exported | Добавляет native file/document delivery для MAX и кеширование входящих документов: non-image `MEDIA:/path` файлы загружаются через `/uploads?type=file`, а входящие file attachments становятся Hermes document events. | Зависит от `074-max-send-message-media-routing`. Raster images остаются на existing native image path; файлы вроде `.txt`, `.md`, `.csv`, `.pdf`, `.docx`, `.xlsx` идут как file attachments, без показа локальных filesystem paths в чате. |
| `076-max-media-directive-safety` | exported | Не даёт документационным примерам `MEDIA:` и markdown/code snippets распознаваться как реальные вложения. | Зависит от `075-max-gateway-file-attachments`. Для MAX `MEDIA:` directives должны быть реальными локальными путями на отдельной plain line, а не placeholder paths, inline code или fenced code blocks. |
| `077-max-markdown-formatting` | exported | Делает исходящие MAX-сообщения менее плоскими: text и captions по умолчанию уходят с official MAX Markdown formatting. | Зависит от `076-max-media-directive-safety`. Добавляет настройку `MAX_TEXT_FORMAT` (`markdown`, `html` или invalid/disabled values для отправки без formatting metadata), сохраняет explicit per-message metadata overrides и обновляет MAX prompt hint под аккуратный MAX-safe Markdown без code block вокруг `MEDIA:` lines. Fresh runtime live sends подтвердили, что MAX рендерит и Markdown, и HTML; если raw Markdown появится снова, сначала перезапустить gateway/tool process, а не менять payload logic. |
| `080-api-server-provider-proxy` | exported | Добавляет opt-in `provider_proxy` mode для OpenAI-compatible API Server: `/v1/models` отдаёт explicit catalog, а `/v1/chat/completions` маршрутизирует запросы к configured provider/model без создания `AIAgent`. | Generic upstream-candidate patch. Поддерживает non-streaming и streaming Chat Completions для OpenAI-compatible provider'ов, плюс compatibility path для `openai-codex`/Responses, который адаптирует Responses streams в OpenAI Chat Completion SSE chunks, мапит `reasoning_effort` и фильтрует sampling params вроде `temperature`, которые ChatGPT Codex отвергает. `/v1/responses` и `/v1/runs` по-прежнему fail-closed как unsupported operation. |
| `200-dashboard-profile-api` | exported | Добавляет authenticated read-only profile inventory API для built-in dashboard. | Первый upstream-candidate patch в UI/control-plane линейке `200`–`249`; не раскрывает secrets, session messages или log contents. |
| `201-dashboard-profile-selector` | exported | Добавляет built-in Profiles page и sidebar selector/cards поверх `200-dashboard-profile-api`. | Показывает model/provider, skills, env presence, gateway status, paths, session counts и log-file metadata; selection не меняет global active profile. |

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
- MAX local-overlay patches `070`-`077` пока не входят в `v2026.4.30` release manifest; в official release нет MAX adapter, значит всю цепочку нужно свежо refresh'ить последовательно с `070`.
- Активные `v2026.4.30` patches сейчас: `020`, `030`, `040`, `050`, `061`, optional `080` и UI/control-plane `200`/`201`.

## Планируемая UI-линейка `200`+

Для Hermes-native multi-profile dashboard зарезервирован отдельный диапазон patch numbers: `200`–`249`. Концепция и first-wave sequence описаны отдельно: [ui-control-plane-plan.md](ui-control-plane-plan.md).

Стартовая последовательность:

| Patch | Статус | Что должен сделать |
|---|---|---|
| `200-dashboard-profile-api` | exported | Authenticated read-only endpoints `/api/dashboard/profiles` и `/api/dashboard/profiles/{name}` для safe profile inventory: model/provider, skills, gateway, sessions metadata, logs metadata. |
| `201-dashboard-profile-selector` | exported | Встроенная dashboard страница Profiles и sidebar selector/cards поверх `200`: model/provider, skills, env, gateway, paths, session counts и log metadata без изменения global active profile. |
| `202-dashboard-profile-aware-pty` | planned | Embedded `hermes --tui` terminal с optional `profile=<name>` поверх существующего PTY bridge. |
| `203-dashboard-terminal-workspace` | planned | Multi-terminal tabs/panes, reconnect/close/restart UX и profile/cwd labels. |
| `204-dashboard-runtime-registry` | planned | Read-only registry для live Hermes/TUI/gateway/worker processes. |
| `205-dashboard-worker-roster` | planned | Worker cards/roster: role, lane, mission, active task/tool, blocked reason. |
| `206-dashboard-session-log-inspector` | planned | Profile-aware sessions/logs/tool-call inspector. |
| `207-dashboard-controlled-actions` | planned | Auth-gated controlled actions после read-only observability: stop/restart selected terminal/worker/gateway. |

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
