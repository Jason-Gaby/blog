#!/bin/bash

VENV_FILE="$1"
PROJECT_ROOT="$2"
OUTPUT_FILE="$3"

echo "=========================================="
echo "Processing with arguments:"
echo "  Source File: $VENV_FILE"
echo "  Project Root: $PROJECT_ROOT"
echo "  Output File: $OUTPUT_FILE"
echo "=========================================="



source "$VENV_FILE"
export DJANGO_SETTINGS_MODULE=mysite.settings.production
cd "$PROJECT_ROOT"
python manage.py dumpdata --indent 2 > "$OUTPUT_FILE"

echo "✓ Processing complete!"
