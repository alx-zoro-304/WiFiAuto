#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/public/downloads"
cp "$ROOT"/tool/*.py "$ROOT"/tool/*.bat "$ROOT"/tool/*.exe "$ROOT"/tool/*.zip "$ROOT/public/downloads/"
cp "$ROOT/version.json" "$ROOT/public/version.json"
echo "Synced tool files + version.json -> public/ (ready for local build)"