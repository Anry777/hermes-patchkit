# Getting started

## 1. Clone PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
python3 scripts/verify.py --self-check
```

Patch catalog and workflow features: [patches.md](patches.md).

## 2. Check upstream compatibility first

Start here when upstream Hermes moved:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

For scripts/CI use the same checker without prompts:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

This checks patches against a temporary upstream clone and writes a report under `reports/`. It does not apply patches or merge upstream into the live checkout.

## 3. Inspect a target checkout

```bash
python3 scripts/doctor.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## 4. Preview one real exported patch

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## 5. Apply for real

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --yes
```

## 6. Roll back if needed

```bash
python3 scripts/rollback.py \
  --repo ~/.hermes/hermes-agent \
  --backup patchkit-backup-YYYYMMDD-HHMMSS \
  --yes
```
