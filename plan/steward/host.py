from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import FastAPI
import uvicorn

from plan.steward.adapters.lazy_zju import LazyZjuAdapter
from plan.steward.adapters.obsidian import ObsidianAdapter
from plan.steward.adapters.work_review import WorkReviewAdapter
from plan.config import resolve_path
from plan.steward.config import (
    StewardSettings,
    load_settings,
)
from plan.steward.events import EventBus
from plan.steward.modules.automation import AutomationRunner, AutomationService
from plan.steward.modules.chat import ChatService
from plan.steward.modules.insights import InsightsService
from plan.steward.modules.notes import NotesService
from plan.steward.modules.overview import OverviewService
from plan.steward.modules.planning import PlanningService
from plan.steward.modules.sources import SourcesService


@dataclass(slots=True)
class AppContainer:
    settings: StewardSettings
    event_bus: EventBus
    planning: PlanningService
    sources: SourcesService
    insights: InsightsService
    notes: NotesService
    chat: ChatService
    automation: AutomationService
    overview: OverviewService
    runner: AutomationRunner
    lazy_zju_adapter: LazyZjuAdapter
    work_review_adapter: WorkReviewAdapter
    obsidian_adapter: ObsidianAdapter | None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _build_container(
    settings: StewardSettings,
    *,
    event_bus: EventBus | None = None,
    chat: ChatService | None = None,
) -> AppContainer:
    event_bus = event_bus or EventBus()
    planning = PlanningService()
    lazy_adapter = LazyZjuAdapter()
    sources = SourcesService(lazy_adapter)
    work_review = WorkReviewAdapter(settings.work_review_root)
    notes_adapter = None
    if settings.obsidian_vault_root is not None:
        notes_adapter = ObsidianAdapter(
            settings.obsidian_vault_root,
            settings.obsidian_generated_dir,
        )
    notes = NotesService(notes_adapter)
    insights = InsightsService(work_review, planning)
    chat = chat or ChatService()
    automation = AutomationService(
        check_in_hours=settings.automation_check_in_hours,
        history_path=resolve_path("tasks").parent / "steward_automation_history.json",
    )
    overview = OverviewService(planning, sources, insights, notes)
    runner = AutomationRunner(
        automation=automation,
        event_bus=event_bus,
        interval_seconds=300,
    )
    return AppContainer(
        settings=settings,
        event_bus=event_bus,
        planning=planning,
        sources=sources,
        insights=insights,
        notes=notes,
        chat=chat,
        automation=automation,
        overview=overview,
        runner=runner,
        lazy_zju_adapter=lazy_adapter,
        work_review_adapter=work_review,
        obsidian_adapter=notes_adapter,
    )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    container: AppContainer = app.state.container
    container.runner.start()
    container.event_bus.publish("host.started", {"status": "ok"})
    yield
    container.event_bus.publish("host.stopping", {"status": "graceful"})
    await container.runner.stop()


def create_app(settings: StewardSettings | None = None) -> FastAPI:
    from plan.steward.api import (
        automation,
        chat,
        events,
        insights,
        notes,
        overview,
        planning,
        sources,
    )
    from plan.steward.api import settings as settings_api

    resolved_settings = settings or load_settings()
    container = _build_container(resolved_settings)
    app = FastAPI(title="Plan Steward Host", lifespan=_lifespan)
    app.state.container = container

    @app.get("/health", tags=["host"])
    def health():
        c: AppContainer = app.state.container
        return {"status": "ok", "version": "1.0.0", "api_version": "v1", "started_at": c.started_at}

    # v1 routes (canonical)
    app.include_router(overview.router, prefix="/v1")
    app.include_router(sources.router, prefix="/v1")
    app.include_router(planning.router, prefix="/v1")
    app.include_router(insights.router, prefix="/v1")
    app.include_router(notes.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(settings_api.router, prefix="/v1")
    app.include_router(automation.router, prefix="/v1")
    app.include_router(events.router, prefix="/v1")

    # legacy routes (no prefix, backward compat)
    app.include_router(overview.router)
    app.include_router(sources.router)
    app.include_router(planning.router)
    app.include_router(insights.router)
    app.include_router(notes.router)
    app.include_router(chat.router)
    app.include_router(settings_api.router)
    app.include_router(automation.router)
    app.include_router(events.router)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Plan Steward backend host.")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    settings = load_settings()
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
        settings.backend_url = f"http://{settings.host}:{settings.port}"
    app = create_app(settings)
    config = uvicorn.Config(app, host=settings.host, port=settings.port)
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
