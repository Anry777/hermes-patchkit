#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

from _common import (
    ManifestContext,
    PatchKitError,
    ensure_git_repo,
    git,
    is_clean_worktree,
    is_placeholder_patch,
    load_manifest,
    patch_file,
    resolve_patch_selection,
)


SAFE_STATUSES = {"applies-cleanly", "already-present"}


@dataclass
class PatchCheckResult:
    patch_id: str
    title: str
    status: str
    patch_path: Path
    detail: str = ""


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)


def infer_remote_name(upstream_ref: str) -> str | None:
    if "/" not in upstream_ref:
        return None
    remote = upstream_ref.split("/", 1)[0]
    return remote or None


def fetch_upstream(repo: Path, upstream_ref: str) -> None:
    remote = infer_remote_name(upstream_ref)
    if not remote:
        return
    result = run_git(repo, "fetch", "--quiet", remote, check=False)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or f"git fetch {remote} failed").strip()
        raise PatchKitError(message)


def clone_candidate(source_repo: Path, upstream_ref: str, tmp_root: Path) -> Path:
    candidate = tmp_root / "upstream-candidate"
    subprocess.run(["git", "clone", "--quiet", "--shared", str(source_repo), str(candidate)], text=True, capture_output=True, check=True)
    # A normal local clone fetches local branches, but not always remote-tracking
    # refs such as refs/remotes/origin/main. Copy those from the live checkout
    # after the live checkout has fetched upstream, so validation does not need
    # a second network clone of the whole Hermes repository.
    run_git(candidate, "fetch", "--quiet", str(source_repo), "+refs/remotes/*:refs/remotes/*", check=False)
    checkout = run_git(candidate, "checkout", "--detach", upstream_ref, check=False)
    if checkout.returncode != 0:
        # Local refs such as ``main`` can be present without the remote prefix.
        fallback_ref = upstream_ref.split("/", 1)[1] if "/" in upstream_ref else upstream_ref
        checkout = run_git(candidate, "checkout", "--detach", fallback_ref, check=False)
    if checkout.returncode != 0:
        message = (checkout.stderr or checkout.stdout or f"cannot checkout {upstream_ref}").strip()
        raise PatchKitError(message)
    return candidate


def git_apply_check(repo: Path, patch_path: Path, reverse: bool = False) -> tuple[bool, str]:
    args = ["apply"]
    if reverse:
        args.append("--reverse")
    args.extend(["--check", str(patch_path)])
    result = run_git(repo, *args, check=False)
    output = (result.stderr or result.stdout or "").strip()
    return result.returncode == 0, output


def classify_patch(candidate_repo: Path, patchkit_root: Path, patch: dict, allow_placeholder: bool = False) -> PatchCheckResult:
    path = patch_file(patchkit_root, patch)
    patch_id = str(patch["id"])
    title = str(patch.get("title_en") or patch.get("title_ru") or patch_id)

    if is_placeholder_patch(path):
        detail = "placeholder patch file"
        return PatchCheckResult(patch_id, title, "placeholder", path, detail)

    applies, apply_detail = git_apply_check(candidate_repo, path)
    if applies:
        return PatchCheckResult(patch_id, title, "applies-cleanly", path)

    reverse_applies, reverse_detail = git_apply_check(candidate_repo, path, reverse=True)
    if reverse_applies:
        return PatchCheckResult(patch_id, title, "already-present", path, "reverse patch applies cleanly")

    detail = apply_detail or reverse_detail or "git apply --check failed"
    return PatchCheckResult(patch_id, title, "conflict", path, detail)


def selected_patch_results(
    repo: Path,
    manifest_ctx: ManifestContext,
    selected: list[dict],
    upstream_ref: str,
    fetch: bool = True,
    allow_placeholder: bool = False,
) -> tuple[list[PatchCheckResult], str, str, str]:
    if fetch:
        fetch_upstream(repo, upstream_ref)

    current_head = run_git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    current_branch = run_git(repo, "branch", "--show-current", check=False).stdout.strip() or "(detached)"
    patchkit_root = manifest_ctx.manifest_path.parent.parent

    with tempfile.TemporaryDirectory(prefix="patchkit-update-") as tmp:
        candidate = clone_candidate(repo, upstream_ref, Path(tmp))
        upstream_head = run_git(candidate, "rev-parse", "--short", "HEAD").stdout.strip()
        results = [classify_patch(candidate, patchkit_root, patch, allow_placeholder=allow_placeholder) for patch in selected]

    return results, current_branch, current_head, upstream_head


def render_summary(results: list[PatchCheckResult], repo: Path, manifest_path: Path, upstream_ref: str, current_branch: str, current_head: str, upstream_head: str, color: bool = True) -> str:
    def mark(status: str) -> str:
        if status == "applies-cleanly":
            return "✓"
        if status == "already-present":
            return "✓"
        if status == "placeholder":
            return "•"
        return "!"

    lines = [
        "Hermes PatchKit update check",
        "",
        f"Repo:      {repo}",
        f"Manifest:  {manifest_path.name}",
        f"Current:   {current_branch} @ {current_head}",
        f"Upstream:  {upstream_ref} @ {upstream_head}",
        "",
        "Patch status:",
    ]
    width = max([len(result.patch_id) for result in results] + [2])
    for result in results:
        lines.append(f"  {mark(result.status)} {result.patch_id:<{width}}  {result.status}")
        if result.detail and result.status not in SAFE_STATUSES:
            first_line = result.detail.splitlines()[0]
            lines.append(f"      {first_line}")
    unsafe = [result for result in results if result.status not in SAFE_STATUSES]
    lines.append("")
    if unsafe:
        lines.append(f"Safe to apply automatically: no ({len(unsafe)} patch(es) need attention)")
    else:
        lines.append("Safe to apply automatically: yes")
    return "\n".join(lines) + "\n"


def render_report(results: list[PatchCheckResult], repo: Path, manifest_path: Path, upstream_ref: str, current_branch: str, current_head: str, upstream_head: str) -> str:
    unsafe = [result for result in results if result.status not in SAFE_STATUSES]
    lines = [
        "# PatchKit upstream update report",
        "",
        f"Generated: {datetime.utcnow().replace(microsecond=0).isoformat()}Z",
        "",
        "## Target",
        "",
        f"- Repo: `{repo}`",
        f"- Current: `{current_branch}` @ `{current_head}`",
        f"- Upstream: `{upstream_ref}` @ `{upstream_head}`",
        f"- Manifest: `{manifest_path}`",
        "",
        "## Patch status",
        "",
        "| Patch | Status | Detail |",
        "|---|---|---|",
    ]
    for result in results:
        detail = result.detail.replace("|", "\\|").splitlines()[0] if result.detail else ""
        lines.append(f"| `{result.patch_id}` | `{result.status}` | {detail} |")
    lines.extend(["", "## Recommendation", ""])
    if unsafe:
        lines.append("Do not update the live Hermes checkout automatically yet.")
        lines.append("")
        lines.append("Patches needing attention:")
        for result in unsafe:
            lines.append(f"- `{result.patch_id}`: `{result.status}`")
    else:
        lines.append("The selected patch set is structurally safe to apply to this upstream candidate.")
        lines.append("Create a backup branch, merge upstream, then run focused tests before committing runtime state.")
    lines.append("")
    return "\n".join(lines)


def write_report(report_dir: Path, report_text: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / ("update-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S") + ".md")
    path.write_text(report_text, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a PatchKit patch set still works against updated upstream Hermes.")
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
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    profile_path = Path(args.profile).expanduser().resolve() if args.profile else None

    try:
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
        summary = render_summary(results, repo, manifest_path, args.upstream, current_branch, current_head, upstream_head, color=not args.no_color)
        print(summary, end="")
        report_text = render_report(results, repo, manifest_path, args.upstream, current_branch, current_head, upstream_head)
        default_report_dir = manifest_path.parent.parent / "reports"
        report_path = write_report(Path(args.report_dir).expanduser().resolve() if args.report_dir else default_report_dir, report_text)
        print(f"Report: {report_path}")
        unsafe = [result for result in results if result.status not in SAFE_STATUSES]
        return 2 if unsafe else 0
    except (PatchKitError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
