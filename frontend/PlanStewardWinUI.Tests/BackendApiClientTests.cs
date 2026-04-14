using System.Net;
using System.Net.Http;
using System.Text;
using PlanStewardClient;
using PlanStewardClient.Models;

namespace PlanStewardWinUI.Tests;

public sealed class BackendApiClientTests
{
    [Fact]
    public async Task GetOverviewSummaryAsync_returns_counts_from_backend()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/overview/summary", request.RequestUri?.AbsolutePath);
                Assert.Equal("?today=2026-04-14", request.RequestUri?.Query);
                return JsonResponse("""
                    {
                      "open_task_count": 3,
                      "high_priority_open_count": 1,
                      "source_item_count": 2,
                      "pending_intake_count": 1,
                      "due_soon_source_count": 1,
                      "overdue_source_count": 0,
                      "notes_indexed_count": 5,
                      "has_daily_report": true,
                      "active_alerts": ["Work review data available"],
                      "daily_brief": "3 open tasks, 1 pending intake item, 1 due soon source item.",
                      "focus_apps": ["VS Code", "Codex"],
                      "recommended_next_actions": [
                        "Review 1 pending source items and accept the ones that should enter planning."
                      ],
                      "recommended_actions": [
                        {
                          "id": "review_intake_queue",
                          "label": "Review Intake Queue",
                          "description": "Open Planning to decide which incoming source items should enter the steward task pool.",
                          "target_page": "planning",
                          "chat_prompt": null,
                          "can_execute": true,
                          "execute_label": "Accept Top Item"
                        },
                        {
                          "id": "sequence_high_priority_tasks",
                          "label": "Sequence High-Priority Work",
                          "description": "Open Chat with a steward prompt to choose the next high-priority task to execute.",
                          "target_page": "chat",
                          "chat_prompt": "Help me sequence my 1 high-priority tasks and choose the next one to execute.",
                          "can_execute": false,
                          "execute_label": null
                        }
                      ]
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        OverviewSummary summary = await client.GetOverviewSummaryAsync("2026-04-14");

        Assert.Equal(3, summary.OpenTaskCount);
        Assert.Equal(1, summary.PendingIntakeCount);
        Assert.True(summary.HasDailyReport);
        Assert.Equal("VS Code", summary.FocusApps[0]);
        Assert.Contains("Review 1 pending source items", summary.RecommendedNextActions[0]);
        Assert.Equal("review_intake_queue", summary.RecommendedActions[0].Id);
        Assert.Equal("chat", summary.RecommendedActions[1].TargetPage);
        Assert.Contains("high-priority tasks", summary.RecommendedActions[1].ChatPrompt);
        Assert.True(summary.RecommendedActions[0].CanExecute);
        Assert.Equal("Accept Top Item", summary.RecommendedActions[0].ExecuteLabel);
        Assert.Contains("Work review data available", summary.ActiveAlerts);
    }

    [Fact]
    public async Task ExecuteOverviewActionAsync_returns_summary_and_generated_draft()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/overview/actions/execute", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "summary": "Daily review draft written for 2026-04-14.",
                      "target_page": "insights",
                      "note_draft": {
                        "path": "D:\\Vault\\Steward\\Daily\\2026-04-14-daily-plan-steward-daily-review-2026-04-14.md",
                        "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CSteward%5CDaily%5C2026-04-14-daily-plan-steward-daily-review-2026-04-14.md"
                      }
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        OverviewActionExecution execution = await client.ExecuteOverviewActionAsync("capture_daily_review", "2026-04-14");

        Assert.Contains("Daily review draft written", execution.Summary);
        Assert.Equal("insights", execution.TargetPage);
        Assert.NotNull(execution.NoteDraft);
        Assert.Contains("2026-04-14-daily", execution.NoteDraft!.Path);
    }

    [Fact]
    public async Task ExecuteOverviewActionAsync_returns_created_task_for_planning_action()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/overview/actions/execute", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "summary": "Accepted \"Lab 3\" into Planning.",
                      "target_page": "planning",
                      "note_draft": null,
                      "created_task": {
                        "id": "task-9",
                        "title": "Lab 3",
                        "project": "courses",
                        "due": "2026-04-15",
                        "priority": 2,
                        "status": "open",
                        "source": "lazy_zju",
                        "ticktick_id": "assignment_42",
                        "time_block": null
                      }
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        OverviewActionExecution execution = await client.ExecuteOverviewActionAsync("review_intake_queue", "2026-04-14");

        Assert.Contains("Accepted", execution.Summary);
        Assert.Equal("planning", execution.TargetPage);
        Assert.Equal("task-9", execution.CreatedTask?.Id);
        Assert.Null(execution.NoteDraft);
    }

    [Fact]
    public async Task Task_lifecycle_calls_planning_endpoints()
    {
        var responses = new Queue<HttpResponseMessage>(new[]
        {
            JsonResponse("""
                {
                  "id": "task-2",
                  "title": "Review adapter",
                  "project": "plan-steward",
                  "due": null,
                  "priority": 2,
                  "status": "open",
                  "source": "local",
                  "ticktick_id": null,
                  "time_block": null
                }
                """, HttpStatusCode.Created),
            JsonResponse("""
                {
                  "id": "task-2",
                  "title": "Review adapter",
                  "project": "plan-steward",
                  "due": null,
                  "priority": 2,
                  "status": "done",
                  "source": "local",
                  "ticktick_id": null,
                  "time_block": null
                }
                """)
        });

        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                if (request.Method == HttpMethod.Post &&
                    request.RequestUri?.AbsolutePath == "/planning/tasks")
                {
                    return responses.Dequeue();
                }

                if (request.Method == HttpMethod.Post &&
                    request.RequestUri?.AbsolutePath == "/planning/tasks/task-2/complete")
                {
                    return responses.Dequeue();
                }

                throw new InvalidOperationException($"Unexpected request {request.Method} {request.RequestUri}");
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        TaskItem created = await client.CreateTaskAsync("Review adapter", "plan-steward", 2);
        TaskItem completed = await client.CompleteTaskAsync("task-2");

        Assert.Equal("task-2", created.Id);
        Assert.Equal("done", completed.Status);
    }

    [Fact]
    public async Task Suggestions_round_trip_calls_planning_suggestion_endpoints()
    {
        var responses = new Queue<HttpResponseMessage>(new[]
        {
            JsonResponse("""
                [
                  {
                    "title": "Lab 3",
                    "source": "lazy_zju",
                    "due": "2026-04-17",
                    "project": "courses",
                    "priority": 2,
                    "external_id": "assignment_42",
                    "reason": "Source item from lazy_zju is not yet tracked in the unified task pool."
                  }
                ]
                """),
            JsonResponse("""
                {
                  "id": "task-3",
                  "title": "Lab 3",
                  "project": "courses",
                  "due": "2026-04-17",
                  "priority": 2,
                  "status": "open",
                  "source": "lazy_zju",
                  "ticktick_id": "assignment_42",
                  "time_block": null
                }
                """, HttpStatusCode.Created)
        });

        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                if (request.Method == HttpMethod.Get &&
                    request.RequestUri?.AbsolutePath == "/planning/suggestions")
                {
                    return responses.Dequeue();
                }

                if (request.Method == HttpMethod.Post &&
                    request.RequestUri?.AbsolutePath == "/planning/suggestions/accept")
                {
                    return responses.Dequeue();
                }

                throw new InvalidOperationException($"Unexpected request {request.Method} {request.RequestUri}");
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        IReadOnlyList<TaskSuggestion> suggestions = await client.GetTaskSuggestionsAsync();
        TaskItem accepted = await client.AcceptTaskSuggestionAsync(suggestions[0]);

        Assert.Single(suggestions);
        Assert.Equal("Lab 3", suggestions[0].Title);
        Assert.Equal("task-3", accepted.Id);
        Assert.Equal("assignment_42", accepted.TickTickId);
    }

    [Fact]
    public async Task SendChatMessageAsync_returns_reply_and_history()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/chat/sessions/default/messages", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "session_id": "default",
                      "reply": "reply:what should I do next?",
                      "starter_prompts": [
                        "What should I focus on next?"
                      ],
                      "suggested_actions": [
                        {
                          "id": "capture_latest_message_as_task",
                          "label": "Capture Latest Request",
                          "description": "Create a planning task from your latest chat request.",
                          "target_module": "planning"
                        }
                      ],
                      "history": [
                        { "role": "user", "content": "what should I do next?" },
                        { "role": "assistant", "content": "reply:what should I do next?" }
                      ]
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        ChatSession session = await client.SendChatMessageAsync("default", "what should I do next?");

        Assert.Equal("reply:what should I do next?", session.Reply);
        Assert.Equal("What should I focus on next?", session.StarterPrompts[0]);
        Assert.Equal("capture_latest_message_as_task", session.SuggestedActions[0].Id);
        Assert.Equal(2, session.History.Count);
    }

    [Fact]
    public async Task GetChatSessionAsync_returns_history_and_starter_prompts()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/chat/sessions/default", request.RequestUri?.AbsolutePath);
                Assert.Equal("?today=2026-04-13", request.RequestUri?.Query);
                return JsonResponse("""
                    {
                      "session_id": "default",
                      "reply": "",
                      "starter_prompts": [
                        "Help me sequence my high-priority tasks.",
                        "What should I focus on next?"
                      ],
                      "suggested_actions": [
                        {
                          "id": "write_daily_review_draft",
                          "label": "Write Today's Review Draft",
                          "description": "Generate today's unified review as an Obsidian draft.",
                          "target_module": "notes"
                        }
                      ],
                      "history": []
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        ChatSession session = await client.GetChatSessionAsync("default", "2026-04-13");

        Assert.Equal("default", session.SessionId);
        Assert.Empty(session.History);
        Assert.Equal(2, session.StarterPrompts.Count);
        Assert.Equal("write_daily_review_draft", session.SuggestedActions[0].Id);
        Assert.Contains("high-priority tasks", session.StarterPrompts[0]);
    }

    [Fact]
    public async Task ExecuteChatActionAsync_returns_summary_session_and_created_entities()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/chat/sessions/default/actions", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "summary": "Added \"Plan next lab deliverable\" to Planning.",
                      "created_task": {
                        "id": "task-5",
                        "title": "Plan next lab deliverable",
                        "project": "steward",
                        "due": null,
                        "priority": 2,
                        "status": "open",
                        "source": "chat",
                        "ticktick_id": null,
                        "time_block": null
                      },
                      "note_draft": null,
                      "session": {
                        "session_id": "default",
                        "reply": "Added \"Plan next lab deliverable\" to Planning.",
                        "starter_prompts": [
                          "What should I focus on next?"
                        ],
                        "suggested_actions": [],
                        "history": [
                          { "role": "user", "content": "plan next lab deliverable" },
                          { "role": "assistant", "content": "reply:plan next lab deliverable" },
                          { "role": "assistant", "content": "Added \"Plan next lab deliverable\" to Planning." }
                        ]
                      }
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        ChatActionExecution execution = await client.ExecuteChatActionAsync("default", "capture_latest_message_as_task");

        Assert.Contains("Planning", execution.Summary);
        Assert.Equal("task-5", execution.CreatedTask?.Id);
        Assert.Null(execution.NoteDraft);
        Assert.Equal(3, execution.Session.History.Count);
    }

    [Fact]
    public async Task GetHealthAsync_returns_backend_module_status()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/settings/health", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "status": "ok",
                      "backend_url": "http://127.0.0.1:8765",
                      "modules": ["overview", "planning", "automation"],
                      "work_review_root": "C:\\Users\\Yohaku\\AppData\\Roaming\\work-review",
                      "obsidian_vault_root": "D:\\Vault"
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        HealthStatus health = await client.GetHealthAsync();

        Assert.Equal("ok", health.Status);
        Assert.Contains("automation", health.Modules);
        Assert.Equal("D:\\Vault", health.ObsidianVaultRoot);
    }

    [Fact]
    public async Task GetSettingsConfigAsync_returns_editable_backend_settings()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/settings/config", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "work_review_root": "C:\\Users\\Yohaku\\AppData\\Roaming\\work-review",
                      "obsidian_vault_root": "D:\\Vault",
                      "obsidian_generated_dir": "Steward\\Daily",
                      "automation_check_in_hours": 4
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        SettingsConfig settings = await client.GetSettingsConfigAsync();

        Assert.Equal("C:\\Users\\Yohaku\\AppData\\Roaming\\work-review", settings.WorkReviewRoot);
        Assert.Equal("D:\\Vault", settings.ObsidianVaultRoot);
        Assert.Equal("Steward\\Daily", settings.ObsidianGeneratedDir);
        Assert.Equal(4, settings.AutomationCheckInHours);
    }

    [Fact]
    public async Task UpdateSettingsConfigAsync_posts_payload_and_returns_reloaded_settings()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/settings/config", request.RequestUri?.AbsolutePath);
                string body = request.Content!.ReadAsStringAsync().Result;
                Assert.Contains("\"work_review_root\":\"C:\\\\Users\\\\Yohaku\\\\AppData\\\\Roaming\\\\work-review\"", body);
                Assert.Contains("\"obsidian_vault_root\":\"D:\\\\Vault\"", body);
                Assert.Contains("\"obsidian_generated_dir\":\"Steward/Daily\"", body);
                Assert.Contains("\"automation_check_in_hours\":4", body);
                return JsonResponse("""
                    {
                      "work_review_root": "C:\\Users\\Yohaku\\AppData\\Roaming\\work-review",
                      "obsidian_vault_root": "D:\\Vault",
                      "obsidian_generated_dir": "Steward/Daily",
                      "automation_check_in_hours": 4
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        SettingsConfig settings = await client.UpdateSettingsConfigAsync(
            new SettingsConfig
            {
                WorkReviewRoot = "C:\\Users\\Yohaku\\AppData\\Roaming\\work-review",
                ObsidianVaultRoot = "D:\\Vault",
                ObsidianGeneratedDir = "Steward/Daily",
                AutomationCheckInHours = 4
            });

        Assert.Equal("D:\\Vault", settings.ObsidianVaultRoot);
        Assert.Equal("Steward/Daily", settings.ObsidianGeneratedDir);
        Assert.Equal(4, settings.AutomationCheckInHours);
    }

    [Fact]
    public async Task GetDetectedObsidianVaultsAsync_returns_detected_paths()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/settings/obsidian/detected-vaults", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    [
                      "D:\\Vault\\Notes\\docs",
                      "D:\\Vault\\Archive"
                    ]
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        IReadOnlyList<string> vaults = await client.GetDetectedObsidianVaultsAsync();

        Assert.Equal(2, vaults.Count);
        Assert.Equal("D:\\Vault\\Notes\\docs", vaults[0]);
    }

    [Fact]
    public async Task UseDetectedObsidianVaultAsync_returns_updated_settings()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/settings/obsidian/use-detected-vault", request.RequestUri?.AbsolutePath);
                string body = request.Content!.ReadAsStringAsync().Result;
                Assert.Contains("\"vault_root\":\"D:\\\\Vault\\\\Notes\\\\docs\"", body);
                return JsonResponse("""
                    {
                      "work_review_root": "C:\\Users\\Yohaku\\AppData\\Roaming\\work-review",
                      "obsidian_vault_root": "D:\\Vault\\Notes\\docs",
                      "obsidian_generated_dir": "Steward/Daily",
                      "automation_check_in_hours": 2
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        SettingsConfig settings = await client.UseDetectedObsidianVaultAsync("D:\\Vault\\Notes\\docs");

        Assert.Equal("D:\\Vault\\Notes\\docs", settings.ObsidianVaultRoot);
        Assert.Equal("Steward/Daily", settings.ObsidianGeneratedDir);
    }

    [Fact]
    public async Task GetNotesDashboardAsync_returns_generated_and_recent_notes()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/notes/dashboard", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "vault_ready": true,
                      "indexed_count": 4,
                      "generated_count": 2,
                      "recent_notes": [
                        {
                          "title": "Plan Steward Daily Review 2026-04-13",
                          "path": "D:\\Vault\\Steward\\Daily\\2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                          "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CSteward%5CDaily%5C2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                          "modified_at": 1776074423
                        },
                        {
                          "title": "Existing Note",
                          "path": "D:\\Vault\\Inbox\\Existing Note.md",
                          "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CInbox%5CExisting%20Note.md",
                          "modified_at": 1776070000
                        }
                      ],
                      "generated_notes": [
                        {
                          "title": "Plan Steward Daily Review 2026-04-13",
                          "path": "D:\\Vault\\Steward\\Daily\\2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                          "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CSteward%5CDaily%5C2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                          "modified_at": 1776074423
                        }
                      ]
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        NotesDashboard dashboard = await client.GetNotesDashboardAsync();

        Assert.True(dashboard.VaultReady);
        Assert.Equal(4, dashboard.IndexedCount);
        Assert.Equal(2, dashboard.GeneratedCount);
        Assert.Equal("Existing Note", dashboard.RecentNotes[1].Title);
        Assert.Single(dashboard.GeneratedNotes);
    }

    [Fact]
    public async Task GetDailyReportAsync_returns_unified_insight_report()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/insights/reports/daily", request.RequestUri?.AbsolutePath);
                Assert.Equal("?date=2026-04-13", request.RequestUri?.Query);
                return JsonResponse("""
                    {
                      "date": "2026-04-13",
                      "summary_markdown": "# Daily Report\n\nUnified summary",
                      "top_apps": ["VS Code", "Codex"],
                      "open_task_count": 4
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        DailyReport report = await client.GetDailyReportAsync("2026-04-13");

        Assert.Equal("2026-04-13", report.Date);
        Assert.Equal(4, report.OpenTaskCount);
        Assert.Equal("VS Code", report.TopApps[0]);
    }

    [Fact]
    public async Task ListEndpoints_return_tasks_sources_and_notes()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                return request.RequestUri?.AbsolutePath switch
                {
                    "/planning/tasks" => JsonResponse("""
                        [
                          {
                            "id": "task-1",
                            "title": "Finish backend host",
                            "project": "plan-steward",
                            "priority": 3,
                            "status": "open",
                            "source": "local",
                            "due": "2026-04-14",
                            "time_block": null
                          }
                        ]
                        """),
                    "/sources/items" => JsonResponse("""
                        [
                          {
                            "title": "Lab 3",
                            "source": "lazy_zju",
                            "due": "2026-04-17",
                            "project": "courses",
                            "priority": 2,
                            "external_id": "assignment_42"
                          }
                        ]
                        """),
                    "/notes/index" => JsonResponse("""
                        {
                          "notes": [
                            {
                              "title": "Existing Note",
                              "path": "D:\\Vault\\Inbox\\Existing Note.md",
                              "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CInbox%5CExisting%20Note.md",
                              "modified_at": 1776000000.0
                            }
                          ]
                        }
                        """),
                    _ => throw new InvalidOperationException($"Unexpected request {request.RequestUri}")
                };
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        IReadOnlyList<TaskItem> tasks = await client.GetTasksAsync();
        IReadOnlyList<SourceItem> sources = await client.GetSourceItemsAsync();
        IReadOnlyList<NoteItem> notes = await client.GetNotesAsync();

        Assert.Single(tasks);
        Assert.Equal("Lab 3", sources[0].Title);
        Assert.Equal("Existing Note", notes[0].Title);
    }

    [Fact]
    public async Task GetSourcesDashboardAsync_returns_tracking_and_urgency_summary()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/sources/dashboard", request.RequestUri?.AbsolutePath);
                Assert.Equal("?today=2026-04-14", request.RequestUri?.Query);
                return JsonResponse("""
                    {
                      "total_count": 2,
                      "tracked_count": 1,
                      "pending_intake_count": 1,
                      "due_soon_count": 1,
                      "overdue_count": 0,
                      "items": [
                        {
                          "title": "Lab 3",
                          "source": "lazy_zju",
                          "due": "2026-04-15",
                          "project": "courses",
                          "priority": 2,
                          "external_id": "assignment_42",
                          "tracking_status": "tracked",
                          "urgency": "due_soon",
                          "tracked_task_status": "open",
                          "recommendation": "Already tracked in planning."
                        },
                        {
                          "title": "HW 4",
                          "source": "lazy_zju",
                          "due": "2026-04-30",
                          "project": "courses",
                          "priority": 0,
                          "external_id": "assignment_99",
                          "tracking_status": "pending_intake",
                          "urgency": "upcoming",
                          "tracked_task_status": null,
                          "recommendation": "Accept into planning to turn this source item into steward-managed work."
                        }
                      ]
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        SourcesDashboard dashboard = await client.GetSourcesDashboardAsync("2026-04-14");

        Assert.Equal(2, dashboard.TotalCount);
        Assert.Equal(1, dashboard.TrackedCount);
        Assert.Equal(1, dashboard.PendingIntakeCount);
        Assert.Equal("tracked", dashboard.Items[0].TrackingStatus);
        Assert.Equal("pending_intake", dashboard.Items[1].TrackingStatus);
    }

    [Fact]
    public async Task GetAutomationStatusAsync_returns_guardrails_and_signals()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/automation/status", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "check_in_hours": 2,
                      "mode_summary": "Active steward mode is monitoring intake pressure, backlog pressure, and review gaps on a 2-hour cadence.",
                      "pending_interventions_count": 3,
                      "guardrails": {
                        "auto_complete": false,
                        "delete_content": false,
                        "overwrite_user_notes": false
                      },
                      "signals": [
                        {
                          "kind": "scheduled_check_in",
                          "summary": "Fixed check-in due every 2 hours.",
                          "guardrails": {
                            "auto_complete": false,
                            "delete_content": false,
                            "overwrite_user_notes": false
                          }
                        },
                        {
                          "kind": "review_gap",
                          "summary": "Today's unified review is missing and should be refreshed.",
                          "guardrails": {
                            "auto_complete": false,
                            "delete_content": false,
                            "overwrite_user_notes": false
                          }
                        }
                      ]
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        AutomationStatus automation = await client.GetAutomationStatusAsync();

        Assert.Equal(2, automation.CheckInHours);
        Assert.Equal(3, automation.PendingInterventionsCount);
        Assert.Contains("2-hour cadence", automation.ModeSummary);
        Assert.False(automation.Guardrails.AutoComplete);
        Assert.Equal("scheduled_check_in", automation.Signals[0].Kind);
        Assert.Equal("review_gap", automation.Signals[1].Kind);
    }

    [Fact]
    public async Task CreateDailyReviewDraftAsync_returns_note_draft_from_backend()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Post, request.Method);
                Assert.Equal("/notes/drafts/daily-review", request.RequestUri?.AbsolutePath);
                return JsonResponse("""
                    {
                      "path": "D:\\Vault\\Steward\\Daily\\2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                      "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CSteward%5CDaily%5C2026-04-13-daily-plan-steward-daily-review-2026-04-13.md"
                    }
                    """, HttpStatusCode.Created);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        NoteDraft draft = await client.CreateDailyReviewDraftAsync("2026-04-13");

        Assert.Contains("2026-04-13-daily-plan-steward-daily-review-2026-04-13.md", draft.Path);
        Assert.StartsWith("obsidian://open", draft.ObsidianUrl);
    }

    [Fact]
    public async Task GetDailyReviewDraftAsync_returns_existing_note_draft_from_backend()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/notes/drafts/daily-review", request.RequestUri?.AbsolutePath);
                Assert.Equal("?date=2026-04-13", request.RequestUri?.Query);
                return JsonResponse("""
                    {
                      "path": "D:\\Vault\\Steward\\Daily\\2026-04-13-daily-plan-steward-daily-review-2026-04-13.md",
                      "obsidian_url": "obsidian://open?path=D%3A%5CVault%5CSteward%5CDaily%5C2026-04-13-daily-plan-steward-daily-review-2026-04-13.md"
                    }
                    """);
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        NoteDraft? draft = await client.GetDailyReviewDraftAsync("2026-04-13");

        Assert.NotNull(draft);
        Assert.Contains("2026-04-13-daily-plan-steward-daily-review-2026-04-13.md", draft!.Path);
        Assert.StartsWith("obsidian://open", draft.ObsidianUrl);
    }

    [Fact]
    public async Task GetDailyReviewDraftAsync_returns_null_when_backend_reports_missing_draft()
    {
        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/notes/drafts/daily-review", request.RequestUri?.AbsolutePath);
                Assert.Equal("?date=2026-04-14", request.RequestUri?.Query);
                return new HttpResponseMessage(HttpStatusCode.NotFound)
                {
                    Content = new StringContent("""{"detail":"Daily review draft not found for 2026-04-14"}""", Encoding.UTF8, "application/json"),
                };
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        NoteDraft? draft = await client.GetDailyReviewDraftAsync("2026-04-14");

        Assert.Null(draft);
    }

    [Fact]
    public async Task SubscribeToEventsAsync_parses_server_sent_events()
    {
        const string eventStream = """
            event: connected
            data: {"message":"connected"}
            
            : keepalive
            
            event: planning.task_created
            data: {
            data:   "title": "Review adapter"
            data: }
            
            """;

        var client = new BackendApiClient(
            new HttpClient(new StubHandler((request) =>
            {
                Assert.Equal(HttpMethod.Get, request.Method);
                Assert.Equal("/events/stream", request.RequestUri?.AbsolutePath);
                return new HttpResponseMessage(HttpStatusCode.OK)
                {
                    Content = new StringContent(eventStream, Encoding.UTF8, "text/event-stream")
                };
            }))
            {
                BaseAddress = new Uri("http://127.0.0.1:8765")
            });

        List<BackendEvent> events = [];
        await foreach (BackendEvent backendEvent in client.SubscribeToEventsAsync())
        {
            events.Add(backendEvent);
        }

        Assert.Equal(2, events.Count);
        Assert.Equal("connected", events[0].EventType);
        Assert.Equal("connected", events[0].Payload.GetProperty("message").GetString());
        Assert.Equal("planning.task_created", events[1].EventType);
        Assert.Equal("Review adapter", events[1].Payload.GetProperty("title").GetString());
    }

    private static HttpResponseMessage JsonResponse(string json, HttpStatusCode statusCode = HttpStatusCode.OK)
    {
        return new HttpResponseMessage(statusCode)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        };
    }

    private sealed class StubHandler(Func<HttpRequestMessage, HttpResponseMessage> responder) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return Task.FromResult(responder(request));
        }
    }
}
