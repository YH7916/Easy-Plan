# Plan Agent CLI — Design Spec

**Date:** 2026-04-12  
**Status:** Approved

## Overview

A personal AI-powered planning CLI that acts as an intelligent layer on top of TickTick. It maintains persistent memory about the user's goals and context, analyzes their situation using Claude API, generates daily time-blocked plans, and optionally syncs with TickTick. Designed to run on Windows with Task Scheduler for daily automation.

---

## Architecture

Single Python package (`plan`) installed locally via `pip install -e .`. No daemon process required — daily automation is handled by Windows Task Scheduler with "run on missed schedule" enabled.

```
D:\Plan\
├── plan/
│   ├── __init__.py
│   ├── cli.py          # Click command definitions
│   ├── agent.py        # Claude API calls, analysis logic
│   ├── memory.py       # Read/write profile.md and context.md
│   ├── ticktick.py     # TickTick sync via ticktick-py (optional)
│   ├── scheduler.py    # Register/update Windows Task Scheduler entry
│   └── sources/        # Pluggable data source adapters
│       ├── __init__.py     # BaseSource ABC + source registry
│       ├── ticktick.py     # TickTick adapter (moved here)
│       └── example.py      # Template for new sources
├── data/
│   ├── profile.md      # Persistent memory: background, goals, constraints
│   ├── context.md      # AI-maintained current state analysis (auto-updated)
│   └── tasks.json      # Local task store (TickTick mirror + local tasks)
├── config.toml         # All user-configurable settings
├── pyproject.toml
└── .env                # API keys (gitignored)
```

---

## Configuration

All behavior is configurable via `config.toml`. No hardcoded values.

```toml
[ai]
provider = "claude"                  # future: openai, gemini, ollama
model = "claude-sonnet-4-6"
api_key_env = "ANTHROPIC_API_KEY"

[schedule]
daily_time = "08:00"                 # time for daily auto-run
enabled = true
run_on_missed = true                 # passed to Task Scheduler

[ticktick]
enabled = false
username = ""
password_env = "TICKTICK_PASSWORD"   # never store password in config file

[paths]
profile = "data/profile.md"
context = "data/context.md"
tasks = "data/tasks.json"

[projects]
# user-defined project areas for goal tracking
# e.g. ["internship", "research", "courses", "health"]
areas = []
```

Change any value via CLI:
```
plan config set schedule.daily_time 09:30
plan config set ticktick.enabled true
```

---

## Commands

### Core

| Command | Description |
|---|---|
| `plan chat` | Conversational input: tell AI your current state, it updates `context.md` |
| `plan analyze` | AI reads profile + context + tasks → generates updated plan |
| `plan daily` | `analyze` + `sync` combined; this is what Task Scheduler calls |
| `plan status` | Show current context summary and today's plan |

### Tasks

| Command | Description |
|---|---|
| `plan task add "title" --project X --due YYYY-MM-DD` | Add a task |
| `plan task list [--project X] [--today]` | List tasks |
| `plan task done <id>` | Mark complete |

### Sync & Config

| Command | Description |
|---|---|
| `plan sync` | Manual TickTick bidirectional sync |
| `plan config set <key> <value>` | Update a config value |
| `plan schedule install` | Register daily task in Windows Task Scheduler |
| `plan schedule uninstall` | Remove scheduled task |

---

## Data Flow

```
profile.md  (persistent, user-edited + AI-updated)
    │
    ├──→ agent.py ──→ Claude API
    │                     │
context.md  (AI-maintained, updated after each chat/analyze)
    │                     │
tasks.json  ←─────────────┘ (AI writes plan as tasks)
    │
    └──→ ticktick.py ──→ TickTick (if enabled)
```

### Memory model

- **`profile.md`** — Long-term memory. Contains: user background, active project areas, goals (short/mid/long term), known constraints (schedule, energy patterns). AI updates this file when significant new information is learned. User can also edit directly.
- **`context.md`** — Short-to-medium term state. Contains: current week's focus, recent blockers, mood/energy notes, upcoming deadlines. AI rewrites this after each `chat` or `analyze` run.
- **`tasks.json`** — Structured task data. Schema: `{id, title, project, due, priority, status, source, ticktick_id}`. `source` is `"local"` or `"ticktick"`.

---

## AI Analysis Logic (`agent.py`)

On each `analyze` call:

1. Load `profile.md`, `context.md`, `tasks.json`
2. Build a prompt with: user context, all open tasks grouped by project area, today's date
3. Ask Claude to:
   - Identify the most important 3-5 tasks for today
   - Generate a time-blocked schedule (e.g., 9:00-10:30 task A, 14:00-15:00 task B)
   - Flag any overdue or neglected items
   - Update `context.md` with any new insights
4. Write the time-blocked plan back to `tasks.json` as today's tasks
5. If TickTick enabled, sync

The prompt is templated and stored in `plan/prompts/analyze.txt` so the user can customize it.

---

## TickTick Sync (`ticktick.py`)

Uses `ticktick-py` library. Sync strategy:

- **Pull first**: fetch all TickTick tasks → merge into `tasks.json` (TickTick wins on conflict for tasks that originated there)
- **Push second**: push local tasks (source=`"local"`) to TickTick, update `ticktick_id`
- Deleted tasks: if a task is marked done locally, mark done in TickTick; vice versa

TickTick credentials: username in `config.toml`, password in `.env` as `TICKTICK_PASSWORD`.

---

## Scheduling (Windows Task Scheduler)

`plan schedule install` creates a Task Scheduler entry:
- Trigger: daily at `config.schedule.daily_time`
- Action: `plan daily`
- Settings: "Run task as soon as possible after a scheduled start is missed" = enabled
- Working directory: `D:\Plan`

---

## Dependencies

```
click          # CLI framework
anthropic      # Claude API
ticktick-py    # TickTick integration (optional)
tomllib        # config parsing (stdlib in Python 3.11+)
python-dotenv  # .env loading
```

---

## Data Source Plugin Interface

All external data sources (TickTick, school homework CLI, calendar, etc.) implement a common `BaseSource` ABC defined in `plan/sources/__init__.py`:

```python
class BaseSource(ABC):
    name: str           # unique identifier, e.g. "ticktick", "school"
    enabled: bool       # from config

    @abstractmethod
    def fetch(self) -> list[SourceItem]:
        """Pull data from the source. Returns normalized items."""

    @abstractmethod
    def push(self, tasks: list[Task]) -> None:
        """Push plan tasks back to the source (no-op if read-only)."""

    @property
    def is_writable(self) -> bool:
        return False    # override to True for bidirectional sources
```

`SourceItem` is a normalized schema that all sources map to:
```python
@dataclass
class SourceItem:
    title: str
    due: date | None
    project: str | None
    priority: int           # 0-3
    source: str             # source name
    external_id: str | None # ID in the external system
    raw: dict               # original data, passed to AI as extra context
```

### Adding a new source

1. Create `plan/sources/myschool.py` implementing `BaseSource`
2. Add a `[sources.myschool]` section to `config.toml`
3. Register it: `plan source add myschool`

The `agent.py` `analyze` loop automatically calls `fetch()` on all enabled sources and includes their items in the AI prompt. No changes needed to core logic.

### Config example

```toml
[sources.ticktick]
enabled = true
writable = true

[sources.school]
enabled = false
cli_command = "school homework list --json"   # shell command that returns JSON
writable = false
```

For shell-command-based sources (like a school homework CLI), a generic `ShellSource` adapter is provided — just point it at a command that outputs JSON matching `SourceItem` schema.

---

## Out of Scope (v1)

- Web UI
- Multi-user support
- Mobile notifications
- Calendar integration (Google Calendar, etc.)
- Cloud deployment / server hosting
