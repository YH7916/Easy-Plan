using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using PlanStewardClient.Models;
using PlanStewardWinUI.ViewModels;

namespace PlanStewardWinUI.Pages;

public sealed class SourcesPage : Page
{
    private readonly SourcesPageViewModel _vm = new();

    private readonly TextBlock _statusText = new()
    {
        Opacity = 0.72,
        TextWrapping = TextWrapping.Wrap,
        Text = "The backend classifies source items so the shell only renders intake state."
    };

    private readonly TextBlock _totalCountText = CreateMetricValue();
    private readonly TextBlock _pendingCountText = CreateMetricValue();
    private readonly TextBlock _dueSoonCountText = CreateMetricValue();
    private readonly TextBlock _overdueCountText = CreateMetricValue();

    private readonly TextBlock _pendingStatusText = new() { Opacity = 0.72, TextWrapping = TextWrapping.Wrap };
    private readonly TextBlock _trackedStatusText = new() { Opacity = 0.72, TextWrapping = TextWrapping.Wrap };
    private readonly StackPanel _pendingPanel = new() { Spacing = 10 };
    private readonly StackPanel _trackedPanel = new() { Spacing = 10 };

    public SourcesPage()
    {
        Content = BuildContent();
        Loaded += Page_Loaded;
    }

    private UIElement BuildContent()
    {
        var refreshButton = new AppBarButton { Icon = new SymbolIcon(Symbol.Refresh), Label = "Refresh" };
        refreshButton.Click += Refresh_Click;

        var commandBar = new CommandBar { DefaultLabelPosition = CommandBarDefaultLabelPosition.Right };
        commandBar.PrimaryCommands.Add(refreshButton);

        var topPanel = new StackPanel { Margin = new Thickness(24, 24, 24, 8), Spacing = 12 };
        topPanel.Children.Add(commandBar);
        topPanel.Children.Add(new TextBlock { FontSize = 28, FontWeight = FontWeights.SemiBold, Text = "Sources" });
        topPanel.Children.Add(_statusText);
        topPanel.Children.Add(BuildMetricsGrid());

        var bodyPanel = new StackPanel { Margin = new Thickness(24, 8, 24, 24), Spacing = 16 };
        bodyPanel.Children.Add(CreateSection("Needs Intake",
            "These source items are visible to the steward but not yet accepted into the unified task pool.",
            new StackPanel { Spacing = 10, Children = { _pendingStatusText, _pendingPanel } }));
        bodyPanel.Children.Add(CreateSection("Already Tracked",
            "These source items already have a matching steward task, so you can review pressure without duplicating work.",
            new StackPanel { Spacing = 10, Children = { _trackedStatusText, _trackedPanel } }));

        var root = new ScrollViewer();
        root.Content = new StackPanel { Children = { topPanel, bodyPanel } };
        return root;
    }

    private Grid BuildMetricsGrid()
    {
        var grid = new Grid { ColumnSpacing = 12 };
        for (int i = 0; i < 4; i++)
        {
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        }
        AddMetricCard(grid, 0, "Visible Items", _totalCountText);
        AddMetricCard(grid, 1, "Pending Intake", _pendingCountText);
        AddMetricCard(grid, 2, "Due Soon", _dueSoonCountText);
        AddMetricCard(grid, 3, "Overdue", _overdueCountText);
        return grid;
    }

    private static void AddMetricCard(Grid grid, int column, string label, TextBlock valueText)
    {
        var panel = new StackPanel { Spacing = 6 };
        panel.Children.Add(new TextBlock { Opacity = 0.68, Text = label });
        panel.Children.Add(valueText);
        var border = new Border
        {
            Padding = new Thickness(16),
            CornerRadius = new CornerRadius(16),
            Background = (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"],
            Child = panel
        };
        Grid.SetColumn(border, column);
        grid.Children.Add(border);
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e) => await LoadAndRender();
    private async void Refresh_Click(object sender, RoutedEventArgs e) => await LoadAndRender();

    private async void AcceptSuggestion_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button button || button.Tag is not SourcesDashboardItem item) return;
        _statusText.Text = await _vm.AcceptItemAsync(item);
        RenderDashboard();
    }

    private async Task LoadAndRender()
    {
        await _vm.LoadAsync();
        _statusText.Text = _vm.StatusText;
        _pendingStatusText.Text = _vm.PendingStatusText;
        _trackedStatusText.Text = _vm.TrackedStatusText;
        RenderDashboard();
    }

    private void RenderDashboard()
    {
        _pendingPanel.Children.Clear();
        _trackedPanel.Children.Clear();

        var dashboard = _vm.Dashboard;
        if (dashboard is null)
        {
            _totalCountText.Text = "-";
            _pendingCountText.Text = "-";
            _dueSoonCountText.Text = "-";
            _overdueCountText.Text = "-";
            _pendingPanel.Children.Add(CreatePlaceholderCard("Backend unavailable for sources dashboard."));
            _trackedPanel.Children.Add(CreatePlaceholderCard("Backend unavailable for sources dashboard."));
            return;
        }

        _totalCountText.Text = dashboard.TotalCount.ToString();
        _pendingCountText.Text = dashboard.PendingIntakeCount.ToString();
        _dueSoonCountText.Text = dashboard.DueSoonCount.ToString();
        _overdueCountText.Text = dashboard.OverdueCount.ToString();

        foreach (SourcesDashboardItem item in dashboard.Items)
        {
            if (item.TrackingStatus == "pending_intake")
                _pendingPanel.Children.Add(CreateCard(item, actionable: true));
            else
                _trackedPanel.Children.Add(CreateCard(item, actionable: false));
        }

        if (dashboard.PendingIntakeCount == 0)
            _pendingPanel.Children.Add(CreatePlaceholderCard("Everything currently visible is already tracked."));
        if (dashboard.TrackedCount == 0)
            _trackedPanel.Children.Add(CreatePlaceholderCard("Tracked source work will appear here once it has matching tasks."));
    }

    private Border CreateCard(SourcesDashboardItem item, bool actionable)
    {
        var contentGrid = new Grid { ColumnSpacing = 12 };
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontSize = 18, FontWeight = FontWeights.SemiBold, Text = item.Title, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.72, Text = item.Recommendation, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Text = $"{item.Source} | {FormatUrgency(item.Urgency)} | {(string.IsNullOrWhiteSpace(item.Project) ? "(no project)" : item.Project)}" });
        if (!string.IsNullOrWhiteSpace(item.Due))
            infoPanel.Children.Add(new TextBlock { Text = $"Due {item.Due}" });
        if (!string.IsNullOrWhiteSpace(item.TrackedTaskStatus))
            infoPanel.Children.Add(new TextBlock { Text = $"Task status: {item.TrackedTaskStatus}" });

        Grid.SetColumn(infoPanel, 0);
        contentGrid.Children.Add(infoPanel);

        if (actionable)
        {
            var acceptButton = new Button { Content = "Accept", Tag = item };
            acceptButton.Click += AcceptSuggestion_Click;
            Grid.SetColumn(acceptButton, 1);
            contentGrid.Children.Add(acceptButton);
        }

        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(14),
            BorderThickness = new Thickness(1),
            BorderBrush = new SolidColorBrush(Microsoft.UI.Colors.Gray),
            Child = contentGrid
        };
    }

    private static Border CreateSection(string title, string description, UIElement content)
    {
        var panel = new StackPanel { Spacing = 8 };
        panel.Children.Add(new TextBlock { FontSize = 20, FontWeight = FontWeights.SemiBold, Text = title });
        panel.Children.Add(new TextBlock { Opacity = 0.72, Text = description, TextWrapping = TextWrapping.Wrap });
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

    private static Border CreatePlaceholderCard(string message)
    {
        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(14),
            BorderThickness = new Thickness(1),
            BorderBrush = new SolidColorBrush(Microsoft.UI.Colors.Gray),
            Child = new TextBlock { Opacity = 0.72, Text = message, TextWrapping = TextWrapping.Wrap }
        };
    }

    private static TextBlock CreateMetricValue() => new()
    {
        FontSize = 28,
        FontWeight = FontWeights.SemiBold,
        Text = "-"
    };

    private static string FormatUrgency(string urgency) => urgency switch
    {
        "overdue" => "Overdue",
        "due_soon" => "Due soon",
        "upcoming" => "Upcoming",
        "unscheduled" => "Unscheduled",
        _ => urgency,
    };
}
