# 2026-06-05 Error Report

## Start-Process Redirect Error

- Cause: PowerShell `Start-Process` was called with the same file path for `-RedirectStandardOutput` and `-RedirectStandardError`.
- Impact: The Vite dev server did not start during visual verification.
- Fix: Use separate stdout and stderr log files when starting the background dev server.
- Prevention: Keep PowerShell process output streams separated, then inspect both log files if startup fails.
