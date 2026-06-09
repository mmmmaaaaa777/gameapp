# 2026-06-09 Verification Notes

## In-app Browser Screenshot Timeout

- Cause: During 375px formation-screen verification, the in-app browser screenshot call timed out at `Page.captureScreenshot`.
- Impact: The screenshot artifact was not captured, but DOM-based layout checks and click verification completed successfully.
- Fix: Continued verification with DOM measurements, the save-button click result, and console-error checks.
- Prevention: Prefer DOM measurements for quick UI placement checks, and retry screenshots only when a visual artifact is required.

## Vite Terminal Mojibake

- Cause: The Vite dev-server log displayed some ANSI/terminal text as mojibake in PowerShell output.
- Impact: The app itself was not affected; lint, tests, build, and browser verification succeeded.
- Fix: No source-code fix was needed.
- Prevention: Use `cmd /c npm ...` for npm commands in this environment and treat terminal banner mojibake as console-output encoding only unless app text is affected.

## PowerShell Multi-path Command Mistake

- Cause: While reviewing all source files, `Get-ChildItem` and `Get-Content` were given multiple paths as plain positional arguments instead of using `-Path` with a comma-separated path list.
- Impact: The review command failed, but no source files were modified and app verification was unaffected.
- Fix: Re-ran the reads with `-Path src,tests,public\assets\equipment` for `Get-ChildItem` and comma-separated paths for `Get-Content`.
- Prevention: Use explicit `-Path` arrays for PowerShell commands that inspect multiple paths.
