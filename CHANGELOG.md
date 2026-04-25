# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog.

## [Unreleased]

### Added
- real exported upstream-fix patches `060-codex-memory-flush-responses-contract` and `061-codex-auxiliary-tool-role-flattening`
- pinned manifest/profile entries for the exported Codex patches
- unittest regression coverage for rollback cleanup after patches add new files

### Changed
- `apply.py` now captures rollback state for exported patches, including patch-created untracked files and pre-apply dirty state when `--force` is used; forced apply now snapshots cleanup baselines after stashing dirty state so same-path untracked and ignored collisions are still recorded for rollback
- `rollback.py` now restores the backup branch, removes only PatchKit-recorded untracked files, re-applies pre-existing dirty state captured during forced apply, and deletes recorded symlinks literally instead of following them into tracked content
- README and getting-started docs now point at a real exported patch flow instead of a placeholder-only example
