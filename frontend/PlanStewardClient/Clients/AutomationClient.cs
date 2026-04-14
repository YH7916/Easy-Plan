using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class AutomationClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public AutomationClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<AutomationStatus> GetAutomationStatusAsync(CancellationToken cancellationToken = default)
        => await GetAsync<AutomationStatus>("/automation/status", cancellationToken);

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
