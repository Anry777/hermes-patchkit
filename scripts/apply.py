#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import subprocess

from _common import PatchKitError, ensure_git_repo, git, is_clean_worktree, is_placeholder_patch, load_manifest, patch_file, resolve_patch_selection


def main() -> int:
    parser = argparse.ArgumentParser(description='Apply a PatchKit profile or explicit patch list to a Hermes checkout.')
    parser.add_argument('--repo', required=True, help='Path to target Hermes git checkout')
    parser.add_argument('--manifest', required=True, help='Manifest path')
    parser.add_argument('--profile', help='Profile path')
    parser.add_argument('--patch', help='Comma-separated patch ids')
    parser.add_argument('--dry-run', action='store_true', help='Preview the resolved patch set without applying')
    parser.add_argument('--yes', action='store_true', help='Skip interactive confirmation')
    parser.add_argument('--force', action='store_true', help='Allow applying on a dirty repo')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    manifest_path = Path(args.manifest).resolve()
    profile_path = Path(args.profile).resolve() if args.profile else None

    try:
        ensure_git_repo(repo)
        manifest_ctx = load_manifest(manifest_path)
        selected = resolve_patch_selection(manifest_ctx, profile_path, args.patch)

        if not is_clean_worktree(repo) and not args.force and not args.dry_run:
            raise PatchKitError('Target repo is dirty. Commit, stash, or rerun with --force.')

        print('Hermes PatchKit')
        print(f"Repo: {repo}")
        print(f"Manifest: {manifest_path.name}")
        print('Selected patches:')
        for patch in selected:
            print(f"  - {patch['id']} ({patch['file']})")

        if args.dry_run:
            print('Dry run complete. No changes applied.')
            return 0

        placeholders = [patch for patch in selected if is_placeholder_patch(patch_file(manifest_path.parent.parent, patch))]
        if placeholders:
            ids = ', '.join(patch['id'] for patch in placeholders)
            raise PatchKitError(f'Cannot apply placeholder patches yet: {ids}')

        if not args.yes:
            answer = input('Apply selected patches? [y/N] ').strip().lower()
            if answer not in {'y', 'yes'}:
                print('Aborted.')
                return 1

        backup_name = 'patchkit-backup-' + datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        git(repo, 'branch', backup_name)
        print(f'Created backup branch: {backup_name}')

        for patch in selected:
            patch_path = patch_file(manifest_path.parent.parent, patch)
            subprocess.run(['git', '-C', str(repo), 'apply', '--check', str(patch_path)], check=True)
            subprocess.run(['git', '-C', str(repo), 'apply', str(patch_path)], check=True)
            print(f"Applied: {patch['id']}")

        print('Apply complete.')
        print(f'Rollback hint: python scripts/rollback.py --repo {repo} --backup {backup_name} --yes')
        return 0
    except (PatchKitError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
