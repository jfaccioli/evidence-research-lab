#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.evidence-research-lab.autonomous"
PLIST_SRC="$ROOT/deploy/macos/com.evidence-research-lab.autonomous.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs/autonomous"
chmod +x "$ROOT/scripts/"*.py "$ROOT/scripts/"*.sh 2>/dev/null || true

sed "s|REPO_ROOT_PLACEHOLDER|${ROOT}|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl kickstart -k "gui/$(id -u)/${LABEL}" 2>/dev/null || true

echo "Installed: $PLIST_DST"
echo "Mode: B (24h marathon) + C (watchdog every 1 hour)"
echo "Watchdog starts/restarts marathon if needed"
echo "Logs: $ROOT/logs/autonomous/"
echo "Pause: touch $ROOT/research_kb/rd/AUTONOMOUS_PAUSE"
echo "Marathon state: cat $ROOT/research_kb/rd/MARATHON_STATE.json"
echo "Watchdog status: cat $ROOT/research_kb/rd/WATCHDOG_STATUS.json"
launchctl print "gui/$(id -u)/${LABEL}" 2>/dev/null | grep -E 'interval|state|runs|last exit' | head -12 || true
