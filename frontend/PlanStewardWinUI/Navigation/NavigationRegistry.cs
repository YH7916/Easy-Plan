using System;
using System.Collections.Generic;
using Microsoft.UI.Xaml.Controls;
using PlanStewardWinUI.Pages;

namespace PlanStewardWinUI.Navigation;

public static class NavigationRegistry
{
    private static readonly Dictionary<string, Type> _pages = new()
    {
        ["home"]     = typeof(HomePage),
        ["sources"]  = typeof(SourcesPage),
        ["planning"] = typeof(PlanningPage),
        ["insights"] = typeof(InsightsPage),
        ["notes"]    = typeof(NotesPage),
        ["chat"]     = typeof(ChatPage),
        ["settings"] = typeof(SettingsPage),
        ["about"]    = typeof(AboutPage),
    };

    public static Type? Resolve(string key) =>
        _pages.TryGetValue(key, out var type) ? type : null;

    public static void Navigate(Frame frame, string key, object? parameter = null)
    {
        var type = Resolve(key);
        if (type is not null)
            frame.Navigate(type, parameter);
    }
}
