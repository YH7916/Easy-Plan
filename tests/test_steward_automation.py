from datetime import datetime, timezone


def test_automation_service_emits_scheduled_and_focus_signals():
    from plan.steward.modules.automation import AutomationService

    service = AutomationService(check_in_hours=2)
    signals = service.evaluate_signals(
        now=datetime(2026, 4, 13, 12, 0, tzinfo=timezone.utc),
        new_source_items=2,
        backlog_pressure=True,
        focus_drift=True,
        last_check_in=datetime(2026, 4, 13, 9, 30, tzinfo=timezone.utc),
    )

    kinds = {signal.kind for signal in signals}
    assert "scheduled_check_in" in kinds
    assert "new_source_items" in kinds
    assert "backlog_pressure" in kinds
    assert "focus_drift" in kinds
    assert all(signal.guardrails.auto_complete is False for signal in signals)
