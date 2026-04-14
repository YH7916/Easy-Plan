using System;
using System.Net.Http;
using PlanStewardClient;

namespace PlanStewardWinUI.Services;

public static class BackendServices
{
    public static readonly Uri BackendUri = new(
        Environment.GetEnvironmentVariable("PLAN_STEWARD_BACKEND_URL")
        ?? "http://127.0.0.1:8765");

    public static BackendApiClient Client { get; } = CreateClient(streaming: false);
    public static BackendApiClient EventsClient { get; } = CreateClient(streaming: true);

    private static BackendApiClient CreateClient(bool streaming)
    {
        var handler = new HttpClientHandler();
        if (BackendUri.IsLoopback)
        {
            handler.UseProxy = false;
        }

        var httpClient = new HttpClient(handler)
        {
            BaseAddress = BackendUri,
            Timeout = streaming ? Timeout.InfiniteTimeSpan : TimeSpan.FromSeconds(10)
        };
        return new BackendApiClient(httpClient);
    }
}
