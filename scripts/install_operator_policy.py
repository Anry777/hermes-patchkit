#!/usr/bin/env python3
"""Install a PatchKit operator policy block into a Hermes profile prompt.

The policy block makes the running profile aware of PatchKit's source-of-truth
split: config.yaml owns non-secret behaviour/settings, .env owns secrets only,
and provider credentials are root-global auth state.

Dry-run is the default. Use --write to update config.yaml and --backup to keep a
timestamped copy before writing.
"""
from __future__ import annotations

import argparse
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

BEGIN_MARKER = "[PATCHKIT_OPERATOR_POLICY_BEGIN]"
END_MARKER = "[PATCHKIT_OPERATOR_POLICY_END]"
BLOCK_RE = re.compile(
    rf"\n*{re.escape(BEGIN_MARKER)}\n.*?\n{re.escape(END_MARKER)}\n*",
    re.DOTALL,
)
SECRET_KEY_RE = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASS|API_KEY|ACCESS_KEY|PRIVATE_KEY|CLIENT_SECRET|AUTH_TOKEN|KEY)$|(_KEY$)",
    re.I,
)


def default_policy_path() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "office-operator-policy.md"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"config root must be a mapping: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = path.with_name(path.name + f".bak_install_operator_policy_{stamp}")
    target.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return target


def build_block(policy_text: str) -> str:
    policy_text = policy_text.strip()
    if not policy_text:
        raise ValueError("policy text is empty")
    return f"{BEGIN_MARKER}\n{policy_text}\n{END_MARKER}"


def install_block(existing_prompt: Any, policy_text: str) -> tuple[str, str]:
    prompt = "" if existing_prompt is None else str(existing_prompt).strip()
    block = build_block(policy_text)
    if BLOCK_RE.search(prompt):
        updated = BLOCK_RE.sub(f"\n\n{block}\n", prompt).strip()
        return updated, "updated"
    if prompt:
        return f"{prompt}\n\n{block}", "inserted"
    return block, "inserted"


def remove_block(existing_prompt: Any) -> tuple[str, str]:
    prompt = "" if existing_prompt is None else str(existing_prompt)
    if not BLOCK_RE.search(prompt):
        return prompt.strip(), "absent"
    updated = BLOCK_RE.sub("\n", prompt).strip()
    return updated, "removed"


def contains_secret_like_policy_line(policy_text: str) -> bool:
    """Guard against accidentally templating live credentials into policy text."""
    for raw in policy_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if SECRET_KEY_RE.search(key.strip()) and value.strip() and "REDACT" not in value.upper():
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Install PatchKit operator policy into Hermes profile agent.system_prompt.")
    parser.add_argument("--home", default="~/.hermes", help="Hermes profile home, default: ~/.hermes")
    parser.add_argument("--config", help="config.yaml path, default: <home>/config.yaml")
    parser.add_argument("--policy", default=str(default_policy_path()), help="Policy text file to install")
    parser.add_argument("--write", action="store_true", help="Write config.yaml. Without this, only print the planned action.")
    parser.add_argument("--backup", action="store_true", help="Create config.yaml backup before writing")
    parser.add_argument("--remove", action="store_true", help="Remove the managed policy block instead of installing/updating it")
    args = parser.parse_args()

    home = Path(args.home).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve() if args.config else home / "config.yaml"
    policy_path = Path(args.policy).expanduser().resolve()

    try:
        config = load_yaml(config_path)
        policy_text = policy_path.read_text(encoding="utf-8", errors="ignore")
        if not args.remove and contains_secret_like_policy_line(policy_text):
            raise ValueError("policy file contains secret-like KEY=value lines; redact or remove them before installing")

        agent_cfg = config.get("agent")
        if agent_cfg is None:
            agent_cfg = {}
            config["agent"] = agent_cfg
        if not isinstance(agent_cfg, dict):
            raise ValueError("config key 'agent' must be a mapping before policy can be installed")

        old_prompt = agent_cfg.get("system_prompt", "")
        if args.remove:
            new_prompt, action = remove_block(old_prompt)
        else:
            new_prompt, action = install_block(old_prompt, policy_text)
        changed = new_prompt != ("" if old_prompt is None else str(old_prompt).strip())
        agent_cfg["system_prompt"] = new_prompt

        print("Hermes operator policy installer")
        print(f"Home:       {home}")
        print(f"Config:     {config_path}")
        print(f"Policy:     {policy_path}")
        print(f"Action:     {action}")
        print(f"Changed:    {'yes' if changed else 'no'}")
        print(f"Prompt len: {len(str(old_prompt or ''))} -> {len(new_prompt)}")

        if not args.write:
            print("Dry run complete. Add --write to update config.yaml.")
            return 0

        backup_path = backup(config_path) if args.backup else None
        dump_yaml(config_path, config)
        if backup_path:
            print(f"Backed up config: {backup_path}")
        print("Policy install complete.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
