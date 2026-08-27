#!/usr/bin/env bash
# Super-Intelligence — Remove Daily Auto-Update Scheduler
set -euo pipefail

REMOVED=false

# systemd
if systemctl --user list-timers 2>/dev/null | grep -q "super-intelligence-update"; then
    systemctl --user stop super-intelligence-update.timer 2>/dev/null || true
    systemctl --user disable super-intelligence-update.timer 2>/dev/null || true
    rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/super-intelligence-update.service"
    rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/super-intelligence-update.timer"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "systemd timer removed."
    REMOVED=true
fi

# launchd
if [ -f "$HOME/Library/LaunchAgents/com.super-intelligence.update.plist" ]; then
    launchctl unload "$HOME/Library/LaunchAgents/com.super-intelligence.update.plist" 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/com.super-intelligence.update.plist"
    echo "launchd plist removed."
    REMOVED=true
fi

# crontab
if crontab -l 2>/dev/null | grep -q "auto-update.sh"; then
    crontab -l 2>/dev/null | grep -v "auto-update.sh" | crontab - 2>/dev/null || true
    echo "crontab entry removed."
    REMOVED=true
fi

if [ "$REMOVED" = false ]; then
    echo "No scheduler found."
fi

echo ""
echo "Note: ~/.super-intelligence/ and update logs remain on disk."
echo "Delete manually if you want to remove all traces."
