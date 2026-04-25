#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect a Hermes fork and prepare patch export steps.')
    parser.add_argument('--fork', required=True, help='Path to the customized Hermes fork')
    parser.add_argument('--upstream-ref', required=True, help='Upstream ref to compare against')
    parser.add_argument('--output-dir', default='patches', help='Where exported patches should go')
    args = parser.parse_args()

    fork = Path(args.fork).resolve()
    cmd = ['git', '-C', str(fork), 'log', '--oneline', f'{args.upstream_ref}..HEAD']
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    print(f'Fork: {fork}')
    print(f'Upstream ref: {args.upstream_ref}')
    print(f'Output dir: {args.output_dir}')
    print()
    print('Fork-only commits:')
    print(result.stdout.strip() or '(none)')
    print()
    print('Next step: split the delta into logical patches and replace placeholder files under patches/.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
