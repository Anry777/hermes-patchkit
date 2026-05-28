# BSL Language Server over WebSocket for Hermes LSP

PatchKit unit: `090-lsp-configured-websocket-transport`
Base: Hermes Agent `v2026.5.16` / `0.14.0`

## Goal

Add reusable support for externally managed LSP servers exposed over WebSocket, so BSL/1C files can be served by BSL Language Server without profile-specific bridges or direct edits to `agent/lsp/servers.py` for every new language.

## What changes

Core files touched by the patch:

- `agent/lsp/client.py` — `LSPClient` now talks through a transport abstraction while preserving the old `command=[...]` stdio constructor path.
- `agent/lsp/transports.py` — new `LSPTransport`, `StdioLSPTransport`, and `WebSocketLSPTransport`.
- `agent/lsp/servers.py` — config-driven custom server definitions and extension/languageId mapping.
- `agent/lsp/manager.py` — per-service registry from config and WebSocket client spawn path.
- `agent/lsp/cli.py` — configured-server aware `status`, `list`, `which`, plus `test` health check and `status --check`.
- `pyproject.toml` — optional `lsp-websocket` extra for `websockets`.
- `tests/agent/lsp/test_configured_servers.py` and `tests/agent/lsp/test_websocket_transport.py` — regression coverage.

## Why WebSocket transport is needed

Before this patch Hermes LSP modeled a server as a local binary launched by Hermes and spoken to through stdio with `Content-Length` framing. A BSL Language Server that is already running at a WebSocket endpoint cannot be represented by that model. This patch separates JSON-RPC client behavior from the transport and lets config define new server entries.

## How to enable BSL LS in profile `1c`

Apply the PatchKit profile/patch first. Then edit only the target profile config, for example via:

```bash
hermes --profile 1c config edit
```

Add a profile-local snippet like `examples/config-bsl-websocket.yaml` and replace the URL placeholder with the real private endpoint:

```yaml
lsp:
  enabled: true
  wait_mode: document
  wait_timeout: 5.0
  servers:
    bsl-language-server:
      language_id: bsl
      extensions:
        - .bsl
      transport:
        type: websocket
        url: ws://<bsl-language-server-host>:8025/lsp
      workspace_root: git
```

No profile path and no private endpoint are hardcoded in core code or in the patch logic.

## Verification

See `test-plan.md`. The minimum live checks after profile config are:

```bash
hermes --profile 1c lsp status
hermes --profile 1c lsp which bsl-language-server
hermes --profile 1c lsp test bsl-language-server
```

Expected successful health check:

```text
connected
initialize: ok
capabilities received
```

## Rollback

Core-code rollback is captured in `rollback.patch` and the manifest `rollback` field. With Git/PatchKit tooling, either roll back the PatchKit apply or reverse-apply the patch in a clean matching checkout.

Profile config rollback is separate and manual:

```text
Remove lsp.servers.bsl-language-server, or remove the legacy lsp.custom_servers.bsl entry, from the target profile config.yaml.
```

The PatchKit unit intentionally does not edit `/root/.hermes/profiles/1c/config.yaml`.

## Security notes

- No auth headers/tokens are logged.
- WebSocket URLs are ordinary config values; keep private/internal URLs out of public commits.
- Missing `websockets` or invalid/unreachable endpoints produce controlled unavailable/failure diagnostics and must not crash Hermes startup, `write_file`, or `patch`.
