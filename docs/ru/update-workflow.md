# Workflow обновления

Нормальное обновление не должно начинаться с live Hermes checkout.

Сначала запускай update checker:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml
```

Или terminal UI:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml
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

## Post-update уборка профиля

После обновления Hermes и apply/refresh patch'ей приведи локальный профиль к нормальной схеме источников истины:

```bash
python3 scripts/clean_profile_config.py --home ~/.hermes --write
```

Если хочешь, чтобы schema migration, runtime dependency pins и cleanup запускались сразу после `scripts/apply.py`, добавь post-apply флаги:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml \
  --migrate-profile-config \
  --pin-runtime-dependencies \
  --clean-profile-config \
  --yes
```

Что делает migration helper:

1. Запускает собственный `hermes_cli.config.migrate_config(interactive=False)` из target checkout, а не хранит копию defaults внутри PatchKit.
2. По умолчанию работает как safe dry-run:
   ```bash
   python3 scripts/migrate_profile_config.py --repo ~/.hermes/hermes-agent --home ~/.hermes
   ```
3. В `--write` режиме создаёт `config.yaml.bak_migrate_profile_<timestamp>` перед изменением live profile.
4. Печатает redacted diff, чтобы API keys/tokens не утекали в terminal output.
5. Должен запускаться до `--clean-profile-config`, потому cleanup строит examples/env hygiene уже из финального migrated config.

Что делает dependency-pin helper:

1. Находит Python target checkout в `venv/bin/python` или `.venv/bin/python`.
2. По умолчанию делает dry-run:
   ```bash
   python3 scripts/pin_runtime_dependencies.py --repo ~/.hermes/hermes-agent
   ```
3. В `--write` режиме вызывает `uv pip install --python <runtime-python> setuptools<80`.
4. Нужен для runtime compatibility pins, которые не являются patch'ами исходников. Текущий pin убирает warning `lark-oapi` / `pkg_resources` на современных setuptools releases.

Что делает cleanup helper:

1. Читает живой `config.yaml` профиля.
2. Создаёт/обновляет `config.yaml.example` рядом с ним: secrets redacted, пустой/runtime-мусор вычищен.
3. Пересобирает `.env` по платформам/интеграциям.
4. Оставляет активными только credential-shaped secrets/tokens/API keys.
5. Non-secret env settings комментирует с причиной: либо `use config.yaml ... instead`, либо `env-only exception`.

Если конкретная интеграция пока реально читает non-secret значение только из env и должна продолжить работать до code-fix'а, используй временный режим:

```bash
python3 scripts/clean_profile_config.py --home ~/.hermes --write --keep-env-only
```

Но нормальная цель остаётся такой: `config.yaml` — поведение и non-secret настройки, `.env` — только secrets/tokens и редкие env-only исключения, которые надо отдельно устранять в коде.

## Если patch конфликтует

Не force'ить его в live checkout.

Нужно refresh'нуть patch на новой upstream базе или пометить его как upstreamed/superseded в новом manifest, если upstream уже несёт нужное поведение.
