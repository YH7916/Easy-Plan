using System.Text.Json;

namespace PlanStewardClient.Models;

public sealed class BackendEvent
{
    public string EventType { get; init; } = string.Empty;

    public JsonElement Payload { get; init; }

    public DateTimeOffset ReceivedAt { get; init; } = DateTimeOffset.UtcNow;
}
