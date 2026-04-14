using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

namespace PlanStewardWinUI.ViewModels;

public sealed class NotesPageViewModel
{
    public NotesDashboard? Dashboard { get; private set; }
    public IReadOnlyList<string> DetectedVaults { get; private set; } = [];
    public string StatusText { get; private set; } = "Loading Obsidian index and steward-generated summaries...";

    public async Task LoadAsync()
    {
        try
        {
            var dashboardTask = BackendServices.Client.GetNotesDashboardAsync();
            var detectedVaultsTask = BackendServices.Client.GetDetectedObsidianVaultsAsync();
            await Task.WhenAll(dashboardTask, detectedVaultsTask);

            Dashboard = await dashboardTask;
            DetectedVaults = await detectedVaultsTask;

            if (!Dashboard.VaultReady)
            {
                StatusText = DetectedVaults.Count > 0
                    ? $"Obsidian vault is not configured yet. Settings already sees {DetectedVaults.Count} detected vault path(s)."
                    : "Obsidian vault is not configured in the backend yet.";
            }
            else
            {
                StatusText = $"Indexed {Dashboard.IndexedCount} notes and {Dashboard.GeneratedCount} steward outputs. Editing stays in Obsidian.";
            }
        }
        catch (Exception ex)
        {
            Dashboard = null;
            DetectedVaults = [];
            StatusText = ex.Message;
        }
    }
}
