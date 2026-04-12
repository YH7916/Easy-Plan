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
        summary = "\n\n".join(session_notes)
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
def daily():
    """Run analyze (called by Windows Task Scheduler for daily planning)."""
    ctx = click.get_current_context()
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


if __name__ == "__main__":
    cli()
