# Roadmap

## v0.1 — Public scaffold
- [x] Create repo skeleton
- [x] Publish bilingual README
- [x] Add manifest/profile model
- [x] Add placeholder scripts and CI validation

## v0.2 — Fork export
- [ ] Export the first 5 logical patches from the current Hermes fork
- [ ] Replace placeholder patch files with real unified diffs
- [ ] Record patch provenance in manifests

## v0.3 — First usable apply flow
- [ ] Make `apply.py` fully apply real patches
- [ ] Make `rollback.py` restore the target repo safely
- [ ] Expand `verify.py` with Hermes smoke checks

## v0.4 — Upstream validation
- [ ] Validate against clean upstream checkout `v2026.4.23`
- [ ] Publish compatibility notes
- [ ] Tag first public release

## Later
- [ ] Support multiple upstream versions with compatibility matrix
- [ ] Add richer interactive selection flow
- [ ] Add patch refresh tooling for new upstream releases
