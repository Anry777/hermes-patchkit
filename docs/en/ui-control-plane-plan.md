# UI Control Plane: concept and patch plan

This document records the direction for a dedicated PatchKit UI line. The goal is a Hermes-native multi-profile dashboard, not a fork of an external chat UI.

Reference projects reviewed:

- `karthikkrishnaswamysr/hermes-agent-admin-ui` — useful as a simple admin-console layout for profiles, sessions, logs, skills, tools and memory, but weak as a runtime foundation.
- `outsourc-e/hermes-workspace` — useful as an agent workspace / swarm IDE reference: terminal panes, worker cards, tmux attach, runtime roster and live status. It is closer to the desired product, but still should not replace the built-in Hermes dashboard/TUI stack.

## Main decision

Build this inside the built-in Hermes dashboard.

The React/Web layer should be a control plane around Hermes, not a second chat engine. The primary interactive agent surface remains the real `hermes --tui` running inside PTY/xterm. Additional panels should read Hermes-native state: profiles, sessions, logs, process/runtime registry, gateway status, tools, skills and memory.

## What to borrow from `hermes-agent-admin-ui`

Useful ideas:

- simple admin navigation: Profiles, Sessions, Logs, Skills, Tools, Memory, Gateway;
- profile cards with model/provider/session/tool/log summaries;
- read-only profile detail before mutation;
- clear status badges and operator-friendly forms;
- separation between “profile administration” and “chat”.

Do not copy:

- a separate FastAPI/chat endpoint as the primary Hermes interaction path;
- manual scanning of `~/.hermes/profiles` instead of Hermes profile helpers;
- unsafe default auth patterns such as dev secrets or admin/admin;
- direct `.env` editing as a generic config store;
- hardcoded root log/session paths without profile-aware `get_hermes_home()`.

## What to borrow from `hermes-workspace`

Useful ideas:

- multi-terminal workspace on xterm;
- terminal attach/restart/reconnect UX;
- tmux-backed long-lived worker sessions;
- worker/agent cards with state, cwd, active tool, last output, current task and blocked reason;
- a roster/spec file idea: role, lane, mission, model and capabilities;
- live worker chat/session inspector;
- reports/checkpoints/inbox/artifacts/previews as UI concepts;
- Swarm/Agent IDE spec as product reference.

Do not copy directly:

- `CLAUDE_*` legacy naming and semantic drift;
- TypeScript reimplementation of Hermes profile path resolution;
- global `active_profile` switching as the primary runtime model;
- separate `/api/send-stream` chat stack;
- terminal PTY code without validating resize/lifecycle/auth behavior;
- hardwired `swarm<N>` assumptions.

## Hermes-native invariants

1. Official Hermes upstream remains the runtime base; UI changes are PatchKit patch units.
2. Primary chat = embedded `hermes --tui` through PTY/xterm, with no parallel React chat rewrite.
3. Profile awareness must be per request / per terminal / per panel, not global `active_profile` plus restart.
4. Python side must use `hermes_cli.profiles` and `get_hermes_home()`; frontend must not guess the filesystem layout.
5. Read-only surfaces first, mutation actions later.
6. All terminal/process/profile mutation endpoints must be auth-gated and audit-friendly.
7. Secrets stay in `.env`; non-secret settings live in `config.yaml`.
8. UI must not pull provider_proxy or IDE traffic into the Hermes agent/session layer.
9. If the upstream dashboard already has a PTY bridge, extend it instead of adding a second terminal protocol without a strong reason.
10. Subagent/delegate/process observability should be a runtime data layer, not only terminal-string parsing.

## Patch numbering

Reserve a separate range for the UI line:

- `200`–`249`: Hermes dashboard / multi-profile UI / agent workspace.
- `250`–`269`: UI integrations around sidecars/previews, if needed.
- `270`–`299`: UI hardening/polish/packaging, if the line grows.

The initial set should live in `200`–`207` and stay separate from provider/gateway patches such as `070`–`080`.

## Proposed patch sequence

### `200-dashboard-profile-api`

Read-only backend foundation for a profile-aware dashboard.

Scope:

- `GET /api/dashboard/profiles` — list profiles through Hermes-native profile helpers;
- `GET /api/dashboard/profiles/{name}` — config/model/provider/skill/gateway/session/log metadata summary;
- session metadata includes counts/recent identifiers, but not session messages or system prompts;
- log metadata includes file name/path/size/mtime, but not log contents;
- profile-name validation and path traversal protection;
- tests around the default profile, named profiles, invalid/missing profiles and dashboard auth.

Why first: it creates a safe read-only base and does not touch chat/PTY runtime.

Status: exported as PatchKit unit `200-dashboard-profile-api` in `manifests/upstream-v2026.4.30.yaml`; runtime commit `591863f7f`. Validation: runtime focused tests `126 passed`, clean `v2026.4.30` PatchKit apply + reverse-check + focused tests `126 passed`, live HTTP smoke on `127.0.0.1:9137` passed for auth gate, list and detail endpoints.

### `201-dashboard-profile-selector`

Frontend selector and profile-aware dashboard shell.

Scope:

- profile dropdown/sidebar in the built-in dashboard;
- profile cards inspired by both reviewed projects;
- status summaries: model/provider/sessions/logs/gateway hints;
- empty/error states that do not kill the embedded terminal;
- no mutation yet.

Why separate: frontend can land without changing PTY lifecycle.

Status: exported as PatchKit unit `201-dashboard-profile-selector`; runtime commit `36471e3b1`, depends on `200-dashboard-profile-api`. Validation: frontend `npm run build` passed, focused eslint on touched files passed, focused runtime tests `8 passed` (`test_dashboard_profile_selector_frontend.py` + `test_web_server_profiles_api.py`), live dashboard smoke on `http://10.50.50.28:9119/profiles` confirmed the sidebar selector, four profile cards, authenticated list/detail API calls and no browser console errors.

### `202-dashboard-profile-aware-pty`

Profile-aware embedded TUI terminal.

Scope:

- extend the existing `/api/pty` path with optional `profile=<name>`;
- spawn `hermes --profile <name> --tui` or equivalent profile-safe environment;
- keep default behavior unchanged when no profile is provided;
- validate profile before spawn;
- expose terminal title metadata: profile, cwd, pid/session id;
- tests for command construction and profile isolation.

Why it matters: this is the first immediately useful milestone — multiple live Hermes TUI instances for different profiles.

Status: exported as PatchKit unit `202-dashboard-profile-aware-pty`; runtime commit `4c6a0e631`, depends on `200-dashboard-profile-api` and `201-dashboard-profile-selector`. The implementation adds `profile=<name>` validation in `/api/pty`, profile-scoped `HERMES_HOME` for the PTY child without a global active-profile switch, forwarding for `resume`/sidecar parameters, Chat page URL propagation, and an “Open terminal” action on the Profiles page. Validation: focused runtime tests `24 passed`, frontend `npm run build` passed, focused eslint on touched files passed, live PTY smoke on `127.0.0.1:9138` confirmed `profile=hermesfix`, `HERMES_HOME=/root/.hermes/profiles/hermesfix`, and `resume=smoke-js`.

### `203-dashboard-terminal-workspace`

Multi-terminal manager in the dashboard.

Scope:

- tabs/panes for multiple PTY sessions;
- terminal lifecycle: open, reconnect, close, restart;
- profile/cwd labels;
- resize persistence;
- non-destructive failure handling;
- auth-gated terminal creation;
- remote browser PTY/WebSocket access only under the explicit public-dashboard opt-in (`--insecure`), otherwise loopback-only.

Reference: borrow UX from `hermes-workspace`, but keep the protocol Hermes-native.

Status: exported as PatchKit unit `203-dashboard-terminal-workspace`; runtime commit `3a324f471`. The first foundation slice removes the live blocker found after `202`: a remote dashboard at `http://10.50.50.28:9119` can open authenticated WebSocket terminal endpoints when started with `--insecure`, while defaults remain loopback-only. Validation: RED test reproduced remote PTY 4403 under a public dashboard, focused `TestPtyWebSocket` now `16 passed`, broader dashboard focused tests `26 passed`; live browser smoke on `http://10.50.50.28:9119/chat?profile=hermesfix` opened remote `/api/pty?profile=hermesfix&resume=live-203-decode` and received PTY output with OSC title `Hermes`.

### `204-dashboard-runtime-registry`

Backend registry for live Hermes/TUI/gateway/worker processes.

Scope:

- read-only process/session registry;
- correlate PTY child, profile, cwd, started_at and last_activity;
- expose status without broad shelling out from the frontend;
- initial subagent/delegate visibility hooks where available;
- no kill/restart yet except existing PTY close;
- no argv/env/output/session/log/memory bodies in registry payloads.

Why separate: runtime observability should be a data layer, not only visual terminal tabs.

Status: exported as PatchKit unit `204-dashboard-runtime-registry`; runtime commit `671b540cc`, depends on `200`–`203`. The implementation adds authenticated read-only `/api/dashboard/runtimes`: dashboard process metadata, public/embedded-chat flags, live PTY sessions with profile/cwd/pid/resume/terminal size, action subprocess liveness and event-channel counts. Validation: focused runtime registry tests `3 passed`, broader dashboard focused tests `29 passed`; live browser smoke on `http://10.50.50.28:9119/chat?profile=hermesfix` opened PTY `resume=live-204-registry`, then `/api/dashboard/runtimes` returned a live PTY session with `profile=hermesfix` and no secrets.

### `205-dashboard-worker-roster`

Agent/worker cards and optional roster metadata.

Scope:

- profile-local or project-local roster metadata: role, lane, mission, preferred model, capabilities;
- worker cards: state, active task, active tool, cwd, last output, blocked reason;
- map long-lived tmux/PTY workers to cards;
- no hardcoded `swarm<N>` naming.

Reference: `hermes-workspace` Swarm2 ideas, but without Claude naming and without a global active-profile model.

Status: exported as PatchKit unit `205-dashboard-worker-roster`; runtime commit `9ea912604`, depends on `200`–`204`. The implementation adds authenticated read-only `/api/dashboard/worker-roster`: configured profile-local workers from `dashboard/worker_roster.json` plus live PTY runtime workers from `204`, exposing only safe role/lane/mission/model/capability/process metadata. Validation: focused worker roster tests `3 passed`, broader dashboard focused tests `32 passed`; live dashboard smoke returned `200` with counts `configured_workers=0`, `runtime_workers=2`, `workers=2` and no secrets.

### `206-dashboard-terminal-profile-lifecycle`

Bugfix/control slice for profile terminal identity and close lifecycle.

Scope:

- Open terminal from the Profiles page creates a unique `/chat?profile=<name>&terminal=<id>` channel;
- Chat no longer reuses the default terminal when moving between profiles;
- authenticated `DELETE /api/dashboard/runtimes/pty/{id}` closes exactly one registered PTY session;
- user-facing `Close terminal` closes the current terminal and removes it from the runtime registry;
- close/reopen does not mutate the global active profile.

Status: exported as PatchKit unit `206-dashboard-terminal-profile-lifecycle`; runtime commit `be1ef4e87`, depends on `200`–`205`. Validation: dashboard focused tests `35 passed`, `npm run build` passed, focused eslint passed; live smoke on `http://10.50.50.28:9119/profiles` confirmed `hermesfix` opens as `/chat?profile=hermesfix&terminal=terminal-hermesfix-...`, `/api/dashboard/runtimes` shows a PTY with `profile=hermesfix`, and `Close terminal` removes the session from the registry.

### `207-dashboard-session-log-inspector`

Profile-aware sessions/logs/tools inspector.

Scope:

- browse recent sessions by profile;
- read recent messages/tool calls via Hermes session APIs/state layer;
- logs tail with redaction and source filter;
- links from worker cards to terminal/session/log views;
- safe read-only default.

Reference: admin-ui pages plus the workspace chat-reader idea, implemented through Hermes-native Python APIs.

Status: exported as PatchKit unit `207-dashboard-session-log-inspector`; runtime commit `2205eb455`, depends on `200`–`206`. The implementation adds authenticated read-only `/api/dashboard/profiles/{name}/sessions`, `/sessions/{session_id}` and `/logs`, plus API client/Profile page wiring for `Session inspector` and `Log inspector`. Endpoints expose safe metadata only: session counts, token/cost/api-call metadata, message/tool-call summaries and log-file stats; they do not expose message bodies, raw tool args, system prompts, log contents, env or secrets. Validation: profile inspector focused tests `5 passed`, broader dashboard focused tests `41 passed`, `npm run build` passed, focused eslint passed; live dashboard smoke on `http://10.50.50.28:9119/profiles?profile=hermesfix` confirmed `200` for sessions/logs and no `API_KEY`/`SECRET` payload leaks.

### `208-dashboard-terminal-workspace-tabs`

Follow-up fix for terminal UX after `206`: the dashboard Chat surface is now an App-level multi-terminal workspace.

Scope:

- tab bar for live embedded terminals;
- default Chat terminal and profile terminals remain mounted as separate PTY panes;
- switching tabs changes the active visible terminal without killing hidden terminals;
- profile `Open terminal` adds a unique tab and keeps the existing default/profile tabs alive;
- closing a tab requires confirmation because it really terminates the PTY process;
- confirmed close calls `DELETE /api/dashboard/runtimes/pty/{id}` and removes only that terminal tab/session.

Status: exported as PatchKit unit `208-dashboard-terminal-workspace-tabs`; runtime commit `ead849a5e`, depends on `200`–`207`. Validation: focused tests `44 passed`, `npm run build`, focused ESLint, live smoke on `10.50.50.28:9119` confirmed default + `hermesfix` tabs remain separate, cancel keeps PTYs, confirm close removes only selected PTY.

### `209-dashboard-assembly-analytics`

Profile-aware analytics and whole-assembly summary.

Implemented scope:

- authenticated `/api/dashboard/analytics/assembly?days=<n>` across default + named profiles;
- per-profile safe rollup: sessions, active sessions, input/output/cache/reasoning tokens, estimated/actual cost, API calls, tool calls, provider/model, last activity and stale flag;
- whole-assembly summary: totals, top profiles by activity, stale profiles, model distribution and provider distribution;
- dashboard Analytics page now loads the assembly rollup alongside existing usage analytics and renders a safe per-profile table;
- degraded profiles return per-profile error metadata instead of breaking the whole summary;
- safety boundary: no session IDs, message bodies, prompts, tool arguments, memory bodies, `.env`, auth files, raw log contents or secrets in the analytics payload.

Status: exported as PatchKit unit `209-dashboard-assembly-analytics`; runtime commit `042f10871`, depends on `200`–`208`. Validation: `scripts/run_tests.sh` focused dashboard suite returned `53 passed`; `npm run build`; focused ESLint for `AnalyticsPage.tsx` and `api.ts`; temporary live smoke on `127.0.0.1:9140` returned analytics totals for 4 observed profiles and authenticated/unauthenticated gates behaved correctly.

Why before controlled actions: first we need visibility into load, cost and activity across the whole assembly; otherwise stop/restart/mutation decisions are blind.

### `210-dashboard-controlled-actions`

Careful mutation layer after read-only UI is proven.

Implemented scope:

- authenticated `/api/dashboard/actions` lists allowlisted dashboard mutation actions with labels, descriptions, danger level and exact confirmation string;
- authenticated `/api/dashboard/actions/{id}/run` runs only allowlisted actions after an exact confirmation match;
- current actions are `gateway-restart` and `hermes-update`, reusing the existing detached Hermes action runner and status logs;
- dashboard SystemActions now goes through the controlled action API instead of directly calling the older restart/update endpoints;
- no profile deletion, arbitrary shell, raw argv editor or unlisted action execution.

Status: exported as PatchKit unit `210-dashboard-controlled-actions`; runtime commit `efcb158cb`, depends on `200`–`209`. Validation: `scripts/run_tests.sh` focused dashboard suite returned `53 passed`; `npm run build`; focused ESLint for `SystemActions.tsx` and `api.ts`; temporary live smoke on `127.0.0.1:9140` listed allowlisted `gateway-restart`/`hermes-update` actions and returned 401 without token. No mutation action was executed during smoke.

Why last in the first wave: mutation without observability is dangerous.

### `211-dashboard-control-plane-unification`

Stabilization slice after the first feature wave. This patch is not another isolated widget; it makes the dashboard speak one language.

Implemented scope:

- authenticated `/api/dashboard/overview` becomes the shared read-only semantic contract for control-plane counts and health;
- new `/overview` page is the default dashboard landing route;
- sidebar status strip uses the same overview contract instead of mixing `/api/status` counters with analytics/runtime counters;
- Sessions page labels distinguish current-profile history from live `Active terminals`;
- gateway platform rows now separate `CONNECTED` from stale/attention state;
- bundled `example` dashboard plugin is hidden in production by default and can be enabled only with `HERMES_DASHBOARD_SHOW_EXAMPLES=1|true|yes`;
- safety boundary: overview returns counts and metadata only, without session IDs, message bodies, prompts, tool args/results, env, auth, memory, logs or secrets.

Status: exported as PatchKit unit `211-dashboard-control-plane-unification`; runtime commit `cd84e8812`, depends on `200`–`210`. Validation: focused dashboard suite returned `25 passed`; `npm run build`; focused ESLint for new/touched control-plane files; `py_compile` for `hermes_cli/web_server.py`. Live dashboard smoke after restarting `hermes-dashboard.service` on `10.50.50.28:9119` passed: root and `/api/status` returned 200, unauthenticated `/api/dashboard/overview` returned 401, authenticated overview returned 200 with 4 profiles, 392 sessions, `active_terminals=0`, `platform_attention=4`, and browser smoke showed no example/demo banner.

Why after controlled actions: once enough pieces existed, the user-visible problem was no longer missing functionality but conflicting semantics. This patch makes later visual polish (`212-dashboard-visual-polish`) safe to do without hiding data-model confusion.

## Acceptance criteria for the first milestone

The minimally useful UI milestone is patches `200`–`203`:

- dashboard lists all Hermes profiles correctly;
- user can choose a profile without changing global active profile;
- user can open embedded TUI terminals for at least two different profiles through profile-aware `/chat`/`/api/pty` URLs;
- default old dashboard chat path still works when no profile is selected;
- profile path traversal attempts fail closed;
- terminal spawn does not leak secrets in frontend-visible metadata;
- focused backend/frontend tests pass.

## Verification policy

For every UI patch:

1. focused Python tests through `scripts/run_tests.sh`, not raw pytest;
2. focused frontend tests/typecheck for `web/` or `ui-tui/` if touched;
3. manual dashboard smoke:
   - default profile terminal;
   - named profile terminal;
   - invalid profile rejected;
   - terminal resize still works;
   - existing `/chat` route still works;
4. PatchKit clean apply against `v2026.4.30` before claiming the patch exported;
5. EN/RU docs updated for user-facing behavior.

## Open questions before implementation

- Should the terminal workspace use only the existing `/api/pty`, or introduce a versioned `/api/terminals` wrapper around it?
- Where should long-lived worker roster metadata live: profile config, project `.hermes/`, or dashboard runtime DB?
- How much subagent/delegate_task activity can be exposed from existing process/session state without invasive core changes?
- Should tmux be an optional integration or a first-class supported backend?
- Which parts are upstream-candidate vs local-overlay? Current read: `200`–`204` can be upstream-candidate; `205`–`208` may start as local-overlay until the product shape stabilizes.
