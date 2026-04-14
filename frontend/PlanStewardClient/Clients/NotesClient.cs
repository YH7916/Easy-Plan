using System.Net.Http.Json;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class NotesClient
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly HttpClient _httpClient;

    public NotesClient(HttpClient httpClient) => _httpClient = httpClient;

    public async Task<IReadOnlyList<NoteItem>> GetNotesAsync(CancellationToken cancellationToken = default)
    {
        NotesIndexResponse response = await GetAsync<NotesIndexResponse>("/notes/index", cancellationToken);
        return response.Notes;
    }

    public async Task<NotesDashboard> GetNotesDashboardAsync(CancellationToken cancellationToken = default)
        => await GetAsync<NotesDashboard>("/notes/dashboard", cancellationToken);

    public async Task<NoteDraft> CreateDailyReviewDraftAsync(
        string date,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.PostAsJsonAsync(
            "/notes/drafts/daily-review",
            new { date },
            cancellationToken);
        response.EnsureSuccessStatusCode();
        return await ReadAsync<NoteDraft>(response, cancellationToken);
    }

    public async Task<NoteDraft?> GetDailyReviewDraftAsync(
        string date,
        CancellationToken cancellationToken = default)
    {
        var response = await _httpClient.GetAsync(
            $"/notes/drafts/daily-review?date={Uri.EscapeDataString(date)}",
            cancellationToken);
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await ReadAsync<NoteDraft>(response, cancellationToken);
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
