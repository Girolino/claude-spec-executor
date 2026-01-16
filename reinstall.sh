#!/bin/bash
#
# Reinstall spec-executor plugin for all projects
#
# Usage:
#   ./reinstall.sh          # Reinstall to user scope
#   ./reinstall.sh --dev    # Start Claude with --plugin-dir (dev mode)
#
# Prerequisites:
#   - Marketplace "fernando-plugins" configured pointing to plugins directory
#   - Run: claude plugin marketplace add /path/to/plugins
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="spec-executor"
MARKETPLACE="fernando-plugins"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== spec-executor reinstall ===${NC}"
echo "Plugin source: $SCRIPT_DIR"
echo ""

# Dev mode - just print the command
if [[ "${1:-}" == "--dev" ]]; then
    echo -e "${GREEN}Dev mode: Run Claude with plugin loaded directly from source${NC}"
    echo ""
    echo "  claude --plugin-dir \"$SCRIPT_DIR\""
    echo ""
    echo "Changes to plugin files will take effect on next Claude restart."
    exit 0
fi

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo -e "${RED}Error: 'claude' CLI not found in PATH${NC}"
    echo "Make sure Claude Code is installed and in your PATH."
    exit 1
fi

# Update marketplace to pick up changes
echo "Updating marketplace..."
claude plugin marketplace update "$MARKETPLACE"

# Uninstall existing plugin (ignore errors if not installed)
echo "Removing existing installation..."
claude plugin uninstall "$PLUGIN_NAME" 2>/dev/null || true

# Install from marketplace
echo "Installing from marketplace..."
claude plugin install "${PLUGIN_NAME}@${MARKETPLACE}" --scope user

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "The plugin is now updated for all projects using it."
echo "Restart any active Claude Code sessions to use the new version."
