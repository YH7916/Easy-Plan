import asyncio


def test_event_bus_replays_history_and_emits_live_packets():
    from plan.steward.events import EventBus

    async def scenario():
        bus = EventBus()
        bus.publish("planning.task_created", {"title": "Finish backend host"})

        async def never_disconnected():
            return False

        stream = bus.stream(is_disconnected=never_disconnected, heartbeat_seconds=60)

        connected = await anext(stream)
        replayed = await anext(stream)

        assert "event: connected" in connected
        assert "event: planning.task_created" in replayed
        assert "Finish backend host" in replayed

        bus.publish("planning.task_completed", {"title": "Finish backend host"})
        live_packet = await anext(stream)

        assert "event: planning.task_completed" in live_packet
        assert "Finish backend host" in live_packet

        await stream.aclose()

    asyncio.run(scenario())
