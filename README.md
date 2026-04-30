# Hermes PatchKit

Keep official Hermes upstream. Carry the fixes and feature patches you actually need.

You patched Hermes. Upstream moved. Now what?

Hermes PatchKit checks your local Hermes fixes against a fresh upstream checkout before it touches your live install.
It tells you which patches still apply, which ones look already upstreamed, and which ones need refresh.

## Featured patch: Provider Proxy Gateway

`080-api-server-provider-proxy` is the big one right now. Upstream Hermes API Server behaves like an agent endpoint tied to the running profile/model. PatchKit adds a separate opt-in mode for a different job: one OpenAI-compatible gateway backed by an explicit catalog of provider models.

In `provider_proxy` mode, `/v1/models` exposes only the allowlisted model IDs, and `/v1/chat/completions` routes by `body.model` to the configured provider/model target. Hermes does not create an `AIAgent` for these calls, so there is no SOUL prompt, tools, memory, sessions, or agent run state in the middle. For `openai-codex`, the patch uses a Responses compatibility path behind the OpenAI-compatible surface.

If you want a local Hermes-hosted endpoint that can front multiple provider models, this is the patch to try first.

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/provider-proxy.yaml \
  --yes
```

## Safe upstream check

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Headless mode for CI/scripts:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

The default update check is safe: it fetches upstream metadata, clones the upstream candidate into `/tmp`, checks the selected patch set there, and writes a report under `reports/`. It does not apply patches or merge upstream into your live checkout.

Example output:

```text
Hermes PatchKit update check

Repo:      /home/me/.hermes/hermes-agent
Manifest:  upstream-v2026.4.23-240-ge5647d78.yaml
Current:   runtime-upstream-v2026.4.23 @ 456dc58
Upstream:  origin/main @ abc1234

Patch status:
  ✓ selected-patch-a                       applies-cleanly
  ✓ selected-patch-b                       already-present
  ! selected-patch-c                       conflict

Safe to apply automatically: no (1 patch(es) need attention)
Report: /path/to/hermes-patchkit/reports/update-20260425-211530.md
```

## Why this exists

A long-lived fork feels fine until upstream starts moving. Then every update turns into a merge job, and the line between “official runtime base” and “my local fixes” disappears.

PatchKit keeps that line visible:

- official Hermes stays the runtime base;
- local changes live as small named patch files;
- profiles describe repeatable patch sets;
- update checks run against a temporary upstream clone first;
- apply and rollback stay explicit.

## Current status

This repository is still early, but it now has a working safety loop:

- `scripts/update.py` — one-command upstream compatibility check with markdown reports;
- `scripts/tui.py` — small terminal UI/guide over the update checker;
- `scripts/doctor.py` — inspect a target checkout and selected patch set;
- `scripts/apply.py` — apply a profile or explicit patch list with backup state;
- `scripts/rollback.py` — roll back a PatchKit apply;
- `scripts/verify.py` — repo self-checks;
- `scripts/grok2api_bridge.py` — helper for a dedicated Grok2API sidecar bridge on top of provider_proxy mode;
- maintained patch and feature catalog: [docs/en/patches.md](docs/en/patches.md).

Recent patch highlights:

- Grok2API sidecar bridge — a protocol-level integration that keeps grok2api outside Hermes while exposing it through the `080` provider_proxy gateway. See [docs/en/sidecars-grok2api.md](docs/en/sidecars-grok2api.md).
- `080-api-server-provider-proxy` — the featured provider gateway patch described above. It turns Hermes API Server into an opt-in OpenAI-compatible proxy over an explicit provider/model catalog, without running the Hermes agent layer for those calls.
- `070`–`077` — the MAX local-overlay chain, from webhook-first text MVP through native images/files and Markdown formatting.

## Quick start

```bash
git clone https://github.com/Anry777/hermes-patchkit.git
cd hermes-patchkit

python3 scripts/verify.py --self-check

python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

If you prefer non-interactive output:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

For a single patch:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --patch codex-auxiliary-tool-role-flattening
```

## Patch status meanings

| Status | Meaning |
|---|---|
| `applies-cleanly` | The patch applies to the upstream candidate. |
| `already-present` | The reverse patch applies, so upstream likely already contains that exact change. |
| `conflict` | The patch no longer applies cleanly and needs refresh or retirement. |
| `placeholder` | The manifest points at a reserved patch ID that is not exported yet. |

`update.py` exits with:

- `0` when the selected patch set is structurally safe;
- `2` when at least one patch needs attention;
- `1` for preflight or execution errors.

## Patch catalog

The maintained list of patch units and workflow features lives in [docs/en/patches.md](docs/en/patches.md).

## Why not just stay on a fork?

| Long-lived fork | PatchKit |
|---|---|
| your runtime base carries custom history | your runtime base can stay official upstream |
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
├── reports/
└── .github/
```

## More

- patch catalog and features: [docs/en/patches.md](docs/en/patches.md)
- Russian README: [README.ru.md](README.ru.md)
- Grok2API sidecar bridge: [docs/en/sidecars-grok2api.md](docs/en/sidecars-grok2api.md)
- update workflow: [docs/en/update-workflow.md](docs/en/update-workflow.md)
- rollback: [docs/en/rollback.md](docs/en/rollback.md)
- roadmap: [ROADMAP.md](ROADMAP.md)
- contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- changelog: [CHANGELOG.md](CHANGELOG.md)

## License

MIT
