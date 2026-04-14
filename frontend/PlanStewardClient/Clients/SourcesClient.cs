using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class SourcesClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public SourcesClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<IReadOnlyList<SourceItem>> GetSourceItemsAsync(CancellationToken cancellationToken = default)
        => await GetAsync<List<SourceItem>>("/sources/items", cancellationToken);

    public async Task<SourcesDashboard> GetSourcesDashboardAsync(
        string? today = null,
        CancellationToken cancellationToken = default)
    {
        string path = "/sources/dashboard";
        if (!string.IsNullOrWhiteSpace(today))
            path += $"?today={Uri.EscapeDataString(today)}";
        return await GetAsync<SourcesDashboard>(path, cancellationToken);
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
