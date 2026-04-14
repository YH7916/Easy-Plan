using System;
using System.Threading.Tasks;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

namespace PlanStewardWinUI.ViewModels;

public sealed class SourcesPageViewModel
{
    public SourcesDashboard? Dashboard { get; private set; }
    public string StatusText { get; private set; } = "The backend classifies source items so the shell only renders intake state.";
    public string PendingStatusText { get; private set; } = string.Empty;
    public string TrackedStatusText { get; private set; } = string.Empty;

    public async Task LoadAsync()
    {
        try
        {
            string today = DateTime.Now.ToString("yyyy-MM-dd");
            Dashboard = await BackendServices.Client.GetSourcesDashboardAsync(today);
            StatusText = $"Sources dashboard loaded for {today}.";

            PendingStatusText = Dashboard.PendingIntakeCount > 0
                ? $"{Dashboard.PendingIntakeCount} items are waiting to be accepted into planning."
                : "No source items are waiting for intake.";
            TrackedStatusText = Dashboard.TrackedCount > 0
                ? $"{Dashboard.TrackedCount} items are already represented in the task pool."
                : "No source items are currently tracked.";
        }
        catch (Exception ex)
        {
            Dashboard = null;
            StatusText = ex.Message;
            PendingStatusText = "Unable to load intake state.";
            TrackedStatusText = "Unable to load tracked source state.";
        }
    }

    public async Task<string> AcceptItemAsync(SourcesDashboardItem item)
    {
        try
        {
            await BackendServices.Client.AcceptTaskSuggestionAsync(new TaskSuggestion
            {
                Title = item.Title,
                Source = item.Source,
                Due = item.Due,
                Project = item.Project,
                Priority = item.Priority,
                ExternalId = item.ExternalId,
                Reason = item.Recommendation
            });
            await LoadAsync();
            return $"Accepted {item.Title} into the unified task pool.";
        }
        catch (Exception ex)
        {
            return ex.Message;
        }
    }
}
