using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class SettingsConfig
{
    [JsonPropertyName("work_review_root")]
    public string WorkReviewRoot { get; set; } = string.Empty;

    [JsonPropertyName("obsidian_vault_root")]
    public string? ObsidianVaultRoot { get; set; }

    [JsonPropertyName("obsidian_generated_dir")]
    public string ObsidianGeneratedDir { get; set; } = "Steward/Daily";

    [JsonPropertyName("automation_check_in_hours")]
    public int AutomationCheckInHours { get; set; } = 2;
}
