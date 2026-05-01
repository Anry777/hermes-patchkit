#!/usr/bin/env python3
"""Post-update profile config hygiene for Hermes PatchKit.

This helper is intentionally outside Hermes patches: it tidies a local Hermes
profile after an upstream update/patch apply.

Policy:
- config.yaml owns non-secret behaviour/settings.
- .env owns secrets/tokens only.
- env-only non-secret variables are not silently kept as active settings; they
  are commented out and reported unless --keep-env-only is used.
- config.yaml.example is generated from live config.yaml with secrets redacted
  and empty/default noise pruned.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import re
import sys
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - exercised only without PyYAML
    print(f"ERROR: PyYAML is required: {exc}")
    raise SystemExit(1)

SECRET_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASS|API_KEY|ACCESS_KEY|PRIVATE_KEY|CLIENT_SECRET|AUTH_TOKEN|KEY)$|(_KEY$)", re.I)
NON_SECRET_HINT_RE = re.compile(r"(URL|HOST|PORT|TIMEOUT|INTERVAL|ENABLED|DEBUG|MODE|TRANSPORT|CHANNEL|CHAT|ROOM|USER|ID|NAME|PROXY|PROXIES|REGION|PROFILE|IMAGE|MODEL|BASE_URL|BUDGET)$", re.I)

# Platform/integration order for human-readable .env files.
PLATFORM_PREFIXES: list[tuple[str, tuple[str, ...]]] = [
    ("Telegram gateway", ("TELEGRAM_",)),
    ("Discord gateway", ("DISCORD_",)),
    ("Slack gateway", ("SLACK_",)),
    ("MAX messenger gateway", ("MAX_",)),
    ("Home Assistant platform/tools", ("HASS_", "HOMEASSISTANT_")),
    ("Hindsight memory backend", ("HINDSIGHT_",)),
    ("Browser / Browserbase tools", ("BROWSER_", "BROWSERBASE_", "CAMOFOX_")),
    ("Terminal backend/tools", ("TERMINAL_", "SUDO_PASSWORD")),
    ("Model/provider credentials", (
        "OPENROUTER_", "ANTHROPIC_", "OPENAI_", "GOOGLE_", "GEMINI_", "XAI_", "DEEPSEEK_",
        "DASHSCOPE_", "MINIMAX_", "MISTRAL_", "GROQ_", "HF_", "GITHUB_", "COPILOT_",
    )),
    ("Tool credentials", ("FAL_", "EXA_", "TAVILY_", "FIRECRAWL_", "NOTION_", "LINEAR_", "AIRTABLE_", "TENOR_")),
    ("Tool debug switches", ("WEB_TOOLS_", "VISION_TOOLS_", "MOA_TOOLS_", "IMAGE_TOOLS_")),
]

CONFIG_BACKED_ENV: dict[str, str] = {
    "HERMES_MAX_ITERATIONS": "config.yaml: agent.max_turns",
    "CONTEXT_COMPRESSION_ENABLED": "config.yaml: compression.enabled",
    "CONTEXT_COMPRESSION_THRESHOLD": "config.yaml: compression.threshold",
    "TERMINAL_TIMEOUT": "config.yaml: terminal.timeout",
    "TERMINAL_LIFETIME_SECONDS": "config.yaml: terminal.lifetime_seconds",
    "TERMINAL_CWD": "config.yaml: terminal.cwd",
    "BROWSER_INACTIVITY_TIMEOUT": "config.yaml: browser.inactivity_timeout",
}

# Some Hermes integrations still read these non-secret values directly from env.
# Keep them active only with --keep-env-only; otherwise comment them and report.
KNOWN_ENV_ONLY_NON_SECRET = {
    "HASS_URL": "Home Assistant URL is still read by Hermes HA adapter/tooling from env in current upstream.",
    "BROWSER_SESSION_TIMEOUT": "Browser session timeout is still env-only in current browser tooling.",
    "BROWSERBASE_PROXIES": "Browserbase proxy toggle is still env-only in current browser tooling.",
    "BROWSERBASE_ADVANCED_STEALTH": "Browserbase stealth toggle is still env-only in current browser tooling.",
    "TERMINAL_MODAL_IMAGE": "Modal terminal image is historically read from env in parts of terminal tooling.",
    "WEB_TOOLS_DEBUG": "Debug switch; keep only while actively debugging.",
    "VISION_TOOLS_DEBUG": "Debug switch; keep only while actively debugging.",
    "MOA_TOOLS_DEBUG": "Debug switch; keep only while actively debugging.",
    "IMAGE_TOOLS_DEBUG": "Debug switch; keep only while actively debugging.",
    "HINDSIGHT_TIMEOUT": "Hindsight runtime timeout is read by the Hindsight integration wrapper.",
    "HINDSIGHT_IDLE_TIMEOUT": "Hindsight runtime idle timeout is read by the Hindsight integration wrapper.",
    "HINDSIGHT_MODE": "Hindsight mode is integration-specific env until profile config support exists.",
    "HINDSIGHT_BANK_ID": "Hindsight bank id is integration-specific env until profile config support exists.",
    "HINDSIGHT_BUDGET": "Hindsight budget is integration-specific env until profile config support exists.",
}

SENSITIVE_CONFIG_KEYS = {
    "api_key", "token", "secret", "password", "client_secret", "access_token", "refresh_token", "private_key",
}

PRUNE_CONFIG_KEYS = {
    # local/runtime state that should not go to an example file
    "last_update_check", "session_id", "active_session", "recent_sessions",
}


def parse_env(path: Path) -> OrderedDict[str, str]:
    values: OrderedDict[str, str] = OrderedDict()
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def is_secret_key(key: str) -> bool:
    # Treat credential-shaped names as secrets. Non-secret exceptions are handled
    # by the config-backed/env-only maps before users rely on generated output.
    return bool(SECRET_RE.search(key))


def platform_for_key(key: str) -> str:
    for title, prefixes in PLATFORM_PREFIXES:
        for prefix in prefixes:
            if key == prefix or key.startswith(prefix):
                return title
    return "Other integration variables"


def redact_config(obj: Any, key_path: tuple[str, ...] = ()) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            skey = str(key)
            if skey in PRUNE_CONFIG_KEYS:
                continue
            low = skey.lower()
            if low in SENSITIVE_CONFIG_KEYS or any(marker in low for marker in ("api_key", "token", "secret", "password")):
                if value in (None, "", [], {}):
                    continue
                out[skey] = "<REDACTED>"
            else:
                cleaned = redact_config(value, key_path + (skey,))
                if cleaned in (None, "", [], {}):
                    continue
                out[skey] = cleaned
        return out
    if isinstance(obj, list):
        cleaned_items = [redact_config(item, key_path) for item in obj]
        return [item for item in cleaned_items if item not in (None, "", [], {})]
    return obj


def write_yaml(path: Path, data: Any) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def render_env(values: OrderedDict[str, str], keep_env_only: bool) -> tuple[str, list[str], list[str]]:
    grouped: dict[str, list[tuple[str, str]]] = OrderedDict()
    for key, value in values.items():
        grouped.setdefault(platform_for_key(key), []).append((key, value))

    lines: list[str] = [
        "# Hermes profile environment",
        "# Source of truth:",
        "# - config.yaml: non-secret behaviour/settings.",
        "# - .env: secrets/tokens only.",
        "# Generated/cleaned by hermes-patchkit scripts/clean_profile_config.py.",
        "",
    ]
    active: list[str] = []
    commented: list[str] = []

    for title in [t for t, _ in PLATFORM_PREFIXES] + ["Other integration variables"]:
        entries = grouped.get(title, [])
        if not entries:
            continue
        emitted_title = False
        for key, value in entries:
            reason = CONFIG_BACKED_ENV.get(key)
            secret = is_secret_key(key)
            env_only_reason = KNOWN_ENV_ONLY_NON_SECRET.get(key)
            should_keep = secret or (keep_env_only and env_only_reason and key not in CONFIG_BACKED_ENV)
            if not emitted_title:
                lines.append(f"# --- {title} ---")
                emitted_title = True
            if should_keep:
                lines.append(f"{key}={value}")
                active.append(key)
            else:
                if reason:
                    lines.append(f"# {key}={value}")
                    lines.append(f"#   disabled: use {reason} instead")
                elif env_only_reason:
                    lines.append(f"# {key}={value}")
                    lines.append(f"#   disabled by strict env policy: {env_only_reason}")
                    lines.append("#   If this integration breaks before Hermes gains config.yaml support, rerun with --keep-env-only.")
                else:
                    lines.append(f"# {key}={value}")
                    lines.append("#   disabled: non-secret env setting; move to config.yaml or document as env-only exception")
                commented.append(key)
        if emitted_title:
            lines.append("")

    return "\n".join(lines).rstrip() + "\n", active, commented


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = path.with_name(path.name + f".bak_clean_profile_{stamp}")
    target.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean Hermes profile config/env after PatchKit update.")
    parser.add_argument("--home", default="~/.hermes", help="Hermes profile home, default: ~/.hermes")
    parser.add_argument("--config", help="config.yaml path, default: <home>/config.yaml")
    parser.add_argument("--env", help=".env path, default: <home>/.env")
    parser.add_argument("--write", action="store_true", help="Write files. Without this, only print planned changes.")
    parser.add_argument("--keep-env-only", action="store_true", help="Keep known env-only non-secret variables active until Hermes supports config.yaml for them.")
    args = parser.parse_args()

    home = Path(args.home).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve() if args.config else home / "config.yaml"
    env_path = Path(args.env).expanduser().resolve() if args.env else home / ".env"
    example_path = config_path.with_name(config_path.name + ".example")

    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}")
        return 1

    config = yaml.safe_load(config_path.read_text(encoding="utf-8", errors="ignore")) or {}
    example_config = redact_config(deepcopy(config))
    env_values = parse_env(env_path)
    env_text, active_env, commented_env = render_env(env_values, keep_env_only=args.keep_env_only)

    print("Hermes profile config cleanup")
    print(f"Home:    {home}")
    print(f"Config:  {config_path}")
    print(f"Example: {example_path}")
    print(f"Env:     {env_path}")
    print(f"Active .env keys after cleanup: {', '.join(active_env) if active_env else '(none)'}")
    print(f"Commented/non-secret .env keys: {', '.join(commented_env) if commented_env else '(none)'}")

    if not args.write:
        print("Dry run complete. Add --write to update config.yaml.example and .env.")
        return 0

    config_backup = backup(example_path)
    env_backup = backup(env_path)
    write_yaml(example_path, example_config)
    env_path.write_text(env_text, encoding="utf-8")
    if config_backup:
        print(f"Backed up old example: {config_backup}")
    if env_backup:
        print(f"Backed up old env: {env_backup}")
    print("Cleanup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
