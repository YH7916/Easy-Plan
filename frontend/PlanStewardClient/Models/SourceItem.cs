using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class SourceItem
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("source")]
    public string Source { get; set; } = string.Empty;

    [JsonPropertyName("due")]
    public string? Due { get; set; }

    [JsonPropertyName("project")]
    public string? Project { get; set; }

    [JsonPropertyName("priority")]
    public int Priority { get; set; }

    [JsonPropertyName("external_id")]
    public string? ExternalId { get; set; }
}
