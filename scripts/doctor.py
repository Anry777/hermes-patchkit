#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _common import PatchKitError, ensure_git_repo, is_clean_worktree, load_manifest, patch_file, is_placeholder_patch, resolve_patch_selection


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect a target Hermes checkout before PatchKit apply.')
    parser.add_argument('--repo', required=True, help='Path to the target Hermes git checkout')
    parser.add_argument('--manifest', required=True, help='Manifest path')
    parser.add_argument('--profile', help='Profile path')
    parser.add_argument('--patch', help='Comma-separated patch ids')
    parser.add_argument('--allow-dirty', action='store_true', help='Do not fail on a dirty worktree')
    parser.add_argument('--allow-placeholder', action='store_true', help='Do not fail on placeholder patch files')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    manifest_path = Path(args.manifest).resolve()
    profile_path = Path(args.profile).resolve() if args.profile else None

    try:
        ensure_git_repo(repo)
        manifest_ctx = load_manifest(manifest_path)
        selected = resolve_patch_selection(manifest_ctx, profile_path, args.patch)

        print(f'Repo: {repo}')
        print(f'Manifest: {manifest_path}')
        print(f'Selected patches: {len(selected)}')

        clean = is_clean_worktree(repo)
        print(f'Worktree clean: {clean}')
        if not clean and not args.allow_dirty:
            raise PatchKitError('Target repo is dirty. Commit, stash, or rerun with --allow-dirty.')

        placeholders = []
        for patch in selected:
            path = patch_file(manifest_path.parent.parent, patch)
            exists = path.exists()
            placeholder = is_placeholder_patch(path)
            print(f"- {patch['id']}: {path} | exists={exists} | placeholder={placeholder}")
            if placeholder:
                placeholders.append(path)

        if placeholders and not args.allow_placeholder:
            raise PatchKitError('Selected patch set still contains placeholder patch files.')

        print('Doctor check passed.')
        return 0
    except PatchKitError as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
