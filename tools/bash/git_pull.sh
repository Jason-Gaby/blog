#!/bin/bash

VENV_FILE="$1"
PROJECT_ROOT="$2"
CONTENT_ROOT="$3"

echo "=========================================="
echo "Processing with arguments:"
echo "  Source File: $VENV_FILE"
echo "  Project Root: $PROJECT_ROOT"
echo "  Content Root: CONTENT_ROOT"
echo "=========================================="


echo "=========================================="
echo "Activating virtual environment:"
source "$VENV_FILE"
echo "Complete."
echo "=========================================="


echo "=========================================="
echo "Pull git for both projects and update for any requirements."
echo "Also install blog content package."
cd "$CONTENT_ROOT"
git pull

cd "$PROJECT_ROOT"
git pull

pip install -e "$CONTENT_ROOT"
echo "Complete."
echo "=========================================="

echo "=========================================="
echo "Restart server:"
sudo systemctl restart gunicorn.service
sleep 1
sudo systemctl status gunicorn.service
echo "=========================================="

echo "✓ Git sync complete!"
