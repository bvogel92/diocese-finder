#!/bin/bash
# Serves Diocese Finder at http://localhost:8765 and opens it.
# Use this only if your browser refuses location access when you open
# "Diocese Finder.html" directly. Close this Terminal window to stop it.
cd "$(dirname "$0")"
if ! xcode-select -p >/dev/null 2>&1; then
  echo "This needs Apple's Command Line Tools (for python3)."
  echo "Run:  xcode-select --install   then double-click this file again."
  read -n 1 -s -r -p "Press any key to close."; exit 1
fi
cp "Diocese Finder.html" index.html 2>/dev/null
( sleep 1; open "http://localhost:8765/" ) &
exec python3 -m http.server 8765 --bind 127.0.0.1
