# Hermes PatchKit

Keep official Hermes Agent upstream. Reapply your custom fixes as small patch packs.

- No long-lived fork drift
- Patch profiles for personal or team setups
- Safe rollback before every apply
- Reapply after upstream updates
- Bilingual docs: English + Russian

Status: early public scaffold. The repository shape, docs, manifest model, and helper scripts are in place. Real patch exports are the next milestone.

## Why this exists

Custom Hermes setups tend to drift into permanent forks. That works for a while, then every upstream update becomes a merge project.

Hermes PatchKit keeps the runtime base clean:
- upstream Hermes stays upstream;
- local behavior lives in isolated patches;
- manifests map patches to supported upstream refs;
- profiles make a known customization set repeatable.

## Quickstart

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit
# Validate the scaffold itself
python scripts/verify.py --self-check

# Inspect a target Hermes checkout before applying anything
python scripts/doctor.py --repo /path/to/hermes-agent --manifest manifests/upstream-v2026.4.23.yaml

# Preview what a profile would try to apply
python scripts/apply.py   --repo /path/to/hermes-agent   --manifest manifests/upstream-v2026.4.23.yaml   --profile minimal   --dry-run
```

## What you get

### 1. Patch manifests
A manifest ties one supported upstream ref to a known patch set.

### 2. Patch profiles
Profiles like `minimal`, `personal`, and `full` turn a pile of patches into a repeatable setup.

### 3. Safe apply workflow
`apply.py` is designed to:
- check repo state;
- resolve selected patches;
- create a backup branch;
- run `git apply --check` before changing anything;
- apply patches or stop on the first unsafe step.

### 4. Rollback path
If an apply goes wrong, `rollback.py` takes the target repo back to a backup branch created right before the run.

## Why PatchKit instead of a fork?

| Long-lived fork | PatchKit |
|---|---|
| Runtime base contains custom history | Runtime base stays official upstream |
| Upgrades accumulate merge debt | Upgrades become patch revalidation |
| Hard to separate public vs private changes | Patch units stay explicit and reviewable |
| Rollback is usually manual | Rollback is part of the workflow |

## Current v1 scope

- 4–5 core patches
- one manifest for upstream `v2026.4.23`
- `apply.py`, `rollback.py`, `verify.py`, `doctor.py`, `export_from_fork.py`
- bilingual README and docs
- issue templates and CI validation

## Repository layout

```text
hermes-patchkit/
├── manifests/
├── profiles/
├── patches/
├── scripts/
├── docs/en/
├── docs/ru/
├── examples/
└── .github/
```

## Current patch candidates

- `010-cli-tui-idle-refresh-fix`
- `020-auth-profile-root-fallback`
- `030-credential-pool-recovery`
- `040-fork-branding-installer` (likely optional/private)
- `050-whatsapp-baileys-pin`

## Safety rules

- PatchKit should refuse dirty target repos unless you pass an explicit override.
- Every apply should create a backup branch.
- `--dry-run` should always be available.
- Private or business-specific overlays should stay separate from public defaults.

## Russian docs

Full Russian docs: [README.ru.md](README.ru.md)

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
