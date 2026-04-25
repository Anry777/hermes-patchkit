# Hermes PatchKit

If you have customized Hermes for yourself, you know how the story usually ends: the fork becomes the product.

Hermes PatchKit takes a different path.
It keeps official Hermes Agent upstream as the base and moves your local behavior into small, named patch files that you can review, reapply, and roll back.

- keep upstream Hermes as upstream
- package local fixes as explicit patches
- group them into repeatable profiles
- create a backup before apply
- dry-run before touching the target repo

## What this repo is today

This repository is the public scaffold for that workflow.

It already contains:
- the repo structure
- bilingual README/docs
- manifest and profile files
- helper scripts for doctor/apply/rollback/verify/export
- stable patch IDs for the first patch candidates

It already contains two real exported patch diffs from the working Hermes delta:
- `060-codex-memory-flush-responses-contract`
- `061-codex-auxiliary-tool-role-flattening`

The rest of the reserved patch IDs are still placeholders. Expanding that set is the next milestone.

## Why bother?

A long-lived fork feels fine until upstream moves.
Then every update becomes a merge job, and the line between “my local fix” and “my runtime base” disappears.

PatchKit is meant to make that line visible again:
- upstream stays clean
- local changes stay isolated
- supported combinations live in manifests
- personal/team setups live in profiles

## What PatchKit is trying to become

A typical run should look like this:

1. point PatchKit at a clean Hermes checkout
2. inspect the target repo
3. select a profile or patch list
4. create a backup branch
5. check whether patches apply cleanly
6. apply them or stop safely
7. roll back if needed

That is the promise.
This first public version is the scaffold that will grow into it.

## Quick look

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit

# sanity-check the repository itself
python3 scripts/verify.py --self-check

# inspect a Hermes checkout before doing anything risky
python3 scripts/doctor.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening

# preview one real exported patch without changing the target repo
python3 scripts/apply.py \
  --repo /path/to/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening \
  --dry-run
```

## Current patch candidates

These are the first logical units reserved in the scaffold:

- `010-cli-tui-idle-refresh-fix`
- `020-auth-profile-root-fallback`
- `030-credential-pool-recovery`
- `040-fork-branding-installer` — likely optional/private
- `050-whatsapp-baileys-pin`

Right now the `.patch` files are placeholders.
They will be replaced with real unified diffs exported from the Hermes fork.

## Why this instead of just staying on a fork?

| Long-lived fork | PatchKit |
|---|---|
| your runtime base carries custom history | your runtime base stays official upstream |
| upstream updates pile up merge debt | upstream updates become patch revalidation |
| public and private changes blur together | each change can stay in its own patch |
| rollback is usually manual | rollback is part of the workflow |

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

## Current scope

The public repo currently includes:
- pinned manifests, including `upstream-v2026.4.23-240-ge5647d78.yaml`
- profiles such as `minimal`, `personal`, `full`, `upstream-fixes`, and `local-overlays`
- a mix of real exported patches (`060`, `061`) and placeholder patch IDs for the remaining planned units
- helper scripts
- repo hygiene for public development

The next real step is still obvious:
export more patches from the Hermes delta and keep validating them on clean upstream checkouts.

## What I want this repo to be good at

Not hype. Not branding. Not “customization platform” marketing copy.

Useful things:
- small diffs
- predictable apply behavior
- clear rollback story
- honest compatibility notes
- less fork drift

## Russian docs

Русская версия: [README.ru.md](README.ru.md)

## More

- roadmap: [ROADMAP.md](ROADMAP.md)
- contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- changelog: [CHANGELOG.md](CHANGELOG.md)

## License

MIT
