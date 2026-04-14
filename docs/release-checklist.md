# Plan Steward v1 Release Checklist

## Pre-release

- [ ] All 75+ backend tests pass: `python -m pytest tests/ -q`
- [ ] C# build succeeds: `dotnet build frontend/PlanStewardWinUI/PlanStewardWinUI.csproj`
- [ ] Backend starts: `python -m plan.steward.host`
- [ ] `/health` returns `{"status": "ok"}`
- [ ] WinUI app launches and connects to backend
- [ ] Overview page loads with real data
- [ ] Settings page saves config and hot-reloads adapters
- [ ] Notes page shows vault index (requires Obsidian vault configured)
- [ ] Chat page sends message and receives reply
- [ ] Planning page shows tasks and accepts suggestions

## Build

```bash
# Backend (Python)
pip install -e .

# Frontend (C#)
cd frontend
dotnet build PlanStewardWinUI/PlanStewardWinUI.csproj -c Release -r win-x64
```

## Runtime requirements

- Windows 11 (or Windows 10 22H2+)
- Windows App SDK 1.6+
- Python 3.13+
- Backend running on `http://127.0.0.1:8765` (default)

## Configuration

On first launch, open Settings and configure:
1. Work Review root path
2. Obsidian vault root (optional)
3. Automation check-in cadence

## Known limitations (v1)

- No auto-start: backend must be started manually before launching WinUI
- No code signing: MSIX packaging requires a developer certificate
- Single-user, local-only: no cloud sync
