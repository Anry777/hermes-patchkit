# Workflow обновления

Нормальное обновление не должно начинаться с live Hermes checkout.

Сначала запускай update checker:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Или terminal UI:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Что происходит:

1. PatchKit проверяет, что target repo — чистый git checkout.
2. Подтягивает выбранный upstream remote, обычно `origin/main`.
3. Клонирует upstream candidate во временную директорию.
4. Проверяет выбранные patch'и на этом временном clone.
5. Классифицирует каждый patch.
6. Пишет markdown report в `reports/`.
7. Не меняет live working tree.

## Статусы

| Status | Meaning |
|---|---|
| `applies-cleanly` | Patch всё ещё применим к новому upstream candidate. |
| `already-present` | Reverse patch применился, значит upstream, вероятно, уже содержит ровно это изменение. |
| `conflict` | Patch больше не применяется чисто: нужен refresh или retirement. |
| `placeholder` | В выбранном profile есть зарезервированный patch ID без real diff. |

## Exit codes

- `0`: выбранный patch set структурно безопасен.
- `2`: хотя бы один patch требует внимания.
- `1`: preflight или выполнение упали.

## Если проверка зелёная

Если все выбранные patch'и получили `applies-cleanly` или `already-present`, live checkout обновляется явно:

```bash
cd ~/.hermes/hermes-agent
git status --short
git branch patchkit-backup-before-upstream-$(date +%Y%m%d-%H%M%S)
git fetch origin
git merge origin/main
```

После этого запускаются focused Hermes tests по затронутым зонам. Если пришлось что-то решать вручную — runtime state коммитится в постоянную рабочую branch.

## Если patch конфликтует

Не force'ить его в live checkout.

Нужно refresh'нуть patch на новой upstream базе или пометить его как upstreamed/superseded в новом manifest, если upstream уже несёт нужное поведение.
