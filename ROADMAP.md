# Roadmap

## v0.1 — Public scaffold
- [x] Create repo skeleton
- [x] Publish bilingual README
- [x] Add manifest/profile model
- [x] Add placeholder scripts and CI validation

## v0.2 — Fork export
- [x] Export first real upstream-fix patches (`020`, `060`, `061`) from the Hermes delta
- [ ] Export the remaining logical patches from the current Hermes fork
- [ ] Replace more placeholder patch files with real unified diffs
- [x] Record patch provenance in manifests

## v0.3 — First usable apply flow
- [x] Make `apply.py` apply exported real patches
- [x] Make `rollback.py` restore tracked state and clean untracked files created by apply
- [ ] Expand `verify.py` with Hermes smoke checks

## v0.4 — Upstream validation
- [x] Validate exported patches against clean upstream checkout `v2026.4.23-240-ge5647d78`
- [ ] Publish compatibility notes
- [ ] Tag first public release

## Later
- [ ] Support multiple upstream versions with compatibility matrix
- [ ] Add richer interactive selection flow
- [ ] Add patch refresh tooling for new upstream releases
