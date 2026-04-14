using System;
using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using PlanStewardClient.Models;
using PlanStewardWinUI.Navigation;
using PlanStewardWinUI.Services;
using Windows.System;

namespace PlanStewardWinUI.Pages;

public sealed class InsightsPage : Page
{
    private readonly CalendarDatePicker _datePicker = new()
    {
        Date = DateTimeOffset.Now
    };

    private readonly AppBarButton _writeDraftButton = new()
    {
        Icon = new SymbolIcon(Symbol.Save),
        Label = "Write Daily Draft"
    };

    private readonly AppBarButton _openSettingsButton = new()
    {
        Icon = new SymbolIcon(Symbol.Setting),
        Label = "Open Settings"
    };

    private readonly Button _openDraftButton = new()
    {
        Content = "Open In Obsidian",
        IsEnabled = false
    };

    private readonly TextBlock _statusText = new()
    {
        Opacity = 0.72,
        TextWrapping = TextWrapping.Wrap,
        Text = "Unified daily review combines Work_Review activity with the steward task pool."
    };

    private readonly TextBlock _metaText = new()
    {
        Opacity = 0.82,
        TextWrapping = TextWrapping.Wrap
    };

    private readonly TextBlock _topAppsText = new()
    {
        TextWrapping = TextWrapping.Wrap
    };

    private readonly TextBlock _draftPathText = new()
    {
        Opacity = 0.72,
        TextWrapping = TextWrapping.Wrap,
        Text = "No Obsidian draft generated in this session."
    };

    private readonly TextBox _reportText = new()
    {
        AcceptsReturn = true,
        IsReadOnly = true,
        TextWrapping = TextWrapping.Wrap,
        MinHeight = 320
    };

    private string? _latestDraftUrl;

    public InsightsPage()
    {
        Content = BuildContent();
        Loaded += Page_Loaded;
    }

    private UIElement BuildContent()
    {
        var refreshButton = new AppBarButton
        {
            Icon = new SymbolIcon(Symbol.Refresh),
            Label = "Refresh"
        };
        refreshButton.Click += Refresh_Click;
        _writeDraftButton.Click += WriteDraft_Click;
        _openDraftButton.Click += OpenDraft_Click;

        var commandBar = new CommandBar
        {
            DefaultLabelPosition = CommandBarDefaultLabelPosition.Right
        };
        commandBar.PrimaryCommands.Add(refreshButton);
        commandBar.PrimaryCommands.Add(_writeDraftButton);
        commandBar.PrimaryCommands.Add(_openSettingsButton);
        _openSettingsButton.Click += OpenSettings_Click;

        var headerPanel = new StackPanel
        {
            Margin = new Thickness(24, 24, 24, 8),
            Spacing = 12
        };
        headerPanel.Children.Add(commandBar);
        headerPanel.Children.Add(new TextBlock
        {
            FontSize = 28,
            FontWeight = FontWeights.SemiBold,
            Text = "Daily Review"
        });
        headerPanel.Children.Add(_statusText);

        var controlsGrid = new Grid
        {
            ColumnSpacing = 12
        };
        controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        controlsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        Grid.SetColumn(_datePicker, 0);
        Grid.SetColumn(_openDraftButton, 1);
        controlsGrid.Children.Add(_datePicker);
        controlsGrid.Children.Add(_openDraftButton);
        headerPanel.Children.Add(controlsGrid);

        var contentPanel = new StackPanel
        {
            Margin = new Thickness(24, 8, 24, 24),
            Spacing = 16
        };
        contentPanel.Children.Add(CreateSection(
            "Review Snapshot",
            _metaText));
        contentPanel.Children.Add(CreateSection(
            "Focus Apps",
            _topAppsText));
        contentPanel.Children.Add(CreateSection(
            "Draft Output",
            _draftPathText));
        contentPanel.Children.Add(CreateSection(
            "Unified Report",
            _reportText));

        var root = new ScrollViewer();
        root.Content = new StackPanel
        {
            Children =
            {
                headerPanel,
                contentPanel,
            }
        };
        return root;
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e)
    {
        await LoadAsync();
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e)
    {
        await LoadAsync();
    }

    private async void WriteDraft_Click(object sender, RoutedEventArgs e)
    {
        string selectedDate = GetSelectedDate();
        _writeDraftButton.IsEnabled = false;

        try
        {
            var draft = await BackendServices.Client.CreateDailyReviewDraftAsync(selectedDate);
            _latestDraftUrl = draft.ObsidianUrl;
            _draftPathText.Text = draft.Path;
            _openDraftButton.IsEnabled = !string.IsNullOrWhiteSpace(_latestDraftUrl);
            _statusText.Text = $"Daily review draft written for {selectedDate}.";
        }
        catch (Exception ex)
        {
            _statusText.Text = ex.Message;
        }
        finally
        {
            _writeDraftButton.IsEnabled = true;
        }
    }

    private async void OpenDraft_Click(object sender, RoutedEventArgs e)
    {
        if (!string.IsNullOrWhiteSpace(_latestDraftUrl) &&
            Uri.TryCreate(_latestDraftUrl, UriKind.Absolute, out var uri))
        {
            await Launcher.LaunchUriAsync(uri);
        }
    }

    private void OpenSettings_Click(object sender, RoutedEventArgs e)
    {
        NavigationRegistry.Navigate(Frame, "settings");
    }

    private async Task LoadAsync()
    {
        string selectedDate = GetSelectedDate();

        try
        {
            var reportTask = BackendServices.Client.GetDailyReportAsync(selectedDate);
            var healthTask = BackendServices.Client.GetHealthAsync();
            var detectedVaultsTask = BackendServices.Client.GetDetectedObsidianVaultsAsync();
            var draftTask = BackendServices.Client.GetDailyReviewDraftAsync(selectedDate);
            await Task.WhenAll(reportTask, healthTask, detectedVaultsTask, draftTask);

            var report = await reportTask;
            HealthStatus health = await healthTask;
            IReadOnlyList<string> detectedVaults = await detectedVaultsTask;
            NoteDraft? existingDraft = await draftTask;
            bool notesConfigured = !string.IsNullOrWhiteSpace(health.ObsidianVaultRoot);

            _writeDraftButton.IsEnabled = notesConfigured;
            _statusText.Text = notesConfigured
                ? existingDraft is not null
                    ? $"Unified review loaded for {selectedDate}. An existing Obsidian draft is ready to reopen."
                    : $"Unified review loaded for {selectedDate}."
                : detectedVaults.Count > 0
                    ? $"Unified review loaded for {selectedDate}. Obsidian output is not configured yet, but Settings found {detectedVaults.Count} detected vault path(s)."
                    : $"Unified review loaded for {selectedDate}. Configure Obsidian in Settings before writing a draft.";
            _metaText.Text = $"Open tasks in steward pool: {report.OpenTaskCount}";
            _topAppsText.Text = report.TopApps.Count > 0
                ? string.Join(", ", report.TopApps)
                : "No dominant apps captured for this date.";
            _reportText.Text = report.SummaryMarkdown;
            if (!notesConfigured)
            {
                _latestDraftUrl = null;
                _draftPathText.Text = "Draft writing is paused until an Obsidian vault is configured in Settings.";
                _openDraftButton.IsEnabled = false;
            }
            else if (existingDraft is not null)
            {
                _latestDraftUrl = existingDraft.ObsidianUrl;
                _draftPathText.Text = existingDraft.Path;
                _openDraftButton.IsEnabled = !string.IsNullOrWhiteSpace(_latestDraftUrl);
            }
            else
            {
                _latestDraftUrl = null;
                _draftPathText.Text = "No daily review draft exists for this date yet.";
                _openDraftButton.IsEnabled = false;
            }
        }
        catch (Exception ex)
        {
            _statusText.Text = ex.Message;
            _metaText.Text = "Unable to load daily review metadata.";
            _topAppsText.Text = "No focus apps available.";
            _reportText.Text = "Unable to fetch the unified daily report.";
            _draftPathText.Text = "Unable to determine whether an Obsidian draft already exists.";
            _latestDraftUrl = null;
            _openDraftButton.IsEnabled = false;
            _writeDraftButton.IsEnabled = false;
        }
    }

    private string GetSelectedDate()
    {
        return (_datePicker.Date ?? DateTimeOffset.Now).ToString("yyyy-MM-dd");
    }

    private static Border CreateSection(string title, UIElement content)
    {
        var panel = new StackPanel
        {
            Spacing = 8
        };
        panel.Children.Add(new TextBlock
        {
            FontSize = 18,
            FontWeight = FontWeights.SemiBold,
            Text = title
        });
        panel.Children.Add(content);

        return new Border
        {
            Padding = new Thickness(16),
            CornerRadius = new CornerRadius(16),
            BorderThickness = new Thickness(1),
            BorderBrush = new SolidColorBrush(Microsoft.UI.Colors.Gray),
            Child = panel
        };
    }
}
