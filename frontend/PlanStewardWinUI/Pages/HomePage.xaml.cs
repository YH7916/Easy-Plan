using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using PlanStewardClient.Models;
using PlanStewardWinUI.Controls;
using PlanStewardWinUI.Navigation;
using PlanStewardWinUI.ViewModels;

namespace PlanStewardWinUI.Pages;

public sealed partial class HomePage : Page
{
    private readonly HomePageViewModel _vm = new();
    private readonly ObservableCollection<string> _nextActions = [];
    private readonly ObservableCollection<string> _focusApps = [];

    public HomePage()
    {
        InitializeComponent();
        NextActionsList.ItemsSource = _nextActions;
        FocusAppsList.ItemsSource = _focusApps;
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e)
    {
        await RefreshAsync();
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e)
    {
        await RefreshAsync();
    }

    private async Task RefreshAsync()
    {
        await _vm.RefreshAsync();

        OpenTaskCountText.Text = _vm.OpenTaskCount;
        HighPriorityCountText.Text = _vm.HighPriorityCount;
        PendingIntakeCountText.Text = _vm.PendingIntakeCount;
        DailyBriefText.Text = _vm.DailyBrief;

        _nextActions.Clear();
        foreach (var action in _vm.NextActions) _nextActions.Add(action);

        _focusApps.Clear();
        foreach (var app in _vm.FocusApps) _focusApps.Add(app);

        RenderRecommendedActions(_vm.RecommendedActions);
    }

    private void RenderRecommendedActions(IReadOnlyList<OverviewAction> actions)
    {
        RecommendedActionsPanel.Children.Clear();
        if (actions.Count == 0)
        {
            RecommendedActionsPanel.Children.Add(new TextBlock
            {
                Opacity = 0.72,
                Text = "No structured handoffs are waiting right now.",
                TextWrapping = TextWrapping.Wrap,
            });
            return;
        }
        foreach (OverviewAction action in actions)
        {
            RecommendedActionsPanel.Children.Add(CreateActionCard(action));
        }
    }

    private Border CreateActionCard(OverviewAction action)
    {
        var grid = new Grid { ColumnSpacing = 12 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontWeight = FontWeights.SemiBold, Text = action.Label, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.72, Text = action.Description, TextWrapping = TextWrapping.Wrap });

        var actionsPanel = new StackPanel { Spacing = 8, VerticalAlignment = VerticalAlignment.Top };
        var openButton = new Button { Content = "Open", Tag = action, VerticalAlignment = VerticalAlignment.Top };
        openButton.Click += OverviewAction_Click;
        actionsPanel.Children.Add(openButton);

        if (action.CanExecute)
        {
            var executeButton = new Button { Content = action.ExecuteLabel ?? "Run", Tag = action, VerticalAlignment = VerticalAlignment.Top };
            executeButton.Click += OverviewActionExecute_Click;
            actionsPanel.Children.Add(executeButton);
        }

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(actionsPanel, 1);
        grid.Children.Add(infoPanel);
        grid.Children.Add(actionsPanel);

        return CardFactory.Card(grid);
    }

    private void OverviewAction_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: OverviewAction action }) return;
        NavigateToTargetPage(action.TargetPage, action.ChatPrompt);
    }

    private async void OverviewActionExecute_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button { Tag: OverviewAction action }) return;
        string today = DateTime.Now.ToString("yyyy-MM-dd");
        var result = await _vm.ExecuteActionAsync(action.Id, today);
        if (result is var (summary, targetPage))
        {
            DailyBriefText.Text = summary;
            await RefreshAsync();
            NavigateToTargetPage(targetPage, action.ChatPrompt);
        }
        else if (_vm.ErrorMessage is not null)
        {
            DailyBriefText.Text = _vm.ErrorMessage;
        }
    }

    private void NavigateToTargetPage(string targetPage, string? chatPrompt)
    {
        NavigationRegistry.Navigate(Frame, targetPage, targetPage == "chat" ? chatPrompt : null);
    }
}
