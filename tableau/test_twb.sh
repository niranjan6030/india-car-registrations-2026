#!/bin/bash
# Open a .twb in Tableau Public; report SCHEMA-FAIL / OTHER-ERROR / OK.
TWB="$1"; LOG="$HOME/Documents/My Tableau Repository/Logs/log.txt"
pkill -x "Tableau Public" 2>/dev/null; sleep 2; : > "$LOG"
open -a "Tableau Public (Apple silicon)" "$TWB"
for i in $(seq 1 30); do
  sleep 1
  code=$(grep -o "errorcode=[a-f0-9]*" "$LOG" 2>/dev/null | head -1 | cut -d= -f2)
  if [ -n "$code" ]; then
    [ "$code" = "d2e8da72" ] && { echo "SCHEMA-FAIL"; pkill -x "Tableau Public"; exit 1; }
    echo "OTHER-ERROR($code)"; pkill -x "Tableau Public"; exit 2
  fi
done
echo "OK"; pkill -x "Tableau Public"; exit 0
