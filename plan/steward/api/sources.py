from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Request

from plan.steward.contracts import SourcesDashboardDto, SourceItemDto, AdapterAvailabilityDto

router = APIRouter(prefix="/sources")


def _current(request: Request):
    return request.app.state.container


@router.get("/items", response_model=list[SourceItemDto])
def source_items(request: Request):
    return _current(request).sources.list_items()


@router.get("/dashboard", response_model=SourcesDashboardDto)
def sources_dashboard(request: Request, today: str | None = None):
    resolved_today = date.fromisoformat(today) if today else None
    return _current(request).sources.dashboard(
        _current(request).planning.list_tasks(),
        today=resolved_today,
    )


@router.get("/adapters", response_model=list[AdapterAvailabilityDto])
def adapters_availability(request: Request):
    container = _current(request)
    results: list[AdapterAvailabilityDto] = []

    lazy = container.lazy_zju_adapter.availability()
    results.append(AdapterAvailabilityDto(name="lazy_zju", **lazy))

    work_review = container.work_review_adapter.availability()
    results.append(AdapterAvailabilityDto(name="work_review", **work_review))

    if container.obsidian_adapter is not None:
        obsidian = container.obsidian_adapter.availability()
        results.append(AdapterAvailabilityDto(name="obsidian", **obsidian))
    else:
        results.append(AdapterAvailabilityDto(name="obsidian", status="not_configured", reason=None))

    return results
