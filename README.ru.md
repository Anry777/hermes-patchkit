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

Что уже появилось сверх scaffold:
- настоящий patch `020-auth-profile-root-fallback`
- настоящий patch `060-codex-memory-flush-responses-contract`
- настоящий patch `061-codex-auxiliary-tool-role-flattening`

Остальные зарезервированные patch IDs пока ещё placeholder'ы. Следующий шаг — продолжать заменять их на реальные export'ы.

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
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening

# Посмотреть один реальный exported patch без изменений в repo
python3 scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## Какие patch'и сейчас зарезервированы

Пока в scaffold заведены такие логические единицы:

- `010-cli-tui-idle-refresh-fix`
- `020-auth-profile-root-fallback` — exported
- `030-credential-pool-recovery`
- `040-fork-branding-installer` — скорее optional/private
- `050-whatsapp-baileys-pin`

Часть patch files уже заменена на реальные exported diffs; оставшиеся placeholder'ы дальше будут заменяться на unified diff'ы из рабочего fork.

## Почему не просто жить на fork

| Долгоживущий fork | PatchKit |
|---|---|
| базовый runtime уже несёт кастомную историю | базовый runtime остаётся официальным upstream |
| обновления копят merge debt | обновления сводятся к проверке patch'ей |
| public и private изменения смешиваются | каждую доработку можно держать отдельно |
| откат обычно ручной | rollback встроен в workflow |

## Что уже покрыто этим scaffold

Сейчас в публичном репо уже есть:
- pinned manifests, включая `upstream-v2026.4.23-240-ge5647d78.yaml`
- profiles `minimal`, `personal`, `full`, `upstream-fixes`, `local-overlays`
- смесь из реальных exported patches (`020`, `060`, `061`) и placeholder patch IDs для остальных запланированных единиц
- helper scripts
- базовая GitHub hygiene для публичной разработки

Следующий по-настоящему важный шаг всё ещё тот же:
продолжать выгружать реальные patch'и из Hermes delta и валидировать их на чистом upstream checkout.

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
