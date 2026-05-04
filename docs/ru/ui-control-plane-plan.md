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

Статус: exported как PatchKit unit `202-dashboard-profile-aware-pty`; runtime commit `4c6a0e631`, зависит от `200-dashboard-profile-api` и `201-dashboard-profile-selector`. Реализация добавляет validation `profile=<name>` в `/api/pty`, profile-scoped `HERMES_HOME` для PTY child без global active-profile switch, forwarding `resume`/sidecar параметров, Chat page URL propagation и кнопку “Open terminal” на Profiles page. Validation: focused runtime tests `24 passed`, frontend `npm run build` passed, focused eslint on touched files passed, live PTY smoke on `127.0.0.1:9138` confirmed `profile=hermesfix`, `HERMES_HOME=/root/.hermes/profiles/hermesfix` и `resume=smoke-js`.

### `203-dashboard-terminal-workspace`

Multi-terminal manager in dashboard.

Состав:

- tabs/panes for multiple PTY sessions;
- terminal lifecycle: open, reconnect, close, restart;
- profile/cwd labels;
- resize persistence;
- non-destructive failure handling;
- auth-gated terminal creation;
- remote browser PTY/WebSocket access только при явном public-dashboard opt-in (`--insecure`), иначе loopback-only.

Reference: брать UX у `hermes-workspace`, но protocol оставить Hermes-native.

Статус: exported как PatchKit unit `203-dashboard-terminal-workspace`; runtime commit `3a324f471`. Первый foundation-slice устраняет live-блокер после `202`: remote dashboard по `http://10.50.50.28:9119` теперь может открывать authenticated WebSocket terminal endpoints при `--insecure`, while defaults stay loopback-only. Validation: RED test reproduced remote PTY 4403 under public dashboard, focused `TestPtyWebSocket` теперь `16 passed`, broader dashboard focused tests `26 passed`; live browser smoke на `http://10.50.50.28:9119/chat?profile=hermesfix` открыл remote `/api/pty?profile=hermesfix&resume=live-203-decode` и получил PTY output с OSC title `Hermes`.

### `204-dashboard-runtime-registry`

Backend registry for live Hermes/TUI/gateway/worker processes.

Состав:

- read-only process/session registry;
- correlate PTY child, profile, cwd, started_at, last_activity;
- expose status without shelling out broadly from frontend;
- initial subagent/delegate visibility hooks where available;
- no kill/restart yet except existing PTY close;
- no argv/env/output/session/log/memory bodies in registry payloads.

Почему отдельно: runtime observability должна быть data layer, а не только визуальные terminal tabs.

Статус: exported как PatchKit unit `204-dashboard-runtime-registry`; runtime commit `671b540cc`, зависит от `200`–`203`. Реализация добавляет authenticated read-only `/api/dashboard/runtimes`: dashboard process metadata, public/embedded-chat flags, live PTY sessions with profile/cwd/pid/resume/terminal size, action subprocess liveness and event-channel counts. Validation: focused runtime registry tests `3 passed`, broader dashboard focused tests `29 passed`; live browser smoke на `http://10.50.50.28:9119/chat?profile=hermesfix` открыл PTY `resume=live-204-registry`, затем `/api/dashboard/runtimes` вернул live PTY session с `profile=hermesfix` без secrets.

### `205-dashboard-worker-roster`

Agent/worker cards and optional roster metadata.

Состав:

- profile-local or project-local roster metadata: role, lane, mission, preferred model, capabilities;
- worker cards: state, active task, active tool, cwd, last output, blocked reason;
- map long-lived tmux/PTY workers to cards;
- no hardcoded `swarm<N>` naming.

Reference: `hermes-workspace` Swarm2 ideas, но без Claude naming и без global active profile model.

Статус: exported как PatchKit unit `205-dashboard-worker-roster`; runtime commit `9ea912604`, зависит от `200`–`204`. Реализация добавляет authenticated read-only `/api/dashboard/worker-roster`: configured profile-local workers из `dashboard/worker_roster.json` плюс live PTY runtime workers из `204`, только safe role/lane/mission/model/capability/process metadata. Validation: focused worker roster tests `3 passed`, broader dashboard focused tests `32 passed`; live dashboard smoke вернул `200` и counts `configured_workers=0`, `runtime_workers=2`, `workers=2` без secrets.

### `206-dashboard-terminal-profile-lifecycle`

Bugfix/control slice for profile terminal identity and close lifecycle.

Состав:

- Open terminal из Profiles page создаёт уникальный `/chat?profile=<name>&terminal=<id>` channel;
- Chat page больше не переиспользует default terminal при переходе между profiles;
- authenticated `DELETE /api/dashboard/runtimes/pty/{id}` закрывает ровно одну registered PTY session;
- user-facing кнопка `Close terminal` закрывает текущий terminal и удаляет его из runtime registry;
- close/reopen не мутирует global active profile.

Статус: exported как PatchKit unit `206-dashboard-terminal-profile-lifecycle`; runtime commit `be1ef4e87`, зависит от `200`–`205`. Validation: dashboard focused tests `35 passed`, `npm run build` passed, focused eslint passed; live smoke на `http://10.50.50.28:9119/profiles` подтвердил, что `hermesfix` открывается как `/chat?profile=hermesfix&terminal=terminal-hermesfix-...`, `/api/dashboard/runtimes` показывает PTY с `profile=hermesfix`, а `Close terminal` удаляет session из registry.

### `207-dashboard-session-log-inspector`

Profile-aware sessions/logs/tools inspector.

Состав:

- browse recent sessions by profile;
- read recent messages/tool calls via Hermes session APIs/state layer;
- logs tail with redaction and source filter;
- links from worker cards to terminal/session/log views;
- safe read-only by default.

Reference: admin-ui pages + workspace chat reader idea, но реализовать через Hermes-native Python APIs.

Статус: exported как PatchKit unit `207-dashboard-session-log-inspector`; runtime commit `2205eb455`, зависит от `200`–`206`. Реализация добавляет authenticated read-only `/api/dashboard/profiles/{name}/sessions`, `/sessions/{session_id}` и `/logs`, плюс API client/Profile page wiring для `Session inspector` и `Log inspector`. Endpoint'ы отдают только safe metadata: session counts, token/cost/api-call metadata, message/tool-call summaries и log-file stat; не отдают message bodies, raw tool args, system prompts, log contents, env или secrets. Validation: profile inspector focused tests `5 passed`, broader dashboard focused tests `41 passed`, `npm run build` passed, focused eslint passed; live dashboard smoke на `http://10.50.50.28:9119/profiles?profile=hermesfix` подтвердил `200` для sessions/logs и отсутствие `API_KEY`/`SECRET` payload leaks.

### `208-dashboard-terminal-workspace-tabs`

Follow-up fix for terminal UX after `206`: the dashboard Chat surface is now an App-level multi-terminal workspace.

Состав:

- tab bar for live embedded terminals;
- default Chat terminal and profile terminals remain mounted as separate PTY panes;
- switching tabs changes the active visible terminal without killing hidden terminals;
- profile `Open terminal` adds a unique tab and keeps the existing default/profile tabs alive;
- closing a tab requires confirmation because it really terminates the PTY process;
- confirmed close calls `DELETE /api/dashboard/runtimes/pty/{id}` and removes only that terminal tab/session.

Статус: exported как PatchKit unit `208-dashboard-terminal-workspace-tabs`; runtime commit `ead849a5e`, depends on `200`–`207`. Validation: focused tests `44 passed`, `npm run build`, focused ESLint, live smoke on `10.50.50.28:9119` confirmed default + `hermesfix` tabs remain separate, cancel keeps PTYs, confirm close removes only selected PTY.

### `209-dashboard-assembly-analytics`

Profile-aware analytics and whole-assembly summary.

Реализованный состав:

- authenticated `/api/dashboard/analytics/assembly?days=<n>` по default + named profiles;
- safe per-profile rollup: sessions, active sessions, input/output/cache/reasoning tokens, estimated/actual cost, API calls, tool calls, provider/model, last activity и stale flag;
- whole-assembly summary: totals, top profiles by activity, stale profiles, model distribution и provider distribution;
- dashboard Analytics page теперь загружает assembly rollup рядом с существующей usage analytics и показывает safe per-profile table;
- degraded profiles возвращают per-profile error metadata, а не ломают всю summary;
- safety boundary: no session IDs, message bodies, prompts, tool arguments, memory bodies, `.env`, auth files, raw log contents или secrets в analytics payload.

Статус: exported как PatchKit unit `209-dashboard-assembly-analytics`; runtime commit `042f10871`, depends on `200`–`208`. Validation: `scripts/run_tests.sh` focused dashboard suite returned `53 passed`; `npm run build`; focused ESLint for `AnalyticsPage.tsx` and `api.ts`; temporary live smoke on `127.0.0.1:9140` returned analytics totals for 4 observed profiles and authenticated/unauthenticated gates behaved correctly.

Почему до controlled actions: сначала нужно видеть нагрузку, стоимость и активность всей сборки, иначе stop/restart/mutation decisions будут слепыми.

### `210-dashboard-controlled-actions`

Careful mutation layer after read-only UI is proven.

Реализованный состав:

- authenticated `/api/dashboard/actions` lists allowlisted dashboard mutation actions with labels, descriptions, danger level и exact confirmation string;
- authenticated `/api/dashboard/actions/{id}/run` запускает только allowlisted actions after exact confirmation match;
- current actions are `gateway-restart` and `hermes-update`, reusing existing detached Hermes action runner and status logs;
- dashboard SystemActions now goes through controlled action API instead of directly calling older restart/update endpoints;
- no profile deletion, arbitrary shell, raw argv editor or unlisted action execution.

Статус: exported как PatchKit unit `210-dashboard-controlled-actions`; runtime commit `efcb158cb`, depends on `200`–`209`. Validation: `scripts/run_tests.sh` focused dashboard suite returned `53 passed`; `npm run build`; focused ESLint for `SystemActions.tsx` and `api.ts`; temporary live smoke on `127.0.0.1:9140` listed allowlisted `gateway-restart`/`hermes-update` actions and returned 401 without token. No mutation action was executed during smoke.

Почему последним в first wave: mutation without observability is dangerous.

### `211-dashboard-control-plane-unification`

Стабилизационный slice после первой feature wave. Это не ещё один отдельный widget, а выравнивание dashboard на один язык и одну semantic model.

Реализованный состав:

- authenticated `/api/dashboard/overview` становится общим read-only semantic contract для control-plane counters и health;
- новая страница `/overview` становится default landing route dashboard;
- sidebar status strip использует тот же overview contract вместо смеси `/api/status`, analytics и runtime counters;
- Sessions page честно разделяет current-profile history и live `Active terminals`;
- gateway platform rows теперь отделяют `CONNECTED` от stale/attention state;
- bundled `example` dashboard plugin скрыт в production по умолчанию и включается только через `HERMES_DASHBOARD_SHOW_EXAMPLES=1|true|yes`;
- safety boundary: overview отдаёт только counts/metadata, без session IDs, message bodies, prompts, tool args/results, env, auth, memory, logs или secrets.

Статус: exported как PatchKit unit `211-dashboard-control-plane-unification`; runtime commit `cd84e8812`, depends on `200`–`210`. Validation: focused dashboard suite returned `25 passed`; `npm run build`; focused ESLint for new/touched control-plane files; `py_compile` for `hermes_cli/web_server.py`. Live dashboard smoke фиксируется после service restart.

Почему после controlled actions: когда частей стало достаточно, главной user-visible проблемой стала не нехватка фич, а конфликтующая семантика. Этот patch делает следующий visual polish (`212-dashboard-visual-polish`) безопасным: он не будет маскировать путаницу в данных.

### `212-dashboard-visual-polish`

Визуальная полировка после `211`. Этот patch не меняет semantic model; он делает уже унифицированный control plane менее шумным и более читабельным.

Реализованный состав:

- shared CSS primitives для dashboard content shell, panel cards, overview hero, metric grid, density table, freshness rows и sidebar status;
- Overview page получила более сильный hero/header, аккуратнее собранные KPI cards, более регулярные gutters и более читаемую profile health table;
- Card primitive теперь получает единый dashboard panel treatment: мягкий background, border contrast, inset highlight, blur/shadow;
- sidebar status strip стал отдельным grouped status block с чуть лучшим contrast/spacing;
- source-contract tests фиксируют, что visual polish живёт в shared primitives, а не в случайных per-page one-off classes;
- data contract `/api/dashboard/overview`, терминология `historical sessions / active terminals / gateway platforms / needs attention` и safety boundary не менялись.

Статус: exported как PatchKit unit `212-dashboard-visual-polish`; runtime commit `57067b399`, depends on `200`–`211`. Validation: RED source-contract tests сначала падали, затем focused dashboard suite returned `27 passed`; `npm run build`; focused ESLint for `OverviewPage.tsx`, `SidebarStatusStrip.tsx`, `card.tsx`, `App.tsx`; `git diff --check`; live smoke на `10.50.50.28:9119/overview?smoke=212` подтвердил root `200`, unauthenticated overview `401`, visual CSS marker в built assets, browser console без ошибок и более чистую hierarchy/spacing без очевидных layout regressions.

Почему после `211`: только после унификации semantic model можно полировать внешний вид, не маскируя конфликтующие источники правды.

### `213-dashboard-overview-semantic-cleanup`

Semantic cleanup после `212`. Этот patch меняет язык Overview и форму contract там, где после `211`/`212` assembly-level данные всё ещё выглядели как страница default profile.

Реализованный состав:

- `/api/dashboard/overview` теперь явно отдаёт `scope: assembly` и `selected_profile` context;
- backend response добавляет structured `attention_items[]` с source, severity, reason, message, action, target kind/id и route;
- backend response добавляет `runtime_health[]` для service/API components вроде `provider-proxy`, используя API/process evidence where available вместо session recency;
- platform rows сохраняют backward-compatible counters, но получают actionable attention metadata;
- Overview copy теперь product-facing (`Hermes control plane...`) и разделяет assembly rollup от selected profile context;
- Sidebar status использует action-required semantics вместо ambiguous attention wording;
- английский number formatting стабилизирован через `en-US`;
- safety boundary остаётся metadata-only: без session IDs, message bodies, prompts, tool args/results, env, auth, memory, logs или secrets.

Статус: exported как PatchKit unit `213-dashboard-overview-semantic-cleanup`; runtime commit `044c33c68`, depends on `200`–`212`. Validation: RED source-contract/API tests сначала падали, затем focused dashboard suite returned `148 passed`; targeted PTY websocket retry passed после unrelated xdist timing flake; `npm run build`; focused ESLint for `OverviewPage.tsx`, `api.ts`, `SidebarStatusStrip.tsx`; `py_compile`; `git diff --check`; live smoke на `127.0.0.1:9119/overview?smoke=213` подтвердил root `200`, unauthenticated overview `401`, authenticated overview `scope=assembly`, selected profile context, provider_proxy runtime health, structured action-required items и отсутствие browser console errors.

Почему после `212`: visual pass сделал ambiguity заметнее. Этот patch закрывает оставшийся semantic mismatch перед добавлением новых dashboard widgets.

### `214-dashboard-messaging-adapters-semantics`

Follow-up semantic slice после `213`. Этот patch убирает остаточный wording “gateway platforms” из Overview и делает status messaging adapters менее alarmist.

Реализованный состав:

- `/api/dashboard/overview` сохраняет backward-compatible `gateway.platforms`/`platform_rows`, но добавляет `messaging_adapters` counters и `adapter_rows`;
- каждая adapter row теперь разделяет `availability` и `event_freshness`;
- connected adapters со stale events помечаются для freshness review, а не как Action required;
- unhealthy adapter state всё ещё создаёт structured action-required items с source `messaging_adapter`;
- Overview copy/cards используют “Messaging adapters” и “Adapter freshness” вместо “Gateway platforms”;
- safety boundary остаётся metadata-only.

Статус: exported как PatchKit unit `214-dashboard-messaging-adapters-semantics`; runtime commit `fa9cef2cb`, depends on `200`–`213`. Validation: RED tests сначала падали на отсутствующей adapter semantics, затем focused dashboard suite returned `148 passed`; `npm run build`; focused ESLint for `OverviewPage.tsx`, `api.ts`, `SidebarStatusStrip.tsx`; `py_compile`; `git diff --check`. Live smoke фиксируется в manifest после dashboard restart.

Почему после `213`: `213` добавил structured action items; `214` добивает vocabulary adapters, чтобы stale-but-connected messaging adapters не выглядели urgent problems.

## Acceptance criteria for first milestone

Минимально полезный UI milestone — patches `200`–`203`:

- dashboard lists all Hermes profiles correctly;
- user can choose profile without changing global active profile;
- user can open embedded TUI terminal for at least two different profiles via profile-aware `/chat`/`/api/pty` URLs;
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
- Какие части считать upstream-candidate, а какие local-overlay? Текущая оценка: `200`–`204` могут быть upstream-candidate; `205`–`208` лучше начать как local-overlay, пока product shape стабилизируется.
