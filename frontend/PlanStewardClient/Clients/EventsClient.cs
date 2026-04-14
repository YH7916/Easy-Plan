using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using PlanStewardClient.Models;

namespace PlanStewardClient.Clients;

public sealed class EventsClient
{
    private readonly HttpClient _httpClient;

    public EventsClient(HttpClient httpClient) => _httpClient = httpClient;

    public async IAsyncEnumerable<BackendEvent> SubscribeToEventsAsync(
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, "/events/stream");
        request.Headers.Accept.ParseAdd("text/event-stream");

        using var response = await _httpClient.SendAsync(
            request,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken);
        response.EnsureSuccessStatusCode();

        using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream, Encoding.UTF8);

        string eventType = "message";
        var dataBuilder = new StringBuilder();

        while (!cancellationToken.IsCancellationRequested)
        {
            string? line = await reader.ReadLineAsync(cancellationToken);
            if (line is null)
                break;

            if (line.Length == 0)
            {
                if (dataBuilder.Length > 0)
                {
                    yield return CreateBackendEvent(eventType, dataBuilder.ToString());
                    eventType = "message";
                    dataBuilder.Clear();
                }
                continue;
            }

            if (line.StartsWith(":", StringComparison.Ordinal))
                continue;

            if (line.StartsWith("event:", StringComparison.Ordinal))
            {
                eventType = line[6..].Trim();
                continue;
            }

            if (line.StartsWith("data:", StringComparison.Ordinal))
            {
                if (dataBuilder.Length > 0)
                    dataBuilder.Append('\n');
                dataBuilder.Append(line[5..].TrimStart());
            }
        }

        if (dataBuilder.Length > 0)
            yield return CreateBackendEvent(eventType, dataBuilder.ToString());
    }

    private static BackendEvent CreateBackendEvent(string eventType, string payloadJson)
    {
        using JsonDocument payloadDocument = JsonDocument.Parse(payloadJson);
        return new BackendEvent
        {
            EventType = eventType,
            Payload = payloadDocument.RootElement.Clone(),
            ReceivedAt = DateTimeOffset.UtcNow,
        };
    }
}
