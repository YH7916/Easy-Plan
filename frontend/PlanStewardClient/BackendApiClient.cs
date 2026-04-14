using PlanStewardClient.Clients;
using PlanStewardClient.Models;

namespace PlanStewardClient;

public sealed class BackendApiClient
{
    public OverviewClient Overview { get; }
    public PlanningClient Planning { get; }
    public SourcesClient Sources { get; }
    public InsightsClient Insights { get; }
    public NotesClient Notes { get; }
    public ChatClient Chat { get; }
    public SettingsClient Settings { get; }
    public AutomationClient Automation { get; }
    public EventsClient Events { get; }

    public BackendApiClient(HttpClient httpClient)
    {
        Overview = new OverviewClient(httpClient);
        Planning = new PlanningClient(httpClient);
        Sources = new SourcesClient(httpClient);
        Insights = new InsightsClient(httpClient);
        Notes = new NotesClient(httpClient);
        Chat = new ChatClient(httpClient);
        Settings = new SettingsClient(httpClient);
        Automation = new AutomationClient(httpClient);
        Events = new EventsClient(httpClient);
    }

    // Overview
    public Task<OverviewSummary> GetOverviewSummaryAsync(string? today = null, CancellationToken cancellationToken = default)
        => Overview.GetOverviewSummaryAsync(today, cancellationToken);

    public Task<OverviewActionExecution> ExecuteOverviewActionAsync(string actionId, string? today = null, CancellationToken cancellationToken = default)
        => Overview.ExecuteOverviewActionAsync(actionId, today, cancellationToken);

    // Planning
    public Task<IReadOnlyList<TaskItem>> GetTasksAsync(CancellationToken cancellationToken = default)
        => Planning.GetTasksAsync(cancellationToken);

    public Task<IReadOnlyList<TaskSuggestion>> GetTaskSuggestionsAsync(CancellationToken cancellationToken = default)
        => Planning.GetTaskSuggestionsAsync(cancellationToken);

    public Task<TaskItem> CreateTaskAsync(string title, string? project, int priority, CancellationToken cancellationToken = default)
        => Planning.CreateTaskAsync(title, project, priority, cancellationToken);

    public Task<TaskItem> AcceptTaskSuggestionAsync(TaskSuggestion suggestion, CancellationToken cancellationToken = default)
        => Planning.AcceptTaskSuggestionAsync(suggestion, cancellationToken);

    public Task<TaskItem> CompleteTaskAsync(string taskId, CancellationToken cancellationToken = default)
        => Planning.CompleteTaskAsync(taskId, cancellationToken);

    // Sources
    public Task<IReadOnlyList<SourceItem>> GetSourceItemsAsync(CancellationToken cancellationToken = default)
        => Sources.GetSourceItemsAsync(cancellationToken);

    public Task<SourcesDashboard> GetSourcesDashboardAsync(string? today = null, CancellationToken cancellationToken = default)
        => Sources.GetSourcesDashboardAsync(today, cancellationToken);

    // Insights
    public Task<DailyReport> GetDailyReportAsync(string date, CancellationToken cancellationToken = default)
        => Insights.GetDailyReportAsync(date, cancellationToken);

    // Notes
    public Task<IReadOnlyList<NoteItem>> GetNotesAsync(CancellationToken cancellationToken = default)
        => Notes.GetNotesAsync(cancellationToken);

    public Task<NotesDashboard> GetNotesDashboardAsync(CancellationToken cancellationToken = default)
        => Notes.GetNotesDashboardAsync(cancellationToken);

    public Task<NoteDraft> CreateDailyReviewDraftAsync(string date, CancellationToken cancellationToken = default)
        => Notes.CreateDailyReviewDraftAsync(date, cancellationToken);

    public Task<NoteDraft?> GetDailyReviewDraftAsync(string date, CancellationToken cancellationToken = default)
        => Notes.GetDailyReviewDraftAsync(date, cancellationToken);

    // Chat
    public Task<ChatSession> GetChatSessionAsync(string sessionId, string? today = null, CancellationToken cancellationToken = default)
        => Chat.GetChatSessionAsync(sessionId, today, cancellationToken);

    public Task<ChatSession> SendChatMessageAsync(string sessionId, string message, CancellationToken cancellationToken = default)
        => Chat.SendChatMessageAsync(sessionId, message, cancellationToken);

    public Task<ChatActionExecution> ExecuteChatActionAsync(string sessionId, string actionId, string? today = null, CancellationToken cancellationToken = default)
        => Chat.ExecuteChatActionAsync(sessionId, actionId, today, cancellationToken);

    // Settings
    public Task<HealthStatus> GetHealthAsync(CancellationToken cancellationToken = default)
        => Settings.GetHealthAsync(cancellationToken);

    public Task<SettingsConfig> GetSettingsConfigAsync(CancellationToken cancellationToken = default)
        => Settings.GetSettingsConfigAsync(cancellationToken);

    public Task<SettingsConfig> UpdateSettingsConfigAsync(SettingsConfig settings, CancellationToken cancellationToken = default)
        => Settings.UpdateSettingsConfigAsync(settings, cancellationToken);

    public Task<IReadOnlyList<string>> GetDetectedObsidianVaultsAsync(CancellationToken cancellationToken = default)
        => Settings.GetDetectedObsidianVaultsAsync(cancellationToken);

    public Task<SettingsConfig> UseDetectedObsidianVaultAsync(string vaultRoot, CancellationToken cancellationToken = default)
        => Settings.UseDetectedObsidianVaultAsync(vaultRoot, cancellationToken);

    // Automation
    public Task<AutomationStatus> GetAutomationStatusAsync(CancellationToken cancellationToken = default)
        => Automation.GetAutomationStatusAsync(cancellationToken);

    // Events
    public IAsyncEnumerable<BackendEvent> SubscribeToEventsAsync(CancellationToken cancellationToken = default)
        => Events.SubscribeToEventsAsync(cancellationToken);
}
