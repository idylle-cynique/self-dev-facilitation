#!/bin/bash

# Git hooks installation script
# This script installs the pre-push hook to restrict unwanted branch pushes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing Git hooks..."

# Install pre-push hook
if [ -f "$SCRIPT_DIR/hooks/pre-push" ]; then
    # Backup existing hook if it exists
    if [ -f "$HOOKS_DIR/pre-push" ]; then
        echo "⚠ Existing pre-push hook found"
        TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
        cp "$HOOKS_DIR/pre-push" "$HOOKS_DIR/pre-push.backup.$TIMESTAMP"
        echo "✓ Backed up to pre-push.backup.$TIMESTAMP"
    fi

    cp "$SCRIPT_DIR/hooks/pre-push" "$HOOKS_DIR/pre-push"
    chmod +x "$HOOKS_DIR/pre-push"
    echo "✓ pre-push hook installed"
else
    echo "✗ pre-push hook file not found"
    exit 1
fi

echo "Git hooks installation completed successfully!"
echo ""
echo "The following restrictions are now active:"
echo "  - Direct push to main branch: BLOCKED"
echo "  - PR-based restrictions: ACTIVE (requires GitHub CLI)"
echo ""
echo "Note: GitHub CLI (gh) is required for full functionality."
echo "Install with: brew install gh (macOS) or apt install gh (Linux)"