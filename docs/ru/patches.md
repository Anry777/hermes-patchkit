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

## Workflow-фичи

| Фича | Entry point | Статус |
|---|---|---|
| Проверка совместимости с upstream | `scripts/update.py` | работает |
| Terminal update dashboard | `scripts/tui.py` | работает |
| Preflight target checkout | `scripts/doctor.py` | работает |
| Apply patch/profile с backup state | `scripts/apply.py` | работает для exported patches |
| Rollback PatchKit apply | `scripts/rollback.py` | работает; есть regression coverage для tracked, untracked и ignored cleanup cases |
| Self-check репозитория | `scripts/verify.py --self-check` | работает |

## Что значат статусы

- `exported`: patch file содержит реальный unified diff.
- `planned`: patch ID оставлен в manifest как запланированная работа, но real diff ещё не готов.
- `needs refresh check`: patch существует, но совместимость с текущим upstream требует review.
- `local-overlay`: поддерживаемая PatchKit integration/customization, полезная локально, но не обязательно upstream-bound.

Удалённые идеи здесь не перечисляются. Этот каталог — только для PatchKit units, которые реально планируется поддерживать.
