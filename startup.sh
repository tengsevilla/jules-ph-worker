#!/usr/bin/env bash
# One-time bootstrap script.
#
# Run this ONCE before attaching this repo to Jules to:
#   1. Verify Python version
#   2. Create the `data` branch on the remote
#   3. Install dependencies
#
# After this runs successfully, Jules' daily scheduled task only needs:
#   python main.py
#
# Jules does NOT auto-execute this file. Set up your Jules Initial Setup
# script via: Jules UI → repo → Configuration tab → Initial Setup.
# Enter: pip install -r requirements.txt
set -euo pipefail

echo "========================================"
echo " jules-ph-worker — Philippine News Feed"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"

# --- Python version check ---
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED="3.10"
if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"; then
    echo "ERROR: Python $REQUIRED+ required, found $PYTHON_VERSION" >&2
    exit 1
fi
echo "Python $PYTHON_VERSION OK"

# --- Clean up any stale worktree from a previous failed run ---
if [ -d "_data_wt" ]; then
    echo "Cleaning up stale worktree from previous run..."
    git worktree remove _data_wt --force 2>/dev/null || rm -rf _data_wt
    git worktree prune 2>/dev/null || true
fi

# --- Bootstrap data branch on first run ---
if ! git ls-remote --exit-code --heads origin data > /dev/null 2>&1; then
    echo ""
    echo "First run: bootstrapping data branch..."
    CURRENT_BRANCH=$(git branch --show-current)

    git checkout --orphan data
    git rm -rf . --quiet 2>/dev/null || true

    mkdir -p daily politicians sectors
    echo "# Philippine News Data" > README.md
    echo "Generated daily by jules-ph-worker. See main branch for source." >> README.md

    git add README.md
    git -c user.email="jules-bot@google.com" \
        -c user.name="Jules (automated)" \
        commit -m "init: create data branch"
    git push origin data

    git checkout "$CURRENT_BRANCH"
    echo "Data branch initialized."
fi

# --- Install / update dependencies ---
echo ""
echo "[1/3] Installing dependencies..."
pip install -r requirements.txt --quiet

# --- Run the full pipeline ---
echo ""
echo "[2/3] Running scraper pipeline..."
python main.py

echo ""
echo "[3/3] Complete."
echo "========================================"
