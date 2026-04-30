# Grok2API sidecar bridge

This is the first PatchKit sidecar bridge: use the existing `080-api-server-provider-proxy` patch to expose a local grok2api deployment through a dedicated Hermes API Server profile.

The point is not to copy grok2api into Hermes. Keep grok2api as a separate sidecar and let Hermes provide the catalog-routed OpenAI-compatible front door.

## What you get

- a local `/v1/models` catalog served by Hermes provider_proxy mode;
- model routing by `body.model` to a grok2api OpenAI-compatible endpoint;
- no Hermes `AIAgent`, SOUL prompt, tools, memory, sessions, or transcript state in the proxy path;
- a reversible PatchKit profile: `profiles/grok2api-sidecar.yaml`;
- a small doctor script: `scripts/grok2api_bridge.py`.

## License and risk boundary

Grok2API is MIT-licensed (`Copyright (c) 2026 Chenyme`) according to the upstream `LICENSE` checked on 2026-04-30. PatchKit does not vendor its code; it integrates by protocol and keeps attribution in `examples/sidecars/grok2api/THIRD_PARTY_NOTICE.md`.

MIT covers the code. It does not change Grok/xAI terms, account-ban risk, Cloudflare/WAF behavior, or the fragility of reverse-engineered web flows. Treat this bridge as an explicit self-hosted sidecar integration, not an official Grok API provider.

## Install the Hermes provider proxy patch

```bash
python3 scripts/apply.py \
  --repo ~/.hermes/hermes-agent \
  --manifest manifests/upstream-v2026.4.23.yaml \
  --profile profiles/grok2api-sidecar.yaml \
  --yes
```

For canary/main testing, use `manifests/canary-main-a1921c43c.yaml` with `profiles/canary-main-grok2api-sidecar.yaml`.

## Start grok2api as a loopback sidecar

```bash
mkdir -p ~/grok2api-sidecar
cp examples/sidecars/grok2api/docker-compose.yml ~/grok2api-sidecar/docker-compose.yml
cp examples/sidecars/grok2api/.env.example ~/grok2api-sidecar/.env
cd ~/grok2api-sidecar
docker compose up -d
```

After first start, configure grok2api itself: set its admin key, API key, app URL if needed, and accounts according to grok2api's own documentation. Keep the container bound to `127.0.0.1` unless you put it behind your own auth and network controls.

## Create a dedicated Hermes profile

Render the config:

```bash
python3 scripts/grok2api_bridge.py render-config \
  --base-url http://127.0.0.1:8000/v1 \
  --public-model grok2api/grok-3 \
  --target-model grok-3
```

Or write a profile skeleton:

```bash
python3 scripts/grok2api_bridge.py write-profile \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --public-model grok2api/grok-3 \
  --target-model grok-3
```

Then fill `~/.hermes/profiles/provider-proxy-grok2api/.env` locally:

```dotenv
OPENAI_API_KEY=<grok2api app.api_key, if configured>
API_SERVER_KEY=<Bearer key for clients calling Hermes API Server>
```

The bridge uses `provider: openai` plus `base_url: http://127.0.0.1:8000/v1`, so the provider_proxy path talks to grok2api as an OpenAI-compatible endpoint.

## Sync the model catalog automatically

Once grok2api is running, you do not need to copy model ids by hand. Ask the sidecar for `/v1/models` and generate the Hermes provider_proxy allowlist from that response:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1
```

Without `--write`, this is a dry run: it prints discovered sidecar ids, the filtered public ids Hermes would expose, and the generated config. The default sync filter is intentionally chat-only: include `^grok-`, exclude `imagine`, `image`, `video`, and `edit`, because the current provider_proxy patch handles `/v1/chat/completions`, not grok2api image/video endpoints.

After reviewing the dry run, write the dedicated profile config:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py sync-models \
  --profile-dir ~/.hermes/profiles/provider-proxy-grok2api \
  --base-url http://127.0.0.1:8000/v1 \
  --write \
  --backup
```

The public ids are prefixed by default, for example `grok2api/grok-4.20-auto` maps to the internal sidecar model `grok-4.20-auto`. To inspect raw sidecar ids without writing config:

```bash
OPENAI_API_KEY=*** \
python3 scripts/grok2api_bridge.py list-models \
  --base-url http://127.0.0.1:8000/v1
```

If grok2api changes its catalog later, rerun `sync-models --write --backup` and restart the Hermes gateway for this profile.

## Doctor checks

Check only the catalog endpoint:

```bash
OPENAI_API_KEY=<sidecar-key> \
python3 scripts/grok2api_bridge.py doctor \
  --base-url http://127.0.0.1:8000/v1 \
  --skip-chat
```

Run a minimal chat smoke:

```bash
OPENAI_API_KEY=<sidecar-key> \
python3 scripts/grok2api_bridge.py doctor \
  --base-url http://127.0.0.1:8000/v1 \
  --model grok-3
```

The script redacts the API key from printed errors/bodies.

## Start Hermes API Server

```bash
hermes --profile provider-proxy-grok2api gateway start
```

Then from a client:

```bash
export API_SERVER_KEY=<Bearer key for Hermes API Server clients>

curl -s http://127.0.0.1:8642/v1/models \
  -H "Authorization: Bearer $API_SERVER_KEY"

curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $API_SERVER_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"grok2api/grok-3","messages":[{"role":"user","content":"say ok"}],"stream":false}'
```

## Operational defaults

- Keep grok2api and Hermes provider_proxy in dedicated profiles/directories.
- Do not expose grok2api directly to the public internet.
- Do not use `latest` blindly for long-running deployments; pin an image tag/digest after your smoke tests.
- Do not put real keys in repository files or examples.
- Keep this out of PatchKit default/minimal profiles; it is an explicit sidecar bridge.
