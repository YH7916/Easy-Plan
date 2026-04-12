"""CLI entry point."""
from __future__ import annotations

import click
from plan.config import get_config


@click.group()
def cli():
    """AI-powered personal planning agent."""


@cli.command()
def chat():
    """Interactive conversation with AI. Updates context.md after each session."""
    from plan.agent import chat_turn
    from plan.memory import append_context

    click.echo("Starting chat session. Type 'exit' or Ctrl-C to quit.\n")
    history: list[dict] = []
    session_notes: list[str] = []

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip().lower() in ("exit", "quit", "q"):
            break

        reply, history = chat_turn(user_input, history)
        click.echo(f"\nAssistant: {reply}\n")
        session_notes.append(f"User: {user_input}\nAssistant: {reply}")

    if session_notes:
        # Ask Claude to summarize the session into 2-3 sentences before appending
        raw_transcript = "\n\n".join(session_notes)
        try:
            summary_prompt = (
                f"Summarize this planning conversation in 2-3 concise sentences, "
                f"focusing on decisions made, tasks identified, and key insights:\n\n{raw_transcript}"
            )
            summary, _ = chat_turn(summary_prompt, [])
        except Exception:
            # Fallback: use last exchange only to avoid unbounded growth
            summary = session_notes[-1] if session_notes else ""
        append_context(f"Chat session summary:\n{summary}")
        click.echo("Context updated.")


@cli.command()
def analyze():
    """Analyze profile + context + tasks and generate a time-blocked daily plan."""
    from plan.agent import run_analyze
    from plan.config import get_config
    from plan.sources import load_sources
    from plan.tasks import upsert_from_source

    cfg = get_config()
    sources = load_sources(cfg)

    extra_items: list[dict] = []
    for src in sources:
        try:
            items = src.fetch()
            extra_items.extend(i.to_task_dict() for i in items)
            upsert_from_source([i.to_task_dict() for i in items])
            click.echo(f"Fetched {len(items)} items from source: {src.name}")
        except Exception as exc:
            click.echo(f"Warning: source {src.name!r} failed: {exc}", err=True)

    click.echo("Running analysis...")
    tasks = run_analyze(extra_items=extra_items)
    scheduled = [t for t in tasks if t.get("time_block")]
    click.echo(f"Done. {len(scheduled)}/{len(tasks)} tasks scheduled.")
    for t in sorted(scheduled, key=lambda x: x.get("time_block", "")):
        click.echo(f"  {t['time_block']}  {t['title']}")


@cli.command()
def review():
    """Analyze your full situation and generate long-term/monthly/weekly goals."""
    from plan.agent import run_review
    click.echo("Analyzing your situation...")
    goals = run_review()
    click.echo("\n" + goals)
    click.echo("\nGoals saved to data/goals.md")


@cli.command("plan")
def plan_cmd():
    """Generate today's concrete tasks from your goals and context."""
    from plan.agent import run_plan
    click.echo("Generating today's tasks from goals...")
    tasks = run_plan()
    open_tasks = [t for t in tasks if t.get("status") == "open"]
    click.echo(f"Done. {len(open_tasks)} open tasks:")
    for t in sorted(open_tasks, key=lambda x: -x.get("priority", 0)):
        proj = f"  [{t['project']}]" if t.get("project") else ""
        click.echo(f"  {'★' * t.get('priority', 0)}  {t['title']}{proj}")


@cli.command()
def daily():
    """Full daily routine: plan today's tasks then schedule them. (Task Scheduler calls this)"""
    ctx = click.get_current_context()
    ctx.invoke(plan_cmd)
    click.echo()
    ctx.invoke(analyze)


@cli.command()
def status():
    """Print today's plan and context summary."""
    from plan.memory import read_context
    from plan.tasks import list_tasks

    context = read_context()
    tasks = list_tasks(status="open")
    scheduled = [t for t in tasks if t.get("time_block")]

    click.echo("=== Context ===")
    click.echo(context[:500] if context else "(no context)")
    click.echo()
    click.echo(f"=== Today's Schedule ({len(scheduled)} tasks) ===")
    if not scheduled:
        click.echo("  No tasks scheduled. Run `plan analyze` to generate a plan.")
    else:
        for t in sorted(scheduled, key=lambda x: x.get("time_block", "")):
            done_marker = "[x]" if t.get("status") == "done" else "[ ]"
            click.echo(f"  {done_marker} {t['time_block']}  {t['title']}")


@cli.group()
def task():
    """Manage tasks."""


@task.command("add")
@click.argument("title")
@click.option("--project", "-p", default=None, help="Project name")
@click.option("--due", "-d", default=None, help="Due date (YYYY-MM-DD)")
@click.option("--priority", "-P", default=0, type=click.IntRange(0, 3),
              help="Priority 0-3 (0=none, 3=high)")
def task_add(title, project, due, priority):
    """Add a new task."""
    from plan.tasks import add_task
    t = add_task(title, project=project, due=due, priority=priority)
    click.echo(f"Added: [{t['id'][:8]}] {t['title']}")


@task.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include done tasks")
@click.option("--project", "-p", default=None)
def task_list(show_all, project):
    """List tasks."""
    from plan.tasks import list_tasks
    status = None if show_all else "open"
    tasks = list_tasks(status=status, project=project)
    if not tasks:
        click.echo("No tasks.")
        return
    for t in tasks:
        done = "x" if t.get("status") == "done" else " "
        tb = f"  [{t['time_block']}]" if t.get("time_block") else ""
        proj = f"  ({t['project']})" if t.get("project") else ""
        click.echo(f"[{done}] {t['id'][:8]}  {t['title']}{proj}{tb}")


@task.command("done")
@click.argument("task_id_prefix")
def task_done(task_id_prefix):
    """Mark a task as done (by ID prefix)."""
    from plan.tasks import load_tasks, mark_done
    tasks = load_tasks()
    matches = [t for t in tasks if t["id"].startswith(task_id_prefix)]
    if not matches:
        click.echo(f"No task found with ID prefix: {task_id_prefix}", err=True)
        raise SystemExit(1)
    if len(matches) > 1:
        click.echo(f"Ambiguous prefix {task_id_prefix!r} matches {len(matches)} tasks.", err=True)
        raise SystemExit(1)
    result = mark_done(matches[0]["id"])
    click.echo(f"Done: {result['title']}")


@cli.command()
def sync():
    """Bidirectional sync with all writable sources (e.g. TickTick)."""
    from plan.config import get_config
    from plan.sources import load_sources
    from plan.tasks import load_tasks, upsert_from_source

    cfg = get_config()
    sources = load_sources(cfg)
    writable = [s for s in sources if s.is_writable]

    if not writable:
        click.echo("No writable sources enabled. Check config.toml.")
        return

    tasks = load_tasks()
    for src in writable:
        try:
            # Pull
            items = src.fetch()
            upsert_from_source([i.to_task_dict() for i in items])
            click.echo(f"Pulled {len(items)} items from {src.name}")
            # Push
            src.push(tasks)
            click.echo(f"Pushed {len(tasks)} tasks to {src.name}")
        except NotImplementedError:
            click.echo(f"Source {src.name!r} does not support push, skipping.")
        except Exception as exc:
            click.echo(f"Sync error for {src.name!r}: {exc}", err=True)


@cli.group("config")
def config_group():
    """Manage configuration."""


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a config key (dot-separated) to a value.

    Examples:
      plan config set ai.model claude-sonnet-4-6
      plan config set schedule.daily_time 07:30
      plan config set sources.ticktick.enabled true
    """
    from plan.config import set_key

    # Coerce common types
    coerced: object = value
    if value.lower() == "true":
        coerced = True
    elif value.lower() == "false":
        coerced = False
    else:
        try:
            coerced = int(value)
        except ValueError:
            try:
                coerced = float(value)
            except ValueError:
                pass  # keep as string

    set_key(key, coerced)
    click.echo(f"Set {key} = {coerced!r}")


@cli.group()
def schedule():
    """Manage Windows Task Scheduler integration."""


@schedule.command("install")
def schedule_install():
    """Register a daily Task Scheduler entry."""
    from plan.config import get
    from plan.scheduler import install, is_installed

    daily_time = get("schedule.daily_time", "08:00")
    if is_installed():
        click.echo("Task already installed. Reinstalling...")
    install(daily_time)
    click.echo(f"Scheduled daily run at {daily_time}.")


@schedule.command("uninstall")
def schedule_uninstall():
    """Remove the Task Scheduler entry."""
    from plan.scheduler import uninstall, is_installed

    if not is_installed():
        click.echo("Task is not installed.")
        return
    uninstall()
    click.echo("Scheduled task removed.")


if __name__ == "__main__":
    cli()
