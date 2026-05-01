#!/usr/bin/env python3
"""Pin selected runtime dependencies in a target Hermes checkout.

PatchKit normally changes source files, not virtualenv contents.  A few upstream
runtime issues are dependency-version compatibility problems, though.  This
helper keeps those operational pins explicit, repeatable, and opt-in instead of
turning them into undocumented one-off shell commands.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


DEFAULT_PINS = ("setuptools<80",)


class PinError(RuntimeError):
    pass


def resolve_python(repo: Path) -> Path:
    for candidate in (repo / "venv" / "bin" / "python", repo / ".venv" / "bin" / "python"):
        if candidate.exists():
            return candidate
    raise PinError(f"Could not find runtime Python under {repo}/venv or {repo}/.venv")


def resolve_uv(explicit_uv: str | None = None) -> str:
    if explicit_uv:
        path = Path(explicit_uv).expanduser()
        if not path.exists():
            raise PinError(f"uv not found: {path}")
        return str(path)
    found = shutil.which("uv")
    if not found:
        raise PinError("uv is required because Hermes runtime venvs may not have pip. Install uv or pass --uv /path/to/uv.")
    return found


def pin_dependencies(repo: Path, packages: list[str], *, uv: str, write: bool) -> None:
    python_bin = resolve_python(repo)
    print("Hermes runtime dependency pins")
    print(f"Repo: {repo}")
    print(f"Python: {python_bin}")
    print("Pins:")
    for package in packages:
        print(f"  - {package}")

    cmd = [uv, "pip", "install", "--python", str(python_bin), *packages]
    if not write:
        print("Dry run complete. Add --write to install pins with uv.")
        return

    subprocess.run(cmd, check=True)
    print("Runtime dependency pinning complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pin runtime dependencies in a Hermes checkout venv.")
    parser.add_argument("--repo", required=True, help="Target Hermes checkout containing venv/ or .venv/")
    parser.add_argument("--write", action="store_true", help="Install pins. Default is dry-run.")
    parser.add_argument("--uv", help="Path to uv executable. Default: first uv on PATH")
    parser.add_argument(
        "--package",
        action="append",
        dest="packages",
        help="Package spec to install. Can be repeated. Default: setuptools<81",
    )
    args = parser.parse_args()

    try:
        repo = Path(args.repo).expanduser().resolve()
        if not repo.exists():
            raise PinError(f"Repo not found: {repo}")
        packages = args.packages or list(DEFAULT_PINS)
        if not packages:
            raise PinError("No package pins selected")
        uv = resolve_uv(args.uv)
        pin_dependencies(repo, packages, uv=uv, write=args.write)
        return 0
    except (PinError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
