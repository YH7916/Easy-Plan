using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class NotesDashboard
{
    [JsonPropertyName("vault_ready")]
    public bool VaultReady { get; set; }

    [JsonPropertyName("indexed_count")]
    public int IndexedCount { get; set; }

    [JsonPropertyName("generated_count")]
    public int GeneratedCount { get; set; }

    [JsonPropertyName("recent_notes")]
    public List<NoteItem> RecentNotes { get; set; } = [];

    [JsonPropertyName("generated_notes")]
    public List<NoteItem> GeneratedNotes { get; set; } = [];
}
