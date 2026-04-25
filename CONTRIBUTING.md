# Contributing

Thanks for helping improve Hermes PatchKit.

## Principles

- Keep official Hermes upstream as the runtime base.
- Keep patches small and logically isolated.
- Prefer reviewable diffs over clever automation.
- Never hide risky repo mutations behind a silent default.
- Do not mix public reusable patches with private business-specific overlays.

## What good contributions look like

### New patch
- one logical change per patch file
- manifest metadata updated
- profile references updated if needed
- verification notes added
- docs updated when user-visible behavior changes

### Script changes
- keep rollback and dry-run behavior safe
- fail loudly on unsupported or dirty repo states
- avoid partial apply states

## Local checks

```bash
python scripts/verify.py --self-check
```

## Pull requests

Before opening a PR:
- explain the problem clearly
- keep the change set focused
- mention whether the change affects manifests, profiles, or docs
- include verification notes

## Non-goals

This project is not trying to replace upstream Hermes.
It is trying to make local customization compatible with upstream Hermes.
