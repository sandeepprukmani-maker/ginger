#!/bin/bash
# Run NL2Playwright converter

cd "$(dirname "$0")"

# Check if browser-use is available
if ! python3 -c "import browser_use" 2>/dev/null; then
    echo "Installing browser-use dependencies..."
    cd ..
    uv sync --dev --all-extras 2>/dev/null || true
    cd nl2playwright
fi

# Run the main application
export PYTHONPATH="../:$PYTHONPATH"
python3 main.py
