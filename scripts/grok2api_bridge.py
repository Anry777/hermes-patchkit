#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin


@dataclass(frozen=True)
class HttpResult:
    method: str
    url: str
    status: int | None
    body: str
    error: str | None = None


def _endpoint(base_url: str, suffix: str) -> str:
    base = base_url.rstrip('/') + '/'
    return urljoin(base, suffix.lstrip('/'))


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {'Content-Type': 'application/json', 'User-Agent': 'Hermes-PatchKit-grok2api-bridge'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return headers


def _request(method: str, url: str, *, api_key: str | None, payload: dict | None = None, timeout: float = 10.0) -> HttpResult:
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=_headers(api_key), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(16000).decode('utf-8', 'replace')
            return HttpResult(method=method, url=url, status=response.status, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read(16000).decode('utf-8', 'replace')
        return HttpResult(method=method, url=url, status=exc.code, body=body, error=str(exc))
    except Exception as exc:
        return HttpResult(method=method, url=url, status=None, body='', error=str(exc))


def _redact(text: str, secret: str | None) -> str:
    if secret:
        return text.replace(secret, '[REDACTED]')
    return text


def _print_result(result: HttpResult, *, api_key: str | None) -> None:
    status = result.status if result.status is not None else 'ERROR'
    print(f'{result.method} {result.url} -> {status}')
    if result.error:
        print(f'  error: {_redact(result.error, api_key)}')
    if result.body:
        body = _redact(result.body, api_key).replace('\n', '\\n')
        print(f'  body: {body[:500]}')


def run_doctor(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get(args.api_key_env or '') or None
    models_result = _request('GET', _endpoint(args.base_url, 'models'), api_key=api_key, timeout=args.timeout)
    _print_result(models_result, api_key=api_key)
    if models_result.status != 200:
        print('grok2api bridge doctor failed: /models did not return HTTP 200')
        return 1

    try:
        models_payload = json.loads(models_result.body)
        ids = [item.get('id') for item in models_payload.get('data', []) if isinstance(item, dict) and item.get('id')]
    except Exception:
        ids = []
    if ids:
        print('models: ' + ', '.join(str(item) for item in ids[:20]))
    else:
        print('models: /models returned 200 but no OpenAI-style data[].id entries were found')

    if args.skip_chat:
        print('grok2api bridge doctor passed: catalog endpoint is reachable')
        return 0

    chat_payload = {
        'model': args.model,
        'messages': [{'role': 'user', 'content': args.prompt}],
        'stream': False,
        'max_tokens': args.max_tokens,
    }
    chat_result = _request('POST', _endpoint(args.base_url, 'chat/completions'), api_key=api_key, payload=chat_payload, timeout=args.timeout)
    _print_result(chat_result, api_key=api_key)
    if chat_result.status != 200:
        print('grok2api bridge doctor failed: chat completion smoke did not return HTTP 200')
        return 1
    print('grok2api bridge doctor passed: /models and /chat/completions are reachable')
    return 0


def render_config(args: argparse.Namespace) -> int:
    if args.format == 'json':
        config = {
            'platforms': {'api_server': {'enabled': True, 'host': args.host, 'port': args.port}},
            'extra': {
                'mode': 'provider_proxy',
                'provider_proxy': {
                    'enabled': True,
                    'require_explicit_model': True,
                    'allow_streaming': False,
                    'models': [{
                        'id': args.public_model,
                        'provider': 'openai',
                        'model': args.target_model,
                        'base_url': args.base_url.rstrip('/'),
                        'api_mode': 'chat_completions',
                        'owned_by': 'grok2api',
                    }],
                },
            },
        }
        print(json.dumps(config, indent=2, ensure_ascii=False))
    else:
        print(f'''# Hermes profile config snippet for a local grok2api sidecar.
# Keep this in a dedicated profile, for example:
#   ~/.hermes/profiles/provider-proxy-grok2api/config.yaml
# Put the sidecar API key in the same profile's .env as OPENAI_API_KEY.

platforms:
  api_server:
    enabled: true
    host: {args.host}
    port: {args.port}

extra:
  mode: provider_proxy
  provider_proxy:
    enabled: true
    require_explicit_model: true
    allow_streaming: false
    models:
      - id: {args.public_model}
        provider: openai
        model: {args.target_model}
        base_url: {args.base_url.rstrip('/')}
        api_mode: chat_completions
        owned_by: grok2api
'''.rstrip())
    print()
    print('# Profile-local .env values:')
    print(f'{args.api_key_env}=<grok2api app.api_key value, if you configured one>')
    print(f'{args.server_key_env}=<Bearer key clients use when calling Hermes API Server>')
    return 0


def write_profile(args: argparse.Namespace) -> int:
    profile_dir = Path(args.profile_dir).expanduser().resolve()
    if profile_dir.exists() and any(profile_dir.iterdir()) and not args.force:
        print(f'ERROR: refusing to overwrite non-empty profile directory without --force: {profile_dir}', file=sys.stderr)
        return 1
    profile_dir.mkdir(parents=True, exist_ok=True)
    config_path = profile_dir / 'config.yaml'
    env_path = profile_dir / '.env'
    config_text = f'''# Generated by hermes-patchkit scripts/grok2api_bridge.py at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
# Dedicated provider_proxy profile for a local grok2api sidecar.

platforms:
  api_server:
    enabled: true
    host: {args.host}
    port: {args.port}

extra:
  mode: provider_proxy
  provider_proxy:
    enabled: true
    require_explicit_model: true
    allow_streaming: false
    models:
      - id: {args.public_model}
        provider: openai
        model: {args.target_model}
        base_url: {args.base_url.rstrip('/')}
        api_mode: chat_completions
        owned_by: grok2api
'''
    env_text = f'''# Fill these locally. Do not commit real values.
{args.api_key_env}=
{args.server_key_env}=
'''
    config_path.write_text(config_text, encoding='utf-8')
    if not env_path.exists() or args.force:
        env_path.write_text(env_text, encoding='utf-8')
    print(f'wrote {config_path}')
    print(f'wrote {env_path}')
    print('next: set secrets in .env, then run: hermes --profile provider-proxy-grok2api gateway start')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Grok2API sidecar bridge helper for Hermes PatchKit provider_proxy mode.')
    sub = parser.add_subparsers(dest='command', required=True)

    doctor = sub.add_parser('doctor', help='Check a grok2api OpenAI-compatible endpoint.')
    doctor.add_argument('--base-url', default='http://127.0.0.1:8000/v1')
    doctor.add_argument('--api-key', default=None, help='Sidecar API key. Prefer --api-key-env for normal use.')
    doctor.add_argument('--api-key-env', default='OPENAI_API_KEY', help='Environment variable containing the sidecar API key.')
    doctor.add_argument('--model', default='grok-3')
    doctor.add_argument('--prompt', default='Reply with only: ok')
    doctor.add_argument('--max-tokens', type=int, default=16)
    doctor.add_argument('--timeout', type=float, default=30.0)
    doctor.add_argument('--skip-chat', action='store_true')
    doctor.set_defaults(func=run_doctor)

    render = sub.add_parser('render-config', help='Print a Hermes provider_proxy config snippet for grok2api.')
    render.add_argument('--format', choices=('yaml', 'json'), default='yaml')
    render.add_argument('--host', default='127.0.0.1')
    render.add_argument('--port', type=int, default=8642)
    render.add_argument('--base-url', default='http://127.0.0.1:8000/v1')
    render.add_argument('--public-model', default='grok2api/grok-3')
    render.add_argument('--target-model', default='grok-3')
    render.add_argument('--api-key-env', default='OPENAI_API_KEY')
    render.add_argument('--server-key-env', default='API_SERVER_KEY')
    render.set_defaults(func=render_config)

    write = sub.add_parser('write-profile', help='Write a dedicated Hermes profile config for grok2api provider_proxy mode.')
    write.add_argument('--profile-dir', default='~/.hermes/profiles/provider-proxy-grok2api')
    write.add_argument('--host', default='127.0.0.1')
    write.add_argument('--port', type=int, default=8642)
    write.add_argument('--base-url', default='http://127.0.0.1:8000/v1')
    write.add_argument('--public-model', default='grok2api/grok-3')
    write.add_argument('--target-model', default='grok-3')
    write.add_argument('--api-key-env', default='OPENAI_API_KEY')
    write.add_argument('--server-key-env', default='API_SERVER_KEY')
    write.add_argument('--force', action='store_true')
    write.set_defaults(func=write_profile)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
