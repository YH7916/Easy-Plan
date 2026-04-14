using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class ChatActionExecution
{
    [JsonPropertyName("summary")]
    public string Summary { get; set; } = string.Empty;

    [JsonPropertyName("session")]
    public ChatSession Session { get; set; } = new();

    [JsonPropertyName("created_task")]
    public TaskItem? CreatedTask { get; set; }

    [JsonPropertyName("note_draft")]
    public NoteDraft? NoteDraft { get; set; }
}
