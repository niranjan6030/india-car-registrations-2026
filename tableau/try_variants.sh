#!/bin/bash
# Open a .twbx and report any dialog window Tableau puts up (dialogs are the real
# signal; several failures never reach the log).
TWB="$1"
pkill -x "Tableau Public" 2>/dev/null; sleep 3
open -a "Tableau Public (Apple silicon)" "$TWB"
sleep 32
osascript -e 'tell application "System Events" to tell process "Tableau Public" to get name of every window' 2>/dev/null
