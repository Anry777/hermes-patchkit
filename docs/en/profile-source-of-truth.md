# Hermes profile source of truth

PatchKit-managed Hermes installs use this policy to prevent profile settings from drifting between `config.yaml`, `.env`, runtime edits, and service state.

## Policy table

| Area | Source of truth | Notes |
| --- | --- | --- |
| Provider OAuth state and credential pools | Root Hermes auth store: `/root/.hermes/auth.json` plus `auth.lock` | Shared across profiles. Do not duplicate provider OAuth tokens into profile `.env` files. |
| Profile non-secret configuration | Profile `config.yaml` | Model/provider selection, gateway behavior, routing policy, tool defaults, terminal/browser settings, and integration options that Hermes can read from config. |
| Profile secrets | Profile `.env` | Tokens, passwords, API keys, private keys, and rare documented env-only exceptions. Keep generated examples redacted. |
| Telegram routing policy | `telegram:` in profile `config.yaml` | Includes allowed users/chats/topics/threads, group allowlists, home channel/thread, mention policy, free-response targets, and channel prompts. Keep `TELEGRAM_BOT_TOKEN` in `.env`. |
| Runtime code fixes | PatchKit patches, manifests, and profiles | A direct runtime edit is temporary until it is represented in PatchKit. |
| Intended office service state | Cleanup plan and final audit report | The plan describes what should be running and why. |
| Actual service state | Hermes CLI-managed systemd units and live health/log checks | Verify with service status, ports, health endpoints, and fresh logs. |
| Cron jobs | Profile-local `cron/jobs.json` | Treat each profile independently unless a migration explicitly changes ownership. |

## Operational rules

1. Prefer moving non-secret settings from `.env` into `config.yaml`, not the other way around.
2. Keep `.env` active lines limited to secrets/tokens/passwords and documented env-only exceptions.
3. If Hermes cannot yet read a non-secret setting from `config.yaml`, document it as an env-only exception and keep the exception narrow.
4. Do not work around provider/auth issues by copying root credentials into named profiles.
5. For office gateway edits: back up files, validate YAML/config loading, restart only the affected gateway service, then inspect fresh logs.
6. Use `scripts/clean_profile_config.py` to normalize `.env`/`config.yaml.example` after updates.
7. Use `scripts/install_operator_policy.py` to inject the short operator policy into a profile's `agent.system_prompt` so the running Hermes profile follows the same split.

## Installing the policy into a profile

Dry-run first:

```bash
python3 scripts/install_operator_policy.py --home ~/.hermes/profiles/1c
```

Write with a backup:

```bash
python3 scripts/install_operator_policy.py --home ~/.hermes/profiles/1c --write --backup
```

The helper writes a managed block in `agent.system_prompt`. Re-running it updates the block in place instead of appending duplicates.
