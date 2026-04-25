# Hermes PatchKit

Если ты долго допиливаешь Hermes под себя, обычно всё заканчивается одинаково: fork перестаёт быть «парой локальных правок» и становится основным продуктом.

Hermes PatchKit нужен, чтобы развернуть эту историю обратно.

Идея простая:
- официальный Hermes остаётся базой
- твои доработки живут в отдельных patch'ах
- patch'и собираются в profiles
- перед apply создаётся backup
- перед реальным изменением всегда можно сделать dry-run

## Что здесь уже есть

Сейчас это не «готовый patch manager», а первый публичный scaffold.

В репозитории уже лежат:
- структура проекта
- README и docs на двух языках
- manifests и profiles
- helper scripts для doctor/apply/rollback/verify/export
- зарезервированные patch IDs под первые реальные доработки

Чего пока нет:
- настоящих `.patch` файлов, выгруженных из рабочего Hermes fork

Это и есть следующий главный шаг.

## Зачем вообще городить отдельный слой

Постоянный fork удобен ровно до того момента, пока upstream не начинает жить своей жизнью.
Потом любое обновление превращается в merge-ремонт, а граница между «официальной базой» и «моими локальными правками» исчезает.

PatchKit нужен, чтобы эту границу вернуть:
- upstream остаётся чистым
- локальные изменения остаются отдельными
- совместимые наборы живут в manifests
- повторяемые конфигурации живут в profiles

## Как это должно работать в нормальном виде

Нормальный сценарий такой:

1. берём чистый checkout Hermes
2. прогоняем doctor
3. выбираем profile или список patch'ей
4. создаём backup branch
5. проверяем, что patch'и применяются чисто
6. применяем их или безопасно останавливаемся
7. при необходимости откатываемся назад

Эта версия репозитория — не финал, а публичный каркас под такой workflow.

## Быстрый взгляд

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit

# Проверить сам репозиторий
python3 scripts/verify.py --self-check

# Проверить целевой Hermes checkout до любых действий
python3 scripts/doctor.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/minimal.yaml

# Посмотреть, что profile попробует сделать, без изменений в repo
python3 scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/minimal.yaml \
  --dry-run
```

## Какие patch'и сейчас зарезервированы

Пока в scaffold заведены такие логические единицы:

- `010-cli-tui-idle-refresh-fix`
- `020-auth-profile-root-fallback`
- `030-credential-pool-recovery`
- `040-fork-branding-installer` — скорее optional/private
- `050-whatsapp-baileys-pin`

Сейчас это placeholder'ы.
Дальше они должны быть заменены на реальные unified diff'ы из рабочего fork.

## Почему не просто жить на fork

| Долгоживущий fork | PatchKit |
|---|---|
| базовый runtime уже несёт кастомную историю | базовый runtime остаётся официальным upstream |
| обновления копят merge debt | обновления сводятся к проверке patch'ей |
| public и private изменения смешиваются | каждую доработку можно держать отдельно |
| откат обычно ручной | rollback встроен в workflow |

## Что уже покрыто этим scaffold

Сейчас в публичном репо уже есть:
- manifest для `v2026.4.23`
- profiles `minimal`, `personal`, `full`
- placeholder patch files со стабильными ID
- helper scripts
- базовая GitHub hygiene для публичной разработки

Следующий по-настоящему важный шаг очевиден:
выгрузить реальные patch'и из Hermes fork и проверить их на чистом upstream checkout.

## Каким я хочу видеть этот репозиторий

Не шумным. Не рекламным. Не «революционной платформой кастомизации».

Хочется другого:
- маленьких diff'ов
- предсказуемого apply
- понятного rollback
- честных compatibility notes
- меньше fork drift

## Документы

- roadmap: [ROADMAP.md](ROADMAP.md)
- contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- changelog: [CHANGELOG.md](CHANGELOG.md)
- English version: [README.md](README.md)

## License

MIT
