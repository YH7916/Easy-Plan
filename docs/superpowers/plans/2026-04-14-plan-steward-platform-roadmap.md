# Plan Steward Platform Consolidation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a finite, healthy v1 of Plan Steward as a Windows local-first execution steward with a decoupled Python backend, a WinUI 3 client shell, stable adapters, and a codebase structure that can continue to evolve without turning into a monolith.

**Architecture:** Keep the backend as the single owner of state, adapters, automation, and orchestration. Keep WinUI as a thin reactive shell over HTTP plus SSE. Before adding more end-user features, split oversized route, page, client, and test files so module boundaries stay explicit and future macOS work can reuse the same backend contract instead of copying Windows UI code.

**Tech Stack:** Python 3.13, FastAPI, pytest, WinUI 3, Windows App SDK, .NET 10, xUnit, local file-backed adapters for LazyZJU, Work_Review, and Obsidian

---

## 1. Current State Snapshot

### Already in place

- Local backend host exists and exposes grouped routes for:
  - `overview`
  - `sources`
  - `planning`
  - `insights`
  - `notes`
  - `chat`
  - `automation`
  - `settings`
- WinUI shell exists with navigation-based pages for the core modules.
- SSE live event stream already works end-to-end.
- Adapters already exist for:
  - `LazyZJU`
  - `Work_Review`
  - `Obsidian`
- Obsidian detection, configuration, generated draft writing, and deep-link flows already work.
- Overview handoff flows already exist between:
  - `Overview -> Planning`
  - `Overview -> Insights`
  - `Overview -> Notes`
  - `Overview -> Chat`
- Test coverage already exists for backend routes and WinUI transport.

### Current structural pressure points

- `D:\Plan\plan\steward\host.py` is already `554` lines and is acting as too much of the backend composition root plus route host.
- `D:\Plan\frontend\PlanStewardClient\BackendApiClient.cs` is already `348` lines and is becoming a transport god-object.
- Several WinUI pages are too large for long-term health:
  - `D:\Plan\frontend\PlanStewardWinUI\Pages\HomePage.xaml.cs` -> `355` lines
  - `D:\Plan\frontend\PlanStewardWinUI\Pages\NotesPage.xaml.cs` -> `407` lines
  - `D:\Plan\frontend\PlanStewardWinUI\Pages\SettingsPage.xaml.cs` -> `316` lines
  - `D:\Plan\frontend\PlanStewardWinUI\Pages\InsightsPage.xaml.cs` -> `294` lines
- Two test files are already oversized:
  - `D:\Plan\tests\test_steward_api.py` -> `860` lines
  - `D:\Plan\frontend\PlanStewardWinUI.Tests\BackendApiClientTests.cs` -> `947` lines
- Repo-root runtime artifacts now exist and should not keep growing there:
  - `steward-host.stdout.log`
  - `steward-host.stderr.log`
  - `temp-obsidian-vault.json`

### Conclusion

The product is no longer in “bootstrap” state. It has entered the stage where structural consolidation must happen before significant new feature growth, or the frontend shell and backend host will both become hard to evolve.

---

## 2. v1 Scope Freeze

This is the fixed scope for v1. Anything outside this list is deferred by default.

### v1 must include

- A stable local backend host with decoupled module APIs and SSE events.
- A WinUI 3 navigation shell that consumes the backend contract only.
- Working modules for:
  - `Overview`
  - `Sources`
  - `Planning`
  - `Insights`
  - `Notes`
  - `Chat`
  - `Settings`
  - `Automation`
- Reused integrations through adapters only:
  - `LazyZJU`
  - `Work_Review`
  - `Obsidian`
- A real automation loop for:
  - morning planning
  - evening review
  - periodic daytime check-ins
- Stable configuration and backend lifecycle handling.
- A clean enough backend contract that a future macOS client can reuse it directly.

### v1 explicitly does not include

- A cloud backend
- Multi-user support
- Obsidian in-app editing
- Rewriting `Work_Review` into an in-house tracker
- Rewriting `LazyZJU` logic when an adapter is enough
- A separate plugin marketplace or general plugin runtime
- macOS UI implementation
- Arbitrarily adding new tabs or new top-level modules

### Feature admission rule for the rest of v1

No new top-level capability enters v1 unless it fits inside one of the eight existing modules. If a request does not map cleanly to those modules, it goes to deferred backlog by default.

---

## 3. Code Health Guardrails

These are project rules, not optional polish.

### Boundary rules

- WinUI never reads or writes domain files directly.
- Adapters remain backend-only.
- Modules communicate through services and contracts, not through each other’s files or storage.
- Frontend pages do not synthesize business logic that the backend could own.
- The HTTP contract remains the only cross-platform UI contract.

### File-shape targets

- Backend route files should stay under roughly `200-250` lines.
- Backend module service files should stay under roughly `200` lines unless they are pure orchestration.
- WinUI page code-behind files should stay under roughly `200-250` lines.
- HTTP client files should be split by module once they exceed roughly `250` lines.
- Test files should be split by module or behavior once they exceed roughly `300-400` lines.

These are not dogma, but any planned work that pushes beyond them must include a split task.

### Repo hygiene rules

- Runtime logs, temp JSON payloads, and ad hoc diagnostics should not accumulate at repo root.
- Generated build outputs remain ignored and out of planning scope.
- Every phase that changes architecture must include route tests or transport tests.
- Every new backend capability must define:
  - route
  - service method
  - DTO or response shape
  - test coverage

---

## 4. Target End-State Structure

This is the structure v1 should move toward before feature-complete signoff.

### Backend target

```text
plan/steward/
  app.py
  container.py
  config.py
  contracts/
    __init__.py
    overview.py
    sources.py
    planning.py
    insights.py
    notes.py
    chat.py
    automation.py
    settings.py
  api/
    __init__.py
    overview.py
    sources.py
    planning.py
    insights.py
    notes.py
    chat.py
    automation.py
    settings.py
    events.py
  adapters/
    lazy_zju.py
    work_review.py
    obsidian.py
  modules/
    overview.py
    sources.py
    planning.py
    insights.py
    notes.py
    chat.py
    automation.py
```

### Frontend target

```text
frontend/
  PlanStewardClient/
    Clients/
      OverviewClient.cs
      SourcesClient.cs
      PlanningClient.cs
      InsightsClient.cs
      NotesClient.cs
      ChatClient.cs
      AutomationClient.cs
      SettingsClient.cs
      EventsClient.cs
    Models/
      ...
  PlanStewardWinUI/
    Navigation/
      NavigationRegistry.cs
    Services/
      BackendServices.cs
      BackendHostSupervisor.cs
    Pages/
      Home/
      Sources/
      Planning/
      Insights/
      Notes/
      Chat/
      Settings/
    ViewModels/
      ...
    Controls/
      ...
```

### Test target

```text
tests/
  steward/
    test_overview_api.py
    test_sources_api.py
    test_planning_api.py
    test_insights_api.py
    test_notes_api.py
    test_chat_api.py
    test_automation_api.py
    test_settings_api.py

frontend/PlanStewardWinUI.Tests/
  OverviewClientTests.cs
  SourcesClientTests.cs
  PlanningClientTests.cs
  InsightsClientTests.cs
  NotesClientTests.cs
  ChatClientTests.cs
  AutomationClientTests.cs
  SettingsClientTests.cs
  EventsClientTests.cs
```

---

## 5. Full v1 Roadmap

This is the finite sequence to finish v1 without uncontrolled growth.

### Phase 0: Structural Consolidation

**Purpose:** Stop the codebase from inflating before adding more behavior.

**Deliverables**

- Split backend route registration out of `host.py`.
- Split `contracts.py` by module.
- Split `BackendApiClient.cs` into module-scoped clients or partials.
- Split large WinUI page code-behind files by introducing:
  - page-specific view models
  - reusable section controls
  - shared navigation helpers
- Split oversized backend and client test files by module.
- Move repo-root runtime artifacts into a dedicated diagnostics or temp location and ignore them properly.

**Definition of done**

- No route host file is acting as both app factory and full API surface.
- No single test file exceeds the agreed budget unless explicitly justified.
- Navigation and transport responsibilities are explicit and discoverable.
- The project structure makes it obvious where to add a new route, page, or DTO without touching unrelated files.

### Phase 1: Backend Platform Hardening

**Purpose:** Finish the backend as a real local platform, not just a growing script host.

**Deliverables**

- Standardize route-level error payloads.
- Add backend contract versioning or capability metadata.
- Normalize SSE event naming and payload shape.
- Add a single host lifecycle model:
  - start
  - health check
  - reconnect
  - shutdown
- Add adapter availability and degradation states.
- Make automation status and intervention history persist cleanly.

**Definition of done**

- The backend can be treated as a stable local service by any UI shell.
- Every module exposes a consistent route shape and error shape.
- Frontend code no longer needs ad hoc handling for inconsistent backend behavior.

### Phase 2: Frontend Shell Consolidation

**Purpose:** Keep WinUI thin, modular, and maintainable.

**Deliverables**

- Replace large page code-behind logic with small view models or presenters.
- Add a central navigation registry so Overview handoffs and page routing do not hardcode page resolution in multiple places.
- Add shared components for:
  - metric cards
  - action cards
  - empty states
  - setup guidance panels
- Introduce a backend connection state service used by all pages.
- Add a host supervisor for backend startup and reconnection, or explicitly keep backend external and document that choice.

**Definition of done**

- Pages mostly orchestrate UI state and command wiring.
- Repeated UI shell behavior lives in reusable controls or services.
- Future macOS work can mirror the shell behavior from the backend contract rather than from WinUI implementation details.

### Phase 3: Complete Core Module Behaviors

**Purpose:** Finish the eight fixed modules to a coherent v1 feature set.

**Deliverables by module**

- `Overview`
  - real command-center cards
  - safe direct actions
  - clear backlog, intake, and review pressure signals
  - no duplicate recommendations once a draft or action already exists
- `Sources`
  - normalized source item dashboard
  - status grouping
  - due pressure
  - change detection since last review
- `Planning`
  - unified task pool
  - intake review
  - high-priority queue
  - today queue
  - time-block recommendations
  - explicit task state transitions
- `Insights`
  - daily report
  - weekly report
  - focus anomalies
  - summary surfaces derived from Work_Review rather than mirrored directly
- `Notes`
  - vault dashboard
  - generated-note lifecycle
  - related-note surfacing
  - safe deep-link navigation
- `Chat`
  - stable session retrieval
  - starter prompts from real state
  - safe action execution
  - graceful failure when upstream chat generation is unavailable
- `Settings`
  - editable configuration
  - adapter setup
  - validation
  - path selection helpers
  - health and test-connect flows
- `Automation`
  - scheduled morning planning
  - scheduled evening review
  - daytime check-ins
  - intervention log
  - guardrail-preserving suggestion updates

**Definition of done**

- Each module is useful on its own.
- Cross-module handoffs are real but still respect boundaries.
- No module requires frontend-side domain hacks to feel complete.

### Phase 4: Automation Runtime and Steward Behavior

**Purpose:** Make the system proactive in a controlled way.

**Deliverables**

- Background automation runner with a clear lifecycle.
- Persistent intervention history and last-run state.
- Trigger handling for:
  - new source pressure
  - task backlog pressure
  - focus anomalies
  - scheduled check-ins
- Guardrails that prevent:
  - auto-completing tasks
  - deleting records
  - overwriting user-authored note content

**Definition of done**

- The product behaves like an active steward instead of a passive dashboard.
- Automation is inspectable, interruptible, and bounded by explicit rules.

### Phase 5: Reliability, Testing, and Release Readiness

**Purpose:** Make v1 shippable instead of merely demoable.

**Deliverables**

- Backend tests organized by module and adapter.
- WinUI transport tests organized by client/module.
- Basic UI smoke tests with mocked backend where appropriate.
- End-to-end smoke flows for:
  - launch shell
  - load overview
  - write daily review
  - reopen existing draft
  - accept source suggestion
  - edit settings
- Packaging and local release instructions for the WinUI app.
- Startup diagnostics and recovery guidance.

**Definition of done**

- Fresh-machine or fresh-session usage is documented and reproducible.
- Regressions in core flows are caught by tests before manual verification.
- WinUI build, launch, and backend health checks are part of the release checklist.

### Phase 6: Contract Freeze for Future macOS Client

**Purpose:** Prepare for a second client without starting it yet.

**Deliverables**

- Freeze the backend DTO and route surface for v1.
- Document the UI-agnostic contract.
- Remove any backend assumptions that leak WinUI-specific concepts.
- Define a compatibility policy for future client versions.

**Definition of done**

- Building a macOS client would be a client implementation task, not a backend redesign task.

---

## 6. What Still Remains After Today

This is the practical “remaining work” list after the current implementation state.

### Must do before calling v1 complete

- Structural split of `host.py`
- Structural split of `BackendApiClient.cs`
- Structural split of oversized WinUI page code-behind files
- Split monolithic test files
- Single backend host lifecycle handling
- Real automation runtime
- Chat degradation and retry strategy
- Planning “today queue” and time-block workflow
- Weekly insights and anomaly summaries
- Settings validation and path-picking UX
- Packaging and release checklist
- Contract freeze documentation

### Nice to have, but not required for v1

- Richer visual polish across pages
- More source adapters beyond the current three
- In-app charts beyond basic textual insight summaries
- Advanced note graphing
- macOS client implementation

---

## 7. Phase Order Recommendation

This is the recommended order. Do not skip ahead.

1. `Phase 0: Structural Consolidation`
2. `Phase 1: Backend Platform Hardening`
3. `Phase 2: Frontend Shell Consolidation`
4. `Phase 3: Complete Core Module Behaviors`
5. `Phase 4: Automation Runtime and Steward Behavior`
6. `Phase 5: Reliability, Testing, and Release Readiness`
7. `Phase 6: Contract Freeze for Future macOS Client`

This order exists to keep the codebase clean while features are finished. Doing Phase 3 or Phase 4 first would keep producing short-term wins while making the repo harder to maintain.

---

## 8. Acceptance Criteria for v1

v1 is complete only when all of the following are true:

- The WinUI app is a thin shell over the backend contract.
- The backend is the only owner of product logic and integrations.
- The eight module surfaces are complete enough for daily personal use.
- Automation runs proactively but safely.
- Existing drafts, tasks, and source states are stateful and reusable across sessions.
- The repo layout is understandable and modular.
- No critical file remains monolithic without a justified reason.
- Core backend and frontend flows are covered by tests.
- The backend contract is ready for a future macOS client.

---

## 9. Immediate Next Execution Plan

This is the next concrete execution sequence implied by the roadmap.

1. Execute `Phase 0` first.
2. Do not add any new top-level feature before `Phase 0` is done.
3. When `Phase 0` is complete, execute `Phase 1` and `Phase 2` in close succession.
4. Only then resume remaining feature-completion work in `Phase 3`.

The main anti-bloat rule for the rest of the project is simple:

> No new feature slice lands unless its destination structure already exists and stays within the module and file-shape guardrails above.
