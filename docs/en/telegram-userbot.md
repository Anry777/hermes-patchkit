# Telegram MTProto userbot plugin

`079-telegram-userbot-platform-plugin` adds an experimental, explicit opt-in Hermes platform named `telegram_userbot`. It is exported in the release manifest but intentionally excluded from the default personal profile. It connects through a Telegram user account over MTProto with Telethon. It does not modify or replace the official `telegram-platform`, which continues to use the Telegram Bot API.

## Risk and scope

Telegram user-account automation can violate Telegram policy or trigger account limitations. Use a dedicated account, a strict allowlist, and explicit operator acceptance. Never expose login codes, API hash, two-factor password, or session material in logs, prompts, config files, or chat output.

The MVP supports:

- profile-local Telethon file sessions and a process lock;
- optional Telethon `StringSession`;
- deny-by-default user/chat allowlists;
- inbound text and profile-local media downloads;
- outbound text, replies, edits, typing, images, documents, and video files;
- human-account system UI suppression: recognized Hermes slash commands are ignored, internal agent failures stay in logs, and approval prompts fail closed;
- dynamic Hermes platform registration without changes to the built-in Telegram Bot API adapter.

## Apply

```bash
cd /root/hermes-patchkit
python3 scripts/apply.py \
  --repo /root/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.7.20.yaml \
  --patch telegram-userbot-platform-plugin \
  --yes
```

The plugin declares `telethon>=1.40.0,<2` as a lazy plugin dependency. Verify the target runtime can import it before bootstrap.

## Profile configuration

Enable the plugin and platform in the target profile:

```yaml
plugins:
  enabled:
    - platforms/telegram_userbot

platforms:
  telegram_userbot:
    enabled: true
    extra:
      work_dir: /root/.hermes/profiles/telegram-userbot/telegram_userbot
      session_name: main
      allow_all_users: false
      allowed_users: []
      allowed_chats: []
      mark_read: false
      download_media: false
      max_media_bytes: 20971520
      max_media_cache_bytes: 268435456
      max_media_cache_files: 1000
      send_typing: true
      human_pacing_enabled: false
      human_pacing_excluded_user_ids: []
      thinking_delay_min_ms: 1200
      thinking_delay_max_ms: 3200
      typing_chars_per_second: 12
      typing_jitter_ratio: 0.15
      typing_delay_min_ms: 1800
      typing_delay_max_ms: 30000
```

`human_pacing_enabled` is disabled by default and affects only the `telegram_userbot` platform. When enabled, the plugin waits for a randomized `thinking_delay_*`, starts the typing indicator, and pads fast generations toward the length-dependent `typing_delay_*` target. `typing_jitter_ratio` controls the symmetric random variation around the calculated typing duration (`0.15` means ±15% and values must be between `0` and `1`). Time already spent generating is counted, and artificial typing is capped by `typing_delay_max_ms`. This contract requires the gateway typing indicator to remain enabled and final responses to be delivered as one non-streaming message; streaming/edit-in-place delivery does not use final-length pacing.

`human_pacing_excluded_user_ids` accepts Telegram sender IDs. Both artificial pauses are bypassed for those senders. The list works in DMs and groups, where sender ID differs from chat ID. Normal model processing time is neither hidden nor padded for excluded senders.

Keep credentials in `/root/.hermes/profiles/telegram-userbot/.env`:

```bash
TELEGRAM_USERBOT_API_ID=...
TELEGRAM_USERBOT_API_HASH=...
TELEGRAM_USERBOT_PHONE=+...
# TELEGRAM_USERBOT_2FA_PASSWORD=...
# TELEGRAM_USERBOT_SESSION_STRING=...
```

`api_id` and `api_hash` are always required. In addition, first-time bootstrap needs the phone number; later runs can use the profile-local session file. A `StringSession` is optional but more sensitive because it directly grants account access. The plugin rejects `api_id`, `api_hash`, `phone`, `session_string`, `two_factor_password`, and `2fa_password` when supplied through `config.yaml`; these values are accepted only from the profile environment.

`work_dir` must resolve under the active profile's `HERMES_HOME`, and `session_name` must be a plain filename. Path traversal and absolute session names are rejected.

Store non-secret allowlists and media limits in `config.yaml`, not `.env`. An `allowed_chats` entry authorizes messages from every participant in that chat; use `allowed_users` when sender-level restriction is required. The adapter applies this deny-by-default admission policy before gateway dispatch and declares the result as its own local access policy, so an admitted user-account message does not enter Hermes' bot-oriented pairing flow. Unknown senders are still dropped at Telethon intake.

Telegram userbot always uses the human-account system-message policy. Recognized Hermes gateway commands such as `/reset`, `/new`, `/approve`, `/status`, and `/sethome` are silently ignored on this transport; even during an active session they do not cancel the running task, replace its guard, or drain pending work. Unknown slash-prefixed text remains ordinary conversation input. Internal agent failures are logged server-side without sending the generic `Sorry, I encountered an unexpected error` reply. Dangerous-command approvals fail closed without buttons or text prompts. Ordinary final model replies are unaffected. Perform operator actions through the profile CLI/terminal or a separate trusted bot channel, not through the user-account chat.

Media download is disabled by default and must be enabled explicitly after accepting the storage risk. When enabled, files with an unknown metadata size or a size above `max_media_bytes` are rejected before transfer. Downloads are serialized and streamed into profile-local files; actual bytes are checked before every write, while byte and file-count quotas are rechecked before retaining the file.

## First authorization

Run the first login in the foreground so Telegram can request a login code and optional 2FA password:

```bash
cd /root/.hermes/hermes-agent
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway run -v --replace
```

A successful file-session bootstrap creates:

```text
/root/.hermes/profiles/telegram-userbot/telegram_userbot/main.session
```

Do not install a background service until the session exists and the allowlist is non-empty.

## Service installation

After successful foreground bootstrap:

```bash
cd /root/.hermes/hermes-agent
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway install --system --force --run-as-user root
venv/bin/python -m hermes_cli.main \
  --profile telegram-userbot \
  gateway start
```

Verify the profile-specific process and log rather than relying on a global gateway PID list:

```bash
ps -eo pid,ppid,stat,lstart,cmd \
  | grep -E '[h]ermes.*--profile telegram-userbot.*gateway'
tail -n 160 /root/.hermes/profiles/telegram-userbot/logs/gateway.log
```

## Verification

Runtime focused tests:

```bash
cd /root/.hermes/hermes-agent
scripts/run_tests.sh \
  tests/plugins/test_telegram_userbot_platform_plugin.py \
  tests/providers/test_plugin_discovery.py \
  tests/gateway/test_platform_registry.py \
  tests/gateway/test_status_command.py
```

PatchKit checks:

```bash
cd /root/hermes-patchkit
python3 -m unittest tests.test_patch_catalog
python3 scripts/verify.py --self-check
```

The release patch must apply cleanly to official `v2026.7.20`, and `git apply -R --check` must succeed after application.
