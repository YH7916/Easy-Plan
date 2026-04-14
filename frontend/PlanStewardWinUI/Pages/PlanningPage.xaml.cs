using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using PlanStewardClient.Models;
using PlanStewardWinUI.Controls;
using PlanStewardWinUI.ViewModels;

namespace PlanStewardWinUI.Pages;

public sealed class PlanningPage : Page
{
    private readonly PlanningPageViewModel _vm = new();

    private readonly TextBox _taskTitleBox = new() { PlaceholderText = "Add a steward-managed task" };
    private readonly TextBox _taskProjectBox = new() { PlaceholderText = "Project" };
    private readonly ComboBox _priorityBox = new() { Width = 120, SelectedIndex = 1 };
    private readonly TextBlock _statusText = new() { Opacity = 0.72, TextWrapping = TextWrapping.Wrap };
    private readonly TextBlock _suggestionsStatusText = new() { Opacity = 0.72, TextWrapping = TextWrapping.Wrap };
    private readonly StackPanel _suggestionsPanel = new() { Spacing = 10 };
    private readonly StackPanel _tasksPanel = new() { Spacing = 10 };

    public PlanningPage()
    {
        _priorityBox.Items.Add("0");
        _priorityBox.Items.Add("1");
        _priorityBox.Items.Add("2");
        _priorityBox.Items.Add("3");
        Content = BuildContent();
        Loaded += Page_Loaded;
    }

    private UIElement BuildContent()
    {
        var refreshButton = new AppBarButton { Icon = new SymbolIcon(Symbol.Refresh), Label = "Refresh" };
        refreshButton.Click += Refresh_Click;

        var addButton = new Button { Content = "Add", Margin = new Thickness(8, 0, 0, 0) };
        addButton.Click += AddTask_Click;

        var inputGrid = new Grid { ColumnSpacing = 12 };
        inputGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(3, GridUnitType.Star) });
        inputGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) });
        inputGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        inputGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        Grid.SetColumn(_taskTitleBox, 0);
        Grid.SetColumn(_taskProjectBox, 1);
        Grid.SetColumn(_priorityBox, 2);
        Grid.SetColumn(addButton, 3);
        inputGrid.Children.Add(_taskTitleBox);
        inputGrid.Children.Add(_taskProjectBox);
        inputGrid.Children.Add(_priorityBox);
        inputGrid.Children.Add(addButton);

        var commandBar = new CommandBar { DefaultLabelPosition = CommandBarDefaultLabelPosition.Right };
        commandBar.PrimaryCommands.Add(refreshButton);

        var topPanel = new StackPanel { Margin = new Thickness(24, 24, 24, 8), Spacing = 12 };
        topPanel.Children.Add(commandBar);
        topPanel.Children.Add(inputGrid);
        topPanel.Children.Add(_statusText);

        var root = new Grid();
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        Grid.SetRow(topPanel, 0);
        root.Children.Add(topPanel);

        var scrollViewer = new ScrollViewer { Margin = new Thickness(24, 8, 24, 24), Content = BuildBodyContent() };
        Grid.SetRow(scrollViewer, 1);
        root.Children.Add(scrollViewer);
        return root;
    }

    private UIElement BuildBodyContent()
    {
        var panel = new StackPanel { Spacing = 16 };
        panel.Children.Add(CardFactory.Section(
            "Source Suggestions",
            new StackPanel { Spacing = 10, Children = { _suggestionsStatusText, _suggestionsPanel } }));
        panel.Children.Add(CardFactory.Section(
            "Unified Task Pool",
            _tasksPanel));
        return panel;
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e) => await LoadAndRender();
    private async void Refresh_Click(object sender, RoutedEventArgs e) => await LoadAndRender();

    private async void AddTask_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_taskTitleBox.Text))
        {
            _statusText.Text = "Enter a task title first.";
            return;
        }
        int priority = int.Parse(_priorityBox.SelectedItem?.ToString() ?? "1");
        string? project = string.IsNullOrWhiteSpace(_taskProjectBox.Text) ? null : _taskProjectBox.Text;
        _statusText.Text = await _vm.AddTaskAsync(_taskTitleBox.Text, project, priority);
        _taskTitleBox.Text = string.Empty;
        _taskProjectBox.Text = string.Empty;
        RenderLists();
    }

    private async void CompleteTask_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button button || button.Tag is not string taskId) return;
        _statusText.Text = await _vm.CompleteTaskAsync(taskId);
        RenderLists();
    }

    private async void AcceptSuggestion_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button button || button.Tag is not TaskSuggestion suggestion) return;
        _statusText.Text = await _vm.AcceptSuggestionAsync(suggestion);
        RenderLists();
    }

    private async Task LoadAndRender()
    {
        await _vm.LoadAsync();
        _statusText.Text = _vm.StatusText;
        _suggestionsStatusText.Text = _vm.SuggestionsStatusText;
        RenderLists();
    }

    private void RenderLists()
    {
        _suggestionsPanel.Children.Clear();
        _tasksPanel.Children.Clear();

        foreach (var suggestion in _vm.Suggestions)
        {
            _suggestionsPanel.Children.Add(CreateSuggestionCard(suggestion));
        }

        foreach (var task in _vm.Tasks)
        {
            _tasksPanel.Children.Add(CreateTaskCard(task.Id, task.Title, task.Project, task.Status));
        }

        if (_vm.Tasks.Count == 0)
        {
            _tasksPanel.Children.Add(CardFactory.Placeholder("No tasks tracked yet."));
        }

        if (_vm.StatusText.Contains("unavailable"))
        {
            _suggestionsPanel.Children.Add(CardFactory.Placeholder("Backend unavailable for suggestions."));
            _tasksPanel.Children.Clear();
            _tasksPanel.Children.Add(CardFactory.Placeholder("Backend unavailable for tasks."));
        }
    }

    private Border CreateSuggestionCard(TaskSuggestion suggestion)
    {
        var contentGrid = new Grid { ColumnSpacing = 12 };
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontSize = 18, FontWeight = FontWeights.SemiBold, Text = suggestion.Title, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.72, Text = suggestion.Reason, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Text = $"{suggestion.Source} | {(string.IsNullOrWhiteSpace(suggestion.Project) ? "(no project)" : suggestion.Project)} | priority {suggestion.Priority}" });
        if (!string.IsNullOrWhiteSpace(suggestion.Due))
        {
            infoPanel.Children.Add(new TextBlock { Text = $"Due {suggestion.Due}" });
        }

        var acceptButton = new Button { Content = "Accept", Tag = suggestion };
        acceptButton.Click += AcceptSuggestion_Click;

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(acceptButton, 1);
        contentGrid.Children.Add(infoPanel);
        contentGrid.Children.Add(acceptButton);

        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(8),
            Background = (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"],
            Child = contentGrid
        };
    }

    private Border CreateTaskCard(string taskId, string title, string? project, string status)
    {
        var contentGrid = new Grid { ColumnSpacing = 12 };
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontSize = 18, FontWeight = FontWeights.SemiBold, Text = title, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.72, Text = string.IsNullOrWhiteSpace(project) ? "(no project)" : project });
        infoPanel.Children.Add(new TextBlock { Text = status });

        var completeButton = new Button { Content = "Complete", Tag = taskId };
        completeButton.Click += CompleteTask_Click;

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(completeButton, 1);
        contentGrid.Children.Add(infoPanel);
        contentGrid.Children.Add(completeButton);

        return new Border
        {
            Padding = new Thickness(14),
            Margin = new Thickness(0, 0, 0, 10),
            CornerRadius = new CornerRadius(8),
            Background = (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"],
            Child = contentGrid
        };
    }
}
