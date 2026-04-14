using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class OverviewActionExecution
{
    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty;

    [JsonPropertyName("target_page")]
    public string TargetPage { get; set; } = string.Empty;

    [JsonPropertyName("note_draft")]
    public NoteDraft? NoteDraft { get; set; }

    [JsonPropertyName("created_task")]
    public TaskItem? CreatedTask { get; set; }
}
