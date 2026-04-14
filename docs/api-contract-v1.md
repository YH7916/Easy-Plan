# Plan Steward Backend API Contract — v1

Version: 1.0.0  
API prefix: `/v1`  
Legacy prefix: `/` (backward compat, will be removed in v2)

## Modules

| Module | Base path |
|--------|-----------|
| Overview | `/v1/overview` |
| Sources | `/v1/sources` |
| Planning | `/v1/planning` |
| Insights | `/v1/insights` |
| Notes | `/v1/notes` |
| Chat | `/v1/chat` |
| Settings | `/v1/settings` |
| Automation | `/v1/automation` |
| Events | `/v1/events` |

## Stability guarantees

- All DTOs in `plan/steward/contracts/` are frozen for v1.
- New fields may be added (additive changes are non-breaking).
- No fields will be removed or renamed in v1.
- Error payloads follow `{"error": str, "message": str, "detail": str|null}`.
- SSE events follow `module.action` naming convention.

## Future macOS client

A macOS client can implement against this contract without changes to the backend.
The only requirement is HTTP + SSE support.
