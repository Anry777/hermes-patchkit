#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import py_compile

from _common import PatchKitError, load_manifest, load_profile


def verify_self(repo_root: Path) -> None:
    required = [
        repo_root / 'README.md',
        repo_root / 'README.ru.md',
        repo_root / 'manifests/upstream-v2026.4.23.yaml',
        repo_root / 'manifests/upstream-v2026.4.30.yaml',
        repo_root / 'profiles/minimal.yaml',
        repo_root / 'profiles/v2026.4.30-upstream-fixes.yaml',
        repo_root / 'profiles/v2026.4.30-personal.yaml',
        repo_root / 'profiles/v2026.4.30-provider-proxy.yaml',
        repo_root / 'profiles/v2026.4.30-grok2api-sidecar.yaml',
        repo_root / 'scripts/apply.py',
        repo_root / 'scripts/doctor.py',
    ]
    missing = [str(path.relative_to(repo_root)) for path in required if not path.exists()]
    if missing:
        raise PatchKitError(f'Missing required files: {", ".join(missing)}')

    load_manifest(repo_root / 'manifests/upstream-v2026.4.23.yaml')
    load_manifest(repo_root / 'manifests/upstream-v2026.4.30.yaml')
    load_profile(repo_root / 'profiles/minimal.yaml')
    load_profile(repo_root / 'profiles/personal.yaml')
    load_profile(repo_root / 'profiles/full.yaml')
    load_profile(repo_root / 'profiles/v2026.4.30-upstream-fixes.yaml')
    load_profile(repo_root / 'profiles/v2026.4.30-personal.yaml')
    load_profile(repo_root / 'profiles/v2026.4.30-provider-proxy.yaml')
    load_profile(repo_root / 'profiles/v2026.4.30-grok2api-sidecar.yaml')

    for script in (repo_root / 'scripts').glob('*.py'):
        py_compile.compile(str(script), doraise=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify PatchKit scaffold or a target workflow setup.')
    parser.add_argument('--self-check', action='store_true', help='Validate the PatchKit repository itself')
    args = parser.parse_args()

    try:
        repo_root = Path(__file__).resolve().parent.parent
        if args.self_check:
            verify_self(repo_root)
            print('Self-check passed.')
            return 0
        raise PatchKitError('No verification mode selected. Try --self-check.')
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
