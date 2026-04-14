using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using PlanStewardClient.Models;
using PlanStewardWinUI.Controls;
using PlanStewardWinUI.ViewModels;

namespace PlanStewardWinUI.Pages;

public sealed class ChatPage : Page
{
    private const string SessionId = "default";

    private readonly ChatPageViewModel _vm = new();

    private readonly StackPanel _messagesPanel = new() { Spacing = 10 };
    private readonly StackPanel _starterPromptsPanel = new() { Spacing = 8 };
    private readonly StackPanel _suggestedActionsPanel = new() { Spacing = 8 };

    private readonly TextBox _chatInputBox = new()
    {
        AcceptsReturn = true,
        PlaceholderText = "Ask the steward what to do next...",
        TextWrapping = TextWrapping.Wrap
    };

    private readonly TextBlock _statusText = new()
    {
        Opacity = 0.72,
        Text = "Loading steward conversation context...",
        TextWrapping = TextWrapping.Wrap
    };

    private readonly Button _sendButton = new() { Content = "Send" };

    private string? _navigationPrompt;

    public ChatPage()
    {
        Content = BuildContent();
        Loaded += Page_Loaded;
    }

    protected override void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        _navigationPrompt = e.Parameter as string;
    }

    private UIElement BuildContent()
    {
        var refreshButton = new AppBarButton { Icon = new SymbolIcon(Symbol.Refresh), Label = "Refresh" };
        refreshButton.Click += Refresh_Click;
        _sendButton.Click += Send_Click;

        var commandBar = new CommandBar { DefaultLabelPosition = CommandBarDefaultLabelPosition.Right };
        commandBar.PrimaryCommands.Add(refreshButton);

        var headerPanel = new StackPanel { Margin = new Thickness(24, 24, 24, 8), Spacing = 12 };
        headerPanel.Children.Add(commandBar);
        headerPanel.Children.Add(new TextBlock { FontSize = 28, FontWeight = FontWeights.SemiBold, Text = "Chat" });
        headerPanel.Children.Add(_statusText);
        headerPanel.Children.Add(CardFactory.Section("Starter Prompts", _starterPromptsPanel));
        headerPanel.Children.Add(CardFactory.Section("Steward Actions", _suggestedActionsPanel));

        var messagesScrollViewer = new ScrollViewer { Margin = new Thickness(24, 8, 24, 12), Content = _messagesPanel };

        var composerGrid = new Grid { Margin = new Thickness(24, 0, 24, 24), ColumnSpacing = 12 };
        composerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        composerGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        Grid.SetColumn(_chatInputBox, 0);
        Grid.SetColumn(_sendButton, 1);
        composerGrid.Children.Add(_chatInputBox);
        composerGrid.Children.Add(_sendButton);

        var root = new Grid();
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        Grid.SetRow(headerPanel, 0);
        Grid.SetRow(messagesScrollViewer, 1);
        Grid.SetRow(composerGrid, 2);
        root.Children.Add(headerPanel);
        root.Children.Add(messagesScrollViewer);
        root.Children.Add(composerGrid);
        return root;
    }

    private async void Page_Loaded(object sender, RoutedEventArgs e)
    {
        await _vm.LoadSessionAsync(SessionId);
        ApplyViewModelState();
        ApplyNavigationPromptIfPresent();
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e)
    {
        await _vm.LoadSessionAsync(SessionId);
        ApplyViewModelState();
    }

    private async void Send_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrWhiteSpace(_chatInputBox.Text)) return;
        string message = _chatInputBox.Text;
        _chatInputBox.Text = string.Empty;
        _sendButton.IsEnabled = false;
        await _vm.SendMessageAsync(SessionId, message);
        ApplyViewModelState();
    }

    private async void StarterPrompt_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string prompt)
        {
            _sendButton.IsEnabled = false;
            await _vm.SendMessageAsync(SessionId, prompt);
            ApplyViewModelState();
        }
    }

    private async void SuggestedAction_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is ChatAction action)
        {
            _sendButton.IsEnabled = false;
            await _vm.ExecuteActionAsync(SessionId, action.Id);
            ApplyViewModelState();
        }
    }

    private void ApplyViewModelState()
    {
        _statusText.Text = _vm.StatusText;
        _sendButton.IsEnabled = _vm.SendEnabled;
        if (_vm.Session is { } session)
        {
            RenderStarterPrompts(session.StarterPrompts);
            RenderSuggestedActions(session.SuggestedActions);
            RenderMessages(session.History);
        }
    }

    private void ApplyNavigationPromptIfPresent()
    {
        if (string.IsNullOrWhiteSpace(_navigationPrompt)) return;
        _chatInputBox.Text = _navigationPrompt;
        _statusText.Text = "Suggested prompt loaded from Overview. Review it or send it as-is.";
        _navigationPrompt = null;
    }

    private void RenderStarterPrompts(IReadOnlyList<string> starterPrompts)
    {
        _starterPromptsPanel.Children.Clear();
        foreach (string prompt in starterPrompts)
        {
            var button = new Button
            {
                Content = prompt,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                HorizontalContentAlignment = HorizontalAlignment.Left,
                Tag = prompt
            };
            button.Click += StarterPrompt_Click;
            _starterPromptsPanel.Children.Add(button);
        }
        if (_starterPromptsPanel.Children.Count == 0)
        {
            _starterPromptsPanel.Children.Add(new TextBlock
            {
                Opacity = 0.72,
                Text = "No starter prompts are available yet.",
                TextWrapping = TextWrapping.Wrap
            });
        }
    }

    private void RenderSuggestedActions(IReadOnlyList<ChatAction> suggestedActions)
    {
        _suggestedActionsPanel.Children.Clear();
        foreach (ChatAction action in suggestedActions)
        {
            _suggestedActionsPanel.Children.Add(CreateActionCard(action));
        }
        if (_suggestedActionsPanel.Children.Count == 0)
        {
            _suggestedActionsPanel.Children.Add(new TextBlock
            {
                Opacity = 0.72,
                Text = "No backend-planned actions are waiting right now.",
                TextWrapping = TextWrapping.Wrap
            });
        }
    }

    private void RenderMessages(IReadOnlyList<ChatMessage> messages)
    {
        _messagesPanel.Children.Clear();
        if (messages.Count == 0)
        {
            _messagesPanel.Children.Add(CreateMessageCard("system", "Start from a steward prompt or write your own request."));
            return;
        }
        foreach (ChatMessage message in messages)
        {
            _messagesPanel.Children.Add(CreateMessageCard(message.Role, message.Content));
        }
    }

    private static Border CreateMessageCard(string role, string content)
    {
        var panel = new StackPanel { Spacing = 4 };
        panel.Children.Add(new TextBlock { FontWeight = FontWeights.SemiBold, Text = role });
        panel.Children.Add(new TextBlock { Text = content, TextWrapping = TextWrapping.Wrap });
        return CardFactory.Card(panel);
    }

    private Border CreateActionCard(ChatAction action)
    {
        var grid = new Grid { ColumnSpacing = 12 };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var infoPanel = new StackPanel { Spacing = 4 };
        infoPanel.Children.Add(new TextBlock { FontWeight = FontWeights.SemiBold, Text = action.Label, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.72, Text = action.Description, TextWrapping = TextWrapping.Wrap });
        infoPanel.Children.Add(new TextBlock { Opacity = 0.64, Text = $"Target module: {action.TargetModule}", TextWrapping = TextWrapping.Wrap });

        var button = new Button { Content = "Run", Tag = action, VerticalAlignment = VerticalAlignment.Top };
        button.Click += SuggestedAction_Click;

        Grid.SetColumn(infoPanel, 0);
        Grid.SetColumn(button, 1);
        grid.Children.Add(infoPanel);
        grid.Children.Add(button);

        return CardFactory.Card(grid);
    }
}
