using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

namespace PlanStewardWinUI.ViewModels;

public sealed class PlanningPageViewModel
{
    public IReadOnlyList<TaskItem> Tasks { get; private set; } = [];
    public IReadOnlyList<TaskSuggestion> Suggestions { get; private set; } = [];
    public string StatusText { get; private set; } = string.Empty;
    public string SuggestionsStatusText { get; private set; } = string.Empty;

    public async Task LoadAsync()
    {
        try
        {
            var tasksTask = BackendServices.Client.GetTasksAsync();
            var suggestionsTask = BackendServices.Client.GetTaskSuggestionsAsync();
            await Task.WhenAll(tasksTask, suggestionsTask);

            Tasks = await tasksTask;
            Suggestions = await suggestionsTask;
            StatusText = $"Unified task pool loaded with {Tasks.Count} tasks.";
            SuggestionsStatusText = Suggestions.Count > 0
                ? $"{Suggestions.Count} source items are ready to be promoted into the steward task pool."
                : "No source suggestions are waiting right now.";
        }
        catch (Exception ex)
        {
            Tasks = [];
            Suggestions = [];
            StatusText = ex.Message;
            SuggestionsStatusText = "Unable to load source-backed suggestions.";
        }
    }

    public async Task<string> AddTaskAsync(string title, string? project, int priority)
    {
        try
        {
            await BackendServices.Client.CreateTaskAsync(title, project, priority);
            await LoadAsync();
            return "Task created.";
        }
        catch (Exception ex)
        {
            return ex.Message;
        }
    }

    public async Task<string> CompleteTaskAsync(string taskId)
    {
        try
        {
            await BackendServices.Client.CompleteTaskAsync(taskId);
            await LoadAsync();
            return $"Completed {taskId}.";
        }
        catch (Exception ex)
        {
            return ex.Message;
        }
    }

    public async Task<string> AcceptSuggestionAsync(TaskSuggestion suggestion)
    {
        try
        {
            await BackendServices.Client.AcceptTaskSuggestionAsync(suggestion);
            await LoadAsync();
            return $"Accepted source suggestion: {suggestion.Title}.";
        }
        catch (Exception ex)
        {
            return ex.Message;
        }
    }
}
