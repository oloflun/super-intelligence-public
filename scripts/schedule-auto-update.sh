#!/usr/bin/env bash
# Super-Intelligence — Schedule Daily Auto-Update
# Usage: bash schedule-auto-update.sh <path-to-auto-update.sh>
set -euo pipefail

UPDATE_SCRIPT="${1:-}"
if [ -z "$UPDATE_SCRIPT" ]; then
  echo "Usage: $0 <path-to-auto-update.sh>"
  echo "Example: $0 ~/super-intelligence/scripts/auto-update.sh"
  exit 1
fi

if [ ! -f "$UPDATE_SCRIPT" ]; then
  echo "ERROR: $UPDATE_SCRIPT not found"
  exit 1
fi

chmod +x "$UPDATE_SCRIPT"

echo "Scheduling daily auto-update via: $UPDATE_SCRIPT"
echo ""

# ── Platform detection ────────────────────────────────────────────────────────
if command -v systemctl &>/dev/null && pidof systemd &>/dev/null 2>&1; then
  # === systemd user timer (Linux native, not WSL) ===
  echo "Detected: systemd (user timer)"

  UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  mkdir -p "$UNIT_DIR"

  cat > "$UNIT_DIR/super-intelligence-update.service" << UNITEOF
[Unit]
Description=Super-Intelligence Daily Update Check
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$UPDATE_SCRIPT
StandardOutput=journal
StandardError=journal
UNITEOF

  cat > "$UNIT_DIR/super-intelligence-update.timer" << TIMEREOF
[Unit]
Description=Daily Super-Intelligence Update Check

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=3600

[Install]
WantedBy=timers.target
TIMEREOF

  systemctl --user daemon-reload
  systemctl --user enable --now super-intelligence-update.timer
  echo "✓ systemd user timer installed (daily with 1h random delay)"
  echo "  Check: systemctl --user status super-intelligence-update.timer"

elif [ "$(uname)" = "Darwin" ]; then
  # === launchd (macOS) ===
  echo "Detected: launchd (macOS)"

  PLIST_DIR="$HOME/Library/LaunchAgents"
  mkdir -p "$PLIST_DIR"
  PLIST="$PLIST_DIR/com.super-intelligence.update.plist"

  cat > "$PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.super-intelligence.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>$UPDATE_SCRIPT</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/.super-intelligence/launchd-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.super-intelligence/launchd-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:$HOME/.local/bin</string>
    </dict>
</dict>
</plist>
PLISTEOF

  launchctl load "$PLIST"
  echo "✓ launchd plist installed (daily at 09:00)"
  echo "  Check: launchctl list | grep super-intelligence"

elif [ "$(uname -s)" = "Linux" ] && command -v crontab &>/dev/null; then
  # === crontab fallback (WSL, minimal Linux) ===
  echo "Detected: crontab (WSL / minimal Linux)"

  CRON_LINE="0 9 * * * $UPDATE_SCRIPT"

  # Remove any existing entry for this script, then add
  (crontab -l 2>/dev/null | grep -v "auto-update.sh" || true; echo "$CRON_LINE") | crontab -

  echo "✓ crontab entry installed (daily at 09:00)"
  echo "  Check: crontab -l | grep auto-update"

else
  echo "WARNING: No supported scheduler detected."
  echo "Manual: add '$UPDATE_SCRIPT' to your scheduler daily."
  echo ""
  echo "  crontab -e  →  0 9 * * * $UPDATE_SCRIPT"
  exit 1
fi

echo ""
echo "Logs will be written to: ~/.super-intelligence/update.log"
echo "To disable: edit ~/.super-intelligence/config.json → auto_update: false"
echo "To remove:  bash $(dirname "$0")/remove-auto-update.sh"
