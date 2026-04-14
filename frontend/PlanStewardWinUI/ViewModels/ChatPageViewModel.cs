using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using PlanStewardClient.Models;
using PlanStewardWinUI.Services;

namespace PlanStewardWinUI.ViewModels;

public sealed class ChatPageViewModel
{
    public ChatSession? Session { get; private set; }
    public string StatusText { get; private set; } = "Loading steward conversation context...";
    public bool SendEnabled { get; private set; } = true;

    public async Task LoadSessionAsync(string sessionId)
    {
        try
        {
            string today = DateTime.Now.ToString("yyyy-MM-dd");
            Session = await BackendServices.Client.GetChatSessionAsync(sessionId, today);
            StatusText = "Conversation context synced with the local steward host.";
        }
        catch (Exception ex)
        {
            Session = new ChatSession
            {
                StarterPrompts = ["What should I focus on next?"],
                SuggestedActions = [],
                History =
                [
                    new ChatMessage
                    {
                        Role = "system",
                        Content = "Backend unavailable. Start the steward host and refresh."
                    }
                ]
            };
            StatusText = ex.Message;
        }
    }

    public async Task SendMessageAsync(string sessionId, string message)
    {
        SendEnabled = false;
        try
        {
            Session = await BackendServices.Client.SendChatMessageAsync(sessionId, message);
            StatusText = "Conversation synced with the local steward host.";
        }
        catch (Exception ex)
        {
            Session = new ChatSession
            {
                StarterPrompts = Session?.StarterPrompts ?? [],
                SuggestedActions = [],
                History =
                [
                    new ChatMessage
                    {
                        Role = "system",
                        Content = "Backend unavailable. Start the steward host and try again."
                    }
                ]
            };
            StatusText = ex.Message;
        }
        finally
        {
            SendEnabled = true;
        }
    }

    public async Task<(string summary, ChatSession session)?> ExecuteActionAsync(string sessionId, string actionId)
    {
        SendEnabled = false;
        try
        {
            string today = DateTime.Now.ToString("yyyy-MM-dd");
            ChatActionExecution execution = await BackendServices.Client.ExecuteChatActionAsync(sessionId, actionId, today);
            Session = execution.Session;
            StatusText = execution.Summary;
            return (execution.Summary, execution.Session);
        }
        catch (Exception ex)
        {
            StatusText = ex.Message;
            return null;
        }
        finally
        {
            SendEnabled = true;
        }
    }
}
