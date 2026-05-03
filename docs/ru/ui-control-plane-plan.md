# UI Control Plane: концепция и patch plan

Этот документ фиксирует направление для отдельной UI-линейки PatchKit. Цель — сделать Hermes-native multi-profile dashboard, а не форкнуть внешний chat UI.

Исходные проекты, которые были разобраны как references:

- `karthikkrishnaswamysr/hermes-agent-admin-ui` — полезен как простой admin-console layout для profiles/sessions/logs/skills/tools/memory, но слаб как runtime foundation.
- `outsourc-e/hermes-workspace` — полезен как agent workspace / swarm IDE reference: terminal panes, worker cards, tmux attach, runtime roster, live status. Технически ближе к нужному продукту, но всё равно не должен заменять родной Hermes dashboard/TUI stack.

## Главный вывод

Делать свой UI нужно внутри built-in Hermes dashboard.

React/Web слой должен быть control plane вокруг Hermes, а не вторым chat engine. Основной interactive agent surface остаётся настоящим `hermes --tui` внутри PTY/xterm. Все дополнительные панели должны читать Hermes-native state: profiles, sessions, logs, process/runtime registry, gateway status, tools, skills, memory.

## Что взять из `hermes-agent-admin-ui`

Полезные идеи:

- простой admin navigation: Profiles, Sessions, Logs, Skills, Tools, Memory, Gateway;
- profile cards с model/provider/session/tool/log summary;
- read-only profile detail before mutation;
- понятные status badges и operator-friendly forms;
- разделение “управление профилями” и “чат”.

Не копировать:

- отдельный FastAPI/chat endpoint как основной путь общения с Hermes;
- ручное сканирование `~/.hermes/profiles` вместо Hermes profile helpers;
- небезопасные default auth patterns вроде dev secret / admin-admin;
- прямое редактирование `.env` как generic config store;
- hardcoded root logs/session paths без profile-aware `get_hermes_home()`.

## Что взять из `hermes-workspace`

Полезные идеи:

- multi-terminal workspace на xterm;
- terminal attach/restart/reconnect UX;
- tmux-backed long-lived worker sessions;
- worker/agent cards со state, cwd, active tool, last output, current task, blocked reason;
- roster/spec file idea: роль, lane, mission, model, capabilities;
- live worker chat/session inspector;
- reports/checkpoints/inbox/artifacts/previews как UI concepts;
- Swarm/Agent IDE spec как product reference.

Не копировать напрямую:

- `CLAUDE_*` legacy naming и semantic drift;
- TypeScript reimplementation of Hermes profile path resolution;
- global `active_profile` switching как основной runtime model;
- separate `/api/send-stream` chat stack;
- terminal PTY code без проверки resize/lifecycle/auth;
- hardwired `swarm<N>` assumptions.

## Hermes-native инварианты

1. Official Hermes upstream остаётся runtime base; UI changes идут PatchKit patch units.
2. Primary chat = embedded `hermes --tui` через PTY/xterm, без parallel React chat rewrite.
3. Profile awareness должна быть per request / per terminal / per panel, а не глобальный `active_profile` + restart.
4. Python side должен использовать `hermes_cli.profiles` и `get_hermes_home()`; frontend не должен угадывать filesystem layout.
5. Сначала read-only surfaces, потом mutation actions.
6. Все terminal/process/profile mutation endpoints auth-gated и audit-friendly.
7. Secrets остаются в `.env`; non-secret settings — в `config.yaml`.
8. UI не должен тащить provider_proxy или IDE traffic в Hermes agent/session layer.
9. Если upstream dashboard уже имеет PTY bridge, расширять его, а не заводить второй terminal protocol без причины.
10. Subagent/delegate/process observability должна быть отдельным runtime layer, а не парсингом случайных terminal strings как единственным источником истины.

## Нумерация patch units

UI-линейку резервируем отдельным диапазоном:

- `200`–`249`: Hermes dashboard / multi-profile UI / agent workspace.
- `250`–`269`: UI integrations around sidecars/previews, если понадобятся.
- `270`–`299`: UI hardening/polish/packaging, если линейка разрастётся.

Текущий стартовый набор должен жить в `200`–`207` и не смешиваться с provider/gateway patches вроде `070`–`080`.

## Предлагаемая patch sequence

### `200-dashboard-profile-api`

Read-only backend foundation для profile-aware dashboard.

Состав:

- `GET /api/dashboard/profiles` — список profiles через Hermes-native profile helpers;
- `GET /api/dashboard/profiles/{name}` — config/model/provider/skill/gateway/session/log metadata summary;
- session metadata включает counts/recent identifiers, но не session messages/system prompt;
- log metadata включает file name/path/size/mtime, но не log contents;
- profile name validation and path traversal protection;
- tests around default profile, named profile, invalid/missing profile and dashboard auth.

Почему первым: даёт безопасную read-only основу и не трогает chat/PTY runtime.

Статус: exported как PatchKit unit `200-dashboard-profile-api` в `manifests/upstream-v2026.4.30.yaml`; runtime commit `591863f7f`. Validation: runtime focused tests `126 passed`, clean `v2026.4.30` PatchKit apply + reverse-check + focused tests `126 passed`, live HTTP smoke on `127.0.0.1:9137` passed for auth gate, list and detail endpoints.

### `201-dashboard-profile-selector`

Frontend selector and profile-aware dashboard shell.

Состав:

- profile dropdown/sidebar in built-in dashboard;
- profile cards inspired by both reviewed projects;
- status summaries: model/provider/sessions/logs/gateway hints;
- empty/error states without killing embedded terminal;
- no mutation yet.

Почему отдельно: frontend can land without changing PTY lifecycle.

Статус: exported как PatchKit unit `201-dashboard-profile-selector`; runtime commit `36471e3b1`, зависит от `200-dashboard-profile-api`. Validation: frontend `npm run build` passed, focused eslint on touched files passed, focused runtime tests `8 passed` (`test_dashboard_profile_selector_frontend.py` + `test_web_server_profiles_api.py`), live dashboard smoke on `http://10.50.50.28:9119/profiles` confirmed sidebar selector, four profile cards, authenticated list/detail API calls and no browser console errors.

### `202-dashboard-profile-aware-pty`

Profile-aware embedded TUI terminal.

Состав:

- extend existing `/api/pty` path with optional `profile=<name>`;
- spawn `hermes --profile <name> --tui` or equivalent profile-safe env;
- default behavior unchanged when profile is omitted;
- validate profile before spawn;
- expose terminal title metadata: profile, cwd, pid/session id;
- tests for command construction/profile isolation.

Почему важно: это первый реально полезный milestone — можно открыть живой Hermes TUI под разными profiles.

### `203-dashboard-terminal-workspace`

Multi-terminal manager in dashboard.

Состав:

- tabs/panes for multiple PTY sessions;
- terminal lifecycle: open, reconnect, close, restart;
- profile/cwd labels;
- resize persistence;
- non-destructive failure handling;
- auth-gated terminal creation.

Reference: брать UX у `hermes-workspace`, но protocol оставить Hermes-native.

### `204-dashboard-runtime-registry`

Backend registry for live Hermes/TUI/gateway/worker processes.

Состав:

- read-only process/session registry;
- correlate PTY child, profile, cwd, started_at, last_activity;
- expose status without shelling out broadly from frontend;
- initial subagent/delegate visibility hooks where available;
- no kill/restart yet except existing PTY close.

Почему отдельно: runtime observability должна быть data layer, а не только визуальные terminal tabs.

### `205-dashboard-worker-roster`

Agent/worker cards and optional roster metadata.

Состав:

- profile-local or project-local roster metadata: role, lane, mission, preferred model, capabilities;
- worker cards: state, active task, active tool, cwd, last output, blocked reason;
- map long-lived tmux/PTY workers to cards;
- no hardcoded `swarm<N>` naming.

Reference: `hermes-workspace` Swarm2 ideas, но без Claude naming и без global active profile model.

### `206-dashboard-session-log-inspector`

Profile-aware sessions/logs/tools inspector.

Состав:

- browse recent sessions by profile;
- read recent messages/tool calls via Hermes session APIs/state layer;
- logs tail with redaction and source filter;
- links from worker cards to terminal/session/log views;
- safe read-only by default.

Reference: admin-ui pages + workspace chat reader idea, но реализовать через Hermes-native Python APIs.

### `207-dashboard-assembly-analytics`

Profile-aware analytics and whole-assembly summary.

Состав:

- reuse existing `/api/analytics/usage` semantics for the default/current dashboard scope, but add profile-safe aggregation across all Hermes profiles;
- per-profile analytics cards: sessions, active/recent sessions, input/output/cache/reasoning tokens, estimated/actual cost when available, API calls, tool calls, top models and top skills;
- whole-assembly summary: totals across default + named profiles, top profiles by activity/cost, inactive/stale profiles, gateway-running profiles, models/providers distribution;
- compare mode: selected profile vs all profiles for the same period (`7d`, `30d`, `90d`);
- preserve safety boundaries: no session messages, prompts, memory bodies, `.env`, auth files or raw log contents in analytics payloads;
- degraded profiles must not break the assembly summary; return per-profile error metadata instead.

Почему до controlled actions: сначала нужно видеть нагрузку, стоимость и активность всей сборки, иначе stop/restart/mutation decisions будут слепыми.

### `208-dashboard-controlled-actions`

Careful mutation layer after read-only UI is proven.

Состав:

- start/stop/restart selected PTY or worker;
- optional gateway status/restart per profile;
- explicit confirmations for destructive actions;
- audit labels in logs;
- no delete profile until a later dedicated patch.

Почему последним в first wave: mutation without observability is dangerous.

## Acceptance criteria for first milestone

Минимально полезный UI milestone — patches `200`–`202`:

- dashboard lists all Hermes profiles correctly;
- user can choose profile without changing global active profile;
- user can open embedded TUI terminal for at least two different profiles at once;
- default old dashboard chat path still works when no profile is selected;
- profile path traversal attempts fail closed;
- terminal spawn does not leak secrets in frontend-visible metadata;
- focused backend/frontend tests pass.

## Verification policy

Для каждого UI patch:

1. focused Python tests through `scripts/run_tests.sh`, not raw pytest;
2. focused frontend tests/typecheck for `web/` or `ui-tui/` if touched;
3. manual smoke in dashboard:
   - default profile terminal;
   - named profile terminal;
   - invalid profile rejected;
   - terminal resize still works;
   - existing `/chat` route still works;
4. PatchKit clean apply against `v2026.4.30` before claiming patch exported;
5. docs EN/RU updated if behavior is user-facing.

## Открытые вопросы перед реализацией

- Terminal workspace должен использовать только существующий `/api/pty` или нужен versioned wrapper `/api/terminals` поверх него?
- Где хранить long-lived worker roster: в profile config, project-local `.hermes/` или dashboard runtime DB?
- Сколько активности `subagent` / `delegate_task` можно показать из уже существующего process/session state без invasive core changes?
- Делать tmux optional integration или first-class supported backend?
- Какие части считать upstream-candidate, а какие local-overlay? Текущая оценка: `200`–`204` могут быть upstream-candidate; `205`–`207` лучше начать как local-overlay, пока product shape стабилизируется.
