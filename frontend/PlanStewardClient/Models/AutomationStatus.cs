using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class AutomationStatus
{
    [JsonPropertyName("check_in_hours")]
    public int CheckInHours { get; set; }

    [JsonPropertyName("mode_summary")]
    public string ModeSummary { get; set; } = string.Empty;

    [JsonPropertyName("pending_interventions_count")]
    public int PendingInterventionsCount { get; set; }

    [JsonPropertyName("guardrails")]
    public AutomationGuardrails Guardrails { get; set; } = new();

    [JsonPropertyName("signals")]
    public List<AutomationSignal> Signals { get; set; } = [];
}

public sealed class AutomationGuardrails
{
    [JsonPropertyName("auto_complete")]
    public bool AutoComplete { get; set; }

    [JsonPropertyName("delete_content")]
    public bool DeleteContent { get; set; }

    [JsonPropertyName("overwrite_user_notes")]
    public bool OverwriteUserNotes { get; set; }
}

public sealed class AutomationSignal
{
    [JsonPropertyName("kind")]
    public string Kind { get; set; } = string.Empty;

    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty;

    [JsonPropertyName("guardrails")]
    public AutomationGuardrails Guardrails { get; set; } = new();
}
