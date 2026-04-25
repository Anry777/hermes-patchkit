from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
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


def worktree_has_changes(repo: Path, include_ignored: bool = False) -> bool:
    args = ['status', '--porcelain']
    if include_ignored:
        args.append('--ignored=matching')
    result = git(repo, *args, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def is_clean_worktree(repo: Path) -> bool:
    return not worktree_has_changes(repo)


def git_dir(repo: Path) -> Path:
    result = git(repo, 'rev-parse', '--git-dir')
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = (repo / path).resolve()
    return path


def patchkit_state_path(repo: Path, backup_name: str) -> Path:
    state_dir = git_dir(repo) / 'patchkit'
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f'{backup_name}.json'


def write_backup_state(repo: Path, backup_name: str, state: dict) -> Path:
    path = patchkit_state_path(repo, backup_name)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return path


def read_backup_state(repo: Path, backup_name: str) -> dict | None:
    path = patchkit_state_path(repo, backup_name)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise PatchKitError(f'Invalid rollback state file: {path}')
    return data


def delete_backup_state(repo: Path, backup_name: str) -> None:
    path = patchkit_state_path(repo, backup_name)
    if path.exists():
        path.unlink()


_FORCE_STASH_EXCLUDE_PATHS = (
    ':(exclude)venv',
    ':(exclude)venv/**',
    ':(exclude).venv',
    ':(exclude).venv/**',
)


def stash_dirty_state(repo: Path, backup_name: str) -> str | None:
    """Capture user dirty state for forced apply without hiding local envs.

    ``git stash push --all`` also removes ignored paths. In Hermes checkouts
    the runtime virtualenv often lives inside the repo as ignored ``venv/``;
    stashing it makes the active install disappear until rollback.  Keep those
    root env directories in place while still stashing tracked, untracked, and
    other ignored paths that may collide with patch-created files.
    """
    before_sha = git(repo, 'rev-parse', '-q', '--verify', 'refs/stash', check=False).stdout.strip()
    result = git(
        repo,
        'stash',
        'push',
        '--all',
        '--message',
        f'patchkit-pre-apply-{backup_name}',
        '--',
        '.',
        *_FORCE_STASH_EXCLUDE_PATHS,
        check=False,
    )
    if result.returncode != 0:
        raise PatchKitError((result.stderr or result.stdout or 'git stash failed').strip())
    stash_sha = git(repo, 'rev-parse', '-q', '--verify', 'refs/stash', check=False).stdout.strip()
    if not stash_sha or stash_sha == before_sha:
        return None
    ref_name = f'refs/patchkit/pre-apply/{backup_name}'
    git(repo, 'update-ref', ref_name, stash_sha)
    git(repo, 'stash', 'drop', 'stash@{0}')
    return ref_name


def list_untracked_files(repo: Path) -> list[str]:
    result = git(
        repo,
        'status',
        '--porcelain=v1',
        '-z',
        '--untracked-files=all',
        '--ignored=traditional',
    )
    entries = []
    for raw in result.stdout.split('\0'):
        if not raw:
            continue
        status = raw[:2]
        if status in {'??', '!!'}:
            entries.append(raw[3:])
    return sorted(entries)


def clean_untracked_paths(repo: Path, paths: Iterable[str]) -> None:
    repo_root = repo.resolve()
    current_candidates = set(list_untracked_files(repo))
    for rel_path in paths:
        if rel_path not in current_candidates:
            continue
        rel = Path(rel_path)
        if rel.is_absolute() or '..' in rel.parts:
            raise PatchKitError(f'refusing to delete non-local path: {rel_path}')
        target = repo_root / rel
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        elif target.exists() or target.is_symlink():
            target.unlink()


def drop_ref(repo: Path, ref_name: str | None) -> None:
    if ref_name:
        git(repo, 'update-ref', '-d', ref_name, check=False)


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
