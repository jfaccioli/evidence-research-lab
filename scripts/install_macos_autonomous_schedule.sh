#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.evidence-research-lab.autonomous"
PLIST_SRC="$ROOT/deploy/macos/com.evidence-research-lab.autonomous.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs/autonomous"
chmod +x "$ROOT/scripts/autonomous_research_tick.sh" "$ROOT/scripts/autonomous_research_tick.py"

# Expand repo path into plist
sed "s|REPO_ROOT_PLACEHOLDER|${ROOT}|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true
# Kick once now
launchctl kickstart -k "gui/$(id -u)/${LABEL}" 2>/dev/null || launchctl start "$LABEL" 2>/dev/null || true

echo "Installed: $PLIST_DST"
echo "Interval: every 4 hours (while Mac awake)"
echo "Logs: $ROOT/logs/autonomous/"
echo "Pause: touch $ROOT/research_kb/rd/AUTONOMOUS_PAUSE"
echo "Status: cat $ROOT/research_kb/rd/AUTONOMOUS_TICK_STATUS.json"
launchctl print "gui/$(id -u)/${LABEL}" 2>/dev/null | head -20 || true
