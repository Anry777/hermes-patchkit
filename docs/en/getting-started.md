# Getting started

## 1. Clone PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
```

## 2. Inspect your Hermes checkout

```bash
python scripts/doctor.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## 3. Preview one real exported patch

```bash
python scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## 4. Apply for real

```bash
python scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --yes
```

## 5. Roll back if needed

```bash
python scripts/rollback.py \
  --repo /path/to/hermes-agent \
  --backup patchkit-backup-YYYYMMDD-HHMMSS \
  --yes
```
