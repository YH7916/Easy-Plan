using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class SettingsClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public SettingsClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<HealthStatus> GetHealthAsync(CancellationToken cancellationToken = default)
        => await GetAsync<HealthStatus>("/settings/health", cancellationToken);

    public async Task<SettingsConfig> GetSettingsConfigAsync(CancellationToken cancellationToken = default)
        => await GetAsync<SettingsConfig>("/settings/config", cancellationToken);

    public async Task<SettingsConfig> UpdateSettingsConfigAsync(
        SettingsConfig settings,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync("/settings/config", settings, cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<SettingsConfig>(response, cancellationToken);
    }

    public async Task<IReadOnlyList<string>> GetDetectedObsidianVaultsAsync(
        CancellationToken cancellationToken = default)
        => await GetAsync<List<string>>("/settings/obsidian/detected-vaults", cancellationToken);

    public async Task<SettingsConfig> UseDetectedObsidianVaultAsync(
        string vaultRoot,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            "/settings/obsidian/use-detected-vault",
            new { vault_root = vaultRoot },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<SettingsConfig>(response, cancellationToken);
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
