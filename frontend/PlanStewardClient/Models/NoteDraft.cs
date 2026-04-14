using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class NoteDraft
{
    [JsonPropertyName("path")]
    public string Path { get; set; } = string.Empty;

    [JsonPropertyName("obsidian_url")]
    public string ObsidianUrl { get; set; } = string.Empty;
}
