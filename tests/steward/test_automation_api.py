import asyncio

from fastapi.testclient import TestClient


def test_automation_status_and_event_stream(steward_env):
    settings, _, _ = steward_env

    from plan.steward.host import create_app
    from plan.steward.contracts import SourceItemDto

    def fake_fetch_items(self):
        return [
            SourceItemDto(
                title="Lab 3",
                source="lazy_zju",
                due="2026-04-15",
                project="courses",
                priority=2,
                external_id="assignment_42",
            )
        ]

    import plan.steward.adapters.lazy_zju as lazy_module
    original_fetch_items = lazy_module.LazyZjuAdapter.fetch_items
    lazy_module.LazyZjuAdapter.fetch_items = fake_fetch_items

    try:
        app = create_app(settings)
        client = TestClient(app)
        status = client.get("/automation/status", params={"now": "2026-04-14T12:00:00"})

        assert status.status_code == 200
        assert status.json()["check_in_hours"] == 2
        assert status.json()["pending_interventions_count"] == 4
        assert "2-hour cadence" in status.json()["mode_summary"]
        assert any(signal["kind"] == "scheduled_check_in" for signal in status.json()["signals"])
        assert any(signal["kind"] == "new_source_items" for signal in status.json()["signals"])
        assert any(signal["kind"] == "backlog_pressure" for signal in status.json()["signals"])
        assert any(signal["kind"] == "review_gap" for signal in status.json()["signals"])
        assert status.json()["guardrails"]["auto_complete"] is False

        async def scenario():
            async def never_disconnected():
                return False

            stream = app.state.container.event_bus.stream(
                is_disconnected=never_disconnected,
                heartbeat_seconds=60,
            )
            connected = await anext(stream)
            replayed = await anext(stream)
            await stream.aclose()
            return connected, replayed

        connected, replayed = asyncio.run(scenario())

        assert "event: connected" in connected
        assert "event: automation.status_checked" in replayed
        assert '"signal_count": 4' in replayed
    finally:
        lazy_module.LazyZjuAdapter.fetch_items = original_fetch_items
