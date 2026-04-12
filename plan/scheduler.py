"""Windows Task Scheduler integration via schtasks.exe."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TASK_NAME = "PlanDailyAgent"


def _python_exe() -> str:
    return sys.executable


def _plan_exe() -> str:
    """Return the path to the plan CLI script."""
    scripts = Path(sys.executable).parent / "Scripts" / "plan.exe"
    if scripts.exists():
        return str(scripts)
    # fallback: python -m plan.cli
    return f"{_python_exe()} -m plan.cli"


def install(daily_time: str = "08:00") -> None:
    """Register a daily Task Scheduler entry that runs `plan daily`."""
    import re
    if not re.fullmatch(r"\d{2}:\d{2}", daily_time):
        raise ValueError(f"daily_time must be HH:MM (e.g. '08:00'), got {daily_time!r}")
    hour, minute = daily_time.split(":")
    plan_cmd = _plan_exe()
    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", TASK_NAME,
        "/TR", f"{plan_cmd} daily",
        "/SC", "DAILY",
        "/ST", f"{hour}:{minute}",
        "/RL", "HIGHEST",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"schtasks /Create failed:\n{result.stderr}")


def uninstall() -> None:
    """Remove the Task Scheduler entry."""
    cmd = ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"schtasks /Delete failed:\n{result.stderr}")


def is_installed() -> bool:
    """Return True if the scheduled task exists."""
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True, text=True,
    )
    return result.returncode == 0
