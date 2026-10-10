#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# NOT PINE CODE — this is a shell script (bash). It is a tool, not a deliverable
# script; the Pine deliverables are cisd-ultimate-proper-v2.pine and
# mx-context-overlay.pine in this folder.
#
# Runs the REAL Pine v6 language service (a TradingView-parity type checker) over .pine files.
# Usage:  bash tools/pine-lint.sh tools/*.pine
# ─────────────────────────────────────────────────────────────────────────────
# Why this exists: `pyne check` (pynescript's ANTLR front-end) validates syntax only. On
# 2026-10-09 it passed a script that TradingView's editor then rejected 63 times, while
# pine-tools - an open-source v6 compiler - reproduced the editor's exact wording (CE10123,
# "cannot apply '==' to array<int> and int") and found all 63 before upload. So this is the
# primary gate. tools/pine-validate.py is the offline fallback for when this clone is missing.
#
# Caveats inherited from the tool's own docs: gotchas/G009 - its --tv mode is NOT the Pine editor
# and skips some editor-only gates on request.*() arguments; gotchas/G010 - RE-class RUNTIME
# errors (invalid ta.* length, out-of-range array.slice) reach neither mode, only the chart
# legend. "clean" here means clean as compiled, not profitable.
set -uo pipefail

CACHE="${PINE_TOOLS_CACHE:-$HOME/pine-tools}"
REPO="https://github.com/folknor/pine-tools.git"
CLI="$CACHE/dist/packages/cli/src/cli.js"

if [ ! -f "$CLI" ]; then
  echo "[pine-lint] building the checker in $CACHE (once, ~30s)..." >&2
  [ -d "$CACHE/.git" ] || git clone -q --depth 1 "$REPO" "$CACHE" >&2 || true
  (
    cd "$CACHE" || exit 1
    # pnpm 9 aborts on this repo's pnpm-workspace.yaml (it has no `packages:` key): it is a
    # single-package repo, so the workspace file is what has to go, not the install.
    [ -f pnpm-workspace.yaml ] && mv pnpm-workspace.yaml pnpm-workspace.yaml.bak
    command -v pnpm >/dev/null || npm i -g pnpm@9 >/dev/null 2>&1 || true
    pnpm install --ignore-scripts >/dev/null 2>&1 || npm install --ignore-scripts >/dev/null 2>&1 || true
    pnpm run build >/dev/null 2>&1 || node scripts/build-extension.js >/dev/null 2>&1 || true
  ) >&2
fi

if [ ! -f "$CLI" ]; then
  echo "[pine-lint] no build available (no network to github/npm?). Falling back to the in-repo checker." >&2
  exec python3 "$(dirname "$0")/pine-validate.py" "$@"
fi

rc=0
for f in "$@"; do
  case "$f" in *.pine) ;; *) continue ;; esac
  node "$CLI" -H "$f" || rc=1
done
if [ "$rc" -eq 0 ]; then echo "[pine-lint] all files clean"; fi
exit $rc
