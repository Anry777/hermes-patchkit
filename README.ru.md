# Hermes PatchKit

Оставь официальный Hermes Agent как базу. Накатывай свои доработки маленькими patch pack'ами.

- без вечного fork drift
- профили патчей для личной и командной настройки
- безопасный rollback перед каждым apply
- повторное применение после обновления upstream
- документация на двух языках: English + Russian

Статус: ранний публичный scaffold. Каркас репозитория, docs, manifest model и helper scripts уже есть. Следующий рубеж — выгрузить реальные patch'и из текущего fork.

## Зачем это нужно

Кастомный Hermes часто быстро превращается в постоянный fork. Сначала это удобно, потом каждое обновление upstream становится отдельным merge-проектом.

Hermes PatchKit меняет схему работы:
- upstream Hermes остаётся upstream;
- локальное поведение живёт в отдельных patch'ах;
- manifests связывают patch set с поддерживаемым upstream ref;
- profiles делают набор доработок воспроизводимым.

## Быстрый старт

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
# Проверить сам scaffold
python scripts/verify.py --self-check

# Проверить целевой checkout Hermes перед apply
python scripts/doctor.py --repo /path/to/hermes-agent --manifest manifests/upstream-v2026.4.23.yaml

# Посмотреть, что profile попробует применить
python scripts/apply.py   --repo /path/to/hermes-agent   --manifest manifests/upstream-v2026.4.23.yaml   --profile minimal   --dry-run
```

## Что здесь есть

### 1. Patch manifests
Manifest привязывает известный upstream ref к конкретному набору patch'ей.

### 2. Patch profiles
Профили вроде `minimal`, `personal`, `full` превращают набор patch'ей в повторяемую конфигурацию.

### 3. Безопасный apply workflow
`apply.py` должен:
- проверить состояние repo;
- разрешить итоговый набор patch'ей;
- создать backup branch;
- выполнить `git apply --check` до любых изменений;
- либо применить patch'и, либо остановиться на первой опасной точке.

### 4. Путь к откату
Если apply прошёл плохо, `rollback.py` возвращает repo к backup branch, созданной прямо перед запуском.

## Почему это лучше, чем жить на fork

| Долгоживущий fork | PatchKit |
|---|---|
| Runtime base уже содержит кастомную историю | Runtime base остаётся официальным upstream |
| Обновления копят merge debt | Обновления сводятся к пере-проверке patch'ей |
| Трудно отделить public и private изменения | Patch units остаются явными и reviewable |
| Откат обычно ручной | Rollback встроен в workflow |

## Текущий v1 scope

- 4–5 основных patch'ей
- один manifest для upstream `v2026.4.23`
- `apply.py`, `rollback.py`, `verify.py`, `doctor.py`, `export_from_fork.py`
- bilingual README и docs
- issue templates и CI validation

## Структура репозитория

```text
hermes-patchkit/
├── manifests/
├── profiles/
├── patches/
├── scripts/
├── docs/en/
├── docs/ru/
├── examples/
└── .github/
```

## Текущие patch candidates

- `010-cli-tui-idle-refresh-fix`
- `020-auth-profile-root-fallback`
- `030-credential-pool-recovery`
- `040-fork-branding-installer` (скорее optional/private)
- `050-whatsapp-baileys-pin`

## Правила безопасности

- PatchKit не должен работать по dirty repo без явного override.
- Перед apply всегда нужен backup branch.
- `--dry-run` должен быть доступен всегда.
- Private/business-specific overlays не должны попадать в public defaults.

## Roadmap

Смотри [ROADMAP.md](ROADMAP.md).

## Contributing

Смотри [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
