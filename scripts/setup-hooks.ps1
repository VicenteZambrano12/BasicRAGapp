#!/usr/bin/env pwsh
# Point git at the versioned hooks in .githooks/ (run once per clone).
$root = git rev-parse --show-toplevel
if (-not $root) { throw "Not inside a git repository." }
Set-Location $root
git config core.hooksPath .githooks
Write-Host "core.hooksPath -> .githooks (pre-push tests enabled)."
