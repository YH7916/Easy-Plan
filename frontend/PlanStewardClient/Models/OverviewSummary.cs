using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class OverviewSummary
{
    [JsonPropertyName("open_task_count")]
    public int OpenTaskCount { get; set; }

    [JsonPropertyName("high_priority_open_count")]
    public int HighPriorityOpenCount { get; set; }

    [JsonPropertyName("source_item_count")]
    public int SourceItemCount { get; set; }

    [JsonPropertyName("pending_intake_count")]
    public int PendingIntakeCount { get; set; }

    [JsonPropertyName("due_soon_source_count")]
    public int DueSoonSourceCount { get; set; }

    [JsonPropertyName("overdue_source_count")]
    public int OverdueSourceCount { get; set; }

    [JsonPropertyName("notes_indexed_count")]
    public int NotesIndexedCount { get; set; }

    [JsonPropertyName("has_daily_report")]
    public bool HasDailyReport { get; set; }

    [JsonPropertyName("active_alerts")]
    public List<string> ActiveAlerts { get; set; } = [];

    [JsonPropertyName("daily_brief")]
    public string DailyBrief { get; set; } = string.Empty;

    [JsonPropertyName("focus_apps")]
    public List<string> FocusApps { get; set; } = [];

    [JsonPropertyName("recommended_next_actions")]
    public List<string> RecommendedNextActions { get; set; } = [];

    [JsonPropertyName("recommended_actions")]
    public List<OverviewAction> RecommendedActions { get; set; } = [];
}

public sealed class OverviewAction
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("target_page")]
    public string TargetPage { get; set; } = string.Empty;

    [JsonPropertyName("chat_prompt")]
    public string? ChatPrompt { get; set; }

    [JsonPropertyName("can_execute")]
    public bool CanExecute { get; set; }

    [JsonPropertyName("execute_label")]
    public string? ExecuteLabel { get; set; }
}
