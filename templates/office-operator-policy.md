Office Hermes source-of-truth policy

Follow this policy before editing Hermes profiles, gateways, bots, or service configuration:

- Provider OAuth state and credential pools live in the root Hermes auth store (`/root/.hermes/auth.json` plus `auth.lock`). Do not copy provider OAuth tokens into profile `.env` files as a workaround.
- config.yaml owns non-secret behavior and routing settings: model/provider selection, gateway policy, Telegram routing, Home Assistant URLs, tool defaults, terminal/browser settings, and integration options that Hermes can read from config.
- .env owns only secrets/tokens/passwords and explicitly documented env-only exceptions. Keep examples redacted.
- Telegram routing policy belongs under `telegram:` in `config.yaml`: allowed users/chats/topics/threads, group allowlists, home channel/thread, mention policy, free-response targets, and channel prompts. Keep only `TELEGRAM_BOT_TOKEN` active in `.env` unless a current runtime limitation is documented.
- Runtime code fixes are represented in PatchKit manifests/profiles/patches before they are considered canonical. A live runtime edit without PatchKit representation is temporary diagnostic state.
- Intended service state is documented in the cleanup plan/final audit; actual state is verified through Hermes CLI-managed systemd units and health/log checks.
- Cron jobs are profile-local state (`cron/jobs.json`) unless explicitly migrated.
- Before changing an office gateway profile: create backups, keep secrets redacted, validate YAML/config loading, restart only the affected service, and inspect fresh logs.
