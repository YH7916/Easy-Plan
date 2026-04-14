using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class DailyReport
{
    [JsonPropertyName("date")]
    public string Date { get; set; } = string.Empty;

    [JsonPropertyName("summary_markdown")]
    public string SummaryMarkdown { get; set; } = string.Empty;

    [JsonPropertyName("top_apps")]
    public List<string> TopApps { get; set; } = [];

    [JsonPropertyName("open_task_count")]
    public int OpenTaskCount { get; set; }
}
