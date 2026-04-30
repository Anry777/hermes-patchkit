#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin


DEFAULT_CHAT_INCLUDE = (r'^grok-',)
DEFAULT_CHAT_EXCLUDE = (r'imagine', r'image', r'video', r'edit')


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


def _api_key_from_args(args: argparse.Namespace) -> str | None:
    return args.api_key or os.environ.get(args.api_key_env or '') or None


def _model_ids_from_body(body: str) -> list[str]:
    payload = json.loads(body)
    data = payload.get('data', [])
    if not isinstance(data, list):
        return []

    ids: list[str] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = str(item.get('id') or '').strip()
        if not model_id or '\x00' in model_id or '\n' in model_id or '\r' in model_id:
            continue
        if model_id in seen:
            continue
        seen.add(model_id)
        ids.append(model_id)
    return ids


def _fetch_model_ids(base_url: str, *, api_key: str | None, timeout: float) -> tuple[HttpResult, list[str]]:
    result = _request('GET', _endpoint(base_url, 'models'), api_key=api_key, timeout=timeout)
    if result.status != 200:
        return result, []
    try:
        return result, _model_ids_from_body(result.body)
    except Exception:
        return result, []


def _compile_patterns(patterns: list[str] | tuple[str, ...] | None) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns or []:
        compiled.append(re.compile(pattern))
    return compiled


def _filter_model_ids(model_ids: list[str], *, include: list[str] | tuple[str, ...] | None, exclude: list[str] | tuple[str, ...] | None) -> list[str]:
    include_patterns = _compile_patterns(include)
    exclude_patterns = _compile_patterns(exclude)

    filtered: list[str] = []
    for model_id in model_ids:
        if include_patterns and not any(pattern.search(model_id) for pattern in include_patterns):
            continue
        if exclude_patterns and any(pattern.search(model_id) for pattern in exclude_patterns):
            continue
        filtered.append(model_id)
    return filtered


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _model_specs(model_ids: list[str], *, prefix: str, base_url: str, owned_by: str) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for model_id in model_ids:
        specs.append({
            'id': f'{prefix}{model_id}',
            'provider': 'openai',
            'model': model_id,
            'base_url': base_url.rstrip('/'),
            'api_mode': 'chat_completions',
            'owned_by': owned_by,
        })
    return specs


def _provider_proxy_config(*, host: str, port: int, models: list[dict[str, str]]) -> dict:
    return {
        'platforms': {'api_server': {'enabled': True, 'host': host, 'port': port}},
        'extra': {
            'mode': 'provider_proxy',
            'provider_proxy': {
                'enabled': True,
                'require_explicit_model': True,
                'allow_streaming': False,
                'models': models,
            },
        },
    }


def _render_config_yaml(*, host: str, port: int, models: list[dict[str, str]]) -> str:
    lines = [
        '# Hermes profile config for a local grok2api sidecar.',
        '# Generated by hermes-patchkit scripts/grok2api_bridge.py.',
        '',
        'platforms:',
        '  api_server:',
        '    enabled: true',
        f'    host: {_yaml_scalar(host)}',
        f'    port: {port}',
        '',
        'extra:',
        '  mode: provider_proxy',
        '  provider_proxy:',
        '    enabled: true',
        '    require_explicit_model: true',
        '    allow_streaming: false',
        '    models:',
    ]
    for spec in models:
        lines.extend([
            f'      - id: {_yaml_scalar(spec["id"])}',
            f'        provider: {_yaml_scalar(spec["provider"])}',
            f'        model: {_yaml_scalar(spec["model"])}',
            f'        base_url: {_yaml_scalar(spec["base_url"])}',
            f'        api_mode: {_yaml_scalar(spec["api_mode"])}',
            f'        owned_by: {_yaml_scalar(spec["owned_by"])}',
        ])
    return '\n'.join(lines) + '\n'


def _print_model_sync_summary(discovered: list[str], selected: list[str], specs: list[dict[str, str]]) -> None:
    print(f'discovered models: {len(discovered)}')
    for model_id in discovered:
        marker = '*' if model_id in selected else '-'
        print(f'  {marker} {model_id}')
    print()
    print(f'exposed chat catalog entries: {len(specs)}')
    for spec in specs:
        print(f'  {spec["id"]} -> {spec["model"]}')


def run_doctor(args: argparse.Namespace) -> int:
    api_key = _api_key_from_args(args)
    models_result, ids = _fetch_model_ids(args.base_url, api_key=api_key, timeout=args.timeout)
    _print_result(models_result, api_key=api_key)
    if models_result.status != 200:
        print('grok2api bridge doctor failed: /models did not return HTTP 200')
        return 1

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


def list_models(args: argparse.Namespace) -> int:
    api_key = _api_key_from_args(args)
    result, discovered = _fetch_model_ids(args.base_url, api_key=api_key, timeout=args.timeout)
    if result.status != 200:
        _print_result(result, api_key=api_key)
        print('grok2api list-models failed: /models did not return HTTP 200', file=sys.stderr)
        return 1

    try:
        selected = _filter_model_ids(discovered, include=args.include, exclude=args.exclude)
    except re.error as exc:
        print(f'ERROR: invalid include/exclude regex: {exc}', file=sys.stderr)
        return 2

    if args.format == 'json':
        print(json.dumps({'models': selected}, indent=2, ensure_ascii=False))
    else:
        for model_id in selected:
            print(model_id)
    return 0


def _single_model_spec(public_model: str, target_model: str, base_url: str) -> list[dict[str, str]]:
    return [{
        'id': public_model,
        'provider': 'openai',
        'model': target_model,
        'base_url': base_url.rstrip('/'),
        'api_mode': 'chat_completions',
        'owned_by': 'grok2api',
    }]


def render_config(args: argparse.Namespace) -> int:
    models = _single_model_spec(args.public_model, args.target_model, args.base_url)
    if args.format == 'json':
        config = _provider_proxy_config(host=args.host, port=args.port, models=models)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return 0

    print('''# Hermes profile config snippet for a local grok2api sidecar.
# Keep this in a dedicated profile, for example:
#   ~/.hermes/profiles/provider-proxy-grok2api/config.yaml
# Put the sidecar API key in the same profile's .env as OPENAI_API_KEY.
'''.rstrip())
    print()
    print(_render_config_yaml(host=args.host, port=args.port, models=models).rstrip())
    print()
    print('# Profile-local .env values:')
    print(f'{args.api_key_env}=<grok2api app.api_key value, if you configured one>')
    print(f'{args.server_key_env}=<Bearer key clients use when calling Hermes API Server>')
    return 0


def sync_models(args: argparse.Namespace) -> int:
    api_key = _api_key_from_args(args)
    result, discovered = _fetch_model_ids(args.base_url, api_key=api_key, timeout=args.timeout)
    if result.status != 200:
        _print_result(result, api_key=api_key)
        print('grok2api sync-models failed: /models did not return HTTP 200', file=sys.stderr)
        return 1
    if not discovered:
        print('grok2api sync-models failed: no OpenAI-style data[].id entries were found', file=sys.stderr)
        return 1

    include = args.include if args.include is not None else list(DEFAULT_CHAT_INCLUDE)
    exclude = args.exclude if args.exclude is not None else list(DEFAULT_CHAT_EXCLUDE)
    try:
        selected = _filter_model_ids(discovered, include=include, exclude=exclude)
    except re.error as exc:
        print(f'ERROR: invalid include/exclude regex: {exc}', file=sys.stderr)
        return 2

    if not selected:
        print('grok2api sync-models failed: filters selected zero chat models', file=sys.stderr)
        return 1

    specs = _model_specs(selected, prefix=args.prefix, base_url=args.base_url, owned_by=args.owned_by)
    config = _provider_proxy_config(host=args.host, port=args.port, models=specs)
    config_text = json.dumps(config, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else _render_config_yaml(host=args.host, port=args.port, models=specs)

    _print_model_sync_summary(discovered, selected, specs)
    print()
    if not args.write:
        print('dry-run: config.yaml was not changed; pass --write to write the dedicated profile config')
        print()
        print(config_text.rstrip())
        return 0

    profile_dir = Path(args.profile_dir).expanduser().resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    config_path = profile_dir / 'config.yaml'
    if config_path.exists() and args.backup:
        backup_path = profile_dir / f'config.yaml.bak-{time.strftime("%Y%m%d-%H%M%S", time.gmtime())}'
        shutil.copy2(config_path, backup_path)
        print(f'backup: {backup_path}')
    config_path.write_text(config_text, encoding='utf-8')
    print(f'wrote {config_path}')
    print('next: restart Hermes gateway for this profile so /v1/models reloads the catalog')
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


def _add_endpoint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--base-url', default='http://127.0.0.1:8000/v1')
    parser.add_argument('--api-key', default=None, help='Sidecar API key. Prefer --api-key-env for normal use.')
    parser.add_argument('--api-key-env', default='OPENAI_API_KEY', help='Environment variable containing the sidecar API key.')
    parser.add_argument('--timeout', type=float, default=30.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Grok2API sidecar bridge helper for Hermes PatchKit provider_proxy mode.')
    sub = parser.add_subparsers(dest='command', required=True)

    doctor = sub.add_parser('doctor', help='Check a grok2api OpenAI-compatible endpoint.')
    _add_endpoint_args(doctor)
    doctor.add_argument('--model', default='grok-3')
    doctor.add_argument('--prompt', default='Reply with only: ok')
    doctor.add_argument('--max-tokens', type=int, default=16)
    doctor.add_argument('--skip-chat', action='store_true')
    doctor.set_defaults(func=run_doctor)

    list_cmd = sub.add_parser('list-models', help='List model ids from the grok2api /v1/models endpoint.')
    _add_endpoint_args(list_cmd)
    list_cmd.add_argument('--include', action='append', default=None, help='Regex of model ids to include. Repeatable. Default: include all.')
    list_cmd.add_argument('--exclude', action='append', default=None, help='Regex of model ids to exclude. Repeatable. Default: exclude none.')
    list_cmd.add_argument('--format', choices=('text', 'json'), default='text')
    list_cmd.set_defaults(func=list_models)

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

    sync = sub.add_parser('sync-models', help='Discover grok2api models and write a dedicated Hermes provider_proxy catalog.')
    _add_endpoint_args(sync)
    sync.add_argument('--profile-dir', default='~/.hermes/profiles/provider-proxy-grok2api')
    sync.add_argument('--host', default='127.0.0.1')
    sync.add_argument('--port', type=int, default=8642)
    sync.add_argument('--prefix', default='grok2api/', help='Public model id prefix exposed by Hermes.')
    sync.add_argument('--owned-by', default='grok2api')
    sync.add_argument('--include', action='append', default=None, help='Regex of sidecar model ids to include. Default: ^grok-')
    sync.add_argument('--exclude', action='append', default=None, help='Regex of sidecar model ids to exclude. Default: imagine|image|video|edit')
    sync.add_argument('--format', choices=('yaml', 'json'), default='yaml')
    sync.add_argument('--write', action='store_true', help='Write config.yaml. Without this, sync-models is a dry run.')
    sync.add_argument('--backup', action='store_true', help='Copy existing config.yaml before overwriting it.')
    sync.set_defaults(func=sync_models)

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
