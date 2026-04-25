from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys
from typing import Iterable


class PatchKitError(RuntimeError):
    pass


@dataclass
class ManifestContext:
    manifest_path: Path
    manifest: dict
    patch_map: dict[str, dict]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise PatchKitError(f"File not found: {path}")
    text = path.read_text(encoding='utf-8')
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PatchKitError(
            f"{path} is not valid JSON-formatted YAML. "
            "This scaffold currently uses JSON-compatible YAML files to avoid external parser dependencies."
        ) from exc
    if not isinstance(data, dict):
        raise PatchKitError(f"Expected mapping in {path}")
    return data


def load_manifest(path: Path) -> ManifestContext:
    manifest = load_yaml(path)
    patches = manifest.get('patches') or []
    if not isinstance(patches, list):
        raise PatchKitError(f"Manifest patches must be a list: {path}")
    patch_map = {}
    for patch in patches:
        if not isinstance(patch, dict):
            raise PatchKitError(f"Invalid patch entry in {path}: {patch!r}")
        patch_id = patch.get('id')
        if not patch_id:
            raise PatchKitError(f"Manifest patch missing id in {path}")
        patch_map[patch_id] = patch
    return ManifestContext(manifest_path=path, manifest=manifest, patch_map=patch_map)


def load_profile(path: Path) -> list[str]:
    data = load_yaml(path)
    patches = data.get('patches') or []
    if not isinstance(patches, list):
        raise PatchKitError(f"Profile patches must be a list: {path}")
    return [str(item) for item in patches]


def ensure_git_repo(repo: Path) -> None:
    if not (repo / '.git').exists():
        raise PatchKitError(f"Not a git repository: {repo}")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(repo), *args], check=check, text=True, capture_output=True)


def is_clean_worktree(repo: Path) -> bool:
    result = git(repo, 'status', '--porcelain', check=False)
    return result.returncode == 0 and not result.stdout.strip()


def resolve_patch_selection(manifest_ctx: ManifestContext, profile_path: Path | None, explicit_patches: str | None) -> list[dict]:
    selected_ids: list[str] = []
    if explicit_patches:
        selected_ids.extend([item.strip() for item in explicit_patches.split(',') if item.strip()])
    elif profile_path:
        selected_ids.extend(load_profile(profile_path))
    else:
        selected_ids.extend([patch_id for patch_id, patch in manifest_ctx.patch_map.items() if patch.get('default')])

    missing = [patch_id for patch_id in selected_ids if patch_id not in manifest_ctx.patch_map]
    if missing:
        raise PatchKitError(f"Unknown patch ids: {', '.join(missing)}")

    return [manifest_ctx.patch_map[patch_id] for patch_id in selected_ids]


def patch_file(repo_root: Path, patch_entry: dict) -> Path:
    return repo_root / patch_entry['file']


def is_placeholder_patch(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding='utf-8', errors='replace')
    return 'PLACEHOLDER PATCH' in text or 'Real unified diff will be exported' in text


def print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)
