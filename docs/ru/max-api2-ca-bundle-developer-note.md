# Developer note: MAX `platform-api2.max.ru` и profile-local CA bundle

## Контекст

Текущий MAX adapter Hermes использует устаревший default URL:

```python
DEFAULT_BASE_URL = "https://platform-api.max.ru"
```

Актуальная документация MAX требует использовать:

```text
https://platform-api2.max.ru
```

Источники:

- https://dev.max.ru/docs-api
- https://dev.max.ru/docs-api/methods/GET/updates
- https://dev.max.ru/docs-api/methods/POST/subscriptions

MAX также требует доверять сертификатной цепочке Минцифры. Текущий Debian/Python trust store эту цепочку не содержит.

## Проверенные факты

Проверка выполнена до установки сертификата:

```text
platform-api2.max.ru leaf issuer:
C=RU, O=The Ministry of Digital Development and Communications,
CN=Russian Trusted Sub CA

Russian Trusted Sub CA issuer:
C=RU, O=The Ministry of Digital Development and Communications,
CN=Russian Trusted Root CA
```

Пользовательский архив:

```text
/root/.hermes/profiles/hermesfix/cache/documents/doc_87a24fb11661_linux_russian_trusted_root_ca_pem.zip
```

SHA-256 архива:

```text
ca99ca9b0022ec8b99d5822502cf3f38d4797bdd02cc098996778421d72d7e24
```

Нужный PEM внутри архива:

```text
russian_trusted_root_ca_pem.crt
```

SHA-256 PEM:

```text
936a43fea6e8e525bcc0f81acd9c3d21b4fc4b9b68acea7906d698005afc6504
```

Subject/issuer PEM:

```text
subject=C=RU, O=The Ministry of Digital Development and Communications,
CN=Russian Trusted Root CA
issuer=C=RU, O=The Ministry of Digital Development and Communications,
CN=Russian Trusted Root CA
serial=1000
notBefore=Mar  1 21:04:15 2022 GMT
notAfter=Feb 27 21:04:15 2032 GMT
```

Fingerprint PEM:

```text
D2:6D:2D:02:31:B7:C3:9F:92:CC:73:85:12:BA:54:10:35:19:E4:40:5D:68:B5:BD:70:3E:97:88:CA:8E:CF:31
```

Live chain fingerprints:

```text
leaf *.max.ru:
78:C8:54:E2:B4:F2:24:80:B1:CA:8E:2E:0C:2A:2A:27:7C:23:79:21:98:AD:8B:34:D1:95:90:59:9D:FD:29:25

Russian Trusted Sub CA:
21:55:78:50:36:C9:00:DB:B5:F1:BB:2A:15:69:C8:0C:55:59:5B:D6:BF:94:86:7A:29:BB:DD:BC:7D:88:A3:F2
```

Проверки:

- `openssl verify -CAfile <root.pem> -untrusted <sub-ca.pem> <leaf.pem>` → `OK`;
- Python TLS-клиент с временным `cafile=<root.pem>` получил от `https://platform-api2.max.ru/` ожидаемый `HTTP 404 method.not.found`, то есть TLS handshake и hostname verification прошли;
- без CA стандартный OpenSSL/Python завершается `CERTIFICATE_VERIFY_FAILED`;
- `russian_trusted_root_ca_gost_2025_pem.crt` в архиве является DER-сертификатом отдельной GOST-цепочки. Для текущего RSA-сертификата `*.max.ru` он не нужен.

Происхождение архива проверено пользователем как официальный источник; технически подтверждено совпадение root subject, issuer-цепочки и успешная криптографическая проверка live server chain.

## Цель патча

Добавить поддержку profile-local CA bundle только для MAX adapter и перевести профиль office `1c_support` на `platform-api2.max.ru`.

Не менять глобальное системное trust store.
Не задавать глобальный `SSL_CERT_FILE`.
Не отключать TLS.
Не использовать `verify=False`.

## Требуемое поведение

### 1. MAX default URL

В `plugins/platforms/max/adapter.py`:

```python
DEFAULT_BASE_URL = "https://platform-api2.max.ru"
```

Существующий `extra.base_url` должен продолжить иметь приоритет для временного rollback/совместимости.

### 2. Scoped CA bundle

Текущий код создаёт client без явного `verify`:

```python
self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
```

Добавить profile-local настройку, например:

```yaml
platforms:
  max:
    enabled: true
    extra:
      base_url: https://platform-api2.max.ru
      ca_bundle: /root/.hermes/profiles/1c_support/certs/max/russian_trusted_root_ca_pem.crt
```

Для profile-safe реализации предпочтительно разрешать путь через `get_hermes_home()`/активный profile и не хардкодить `~/.hermes` в runtime code. Если путь задаётся явно в config, проверить, что он существует, является regular file и читаем процессом.

`MaxAdapter._get_client()` должен передавать этот путь только своему `httpx.AsyncClient`:

```python
verify = str(ca_bundle_path) if ca_bundle_path else True
self._client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=10.0),
    verify=verify,
)
```

Требования:

- hostname verification остаётся включённой;
- `verify=True` остаётся default при отсутствии custom bundle;
- отсутствующий/нечитаемый bundle должен давать понятную ошибку при старте MAX, а не silently fallback на `verify=False`;
- не использовать `SSL_CERT_FILE`, поскольку он влияет на другие HTTP-клиенты в том же gateway process;
- не устанавливать CA в `/etc/ssl`, Python `certifi` или системное trust store в рамках PatchKit;
- не добавлять сертификат в `.env` — это не secret и должен быть file/config artifact.

### 3. Profile-local artifact

Для office `1c_support` ожидаемый путь:

```text
/root/.hermes/profiles/1c_support/certs/max/russian_trusted_root_ca_pem.crt
```

Рекомендуемые permissions:

```text
certs/       0700 или 0750
max/         0700 или 0750
*.crt        0644 или 0600
```

CA public, но profile-local размещение уменьшает область доверия и не меняет trust store системы.

Не коммитить токены или другие secrets. Публичный CA можно либо доставлять как PatchKit asset, либо класть отдельным deployment artifact с pinned SHA-256 из раздела выше. При выборе asset не добавлять GOST DER-сертификат без доказанной необходимости.

### 4. MAX API transport

Это отдельный TLS/CA fix. WebSocket не является workaround:

- `wss://` всё равно использует TLS и требует проверки сертификата;
- `ws://` отключает TLS и небезопасен;
- текущий MAX Bot API документирует HTTPS, Long Polling и Webhook, но не WebSocket;
- production MAX рекомендует `POST /subscriptions`/Webhook;
- `GET /updates` остаётся допустимым для development/testing.

Не добавлять WebSocket transport в рамках этой задачи.

## Tests

Добавить исполняемые regression tests, не проверки текста исходника.

Минимально:

1. `MaxAdapter` с configured `ca_bundle` создаёт `httpx.AsyncClient` с `verify=<expected path>`.
2. Без `ca_bundle` client создаётся с обычным `verify=True`.
3. Missing/non-regular `ca_bundle` завершается понятной config/startup error.
4. `base_url` default равен `https://platform-api2.max.ru`.
5. Explicit `extra.base_url` продолжает override default.
6. Existing `GET /updates`, `POST /subscriptions`, `POST /messages`, `PUT /messages` и auth header behavior не ломаются.
7. CA path не попадает в outbound payloads, logs не содержат token.
8. Test remains profile-safe and does not write into real `/root/.hermes/`; use `tmp_path`/`HERMES_HOME` fixture.

Focused commands:

```bash
cd /root/.hermes/hermes-agent
scripts/run_tests.sh tests/gateway/test_max.py -q
scripts/run_tests.sh tests/plugins/test_max_platform_plugin.py -q
```

Если runner требует временный `pytest_split` shim, использовать canonical shim из `hermes-agent` maintenance skill, не запускать raw pytest вместо wrapper.

## PatchKit placement

Текущая active release line:

```text
v2026.7.20
/root/hermes-patchkit/patches/v2026.7.20/010-personal-overlay.patch
/root/hermes-patchkit/profiles/v2026.7.20-personal.yaml
```

MAX Bot API уже входит в personal overlay. Добавить изменение в этот существующий patch unit; не создавать отдельный второй MAX patch и не редактировать live runtime без соответствующего PatchKit diff.

Патч должен содержать code/tests/config/schema behavior. Public CA artifact и profile deployment step должны быть представлены отдельно и не смешиваться с secrets.

## Office rollout acceptance

После clean apply на official upstream release:

1. создать profile-local CA artifact в `1c_support`;
2. установить `ca_bundle` и `base_url: https://platform-api2.max.ru` в `1c_support/config.yaml`;
3. restart только `hermes-gateway-1c_support.service`;
4. проверить `active/running`, `NRestarts=0`;
5. в redacted log подтвердить MAX connected/polling без TLS error;
6. read-only API probe `/me` с токеном должен вернуть `HTTP 200`;
7. `/updates?timeout=1` должен вернуть `HTTP 200` без вывода token;
8. подтвердить, что local root MAX остаётся disabled и его `.env` не содержит `MAX_BOT_TOKEN`;
9. выполнить `git diff --check`, PatchKit self-check, clean apply и reverse-check.

Текущий operational state до применения патча:

- local root MAX отключён, `MAX_BOT_TOKEN` локально удалён;
- office `1c_support` временно работает через старый `https://platform-api.max.ru`;
- office `1c_support` unit был проверен как `active/running`, `NRestarts=0`;
- office token находится только в profile-local `.env` с mode `0600`;
- сертификаты и system trust store пока не изменялись.
