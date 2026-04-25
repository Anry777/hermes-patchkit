# Быстрый старт

## 1. Клонируй PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
python3 scripts/verify.py --self-check
```

Каталог patch'ей и workflow-фич: [patches.md](patches.md).

## 2. Сначала проверь совместимость с upstream

Если upstream Hermes обновился, начинать лучше отсюда:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Для scripts/CI есть тот же checker без prompt'ов:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Это проверяет patch'и на временном upstream clone и пишет report в `reports/`. Live checkout при этом не получает patch apply или upstream merge.

## 3. Проверь target checkout

```bash
python3 scripts/doctor.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## 4. Посмотри один real exported patch в dry-run

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## 5. Реальное применение

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --yes
```

## 6. Откат, если нужен

```bash
python3 scripts/rollback.py \
  --repo ~/.hermes/hermes-agent \
  --backup patchkit-backup-YYYYMMDD-HHMMSS \
  --yes
```
