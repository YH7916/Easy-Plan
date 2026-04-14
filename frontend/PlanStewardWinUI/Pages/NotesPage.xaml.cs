using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using PlanStewardClient.Models;
using PlanStewardWinUI.Controls;
using PlanStewardWinUI.Navigation;
using PlanStewardWinUI.ViewModels;
using Windows.System;

namespace PlanStewardWinUI.Pages;

public sealed class NotesPage : Page
{
    private readonly NotesPageViewModel _vm = new();

    private readonly AppBarButton _openSettingsButton = new()
    {
        Icon = new SymbolIcon(Symbol.Setting),
        Label = "Open Settings"
    };

    private readonly TextBlock _statusText = new()
    {
        Opacity = 0.72,
        Text = "Loading Obsidian index and steward-generated summaries...",
        TextWrapping = TextWrapping.Wrap
    };

    private readonly StackPanel _summaryPanel = new() { Spacing = 12 };
    private readonly StackPanel _generatedNotesPanel = new() { Spacing = 10 };
    private readonly StackPanel _recentNotesPanel = new() { Spacing = 10 };

    public NotesPage()
    {
        Content = BuildContent();
        Loaded += Page_Loaded;
    }

    private UIElement BuildContent()
    {
        var refreshButton = new AppBarButton { Icon = new SymbolIcon(Symbol.Refresh), Label = "Refresh" };
        refreshButton.Click += Refresh_Click;
        _openSettingsButton.Click += OpenSettings_Click;

        var commandBar = new CommandBar { DefaultLabelPosition = CommandBarDefaultLabelPosition.Right };
        commandBar.PrimaryCommands.Add(refreshButton);
        commandBar.PrimaryCommands.Add(_openSettingsButton);

        var headerPanel = new StackPanel { Margin = new Thickness(24, 24, 24, 8), Spacing = 12 };
        headerPanel.Children.Add(commandBar);
        headerPanel.Children.Add(new TextBlock { FontSize = 28, FontWeight = FontWeights.SemiBold, Text = "Notes" });
        headerPanel.Children.Add(_statusText);

        var contentPanel = new StackPanel { Margin = new Thickness(24, 8, 24, 24), Spacing = 16 };
        contentPanel.Children.Add(CardFactory.Section("Vault Snapshot", _summaryPanel));
        contentPanel.Children.Add(CardFactory.Section("Steward Output", _generatedNotesPanel));
        contentPanel.Children.Add(CardFactory.Section("Recent Vault Notes", _recentNotesPanel));

        return new ScrollViewer
        {
            Content = new StackPanel { Children = { headerPanel, contentPanel } }
        };
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e) => await LoadAndRender();
    private async void Refresh_Click(object sender, RoutedEventArgs e) => await LoadAndRender();

    private async void OpenNote_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button &&
            button.Tag is string obsidianUrl &&
            Uri.TryCreate(obsidianUrl, UriKind.Absolute, out var uri))
        {
            await Launcher.LaunchUriAsync(uri);
        }
    }

    private void OpenSettings_Click(object sender, RoutedEventArgs e) => NavigationRegistry.Navigate(Frame, "settings");

    private async Task LoadAndRender()
    {
        await _vm.LoadAsync();
        _statusText.Text = _vm.StatusText;

        _summaryPanel.Children.Clear();
        _generatedNotesPanel.Children.Clear();
        _recentNotesPanel.Children.Clear();

        var dashboard = _vm.Dashboard;
        if (dashboard is null)
        {
            RenderSummaryCards(false, 0, 0, 0);
            _generatedNotesPanel.Children.Add(CardFactory.Placeholder(
                "Unable to load steward outputs — The local steward host is unavailable or returned an unexpected response."));
            _recentNotesPanel.Children.Add(CardFactory.Placeholder(
                "Unable to load recent notes — Start the backend host and refresh this page."));
            return;
        }

        if (!dashboard.VaultReady)
        {
            RenderSummaryCards(false, 0, 0, 0);
            _generatedNotesPanel.Children.Add(CardFactory.Placeholder(
                "No generated summaries available — " + (_vm.DetectedVaults.Count > 0
                    ? "Open Settings, apply one of the detected vaults, then generate a daily review from Insights."
                    : "Configure the Obsidian vault root in backend settings, then generate a daily review from Insights.")));
            _recentNotesPanel.Children.Add(CardFactory.Placeholder(
                "No vault notes indexed — " + (_vm.DetectedVaults.Count > 0
                    ? "Open Settings to finish vault setup. Recent notes will appear here right after the backend reconnects to that vault."
                    : "Once the vault is configured, recent notes will appear here for quick navigation.")));
            return;
        }

        RenderSummaryCards(true, dashboard.IndexedCount, dashboard.GeneratedCount, dashboard.RecentNotes.Count);
        RenderNotesList(_generatedNotesPanel, dashboard.GeneratedNotes,
            "No steward summaries yet", "Generate a daily review in Insights to create the first Obsidian draft.");
        RenderNotesList(_recentNotesPanel, dashboard.RecentNotes,
            "No recent notes available", "The backend could not find any markdown notes to index.");
    }

    private void RenderSummaryCards(bool vaultReady, int indexedCount, int generatedCount, int recentCount)
    {
        _summaryPanel.Children.Clear();
        var grid = new Grid { ColumnSpacing = 16 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        var card0 = CardFactory.Metric("Vault Status", vaultReady ? "Ready" : "Needs Setup");
        var card1 = CardFactory.Metric("Indexed", indexedCount.ToString());
        var card2 = CardFactory.Metric("Generated", generatedCount.ToString());

        Grid.SetColumn(card0, 0);
        Grid.SetColumn(card1, 1);
        Grid.SetColumn(card2, 2);
        grid.Children.Add(card0);
        grid.Children.Add(card1);
        grid.Children.Add(card2);
        _summaryPanel.Children.Add(grid);
    }

    private void RenderNotesList(Panel panel, IReadOnlyList<NoteItem> notes, string emptyTitle, string emptyMessage)
    {
        panel.Children.Clear();
        if (notes.Count == 0)
        {
            panel.Children.Add(CardFactory.Placeholder($"{emptyTitle} — {emptyMessage}"));
            return;
        }
        foreach (NoteItem note in notes)
        {
            panel.Children.Add(CreateNoteCard(note));
        }
    }

    private Border CreateNoteCard(NoteItem note)
    {
        var contentGrid = new Grid { ColumnSpacing = 12 };
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontSize = 16, FontWeight = FontWeights.SemiBold, Text = note.Title, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { FontSize = 14, Opacity = 0.72, Text = FormatModifiedAt(note.ModifiedAt), TextWrapping = TextWrapping.Wrap });

        var openButton = new Button
        {
            Content = "Open In Obsidian",
            Tag = note.ObsidianUrl,
            IsEnabled = !string.IsNullOrWhiteSpace(note.ObsidianUrl),
            VerticalAlignment = VerticalAlignment.Top
        };
        openButton.Click += OpenNote_Click;

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(openButton, 1);
        contentGrid.Children.Add(infoPanel);
        contentGrid.Children.Add(openButton);

        return CardFactory.Card(contentGrid);
    }

    private static string FormatModifiedAt(double modifiedAt)
    {
        if (modifiedAt <= 0) return "Updated time unavailable";
        DateTimeOffset timestamp = DateTimeOffset.FromUnixTimeSeconds((long)Math.Round(modifiedAt));
        return $"Updated {timestamp.ToLocalTime():yyyy-MM-dd HH:mm}";
    }
}
