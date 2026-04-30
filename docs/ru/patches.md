# Patch'и и фичи

Это публичный каталог поддерживаемых patch units и workflow-фич PatchKit. README ссылается сюда, а не дублирует список patch'ей прямо на первом экране.

Совместимость не статична. Перед apply нужно запускать `scripts/update.py` или `scripts/tui.py` против своего Hermes checkout.

## Доступные patch units

| Patch | Статус | Что делает | Примечания |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Убирает idle CLI/TUI repaint, который тянул terminal viewport. | На последнем live smoke check применяется чисто. |
| `020-auth-profile-root-fallback` | exported | Даёт profile auth stores фолбэк на root auth store, если в profile ещё нет `auth.json`. | Есть focused auth/profile regression coverage. |
| `030-credential-pool-recovery` | exported | Улучшает credential-pool recovery: отслеживает active credential ID, не возвращает invalid credentials через cooldown recovery и откладывает round-robin rotation до release lease. | Перенесён из legacy fork commits `e17a823c` и `97fa2dbc`; зависит от `020-auth-profile-root-fallback`. |
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
| `080-api-server-provider-proxy` | exported | Добавляет opt-in `provider_proxy` mode для OpenAI-compatible API Server: `/v1/models` отдаёт explicit catalog, а `/v1/chat/completions` маршрутизирует запросы к configured provider/model без создания `AIAgent`. | Generic upstream-candidate patch. Поддерживает non-streaming Chat Completions passthrough для OpenAI-compatible provider'ов и compatibility path для `openai-codex`/Responses; streaming, `/v1/responses` и `/v1/runs` fail-closed как unsupported operation. |

## Заметные patch'и

### `080-api-server-provider-proxy`

Это сейчас флагманский feature patch в PatchKit. Это не очередная настройка “запусти того же Hermes agent на другой модели”. Patch добавляет отдельный режим API Server для случая, когда нужен стандартный OpenAI-compatible endpoint поверх нескольких provider models.

Upstream Hermes сегодня не даёт такого разделения provider gateway и agent endpoint: его API Server path завязан на работающий Hermes agent/profile. `080` добавляет недостающую границу. Если включить `mode: provider_proxy` и задать allowlist `provider_proxy.models`, сервер становится catalog-routed provider proxy. В этом режиме:

- `/v1/models` возвращает только configured public model IDs;
- `/v1/chat/completions` маршрутизирует запрос по `body.model` к configured provider/model target;
- Hermes обходит `AIAgent`, поэтому нет Hermes tools, memory, sessions, SOUL/context injection и agent run semantics;
- OpenAI-compatible provider'ы идут через non-streaming Chat Completions passthrough;
- `openai-codex` / Responses provider'ы идут через compatibility adapter;
- streaming, `/v1/responses` и `/v1/runs` fail-closed до отдельных follow-up patch'ей.

Если нужен только provider gateway patch, используй отдельный profile:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/provider-proxy.yaml \
  --yes
```

Для canary/main — `manifests/canary-main-a1921c43c.yaml` и `profiles/canary-main-provider-proxy.yaml`.

### Grok2API sidecar bridge

Первый sidecar pack поверх provider_proxy описан в [sidecars-grok2api.md](sidecars-grok2api.md). grok2api остаётся отдельным сервисом, PatchKit добавляет profiles, которые выбирают только `080`, кладёт loopback Docker Compose/config examples и даёт `scripts/grok2api_bridge.py` для render config и smoke checks endpoint'а. Это явно sidecar integration, не vendored Grok provider и не часть default profiles.

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
