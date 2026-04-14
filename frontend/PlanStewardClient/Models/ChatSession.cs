using System.Text.Json.Serialization;

namespace PlanStewardClient.Models;

public sealed class ChatSession
{
    [JsonPropertyName("session_id")]
    public string SessionId { get; set; } = string.Empty;

    [JsonPropertyName("reply")]
    public string Reply { get; set; } = string.Empty;

    [JsonPropertyName("starter_prompts")]
    public List<string> StarterPrompts { get; set; } = [];

    [JsonPropertyName("suggested_actions")]
    public List<ChatAction> SuggestedActions { get; set; } = [];

    [JsonPropertyName("history")]
    public List<ChatMessage> History { get; set; } = [];
}

public sealed class ChatAction
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("label")]
    public string Label { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("target_module")]
    public string TargetModule { get; set; } = string.Empty;
}

public sealed class ChatMessage
{
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}
