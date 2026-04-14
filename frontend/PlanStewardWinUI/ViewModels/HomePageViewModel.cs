using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

namespace PlanStewardWinUI.ViewModels;

public sealed class HomePageViewModel
{
    public OverviewSummary? Overview { get; private set; }
    public HealthStatus? Health { get; private set; }
    public AutomationStatus? Automation { get; private set; }
    public bool HasData => Overview is not null;

    public string OpenTaskCount => Overview?.OpenTaskCount.ToString() ?? "-";
    public string HighPriorityCount => Overview?.HighPriorityOpenCount.ToString() ?? "-";
    public string PendingIntakeCount => Overview?.PendingIntakeCount.ToString() ?? "-";
    public string DueSoonCount => Overview?.DueSoonSourceCount.ToString() ?? "-";
    public string OverdueCount => Overview?.OverdueSourceCount.ToString() ?? "-";
    public string CheckInHours => Automation is not null ? $"{Automation.CheckInHours}h" : "-";
    public string DailyBrief => Overview?.DailyBrief ?? "Backend unavailable. Start the local steward host and refresh.";
    public string HealthText => Health is not null
        ? $"Status: {Health.Status}\nBackend: {Health.BackendUrl}\nModules: {string.Join(", ", Health.Modules)}"
        : string.Empty;
    public string ReviewStatusText => Overview is not null
        ? $"Daily review: {(Overview.HasDailyReport ? "Available" : "Missing")}\nIndexed notes: {Overview.NotesIndexedCount}\nVisible source items: {Overview.SourceItemCount}"
        : "Overview unavailable until the backend is reachable.";

    public IReadOnlyList<string> Alerts => Overview?.ActiveAlerts ?? ["Unable to reach backend host."];
    public IReadOnlyList<string> Signals { get; private set; } = [];
    public IReadOnlyList<string> NextActions => Overview?.RecommendedNextActions ?? ["Reconnect the local backend host to restore steward recommendations."];
    public IReadOnlyList<OverviewAction> RecommendedActions => Overview?.RecommendedActions ?? [];
    public IReadOnlyList<string> FocusApps => Overview?.FocusApps ?? ["No focus context available."];

    public string? ErrorMessage { get; private set; }

    public async Task RefreshAsync()
    {
        ErrorMessage = null;
        try
        {
            string today = DateTime.Now.ToString("yyyy-MM-dd");
            var overviewTask = BackendServices.Client.GetOverviewSummaryAsync(today);
            var healthTask = BackendServices.Client.GetHealthAsync();
            var automationTask = BackendServices.Client.GetAutomationStatusAsync();
            await Task.WhenAll(overviewTask, healthTask, automationTask);

            Overview = await overviewTask;
            Health = await healthTask;
            Automation = await automationTask;

            var signals = new List<string>();
            foreach (var signal in Automation.Signals)
            {
                signals.Add($"{signal.Kind}: {signal.Summary}");
            }
            Signals = signals;
        }
        catch (Exception ex)
        {
            Overview = null;
            Health = null;
            Automation = null;
            Signals = [];
            ErrorMessage = ex.Message;
        }
    }

    public async Task<(string summary, string targetPage)?> ExecuteActionAsync(string actionId, string today)
    {
        try
        {
            OverviewActionExecution execution = await BackendServices.Client.ExecuteOverviewActionAsync(actionId, today);
            return (execution.Summary, execution.TargetPage);
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
            return null;
        }
    }

    public static string FormatEvent(BackendEvent backendEvent)
    {
        return backendEvent.EventType switch
        {
            "connected" => "Backend event stream connected.",
            "planning.task_created" => $"New task suggested: {ReadValue(backendEvent.Payload, "title", "Untitled task")}",
            "planning.task_completed" => $"Task completed: {ReadValue(backendEvent.Payload, "title", "Untitled task")}",
            "planning.suggestion_accepted" => $"Source item accepted into planning: {ReadValue(backendEvent.Payload, "title", "Untitled task")}.",
            "insights.report_generated" => $"Daily insight refreshed for {ReadValue(backendEvent.Payload, "date", "today")}.",
            "notes.daily_draft_written" => $"Daily note draft written to {ReadValue(backendEvent.Payload, "path", "configured notes folder")}.",
            "notes.daily_review_draft_written" => $"Daily review note written for {ReadValue(backendEvent.Payload, "date", "today")}.",
            "chat.message_processed" => $"Chat reply ready for session {ReadValue(backendEvent.Payload, "session_id", "default")}.",
            "chat.action_executed" => $"Chat action executed: {ReadValue(backendEvent.Payload, "summary", "Steward handoff completed")}.",
            "overview.action_executed" => $"Overview action executed: {ReadValue(backendEvent.Payload, "summary", "Steward handoff completed")}.",
            "settings.config_updated" => $"Settings updated. Obsidian vault: {ReadValue(backendEvent.Payload, "obsidian_vault_root", "(not configured)")}.",
            "automation.status_checked" => $"Automation reviewed {ReadValue(backendEvent.Payload, "signal_count", "0")} active signals.",
            _ => $"{backendEvent.EventType}: {backendEvent.Payload}"
        };
    }

    private static string ReadValue(JsonElement payload, string propertyName, string fallback)
    {
        if (!payload.TryGetProperty(propertyName, out JsonElement property))
        {
            return fallback;
        }

        return property.ValueKind switch
        {
            JsonValueKind.String => property.GetString() ?? fallback,
            JsonValueKind.Number => property.ToString(),
            JsonValueKind.True => bool.TrueString,
            JsonValueKind.False => bool.FalseString,
            _ => property.ToString() ?? fallback,
        };
    }
}
