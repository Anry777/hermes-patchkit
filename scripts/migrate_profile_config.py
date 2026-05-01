#!/usr/bin/env python3
"""Run the target Hermes checkout's config schema migration for one profile.

PatchKit owns the update lifecycle, but Hermes owns its own config schema.  This
helper bridges the two safely: it delegates migration to the target runtime's
``hermes_cli.config.migrate_config()``, wraps it with dry-run/backup/diff, and
keeps secrets out of terminal output.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable


SECRET_LINE_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|client[_-]?secret|access[_-]?token|refresh[_-]?token)"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)^([+\- ]?\s*[^#\n:=]*(?:api[_-]?key|token|secret|password|client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*).*$"
)


class MigrationError(RuntimeError):
    pass


def resolve_python(repo: Path) -> str:
    for candidate in (repo / "venv" / "bin" / "python", repo / ".venv" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = path.with_name(path.name + f".bak_migrate_profile_{stamp}")
    target.write_bytes(path.read_bytes())
    return target


def copy_relevant_home(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("config.yaml", ".env"):
        source = src / name
        if source.exists():
            shutil.copy2(source, dst / name)

    # Hermes migration v20→v21 inspects user plugin manifests.  Copy only the
    # lightweight metadata it needs; do not copy sessions/logs/auth stores into
    # dry-run scratch space.
    plugins = src / "plugins"
    if plugins.is_dir():
        for manifest in list(plugins.glob("*/plugin.yaml")) + list(plugins.glob("*/plugin.yml")):
            rel = manifest.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest, target)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def redact_line(line: str) -> str:
    if not SECRET_LINE_RE.search(line):
        return line
    replaced = SECRET_ASSIGNMENT_RE.sub(r"\1<REDACTED>", line.rstrip("\n"))
    if replaced != line.rstrip("\n"):
        return replaced + ("\n" if line.endswith("\n") else "")
    # If a secret-shaped line does not look like key=value/key: value, do not
    # risk printing its content as diff context.
    prefix = line[:1] if line[:1] in {"+", "-", " "} else ""
    return f"{prefix}<REDACTED secret-shaped line>" + ("\n" if line.endswith("\n") else "")


def redacted_unified_diff(before: str, after: str, *, fromfile: str, tofile: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
    )
    return "".join(redact_line(line) for line in lines)


def run_target_migration(repo: Path, home: Path, python_bin: str) -> dict:
    config_module = repo / "hermes_cli" / "config.py"
    if not config_module.exists():
        raise MigrationError(f"Target repo does not look like Hermes checkout: missing {config_module}")

    code = r'''
import json
import os
from pathlib import Path
import sys

repo = Path(os.environ["PATCHKIT_HERMES_REPO"])
home = Path(os.environ["HERMES_HOME"])
sys.path.insert(0, str(repo))

from hermes_cli.config import check_config_version, migrate_config

before = check_config_version()
result = migrate_config(interactive=False, quiet=True)
after = check_config_version()
print(json.dumps({"before": before, "after": after, "result": result}, sort_keys=True))
'''
    env = os.environ.copy()
    env["PATCHKIT_HERMES_REPO"] = str(repo)
    env["HERMES_HOME"] = str(home)
    env.pop("HERMES_PROFILE", None)
    env["PYTHONPATH"] = str(repo) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    proc = subprocess.run(
        [python_bin, "-c", code],
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        stderr = "\n".join(redact_line(line) for line in proc.stderr.splitlines())
        stdout = "\n".join(redact_line(line) for line in proc.stdout.splitlines())
        raise MigrationError((stderr or stdout or f"migration subprocess failed with code {proc.returncode}").strip())

    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise MigrationError(f"Could not parse migration result: {proc.stdout!r}") from exc


def migration_diffs(before_home: Path, after_home: Path) -> list[str]:
    chunks: list[str] = []
    for name in ("config.yaml", ".env"):
        before = read_text(before_home / name)
        after = read_text(after_home / name)
        if before == after:
            continue
        diff = redacted_unified_diff(before, after, fromfile=f"before/{name}", tofile=f"after/{name}")
        if diff:
            chunks.append(diff)
    return chunks


def print_summary(home: Path, migration: dict, diffs: Iterable[str], *, dry_run: bool) -> None:
    before = migration.get("before", [None, None])
    after = migration.get("after", [None, None])
    print("Hermes profile config migration")
    print(f"Home: {home}")
    print(f"Config version: {before[0]} → {after[0]} (latest {after[1]})")
    result = migration.get("result") or {}
    added = result.get("config_added") or []
    warnings = result.get("warnings") or []
    if added:
        print("Config additions/migrations:")
        for item in added:
            print(f"  - {item}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")

    diff_list = list(diffs)
    if diff_list:
        print("Diff:")
        for diff in diff_list:
            print(diff, end="" if diff.endswith("\n") else "\n")
    else:
        print("No config/env file changes.")

    if dry_run:
        print("Dry run complete. Add --write to update the profile config.")
    else:
        print("Migration complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a Hermes profile config using the target Hermes checkout.")
    parser.add_argument("--repo", required=True, help="Target Hermes checkout whose hermes_cli.config owns the schema")
    parser.add_argument("--home", required=True, help="Hermes profile home containing config.yaml")
    parser.add_argument("--write", action="store_true", help="Write migration to the real profile. Default is dry-run.")
    parser.add_argument("--python", help="Python interpreter to run target Hermes migration. Default: repo venv/.venv, then current Python")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    home = Path(args.home).expanduser().resolve()
    config_path = home / "config.yaml"
    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}")
        return 1

    python_bin = args.python or resolve_python(repo)

    try:
        if args.write:
            config_backup = backup(config_path)
            env_backup = backup(home / ".env")
            before_tmp = None
            with tempfile.TemporaryDirectory() as tmp:
                before_tmp = Path(tmp) / "before"
                copy_relevant_home(home, before_tmp)
                migration = run_target_migration(repo, home, python_bin)
                diffs = migration_diffs(before_tmp, home)
            print_summary(home, migration, diffs, dry_run=False)
            if config_backup:
                print(f"Backed up config: {config_backup}")
            if env_backup:
                print(f"Backed up env: {env_backup}")
        else:
            with tempfile.TemporaryDirectory() as tmp:
                scratch_home = Path(tmp) / "home"
                copy_relevant_home(home, scratch_home)
                migration = run_target_migration(repo, scratch_home, python_bin)
                diffs = migration_diffs(home, scratch_home)
                print_summary(home, migration, diffs, dry_run=True)
        return 0
    except MigrationError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
