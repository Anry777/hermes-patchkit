# Patch'и и фичи

Это публичный каталог поддерживаемых patch units и workflow-фич PatchKit. README ссылается сюда, а не дублирует список patch'ей прямо на первом экране.

Совместимость не статична. Перед apply нужно запускать `scripts/update.py` или `scripts/tui.py` против своего Hermes checkout.

## Доступные patch units

| Patch | Статус | Что делает | Примечания |
|---|---|---|---|
| `010-cli-tui-idle-refresh-fix` | exported | Убирает idle CLI/TUI repaint, который тянул terminal viewport. | На последнем live smoke check применяется чисто. |
| `020-auth-profile-root-fallback` | exported | Позволяет profile auth store fallback'иться на root auth store, если у профиля ещё нет `auth.json`. | Есть focused regression tests по auth/profile поведению. |
| `060-codex-memory-flush-responses-contract` | exported, needs refresh check | Держит Codex memory flush в рамках Responses transport contract. | Конфликтует с текущим fetched upstream в `run_agent.py`; перед следующим live upstream merge нужен refresh или retirement. |
| `061-codex-auxiliary-tool-role-flattening` | exported | Flatten'ит unsupported transcript roles вроде `tool` перед auxiliary Codex Responses calls. | На последнем live smoke check применяется чисто. |

## Запланированные patch units

| Patch | Статус | Что должен сделать | Примечания |
|---|---|---|---|
| `030-credential-pool-recovery` | planned | Улучшить credential-pool recovery и разделить exhausted credentials от invalid credentials. | Остаётся в manifest как planned work, но не входит в active profiles, пока нет real diff. |

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

Удалённые идеи здесь не перечисляются. Этот каталог — только для PatchKit units, которые реально планируется поддерживать.
