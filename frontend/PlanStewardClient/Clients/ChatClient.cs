using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class ChatClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public ChatClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<ChatSession> GetChatSessionAsync(
        string sessionId,
        string? today = null,
        CancellationToken cancellationToken = default)
    {
        string path = $"/chat/sessions/{sessionId}";
        if (!string.IsNullOrWhiteSpace(today))
            path += $"?today={Uri.EscapeDataString(today)}";
        return await GetAsync<ChatSession>(path, cancellationToken);
    }

    public async Task<ChatSession> SendChatMessageAsync(
        string sessionId,
        string message,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            $"/chat/sessions/{sessionId}/messages",
            new { message },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<ChatSession>(response, cancellationToken);
    }

    public async Task<ChatActionExecution> ExecuteChatActionAsync(
        string sessionId,
        string actionId,
        string? today = null,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            $"/chat/sessions/{sessionId}/actions",
            new { action_id = actionId, today },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<ChatActionExecution>(response, cancellationToken);
    }

    private async Task<T> GetAsync<T>(string path, CancellationToken cancellationToken)
    {
        var response = await _httpClient.GetAsync(path, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<T>(response, cancellationToken);
    }

    private static async Task<T> ReadAsync<T>(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        T? value = await response.Content.ReadFromJsonAsync<T>(JsonOptions, cancellationToken);
        return value ?? throw new InvalidOperationException("Backend returned an empty payload.");
    }
}
