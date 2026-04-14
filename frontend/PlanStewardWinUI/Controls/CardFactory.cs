using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

namespace PlanStewardWinUI.Controls;

public static class CardFactory
{
    private static Brush LayerBrush =>
        (Brush)Application.Current.Resources["LayerFillColorDefaultBrush"];

    /// <summary>Section container with title and content.</summary>
    public static Border Section(string title, UIElement content)
    {
        var panel = new StackPanel { Spacing = 8 };
        panel.Children.Add(new TextBlock
        {
            FontSize = 16,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Text = title
        });
        panel.Children.Add(content);
        return new Border
        {
            Padding = new Thickness(16),
            CornerRadius = new CornerRadius(8),
            Background = LayerBrush,
            Child = panel
        };
    }

    /// <summary>Empty state / placeholder card.</summary>
    public static Border Placeholder(string message)
    {
        return new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(8),
            Background = LayerBrush,
            Child = new TextBlock
            {
                Opacity = 0.72,
                Text = message,
                TextWrapping = TextWrapping.Wrap
            }
        };
    }

    /// <summary>Metric card: label + big number.</summary>
    public static Border Metric(string label, string value)
    {
        var panel = new StackPanel { Spacing = 6 };
        panel.Children.Add(new TextBlock { Opacity = 0.68, Text = label });
        panel.Children.Add(new TextBlock
        {
            FontSize = 28,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Text = value
        });
        return new Border
        {
            Padding = new Thickness(16),
            CornerRadius = new CornerRadius(8),
            Background = LayerBrush,
            Child = panel
        };
    }

    /// <summary>Generic content card with background.</summary>
    public static Border Card(UIElement content, double padding = 14)
    {
        return new Border
        {
            Padding = new Thickness(padding),
            CornerRadius = new CornerRadius(8),
            Background = LayerBrush,
            Child = content
        };
    }
}
