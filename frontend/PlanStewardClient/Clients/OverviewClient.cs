using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class OverviewClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public OverviewClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<OverviewSummary> GetOverviewSummaryAsync(
        string? today = null,
        CancellationToken cancellationToken = default)
    {
        string path = "/overview/summary";
        if (!string.IsNullOrWhiteSpace(today))
            path += $"?today={Uri.EscapeDataString(today)}";
        return await GetAsync<OverviewSummary>(path, cancellationToken);
    }

    public async Task<OverviewActionExecution> ExecuteOverviewActionAsync(
        string actionId,
        string? today = null,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            "/overview/actions/execute",
            new { action_id = actionId, today },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<OverviewActionExecution>(response, cancellationToken);
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
