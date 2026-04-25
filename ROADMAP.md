# Roadmap

## v0.1 — Public scaffold
- [x] Create repo skeleton
- [x] Publish bilingual README
- [x] Add manifest/profile model
- [x] Add placeholder scripts and CI validation

## v0.2 — Fork export
- [x] Export first real upstream-fix patches (`020`, `060`, `061`) from the Hermes delta
- [ ] Finish the remaining planned upstream-fix patch (`030`) or remove it from the manifest
- [x] Remove unsupported placeholder patch ideas from the public manifest/profile set
- [x] Record patch provenance in manifests

## v0.3 — First usable apply flow
- [x] Make `apply.py` apply exported real patches
- [x] Make `rollback.py` restore tracked state and clean untracked files created by apply
- [x] Add `update.py` to check selected patches against a temporary upstream candidate before touching live runtime
- [x] Add a small `tui.py` flow for update status/report viewing
- [ ] Expand `verify.py` with Hermes smoke checks

## v0.4 — Upstream validation
- [x] Validate exported patches against clean upstream checkout `v2026.4.23-240-ge5647d78`
- [x] Publish first compatibility/update workflow docs around `update.py`
- [ ] Add patch refresh tooling for new upstream releases
- [ ] Tag first public release

## Later
- [ ] Support multiple upstream versions with compatibility matrix
- [ ] Replace the simple terminal UI with a richer Textual UI when packaging is ready
- [ ] Add guided patch refresh tooling for conflicted patches
