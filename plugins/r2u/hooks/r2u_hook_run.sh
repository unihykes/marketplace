#!/usr/bin/env bash
LOG_FILE="$(pwd)/.codex/logs/hooks.log"
EXECUTOR="/usr/bin/python3"
EVENT_NAME="$1"
EVENT_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/r2u_hook_on_${EVENT_NAME}.py"

# echo "[$(date '+%Y-%m-%d %H:%M:%S')] PLUGIN_ROOT=$PLUGIN_ROOT" >> "$LOG_FILE"
# echo "[$(date '+%Y-%m-%d %H:%M:%S')] PLUGIN_DATA=$PLUGIN_DATA" >> "$LOG_FILE"
# echo "[$(date '+%Y-%m-%d %H:%M:%S')] EXECUTOR=$EXECUTOR" >> "$LOG_FILE"

if [ ! -f "$LOG_FILE" ]; then
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] execute $EVENT_SCRIPT" >> "$LOG_FILE"
"$EXECUTOR" "$EVENT_SCRIPT" 2>> "$LOG_FILE"
ERRORLEVEL=$?

if [ $ERRORLEVEL -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] hook failed with exit code $ERRORLEVEL" >> "$LOG_FILE"
fi
