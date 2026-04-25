#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from _common import PatchKitError, ensure_git_repo, is_clean_worktree, load_manifest, resolve_patch_selection
from update import render_report, render_summary, selected_patch_results, write_report, SAFE_STATUSES


def run_check(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    profile_path = Path(args.profile).expanduser().resolve() if args.profile else None

    ensure_git_repo(repo)
    if not is_clean_worktree(repo) and not args.allow_dirty:
        raise PatchKitError("Target repo is dirty. Commit, stash, or rerun with --allow-dirty.")

    manifest_ctx = load_manifest(manifest_path)
    selected = resolve_patch_selection(manifest_ctx, profile_path, args.patch)
    results, current_branch, current_head, upstream_head = selected_patch_results(
        repo,
        manifest_ctx,
        selected,
        args.upstream,
        fetch=not args.no_fetch,
        allow_placeholder=args.allow_placeholder,
    )

    print("PatchKit TUI")
    print("============")
    print()
    print(render_summary(results, repo, manifest_path, args.upstream, current_branch, current_head, upstream_head, color=not args.no_color), end="")
    report_text = render_report(results, repo, manifest_path, args.upstream, current_branch, current_head, upstream_head)
    default_report_dir = manifest_path.parent.parent / "reports"
    report_path = write_report(Path(args.report_dir).expanduser().resolve() if args.report_dir else default_report_dir, report_text)
    print(f"Report: {report_path}")
    print()
    unsafe = [result for result in results if result.status not in SAFE_STATUSES]
    if unsafe:
        print("Next action: refresh or retire the patches marked above before applying an upstream update.")
        return 2
    print("Next action: create a backup branch, merge upstream, then run focused Hermes tests.")
    return 0


def interactive(args: argparse.Namespace) -> int:
    while True:
        print("PatchKit TUI")
        print("============")
        print(f"Repo:     {Path(args.repo).expanduser()}")
        print(f"Manifest: {Path(args.manifest).expanduser()}")
        if args.profile:
            print(f"Profile:  {Path(args.profile).expanduser()}")
        if args.patch:
            print(f"Patches:  {args.patch}")
        print()
        print("Actions:")
        print("  c  Check upstream compatibility")
        print("  q  Quit")
        choice = input("Select action [c/q]: ").strip().lower() or "c"
        print()
        if choice == "q":
            return 0
        if choice == "c":
            return run_check(args)
        print("Unknown action.")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Small terminal UI for PatchKit upstream update checks.")
    parser.add_argument("--repo", required=True, help="Path to the live Hermes git checkout")
    parser.add_argument("--manifest", required=True, help="PatchKit manifest path")
    parser.add_argument("--profile", help="PatchKit profile path")
    parser.add_argument("--patch", help="Comma-separated patch ids")
    parser.add_argument("--upstream", default="origin/main", help="Upstream ref to validate against, default: origin/main")
    parser.add_argument("--report-dir", help="Directory for markdown update reports, default: <patchkit>/reports")
    parser.add_argument("--no-fetch", action="store_true", help="Do not fetch the upstream remote before checking")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running against a dirty live checkout")
    parser.add_argument("--allow-placeholder", action="store_true", help="Report placeholders instead of failing selection")
    parser.add_argument("--no-color", action="store_true", help="Reserved for stable output in tests")
    parser.add_argument("--once", action="store_true", help="Render one dashboard/check and exit without prompting")
    args = parser.parse_args()

    try:
        if args.once:
            return run_check(args)
        return interactive(args)
    except (PatchKitError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
