using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class PlanningClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public PlanningClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<IReadOnlyList<TaskItem>> GetTasksAsync(CancellationToken cancellationToken = default)
        => await GetAsync<List<TaskItem>>("/planning/tasks", cancellationToken);

    public async Task<IReadOnlyList<TaskSuggestion>> GetTaskSuggestionsAsync(CancellationToken cancellationToken = default)
        => await GetAsync<List<TaskSuggestion>>("/planning/suggestions", cancellationToken);

    public async Task<TaskItem> CreateTaskAsync(
        string title,
        string? project,
        int priority,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            "/planning/tasks",
            new { title, project, priority },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<TaskItem>(response, cancellationToken);
    }

    public async Task<TaskItem> AcceptTaskSuggestionAsync(
        TaskSuggestion suggestion,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            "/planning/suggestions/accept",
            suggestion,
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<TaskItem>(response, cancellationToken);
    }

    public async Task<TaskItem> CompleteTaskAsync(string taskId, CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsync(
            $"/planning/tasks/{taskId}/complete",
            content: null,
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<TaskItem>(response, cancellationToken);
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
