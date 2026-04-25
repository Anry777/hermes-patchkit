#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _common import PatchKitError, ensure_git_repo, git


def main() -> int:
    parser = argparse.ArgumentParser(description='Rollback a target repo to a PatchKit backup branch.')
    parser.add_argument('--repo', required=True, help='Path to target repo')
    parser.add_argument('--backup', help='Backup branch to restore')
    parser.add_argument('--list', action='store_true', help='List available backup branches')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation')
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    try:
        ensure_git_repo(repo)
        branches = git(repo, 'for-each-ref', '--format=%(refname:short)', 'refs/heads/patchkit-backup-*').stdout.splitlines()
        if args.list or not args.backup:
            print('Available backups:')
            for branch in branches:
                print(f'  - {branch}')
            return 0 if branches else 1

        if args.backup not in branches:
            raise PatchKitError(f'Backup branch not found: {args.backup}')

        if not args.yes:
            answer = input(f'Reset {repo} to {args.backup}? [y/N] ').strip().lower()
            if answer not in {'y', 'yes'}:
                print('Aborted.')
                return 1

        git(repo, 'reset', '--hard', args.backup)
        print(f'Restored repo to {args.backup}')
        return 0
    except PatchKitError as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
