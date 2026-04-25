# Update workflow

The normal update workflow should not start in your live Hermes checkout.

Start with the update checker:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

Or use the terminal UI:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23-240-ge5647d78.yaml \
  --profile profiles/upstream-fixes.yaml
```

What happens:

1. PatchKit checks that the target repo is a clean git checkout.
2. It fetches the selected upstream remote, usually `origin/main`.
3. It clones the upstream candidate into a temporary directory.
4. It checks the selected patches against that temporary clone.
5. It classifies every patch.
6. It writes a markdown report under `reports/`.
7. It leaves the live working tree unchanged.

## Statuses

| Status | Meaning |
|---|---|
| `applies-cleanly` | The patch can still be applied to the new upstream candidate. |
| `already-present` | The reverse patch applies, so upstream likely already contains that exact change. |
| `conflict` | The patch no longer applies cleanly and needs refresh or retirement. |
| `placeholder` | The selected profile contains a reserved patch ID without a real diff yet. |

## Exit codes

- `0`: selected patch set is structurally safe.
- `2`: at least one patch needs attention.
- `1`: preflight or execution error.

## After a green check

If every selected patch is `applies-cleanly` or `already-present`, update the live checkout manually and explicitly:

```bash
cd ~/.hermes/hermes-agent
git status --short
git branch patchkit-backup-before-upstream-$(date +%Y%m%d-%H%M%S)
git fetch origin
git merge origin/main
```

Then run the focused Hermes tests for the affected patch areas and commit the runtime state if you resolved anything manually.

## If a patch conflicts

Do not force it into the live checkout.

Refresh the patch against the new upstream base, or mark it as upstreamed/superseded in the next manifest if upstream already carries the behavior.
