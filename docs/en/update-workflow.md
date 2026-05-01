# Update workflow

The normal update workflow should not start in your live Hermes checkout.

Start with the update checker:

```bash
python3 scripts/update.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml
```

Or use the terminal UI:

```bash
python3 scripts/tui.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml
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

## Post-update profile cleanup

After updating Hermes and applying/refreshing patches, normalize the local profile config/env split:

```bash
python3 scripts/clean_profile_config.py --home ~/.hermes --write
```

If you want schema migration and cleanup to run immediately after `scripts/apply.py`, add both post-apply flags:

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.30.yaml \
  --profile profiles/v2026.4.30-upstream-fixes.yaml \
  --migrate-profile-config \
  --clean-profile-config \
  --yes
```

The migration helper:

1. Runs the target checkout's own `hermes_cli.config.migrate_config(interactive=False)` instead of carrying copied defaults in PatchKit.
2. Supports safe dry-run by default:
   ```bash
   python3 scripts/migrate_profile_config.py --repo ~/.hermes/hermes-agent --home ~/.hermes
   ```
3. In `--write` mode, creates `config.yaml.bak_migrate_profile_<timestamp>` before changing the live profile.
4. Prints a redacted diff, so API keys/tokens do not leak into terminal output.
5. Should run before `--clean-profile-config`, because cleanup generates examples/env hygiene from the final migrated config.

The cleanup helper:

1. Reads the live profile `config.yaml`.
2. Creates/updates `config.yaml.example` next to it with secrets redacted and empty/runtime noise pruned.
3. Rebuilds `.env` grouped by platform/integration.
4. Keeps only credential-shaped secrets/tokens/API keys active by default.
5. Comments non-secret env settings with a reason: either `use config.yaml ... instead` or `env-only exception`.

If a current Hermes integration still reads a non-secret setting only from env and must keep working until a code fix lands, use the temporary compatibility mode:

```bash
python3 scripts/clean_profile_config.py --home ~/.hermes --write --keep-env-only
```

The target policy remains: `config.yaml` owns behaviour and non-secret settings; `.env` owns only secrets/tokens and rare env-only exceptions that should be fixed in code later.

## If a patch conflicts

Do not force it into the live checkout.

Refresh the patch against the new upstream base, or mark it as upstreamed/superseded in the next manifest if upstream already carries the behavior.
