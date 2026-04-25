# Быстрый старт

## 1. Клонируй PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
```

## 2. Проверь свой checkout Hermes

```bash
python scripts/doctor.py --repo /path/to/hermes-agent --manifest manifests/upstream-v2026.4.23.yaml
```

## 3. Посмотри profile в dry-run

```bash
python scripts/apply.py   --repo /path/to/hermes-agent   --manifest manifests/upstream-v2026.4.23.yaml   --profile minimal   --dry-run
```

## 4. Реальное применение

Когда placeholder patch files будут заменены на настоящие diff'ы, запусти ту же команду без `--dry-run`.
