using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class NoteItem
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("path")]
    public string Path { get; set; } = string.Empty;

    [JsonPropertyName("obsidian_url")]
    public string ObsidianUrl { get; set; } = string.Empty;

    [JsonPropertyName("modified_at")]
    public double ModifiedAt { get; set; }
}

public sealed class NotesIndexResponse
{
    [JsonPropertyName("notes")]
    public List<NoteItem> Notes { get; set; } = [];
}
