using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class TaskItem
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("project")]
    public string? Project { get; set; }

    [JsonPropertyName("priority")]
    public int Priority { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("source")]
    public string Source { get; set; } = string.Empty;

    [JsonPropertyName("ticktick_id")]
    public string? TickTickId { get; set; }

    [JsonPropertyName("due")]
    public string? Due { get; set; }

    [JsonPropertyName("time_block")]
    public string? TimeBlock { get; set; }
}
