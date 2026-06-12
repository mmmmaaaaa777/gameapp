# 2026-06-12 Verification Notes

## Browser Skill Path Lookup Error

- Cause: The cached Browser skill path shown in the Codex session metadata did not exist on disk in this environment.
- Impact: Only the attempt to read that local skill file failed. Source code and app behavior were not affected.
- Fix: Continued verification with the available local tooling instead of relying on that stale cache path.
- Prevention: When plugin cache versions differ, discover available tools dynamically before reading a cached skill path directly.

## PowerShell Source Preview Mojibake

- Cause: Japanese text in UTF-8 CSS displayed as mojibake when previewed with PowerShell `Get-Content` in this session.
- Impact: Terminal preview output was misleading, but the source file itself was valid UTF-8. `rg`, TypeScript, lint, and Vite build all read the strings correctly.
- Fix: Verified the same strings with UTF-8-aware search and build output instead of relying on the PowerShell preview.
- Prevention: Prefer `rg`, browser rendering, or explicit UTF-8 reads when checking Japanese UI strings on Windows PowerShell.
