# Getting started

## 1. Clone PatchKit

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
```

## 2. Inspect your Hermes checkout

```bash
python scripts/doctor.py --repo /path/to/hermes-agent --manifest manifests/upstream-v2026.4.23.yaml
```

## 3. Preview a profile

```bash
python scripts/apply.py   --repo /path/to/hermes-agent   --manifest manifests/upstream-v2026.4.23.yaml   --profile minimal   --dry-run
```

## 4. Apply for real

Once the placeholder patch files are replaced with exported diffs, rerun without `--dry-run`.
