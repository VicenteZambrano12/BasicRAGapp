#!/bin/sh
# Point git at the versioned hooks in .githooks/ (run once per clone).
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
echo "core.hooksPath -> .githooks (pre-push tests enabled)."
