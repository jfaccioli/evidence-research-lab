#!/bin/zsh
set -euo pipefail
LABEL="com.evidence-research-lab.autonomous"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
rm -f "$PLIST_DST"
echo "Removed $LABEL"
