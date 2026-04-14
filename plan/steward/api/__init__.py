from __future__ import annotations

from fastapi import HTTPException

from plan.steward.contracts import ErrorDto


def steward_error(
    status_code: int,
    error: str,
    message: str,
    detail: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorDto(error=error, message=message, detail=detail).model_dump(),
    )


__all__ = [
    "overview",
    "sources",
    "planning",
    "insights",
    "notes",
    "chat",
    "settings",
    "automation",
    "events",
    "steward_error",
]
