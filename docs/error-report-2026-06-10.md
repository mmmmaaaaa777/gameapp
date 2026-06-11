# 2026-06-10 Verification Notes

## PowerShell Source Preview Mojibake

- Cause: Some Japanese strings displayed as mojibake when inspected through PowerShell command output in this Codex desktop session.
- Impact: The issue was observed in terminal preview output while reading files. The app source remains UTF-8, and user-facing strings touched in this change were re-written as normal Japanese text.
- Fix: Avoided relying on terminal-rendered Japanese for validation and verified source changes through TypeScript, lint, build, tests, and browser rendering.
- Prevention: Prefer app/browser rendering or UTF-8-aware tooling when checking Japanese UI strings in this Windows PowerShell environment.

## Temporary Vite Log Cleanup Command

- Cause: A `Remove-Item -LiteralPath` cleanup command was issued with two comma-separated relative paths, and it did not remove the generated Vite log files in this PowerShell session.
- Impact: The temporary `.vite-v321.*.log` files remained untracked until the cleanup was retried. Source code and verification results were not affected.
- Fix: Removed each generated log file using explicit individual `-LiteralPath` values.
- Prevention: For temporary file cleanup in PowerShell, prefer separate `Remove-Item -LiteralPath` calls or resolve each path before deletion.

## In-app Browser Battle Progress Throttle

- Cause: During v3.2.2 mobile verification, the in-app browser battle loop stopped advancing reliably while the tab was backgrounded. Temporarily showing the browser also reset the viewport to the normal desktop width.
- Impact: Boss selection, sortie prep, and battle HUD were verified at 375px, but reaching the result screen through a full real-time battle was not reliable in that browser session.
- Fix: Verified result data retention through unit tests and verified the visible 375px screens that could be reached deterministically. Reset the browser viewport/visibility after the check.
- Prevention: For long real-time battle verification, keep the browser visible from the start or rely on deterministic tests for result-state retention.
