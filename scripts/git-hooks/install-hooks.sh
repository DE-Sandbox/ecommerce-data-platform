#!/bin/bash
# Install git hooks

HOOKS_DIR="$(dirname "$0")"
GIT_DIR="$(git rev-parse --git-dir)"

echo "📎 Installing git hooks..."

# Copy all hooks
for hook in "$HOOKS_DIR"/*; do
    if [ -f "$hook" ] && [ "$(basename "$hook")" != "install-hooks.sh" ]; then
        hook_name=$(basename "$hook")
        cp "$hook" "$GIT_DIR/hooks/$hook_name"
        chmod +x "$GIT_DIR/hooks/$hook_name"
        echo "✅ Installed $hook_name"
    fi
done

echo "🎉 Git hooks installed successfully!"
