using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class SourcesDashboardItem
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

    [JsonPropertyName("tracking_status")]
    public string TrackingStatus { get; set; } = string.Empty;

    [JsonPropertyName("urgency")]
    public string Urgency { get; set; } = string.Empty;

    [JsonPropertyName("tracked_task_id")]
    public string? TrackedTaskId { get; set; }

    [JsonPropertyName("tracked_task_status")]
    public string? TrackedTaskStatus { get; set; }

    [JsonPropertyName("recommendation")]
    public string Recommendation { get; set; } = string.Empty;
}

public sealed class SourcesDashboard
{
    [JsonPropertyName("total_count")]
    public int TotalCount { get; set; }

    [JsonPropertyName("tracked_count")]
    public int TrackedCount { get; set; }

    [JsonPropertyName("pending_intake_count")]
    public int PendingIntakeCount { get; set; }

    [JsonPropertyName("due_soon_count")]
    public int DueSoonCount { get; set; }

    [JsonPropertyName("overdue_count")]
    public int OverdueCount { get; set; }

    [JsonPropertyName("items")]
    public List<SourcesDashboardItem> Items { get; set; } = [];
}
