// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace PlanStewardWinUI.Pages;

public sealed partial class SettingsPage : Page
{
    public SettingsPage()
    {
        InitializeComponent();
    }

    private async void Page_Loaded(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        await RefreshAsync();
    }

    private async void Refresh_Click(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        await RefreshAsync();
    }

    private async void Save_Click(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        await SaveAsync();
    }

    private async Task RefreshAsync()
    {
        try
        {
            SetBusy(true);
            HideStatus();
            await LoadDataAsync();
        }
        catch (Exception ex)
        {
            BackendUrlText.Text = ex.Message;
            WorkReviewRootText.Text = "Unable to read backend settings.";
            ObsidianRootText.Text = string.Empty;
            AutomationModeText.Text = "Automation status unavailable.";
            AutomationInterventionCountText.Text = string.Empty;
            ShowStatus($"Unable to load backend settings: {ex.Message}", InfoBarSeverity.Error);
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async Task SaveAsync()
    {
        try
        {
            SetBusy(true);
            HideStatus();
            SettingsConfig payload = BuildPayload();
            await BackendServices.Client.UpdateSettingsConfigAsync(payload);
            await LoadDataAsync();
            ShowStatus("Settings saved and backend adapters reloaded.", InfoBarSeverity.Success);
        }
        catch (Exception ex)
        {
            ShowStatus($"Unable to save settings: {ex.Message}", InfoBarSeverity.Error);
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async Task LoadDataAsync()
    {
        var configTask = BackendServices.Client.GetSettingsConfigAsync();
        var detectedVaultsTask = BackendServices.Client.GetDetectedObsidianVaultsAsync();
        var healthTask = BackendServices.Client.GetHealthAsync();
        var automationTask = BackendServices.Client.GetAutomationStatusAsync();
        await Task.WhenAll(configTask, detectedVaultsTask, healthTask, automationTask);

        ApplyConfig(await configTask);
        RenderDetectedVaults(await detectedVaultsTask);
        var health = await healthTask;
        var automation = await automationTask;
        BackendUrlText.Text = health.BackendUrl;
        WorkReviewRootText.Text = $"Work Review: {health.WorkReviewRoot}";
        ObsidianRootText.Text = $"Obsidian: {health.ObsidianVaultRoot ?? "(not configured)"}";

        AutomationModeText.Text = automation.ModeSummary;
        AutomationInterventionCountText.Text = $"Pending interventions: {automation.PendingInterventionsCount}";
    }

    private SettingsConfig BuildPayload()
    {
        if (string.IsNullOrWhiteSpace(WorkReviewRootBox.Text))
        {
            throw new InvalidOperationException("Work Review root cannot be empty.");
        }

        if (string.IsNullOrWhiteSpace(ObsidianGeneratedDirBox.Text))
        {
            throw new InvalidOperationException("Obsidian generated folder cannot be empty.");
        }

        if (double.IsNaN(CheckInHoursBox.Value) || CheckInHoursBox.Value < 1 || CheckInHoursBox.Value > 24)
        {
            throw new InvalidOperationException("Automation check-in cadence must stay between 1 and 24 hours.");
        }

        return new SettingsConfig
        {
            WorkReviewRoot = WorkReviewRootBox.Text.Trim(),
            ObsidianVaultRoot = string.IsNullOrWhiteSpace(ObsidianVaultRootBox.Text)
                ? null
                : ObsidianVaultRootBox.Text.Trim(),
            ObsidianGeneratedDir = ObsidianGeneratedDirBox.Text.Trim(),
            AutomationCheckInHours = (int)Math.Round(CheckInHoursBox.Value),
        };
    }

    private void ApplyConfig(SettingsConfig config)
    {
        WorkReviewRootBox.Text = config.WorkReviewRoot;
        ObsidianVaultRootBox.Text = config.ObsidianVaultRoot ?? string.Empty;
        ObsidianGeneratedDirBox.Text = config.ObsidianGeneratedDir;
        CheckInHoursBox.Value = config.AutomationCheckInHours;
    }

    private void RenderDetectedVaults(IReadOnlyList<string> vaults)
    {
        DetectedVaultsPanel.Children.Clear();

        if (vaults.Count == 0)
        {
            DetectedVaultsPanel.Children.Add(CreatePlaceholderCard(
                "No vaults detected",
                "Open an Obsidian vault once and it will usually appear here automatically."));
            return;
        }

        foreach (string vault in vaults)
        {
            DetectedVaultsPanel.Children.Add(CreateDetectedVaultCard(vault));
        }
    }

    private Border CreateDetectedVaultCard(string vaultPath)
    {
        var grid = new Grid
        {
            ColumnSpacing = 12
        };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel
        {
            Spacing = 4
        };
        infoPanel.Children.Add(new TextBlock
        {
            FontWeight = FontWeights.SemiBold,
            Text = "Detected vault",
            TextWrapping = TextWrapping.Wrap,
        });
        infoPanel.Children.Add(new TextBlock
        {
            Opacity = 0.72,
            Text = vaultPath,
            TextWrapping = TextWrapping.Wrap,
        });

        var useButton = new Button
        {
            Content = "Use This Vault",
            Tag = vaultPath,
            VerticalAlignment = VerticalAlignment.Top,
        };
        useButton.Click += UseDetectedVault_Click;

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(useButton, 1);
        grid.Children.Add(infoPanel);
        grid.Children.Add(useButton);

        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(8),
            Background = (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"],
            Child = grid,
        };
    }

    private static Border CreatePlaceholderCard(string title, string description)
    {
        var panel = new StackPanel
        {
            Spacing = 4
        };
        panel.Children.Add(new TextBlock
        {
            FontWeight = FontWeights.SemiBold,
            Text = title,
            TextWrapping = TextWrapping.Wrap,
        });
        panel.Children.Add(new TextBlock
        {
            Opacity = 0.72,
            Text = description,
            TextWrapping = TextWrapping.Wrap,
        });

        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(8),
            Background = (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"],
            Child = panel,
        };
    }

    private async void UseDetectedVault_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: string vaultPath })
        {
            return;
        }

        try
        {
            SetBusy(true);
            HideStatus();
            await BackendServices.Client.UseDetectedObsidianVaultAsync(vaultPath);
            await LoadDataAsync();
            ShowStatus("Detected vault applied and backend adapters reloaded.", InfoBarSeverity.Success);
        }
        catch (Exception ex)
        {
            ShowStatus($"Unable to apply detected vault: {ex.Message}", InfoBarSeverity.Error);
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void SetBusy(bool isBusy)
    {
        RefreshButton.IsEnabled = !isBusy;
        SaveButton.IsEnabled = !isBusy;
        WorkReviewRootBox.IsEnabled = !isBusy;
        ObsidianVaultRootBox.IsEnabled = !isBusy;
        ObsidianGeneratedDirBox.IsEnabled = !isBusy;
        CheckInHoursBox.IsEnabled = !isBusy;
    }

    private void ShowStatus(string message, InfoBarSeverity severity)
    {
        ConfigStatusBar.Message = message;
        ConfigStatusBar.Severity = severity;
        ConfigStatusBar.IsOpen = true;
    }

    private void HideStatus()
    {
        ConfigStatusBar.IsOpen = false;
    }
}
