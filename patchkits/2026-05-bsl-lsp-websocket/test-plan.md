# Test plan: BSL/WebSocket LSP PatchKit unit

Patch unit: `090-lsp-configured-websocket-transport`
Base: Hermes Agent `v2026.5.16` / `0.14.0`

## Automated tests

Run from the Hermes checkout after applying the patch:

```bash
PYTHONPATH=/tmp/hermes_pytest_split_shim:${PYTHONPATH:-} scripts/run_tests.sh \
  tests/agent/lsp/test_configured_servers.py \
  tests/agent/lsp/test_websocket_transport.py -q

PYTHONPATH=/tmp/hermes_pytest_split_shim:${PYTHONPATH:-} scripts/run_tests.sh \
  tests/agent/lsp -q

PYTHONPATH=/tmp/hermes_pytest_split_shim:${PYTHONPATH:-} scripts/run_tests.sh \
  tests/agent/lsp \
  tests/tools/test_file_tools.py \
  tests/tools/test_patch_parser.py -q

venv/bin/python -m compileall -q agent/lsp tests/agent/lsp
git diff --check
```

Expected result: all tests pass; no whitespace/syntax errors.

## CLI smoke after profile config

After adding a profile-local `lsp.servers.bsl-language-server` WebSocket config:

```bash
hermes --profile 1c lsp status
hermes --profile 1c lsp list
hermes --profile 1c lsp which bsl-language-server
hermes --profile 1c lsp test bsl-language-server
# or
hermes --profile 1c lsp status --check
```

Expected for a reachable endpoint:

```text
bsl-language-server [configured] .bsl
websocket ws://.../lsp
connected
initialize: ok
capabilities received
```

Expected for invalid/missing dependency/unreachable endpoint: controlled unavailable/error status; Hermes startup and write_file/patch must not crash.

## Manual BSL diagnostic smoke

1. Work inside a git workspace.
2. Add or edit a `.bsl` file.
3. Trigger `write_file` or `patch`.
4. Check post-write diagnostics and `~/.hermes/profiles/1c/logs/agent.log` for `lsp[bsl-language-server]` entries.
