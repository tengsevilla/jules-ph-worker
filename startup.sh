#!/usr/bin/env bash
# One-time setup script.
#
# Run this ONCE before attaching this repo to Jules to install dependencies.
# After this runs, Jules' daily scheduled task only needs: python main.py
set -euo pipefail

echo "========================================"
echo " jules-ph-worker — Philippine News Feed"
echo " $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "========================================"

# --- Python version check ---
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"; then
    echo "ERROR: Python 3.10+ required, found $PYTHON_VERSION" >&2
    exit 1
fi
echo "Python $PYTHON_VERSION OK"

# --- Install dependencies ---
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "Setup complete. Jules can now run: python main.py"
echo "========================================"
