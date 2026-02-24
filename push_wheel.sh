#!/usr/bin/env bash
set -e

WHEEL_PATH=$1

echo "📦 Found wheel at: $WHEEL_PATH"

# Find twine (check venv first, then system)
TWINE=""
WORKSPACE_ROOT="${BUILD_WORKSPACE_DIRECTORY:-$(cd "$(dirname "$0")" && git rev-parse --show-toplevel 2>/dev/null || pwd)}"
if [ -x "$WORKSPACE_ROOT/.venv/bin/twine" ]; then
    TWINE="$WORKSPACE_ROOT/.venv/bin/twine"
elif command -v twine &> /dev/null; then
    TWINE="twine"
else
    echo "❌ Error: 'twine' not found. Please install it (pip install twine)."
    exit 1
fi

echo "🚀 Uploading to Cloudsmith via .pypirc config..."
"$TWINE" upload --repository cloudsmith "$WHEEL_PATH"
