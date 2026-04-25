# Быстрый старт

## 1. Клонируй PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
```

## 2. Проверь свой checkout Hermes

```bash
python scripts/doctor.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## 3. Посмотри один реальный exported patch в dry-run

```bash
python scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## 4. Реальное применение

```bash
python scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --yes
```

## 5. Откат, если нужен

```bash
python scripts/rollback.py \
  --repo /path/to/hermes-agent \
  --backup patchkit-backup-YYYYMMDD-HHMMSS \
  --yes
```
