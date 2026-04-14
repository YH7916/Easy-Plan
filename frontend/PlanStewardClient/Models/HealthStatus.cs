using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class HealthStatus
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("backend_url")]
    public string BackendUrl { get; set; } = string.Empty;

    [JsonPropertyName("modules")]
    public List<string> Modules { get; set; } = [];

    [JsonPropertyName("work_review_root")]
    public string WorkReviewRoot { get; set; } = string.Empty;

    [JsonPropertyName("obsidian_vault_root")]
    public string? ObsidianVaultRoot { get; set; }
}
